from typing import Dict, Any, TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents import (
    web_research_agent,
    keyword_intelligence_agent,
    competitor_gap_agent,
    blog_strategy_agent,
    blog_writing_agent,
    seo_agent,
    image_agent,
    quality_agent,
    fact_verification_agent,
)
from app.database import AsyncSessionLocal
from app.config import settings
from app.utils.logger import logger
import operator


class WorkflowState(TypedDict):
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
    regenerate_section: Literal["outline", "blog_content", "seo", "image", "all", None]


class BlogGenerationWorkflow:
    def __init__(self):
        self.graph = None
        self.checkpointer = None

    async def _get_checkpointer(self):
        """Initialize checkpointer for LangGraph (Postgres or Memory)."""
        if self.checkpointer is None:
            try:
                if settings.langgraph_checkpoint_type == "postgres":
                    # Use AsyncPostgresSaver for PostgreSQL-backed state persistence
                    self.checkpointer = AsyncPostgresSaver.from_conn_string(settings.database_sync_url)
                    logger.info("LangGraph checkpointer initialized with AsyncPostgresSaver")
                else:
                    self.checkpointer = MemorySaver()
                    logger.info("LangGraph checkpointer initialized with MemorySaver")
            except Exception as e:
                logger.error(f"Failed to initialize checkpointer: {e}")
                raise
        return self.checkpointer

    async def build_graph(self):
        """Build the LangGraph workflow graph."""
        if self.graph is not None:
            return self.graph

        workflow = StateGraph(WorkflowState)

        # Add nodes for each agent
        workflow.add_node("web_research", self._web_research_node)
        workflow.add_node("keyword_intelligence", self._keyword_intelligence_node)
        workflow.add_node("competitor_gap", self._competitor_gap_node)
        workflow.add_node("blog_strategy", self._blog_strategy_node)
        workflow.add_node("blog_writing", self._blog_writing_node)
        workflow.add_node("seo", self._seo_node)
        workflow.add_node("image", self._image_node)
        workflow.add_node("quality", self._quality_node)
        workflow.add_node("fact_verification", self._fact_verification_node)

        # Add conditional routing nodes
        workflow.add_node("blog_strategy_approval", self._blog_strategy_approval_node)
        workflow.add_node("final_approval", self._final_approval_node)
        workflow.add_node("regenerate_outline", self._regenerate_outline_node)
        workflow.add_node("regenerate_blog", self._regenerate_blog_node)
        workflow.add_node("regenerate_seo", self._regenerate_seo_node)
        workflow.add_node("regenerate_image", self._regenerate_image_node)
        workflow.add_node("regenerate_all", self._regenerate_all_node)

        # Stage 1: Research to Outline
        workflow.set_entry_point("web_research")
        workflow.add_edge("web_research", "keyword_intelligence")
        workflow.add_edge("keyword_intelligence", "competitor_gap")
        workflow.add_edge("competitor_gap", "blog_strategy")

        # Blog Strategy approval checkpoint
        workflow.add_edge("blog_strategy", "blog_strategy_approval")
        workflow.add_conditional_edges(
            "blog_strategy_approval",
            self._check_blog_strategy_approval,
            {
                "approved": "blog_writing",
                "regenerate": "regenerate_outline",
                "pending": END  # Wait for human approval
            }
        )

        # Stage 2: Writing to Final Verification
        workflow.add_edge("blog_writing", "seo")
        workflow.add_edge("seo", "image")
        workflow.add_edge("image", "quality")
        workflow.add_edge("quality", "fact_verification")

        # Final approval checkpoint
        workflow.add_edge("fact_verification", "final_approval")
        workflow.add_conditional_edges(
            "final_approval",
            self._check_final_approval,
            {
                "approved": END,
                "regenerate_outline": "regenerate_outline",
                "regenerate_blog": "regenerate_blog",
                "regenerate_seo": "regenerate_seo",
                "regenerate_image": "regenerate_image",
                "regenerate_all": "regenerate_all",
                "pending": END  # Wait for human approval
            }
        )

        # Regeneration loops back to appropriate stage
        workflow.add_edge("regenerate_outline", "blog_strategy_approval")
        workflow.add_edge("regenerate_blog", "seo")
        workflow.add_edge("regenerate_seo", "image")
        workflow.add_edge("regenerate_image", "quality")
        workflow.add_edge("regenerate_all", "blog_writing")

        # Compile with checkpointer
        checkpointer = await self._get_checkpointer()
        self.graph = workflow.compile(checkpointer=checkpointer)

        logger.info("LangGraph workflow built successfully")
        return self.graph

    async def _web_research_node(self, state: WorkflowState) -> WorkflowState:
        """Execute web research agent."""
        logger.info("Executing web research node")
        result = await web_research_agent.execute(
            topic=state["topic"],
            company_description=state.get("company_description", ""),
        )
        state["research_results"] = result.get("results", [])
        state["current_stage"] = "web_research"
        return state

    async def _keyword_intelligence_node(self, state: WorkflowState) -> WorkflowState:
        """Execute keyword intelligence agent."""
        logger.info("Executing keyword intelligence node")
        result = await keyword_intelligence_agent.execute(
            topic=state["topic"],
            research_results=list(state["research_results"]),
        )
        state["keywords"] = result
        state["current_stage"] = "keyword_intelligence"
        return state

    async def _competitor_gap_node(self, state: WorkflowState) -> WorkflowState:
        """Execute competitor gap agent."""
        logger.info("Executing competitor gap node")
        result = await competitor_gap_agent.execute(
            topic=state["topic"],
            research_results=list(state["research_results"]),
        )
        state["competitor_analysis"] = result
        state["current_stage"] = "competitor_gap"
        return state

    async def _blog_strategy_node(self, state: WorkflowState) -> WorkflowState:
        """Execute blog strategy agent."""
        logger.info("Executing blog strategy node")
        result = await blog_strategy_agent.execute(
            topic=state["topic"],
            target_word_count=state["target_word_count"],
            audience=state["audience"],
            tone=state["tone"],
            keywords=state["keywords"],
            competitor_analysis=state["competitor_analysis"],
        )
        state["outline"] = result
        state["current_stage"] = "blog_strategy"
        state["approval_status"] = "pending"
        state["approval_stage"] = "blog_strategy"
        return state

    async def _blog_writing_node(self, state: WorkflowState) -> WorkflowState:
        """Execute blog writing agent."""
        logger.info("Executing blog writing node")
        result = await blog_writing_agent.execute(
            topic=state["topic"],
            outline=state["outline"].get("outline", []),
            keywords=state["keywords"],
            tone=state["tone"],
            audience=state["audience"],
        )
        state["blog_content"] = result.get("content", "")
        state["current_stage"] = "blog_writing"
        return state

    async def _seo_node(self, state: WorkflowState) -> WorkflowState:
        """Execute SEO agent."""
        logger.info("Executing SEO node")
        result = await seo_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            keywords=state["keywords"],
        )
        state["seo_metadata"] = result
        state["current_stage"] = "seo"
        return state

    async def _image_node(self, state: WorkflowState) -> WorkflowState:
        """Execute image agent."""
        logger.info("Executing image node")
        result = await image_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            tone=state["tone"],
        )
        state["image_details"] = result
        state["current_stage"] = "image"
        return state

    async def _quality_node(self, state: WorkflowState) -> WorkflowState:
        """Execute quality agent."""
        logger.info("Executing quality node")
        result = await quality_agent.execute(content=state["blog_content"])
        state["quality_report"] = result
        state["current_stage"] = "quality"
        return state

    async def _fact_verification_node(self, state: WorkflowState) -> WorkflowState:
        """Execute fact verification agent."""
        logger.info("Executing fact verification node")
        result = await fact_verification_agent.execute(
            content=state["blog_content"],
            research_results=list(state["research_results"]),
        )
        state["fact_verification_report"] = result
        state["current_stage"] = "fact_verification"
        state["approval_status"] = "pending"
        state["approval_stage"] = "final_review"
        return state

    async def _blog_strategy_approval_node(self, state: WorkflowState) -> WorkflowState:
        """Check blog strategy approval status."""
        logger.info(f"Blog strategy approval status: {state.get('approval_status')}")
        state["current_stage"] = "blog_strategy_approval"
        return state

    async def _final_approval_node(self, state: WorkflowState) -> WorkflowState:
        """Check final approval status."""
        logger.info(f"Final approval status: {state.get('approval_status')}")
        state["current_stage"] = "final_approval"
        return state

    def _check_blog_strategy_approval(self, state: WorkflowState) -> str:
        """Determine next step based on blog strategy approval."""
        approval = state.get("approval_status", "pending")
        if approval == "approved":
            return "approved"
        elif approval == "regenerate":
            return "regenerate"
        else:
            return "pending"

    def _check_final_approval(self, state: WorkflowState) -> str:
        """Determine next step based on final approval."""
        approval = state.get("approval_status", "pending")
        if approval == "approved":
            return "approved"
        elif approval == "regenerate":
            regenerate_section = state.get("regenerate_section", "all")
            return f"regenerate_{regenerate_section}"
        else:
            return "pending"

    async def _regenerate_outline_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate outline (either via agent or user edit)."""
        logger.info("Regenerating outline")
        state["current_stage"] = "regenerate_outline"
        # If outline was manually edited, it's already in state
        # Otherwise, regenerate via agent
        if not state.get("outline") or state.get("regenerate_section") == "outline":
            result = await blog_strategy_agent.execute(
                topic=state["topic"],
                target_word_count=state["target_word_count"],
                audience=state["audience"],
                tone=state["tone"],
                keywords=state["keywords"],
                competitor_analysis=state["competitor_analysis"],
            )
            state["outline"] = result
        state["approval_status"] = "pending"
        state["approval_stage"] = "blog_strategy"
        return state

    async def _regenerate_blog_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate blog content."""
        logger.info("Regenerating blog content")
        state["current_stage"] = "regenerate_blog"
        result = await blog_writing_agent.execute(
            topic=state["topic"],
            outline=state["outline"].get("outline", []),
            keywords=state["keywords"],
            tone=state["tone"],
            audience=state["audience"],
        )
        state["blog_content"] = result.get("content", "")
        return state

    async def _regenerate_seo_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate SEO metadata."""
        logger.info("Regenerating SEO metadata")
        state["current_stage"] = "regenerate_seo"
        result = await seo_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            keywords=state["keywords"],
        )
        state["seo_metadata"] = result
        return state

    async def _regenerate_image_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate image."""
        logger.info("Regenerating image")
        state["current_stage"] = "regenerate_image"
        result = await image_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            tone=state["tone"],
        )
        state["image_details"] = result
        return state

    async def _regenerate_all_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate entire blog from outline onwards."""
        logger.info("Regenerating entire blog")
        state["current_stage"] = "regenerate_all"
        # Regenerate blog content
        result = await blog_writing_agent.execute(
            topic=state["topic"],
            outline=state["outline"].get("outline", []),
            keywords=state["keywords"],
            tone=state["tone"],
            audience=state["audience"],
        )
        state["blog_content"] = result.get("content", "")
        # Regenerate SEO
        seo_result = await seo_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            keywords=state["keywords"],
        )
        state["seo_metadata"] = seo_result
        # Regenerate image
        image_result = await image_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            tone=state["tone"],
        )
        state["image_details"] = image_result
        return state

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
        """
        graph = await self.build_graph()

        initial_state: WorkflowState = {
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

    async def resume_workflow(
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
            action: "approve", "reject", or "regenerate"
            updated_outline: User-edited outline (optional)
            regenerate_section: "outline", "blog_content", "seo", "image", or "all"
        """
        graph = await self.build_graph()
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}

        # Build update dict with only the fields that changed
        update_dict = {}
        
        # Update approval status
        if action == "approve":
            update_dict["approval_status"] = "approved"
            logger.info(f"Workflow approved at stage: {current_state.values.get('approval_stage')}")
        elif action == "regenerate":
            update_dict["approval_status"] = "regenerate"
            update_dict["regenerate_section"] = regenerate_section or "all"
            logger.info(f"Workflow regeneration requested for: {regenerate_section}")
        else:
            update_dict["approval_status"] = "rejected"
            logger.info(f"Workflow rejected at stage: {current_state.values.get('approval_stage')}")

        # Update outline if provided
        if updated_outline:
            update_dict["outline"] = updated_outline
            logger.info("Updated outline provided")

        # Update the state in the graph
        await graph.aupdate_state(config, update_dict)

        # Resume execution (pass None to continue from where it was interrupted)
        result = await graph.ainvoke(None, config)
        logger.info(f"Workflow resumed successfully")

        return result

    async def get_workflow_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get the current status of the workflow.
        """
        graph = await self.build_graph()
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}

        state = await graph.aget_state(config)
        current_stage = state.values.get("current_stage", "unknown") if state.values else "not_started"
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
            "next": state.next if state else [],
            "is_complete": state.next == [] if state else False,
            # Include relevant data based on stage
            "outline": state.values.get("outline", {}) if state.values else {},
            "blog_content": state.values.get("blog_content", "") if state.values else "",
            "seo_metadata": state.values.get("seo_metadata", {}) if state.values else {},
            "image_details": state.values.get("image_details", {}) if state.values else {},
            "quality_report": state.values.get("quality_report", {}) if state.values else {},
            "fact_verification_report": state.values.get("fact_verification_report", {}) if state.values else {},
        }


blog_generation_workflow = BlogGenerationWorkflow()
