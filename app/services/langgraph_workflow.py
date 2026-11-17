"""Main workflow orchestration for blog generation."""
from typing import Dict, Any, TypedDict, Sequence, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.database import AsyncSessionLocal
from app.config import settings
from app.services.workflow.graph import build_workflow_graph, WorkflowState
from app.services.workflow.persistence import persist_workflow_output
from app.utils.logger import logger


def _is_transient_connection_error(e: Exception) -> bool:
    """Check if an exception is a transient connection error that warrants retry.

    Returns True for:
    - SQLAlchemy DisconnectionError (connection lost during operation)
    - DBAPIError with connection-related error codes (PostgreSQL-specific)
    - Connection timeout errors
    Returns False for:
    - Validation errors
    - Business logic errors
    - Not found errors
    - Permission errors
    """
    from sqlalchemy.exc import DisconnectionError, DBAPIError
    
    if isinstance(e, DisconnectionError):
        return True

    if isinstance(e, DBAPIError):
        # Check for PostgreSQL connection error codes
        # 08001: connection does not exist
        # 08003: connection not established
        # 08006: connection failure
        # 08007: transaction rollback due to failure
        # 53XXX: all PostgreSQL connection-related errors
        orig = e.orig
        if orig and hasattr(orig, 'pgcode'):
            pgcode = orig.pgcode
            if pgcode in ('08001', '08003', '08006', '08007') or (pgcode and pgcode.startswith('53')):
                return True

    # Check for common connection error messages as fallback
    error_msg = str(e).lower()
    transient_keywords = [
        'connection',
        'timeout',
        'network',
        'broken pipe',
        'connection refused',
        'connection reset',
        'could not connect',
    ]
    return any(keyword in error_msg for keyword in transient_keywords)


class BlogGenerationWorkflowState(TypedDict):
    """Typed state definition for the workflow."""
    project_id: int
    topic: str
    target_word_count: int
    audience: str
    tone: str
    company_description: str
    company_website: str
    research_results: Sequence[Dict[str, Any]]
    keywords: Dict[str, Any]
    competitor_analysis: Dict[str, Any]
    outline: Dict[str, Any]
    blog_content: str
    seo_metadata: Dict[str, Any]
    image_details: Dict[str, Any]
    quality_report: Dict[str, Any]
    fact_verification_report: Dict[str, Any]
    current_stage: str
    error: str
    # Approval fields
    approval_status: Literal["pending", "approved", "rejected", "regenerate"]
    approval_stage: Literal["blog_strategy", "final_review", None]
    regenerate_section: Literal["outline", "blog_content", "seo", "image", "verification", "all", None]
    # When True, LLM calls skip the Redis response cache (set by regenerate nodes)
    bypass_llm_cache: bool
    # ID of the persisted BlogVersion row (set when workflow completes)
    blog_version_id: int
    # Status of persistence to database
    persistence_status: Literal["pending", "success", "failed", None]


class BlogGenerationWorkflow:
    """Orchestrates the blog generation workflow using LangGraph."""
    
    def __init__(self):
        self.graph = None
        self.checkpointer = None
        self._checkpointer_cm = None

    async def _get_checkpointer(self):
        """Initialize checkpointer for LangGraph (Postgres or Memory)."""
        if self.checkpointer is None:
            try:
                if settings.langgraph_checkpoint_type == "postgres":
                    # from_conn_string() returns an async context manager;
                    # enter it once and keep it alive for the app lifetime.
                    self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(settings.database_sync_url)
                    self.checkpointer = await self._checkpointer_cm.__aenter__()
                    await self.checkpointer.setup()
                    logger.info("LangGraph checkpointer initialized with AsyncPostgresSaver")
                else:
                    self.checkpointer = MemorySaver()
                    logger.info("LangGraph checkpointer initialized with MemorySaver")
            except Exception as e:
                logger.error(f"Failed to initialize checkpointer: {e}")
                raise
        return self.checkpointer

    async def _reset_graph(self):
        """Drop the cached graph/checkpointer so fresh DB connections are opened.

        Needed when postgres/redis restart underneath the app: the checkpointer
        holds pooled connections that don't recover on their own.
        """
        if self._checkpointer_cm is not None:
            try:
                await self._checkpointer_cm.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing checkpointer context: {e}")
        self._checkpointer_cm = None
        self.checkpointer = None
        self.graph = None

    async def build_graph(self):
        """Build the LangGraph workflow graph."""
        if self.graph is not None:
            return self.graph

        workflow = StateGraph(BlogGenerationWorkflowState)
        
        # Build graph structure using the extracted function
        workflow = build_workflow_graph(workflow, settings.enable_image_generation)

        # Compile with checkpointer. interrupt_before pauses the graph BEFORE
        # the approval nodes execute, so the thread stays resumable (unlike
        # routing "pending" to END, which terminates the thread).
        checkpointer = await self._get_checkpointer()
        self.graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["blog_strategy_approval", "final_approval"],
        )

        logger.info("LangGraph workflow built successfully")
        return self.graph

    async def _aget_state_with_retry(self, config: Dict[str, Any]):
        """Read graph state, rebuilding graph+checkpointer once on transient connection errors."""
        graph = await self.build_graph()
        try:
            return await graph.aget_state(config)
        except Exception as e:
            if _is_transient_connection_error(e):
                logger.warning(f"aget_state failed with transient connection error ({e}); rebuilding graph/checkpointer")
                await self._reset_graph()
                graph = await self.build_graph()
                return await graph.aget_state(config)
            else:
                # Non-transient error: raise immediately without retry
                raise

    def _validate_start_workflow_input(
        self,
        project_id: int,
        topic: str,
        target_word_count: int,
        audience: str,
        tone: str,
    ) -> None:
        """Validate input parameters for starting a workflow."""
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
        if not topic or not isinstance(topic, str):
            raise ValueError("topic must be a non-empty string")
        if not isinstance(target_word_count, int) or target_word_count <= 0:
            raise ValueError("target_word_count must be a positive integer")
        if audience is not None and not isinstance(audience, str):
            raise ValueError("audience must be a string")
        if tone is not None and not isinstance(tone, str):
            raise ValueError("tone must be a string")

    async def start_workflow(
        self,
        project_id: int,
        topic: str,
        target_word_count: int,
        audience: str,
        tone: str,
        company_description: str = "",
        company_website: str = "",
    ) -> str:
        """
        Start the workflow and return the thread ID.
        
        Args:
            project_id: The project ID to associate with this workflow
            topic: The blog topic
            target_word_count: Target word count for the blog
            audience: Target audience
            tone: Writing tone
            company_description: Optional company description
            company_website: Optional company website
            
        Returns:
            The thread ID for this workflow instance
        """
        # Validate inputs
        self._validate_start_workflow_input(
            project_id, topic, target_word_count, audience, tone
        )
        
        graph = await self.build_graph()

        initial_state: BlogGenerationWorkflowState = {
            "project_id": project_id,
            "topic": topic,
            "target_word_count": target_word_count,
            "audience": audience,
            "tone": tone,
            "company_description": company_description,
            "company_website": company_website,
            "research_results": [],
            "keywords": {},
            "competitor_analysis": {},
            "outline": {},
            "blog_content": "",
            "seo_metadata": {},
            "image_details": {},
            "quality_report": {},
            "fact_verification_report": {},
            "current_stage": "start",
            "error": "",
            "approval_status": "pending",
            "approval_stage": None,
            "regenerate_section": None,
            "bypass_llm_cache": False,
            "blog_version_id": 0,
            "persistence_status": None,
        }

        # Use project_id as thread_id for simplicity
        thread_id = str(project_id)

        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph (will stop at first interrupt)
        try:
            # Invoke the graph asynchronously since nodes are async
            result = await graph.ainvoke(initial_state, config)
            logger.info(f"Workflow started with thread_id: {thread_id}")
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            raise

        logger.info(f"Workflow started with thread_id: {thread_id}")
        return thread_id

    def _validate_resume_workflow_input(
        self,
        project_id: int,
        action: str,
        regenerate_section: str = None,
    ) -> None:
        """Validate input parameters for resuming a workflow."""
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
        
        valid_actions = ["approve", "reject", "regenerate", "retry_persistence"]
        if action not in valid_actions:
            raise ValueError(f"action must be one of {valid_actions}")
        
        if action == "regenerate" and regenerate_section:
            valid_sections = ["outline", "blog_content", "seo", "image", "verification", "all"]
            if regenerate_section not in valid_sections:
                raise ValueError(f"regenerate_section must be one of {valid_sections}")

    async def resume_workflow(
        self,
        project_id: int,
        action: str = "approve",
        updated_outline: Dict[str, Any] = None,
        regenerate_section: str = None,
    ) -> Dict[str, Any]:
        """
        Resume the workflow after approval/rejection.

        Retries once after rebuilding the graph/checkpointer on transient
        connection errors only — covers stale DB connections left behind by
        a postgres restart. Non-transient errors are raised immediately.
        
        Args:
            project_id: Project ID
            action: "approve", "reject", "regenerate", or "retry_persistence"
            updated_outline: User-edited outline (optional)
            regenerate_section: "outline", "blog_content", "seo", "image", "verification", or "all"
            
        Returns:
            The workflow state after resuming
        """
        # Validate inputs
        self._validate_resume_workflow_input(project_id, action, regenerate_section)
        
        try:
            return await self._resume_workflow(project_id, action, updated_outline, regenerate_section)
        except Exception as e:
            if _is_transient_connection_error(e):
                logger.warning(f"resume_workflow failed with transient connection error ({e}); rebuilding graph/checkpointer")
                await self._reset_graph()
                return await self._resume_workflow(project_id, action, updated_outline, regenerate_section)
            else:
                # Non-transient error: raise immediately without retry
                raise

    async def _resume_workflow(
        self,
        project_id: int,
        action: str = "approve",
        updated_outline: Dict[str, Any] = None,
        regenerate_section: str = None,
    ) -> Dict[str, Any]:
        """
        Resume the workflow after approval/rejection.

        Args:
            project_id: Project ID
            action: "approve", "reject", "regenerate", or "retry_persistence"
            updated_outline: User-edited outline (optional)
            regenerate_section: "outline", "blog_content", "seo", "image", "verification", or "all"
        """
        graph = await self.build_graph()
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}

        # Handle retry_persistence action separately
        if action == "retry_persistence":
            return await self._retry_persistence(graph, config)

        # Build update dict with only the fields that changed
        update_dict = {}
        current_state = await graph.aget_state(config)
        current_stage = current_state.values.get("approval_stage") if current_state.values else None

        # Update approval status
        if action == "approve":
            update_dict["approval_status"] = "approved"
            logger.info(f"Workflow approved at stage: {current_stage}")
        elif action == "regenerate":
            update_dict["approval_status"] = "regenerate"
            update_dict["regenerate_section"] = regenerate_section or "all"
            logger.info(f"Workflow regeneration requested for: {regenerate_section}")
        else:
            update_dict["approval_status"] = "rejected"
            logger.info(f"Workflow rejected at stage: {current_stage}")

        # Update outline if provided
        if updated_outline:
            update_dict["outline"] = updated_outline
            logger.info("Updated outline provided")

        # Update the state in the graph
        await graph.aupdate_state(config, update_dict)

        # Resume execution (pass None to continue from where it was interrupted)
        result = await graph.ainvoke(None, config)
        logger.info(f"Workflow resumed successfully")

        # If the graph ran to completion with an approval, persist outputs to DB
        final_state = await graph.aget_state(config)
        if (
            final_state.values
            and len(final_state.next) == 0
            and final_state.values.get("approval_status") == "approved"
        ):
            try:
                async with AsyncSessionLocal() as db:
                    blog_version_id = await persist_workflow_output(db, final_state.values)
                    if blog_version_id:
                        await graph.aupdate_state(config, {"blog_version_id": blog_version_id, "persistence_status": "success"})
                    else:
                        await graph.aupdate_state(config, {"persistence_status": "failed"})
                        raise Exception("Persistence returned zero blog_version_id")
            except Exception as e:
                logger.error(f"Failed to persist workflow output: {e}")
                await graph.aupdate_state(config, {"persistence_status": "failed"})
                raise

        return result

    async def _retry_persistence(self, graph, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retry persistence of workflow output without regenerating content.

        Used when the initial persistence attempt failed but content is available.
        """
        logger.info("Retrying workflow output persistence")
        current_state = await graph.aget_state(config)

        if not current_state.values:
            raise Exception("No workflow state found for retry")

        # Check if we have the necessary data to persist
        if not current_state.values.get("blog_content"):
            raise Exception("No blog content available to persist")

        try:
            async with AsyncSessionLocal() as db:
                blog_version_id = await persist_workflow_output(db, current_state.values)
                if blog_version_id:
                    await graph.aupdate_state(config, {"blog_version_id": blog_version_id, "persistence_status": "success"})
                    logger.info(f"Retry persistence successful: blog_version_id={blog_version_id}")
                else:
                    await graph.aupdate_state(config, {"persistence_status": "failed"})
                    raise Exception("Retry persistence returned zero blog_version_id")
        except Exception as e:
            logger.error(f"Retry persistence failed: {e}")
            await graph.aupdate_state(config, {"persistence_status": "failed"})
            raise

        return {"current_stage": "final_approval", "persistence_status": "success"}

    async def reset_workflow(self, project_id: int) -> None:
        """Delete checkpointed state for a project so the workflow restarts from scratch."""
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
            
        try:
            checkpointer = await self._get_checkpointer()
            await checkpointer.adelete_thread(str(project_id))
            logger.info(f"Cleared workflow checkpoint for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to clear workflow checkpoint for project {project_id}: {e}")

    async def get_workflow_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get the current status of the workflow.
        
        Args:
            project_id: The project ID to query
            
        Returns:
            Dictionary containing workflow status information
        """
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer")
            
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}

        state = await self._aget_state_with_retry(config)
        current_stage = state.values.get("current_stage", "unknown") if state.values else "not_started"
        # While interrupted before an approval node, current_stage still shows
        # the last executed node — report the gate the workflow is paused at.
        next_nodes = state.next if state else []
        if "blog_strategy_approval" in next_nodes:
            current_stage = "blog_strategy_approval"
        elif "final_approval" in next_nodes:
            current_stage = "final_approval"
        approval_status = state.values.get("approval_status", "none") if state.values else "none"
        approval_stage = state.values.get("approval_stage", None) if state.values else None
        
        # Determine if waiting for approval
        is_waiting_approval = approval_status == "pending" and approval_stage is not None
        
        return {
            "project_id": project_id,
            "current_stage": current_stage,
            "approval_status": approval_status,
            "approval_stage": approval_stage,
            "is_waiting_approval": is_waiting_approval,
            "next": next_nodes,
            # state.next is a tuple; () means the graph ran to END
            "is_complete": len(next_nodes) == 0,
            # Include relevant data based on stage
            "outline": state.values.get("outline", {}) if state.values else {},
            "blog_content": state.values.get("blog_content", "") if state.values else "",
            "seo_metadata": state.values.get("seo_metadata", {}) if state.values else {},
            "image_details": state.values.get("image_details", {}) if state.values else {},
            "quality_report": state.values.get("quality_report", {}) if state.values else {},
            "fact_verification_report": state.values.get("fact_verification_report", {}) if state.values else {},
            "image_generation_enabled": settings.enable_image_generation,
            "blog_version_id": state.values.get("blog_version_id", 0) if state.values else 0,
            "persistence_status": state.values.get("persistence_status", None) if state.values else None,
        }


blog_generation_workflow = BlogGenerationWorkflow()
