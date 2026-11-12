from typing import Dict, Any, TypedDict, Sequence, Literal
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
from app.models import (
    Outline,
    BlogVersion,
    SEOMetadata,
    ImageGeneration,
    QualityReport,
    FactVerificationReport,
    Approval,
)
from app.models.outline import OutlineStatus
from app.models.blog import BlogStatus
from app.models.approval import ApprovalStage, ApprovalStatus
from sqlalchemy import select, delete
from datetime import datetime
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
    regenerate_section: Literal["outline", "blog_content", "seo", "image", "verification", "all", None]
    # When True, LLM calls skip the Redis response cache (set by regenerate nodes)
    bypass_llm_cache: bool
    # ID of the persisted BlogVersion row (set when workflow completes)
    blog_version_id: int


class BlogGenerationWorkflow:
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

        workflow = StateGraph(WorkflowState)

        # Add nodes for each agent
        workflow.add_node("web_research", self._web_research_node)
        workflow.add_node("keyword_intelligence", self._keyword_intelligence_node)
        workflow.add_node("competitor_gap", self._competitor_gap_node)
        workflow.add_node("blog_strategy", self._blog_strategy_node)
        workflow.add_node("blog_writing", self._blog_writing_node)
        workflow.add_node("seo", self._seo_node)
        # workflow.add_node("image", self._image_node) # uncomment when api is available
        workflow.add_node("quality", self._quality_node)
        workflow.add_node("fact_verification", self._fact_verification_node)

        # Add conditional routing nodes
        workflow.add_node("blog_strategy_approval", self._blog_strategy_approval_node)
        workflow.add_node("final_approval", self._final_approval_node)
        workflow.add_node("regenerate_outline", self._regenerate_outline_node)
        workflow.add_node("regenerate_seo", self._regenerate_seo_node)
        # workflow.add_node("regenerate_image", self._regenerate_image_node) # uncomment when api is available
        workflow.add_node("regenerate_all", self._regenerate_all_node)
        workflow.add_node("regenerate_verification", self._regenerate_verification_node)

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
        # workflow.add_edge("seo", "image")
        workflow.add_edge("seo", "quality")
        workflow.add_edge("quality", "fact_verification")

        # Final approval checkpoint
        workflow.add_edge("fact_verification", "final_approval")
        workflow.add_conditional_edges(
            "final_approval",
            self._check_final_approval,
            {
                "approved": END,
                "regenerate_outline": "regenerate_outline",
                "regenerate_seo": "regenerate_seo",
                # "regenerate_image": "regenerate_image",
                "regenerate_verification": "regenerate_verification",
                "regenerate_all": "regenerate_all",
                "pending": END  # Wait for human approval
            }
        )

        # Regeneration loops: each re-runs only its own node, then returns to
        # the final approval checkpoint. State (outline, content, keywords,
        # research) is read from the checkpoint — nothing upstream re-runs.
        workflow.add_edge("regenerate_seo", "final_approval")
        # workflow.add_edge("regenerate_image", "final_approval")
        workflow.add_edge("regenerate_verification", "fact_verification")
        # regenerate_all already produces blog+seo+image; continue to quality
        # and fact verification so reports stay consistent (avoids re-running
        # blog_writing/seo/image a second time).
        workflow.add_edge("regenerate_all", "quality")

        # Regenerate outline is reachable from both approval checkpoints and
        # always returns to the first approval gate: a new outline invalidates
        # any downstream content, so the user must approve the outline again
        # before blog content, SEO, etc. are generated.
        workflow.add_edge("regenerate_outline", "blog_strategy_approval")

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
        """Read graph state, rebuilding graph+checkpointer once on stale-connection errors."""
        graph = await self.build_graph()
        try:
            return await graph.aget_state(config)
        except Exception as e:
            logger.warning(f"aget_state failed ({e}); rebuilding graph/checkpointer")
            await self._reset_graph()
            graph = await self.build_graph()
            return await graph.aget_state(config)

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
            use_cache=not state.get("bypass_llm_cache", False),
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
            target_word_count=state["target_word_count"],
            use_cache=not state.get("bypass_llm_cache", False),
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
            use_cache=not state.get("bypass_llm_cache", False),
        )
        state["seo_metadata"] = result
        state["current_stage"] = "seo"
        return state

    async def _image_node(self, state: WorkflowState) -> WorkflowState:
        """Execute image agent."""
        if not settings.enable_image_generation:
            logger.info("Image generation is disabled, skipping")
            state["current_stage"] = "image"
            state["image_details"] = {}
            return state
        logger.info("Executing image node")
        result = await image_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            tone=state["tone"],
            use_cache=not state.get("bypass_llm_cache", False),
        )
        state["image_details"] = result
        state["current_stage"] = "image"
        return state

    async def _quality_node(self, state: WorkflowState) -> WorkflowState:
        """Execute quality agent."""
        logger.info("Executing quality node")
        result = await quality_agent.execute(
            content=state["blog_content"],
            use_cache=not state.get("bypass_llm_cache", False),
        )
        state["quality_report"] = result
        state["current_stage"] = "quality"
        return state

    async def _fact_verification_node(self, state: WorkflowState) -> WorkflowState:
        """Execute fact verification agent."""
        logger.info("Executing fact verification node")
        result = await fact_verification_agent.execute(
            content=state["blog_content"],
            research_results=list(state["research_results"]),
            use_cache=not state.get("bypass_llm_cache", False),
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
            # Blog content feeds SEO, image, quality and fact verification —
            # regenerating it requires regenerating everything downstream.
            if regenerate_section in ("blog_content", "blog"):
                regenerate_section = "all"
            return f"regenerate_{regenerate_section}"
        else:
            return "pending"

    async def _regenerate_outline_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate the outline via the blog strategy agent."""
        logger.info("Regenerating outline")
        state["current_stage"] = "regenerate_outline"
        # User asked for fresh content — bypass the LLM response cache so a
        # repeated regeneration doesn't return the cached outline.
        state["bypass_llm_cache"] = True
        # Reaching this node means the user asked for a new outline, so always
        # regenerate via the agent regardless of regenerate_section. The
        # approval is reset to the first gate: the user can then edit the
        # outline, regenerate again, or approve it to resume content generation.
        result = await blog_strategy_agent.execute(
            topic=state["topic"],
            target_word_count=state["target_word_count"],
            audience=state["audience"],
            tone=state["tone"],
            keywords=state["keywords"],
            competitor_analysis=state["competitor_analysis"],
            use_cache=False,
        )
        state["outline"] = result
        state["approval_status"] = "pending"
        state["approval_stage"] = "blog_strategy"
        return state

    async def _regenerate_seo_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate SEO metadata."""
        logger.info("Regenerating SEO metadata")
        state["current_stage"] = "regenerate_seo"
        state["bypass_llm_cache"] = True
        result = await seo_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            keywords=state["keywords"],
            use_cache=False,
        )
        state["seo_metadata"] = result
        state["approval_status"] = "pending"
        state["approval_stage"] = "final_review"
        return state

    async def _regenerate_image_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate image."""
        if not settings.enable_image_generation:
            logger.info("Image generation is disabled, skipping")
            state["current_stage"] = "regenerate_image"
            state["image_details"] = {}
            state["approval_status"] = "pending"
            state["approval_stage"] = "final_review"
            return state
        logger.info("Regenerating image")
        state["current_stage"] = "regenerate_image"
        state["bypass_llm_cache"] = True
        result = await image_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            tone=state["tone"],
            use_cache=False,
        )
        state["image_details"] = result
        state["approval_status"] = "pending"
        state["approval_stage"] = "final_review"
        return state

    async def _regenerate_verification_node(self, state: WorkflowState) -> WorkflowState:
        """Re-run fact verification only, keeping all other outputs."""
        logger.info("Regenerating fact verification")
        state["current_stage"] = "regenerate_verification"
        # The fact_verification node reads this flag to skip the LLM cache.
        state["bypass_llm_cache"] = True
        state["fact_verification_report"] = {}
        return state

    async def _regenerate_all_node(self, state: WorkflowState) -> WorkflowState:
        """Regenerate entire blog from outline onwards."""
        logger.info("Regenerating entire blog")
        state["current_stage"] = "regenerate_all"
        state["bypass_llm_cache"] = True
        # Regenerate blog content
        result = await blog_writing_agent.execute(
            topic=state["topic"],
            outline=state["outline"].get("outline", []),
            keywords=state["keywords"],
            tone=state["tone"],
            audience=state["audience"],
            target_word_count=state["target_word_count"],
            use_cache=False,
        )
        state["blog_content"] = result.get("content", "")
        # Regenerate SEO
        seo_result = await seo_agent.execute(
            topic=state["topic"],
            content=state["blog_content"],
            keywords=state["keywords"],
            use_cache=False,
        )
        state["seo_metadata"] = seo_result
        # Regenerate image only if enabled
        if settings.enable_image_generation:
            try:
                image_result = await image_agent.execute(
                    topic=state["topic"],
                    content=state["blog_content"],
                    tone=state["tone"],
                    use_cache=False,
                )
                state["image_details"] = image_result
            except Exception as e:
                logger.warning(f"Image generation failed, continuing without image: {e}")
                state["image_details"] = {}
        else:
            logger.info("Image generation is disabled, skipping")
            state["image_details"] = {}
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
            "bypass_llm_cache": False,
            "blog_version_id": 0,
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

        Retries once after rebuilding the graph/checkpointer — covers stale
        DB connections left behind by a postgres restart.
        """
        try:
            return await self._resume_workflow(project_id, action, updated_outline, regenerate_section)
        except Exception:
            await self._reset_graph()
            return await self._resume_workflow(project_id, action, updated_outline, regenerate_section)

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
            action: "approve", "reject", or "regenerate"
            updated_outline: User-edited outline (optional)
            regenerate_section: "outline", "blog_content", "seo", "image", or "all"
        """
        graph = await self.build_graph()
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}

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
                blog_version_id = await self._persist_workflow_output(final_state.values)
                if blog_version_id:
                    await graph.aupdate_state(config, {"blog_version_id": blog_version_id})
            except Exception as e:
                logger.error(f"Failed to persist workflow output: {e}")

        return result

    async def _persist_workflow_output(self, state: Dict[str, Any]) -> int:
        """
        Save final workflow output to the database so the REST APIs
        (blogs, SEO metadata, reports, approvals, PDF export) work.
        Upserts the latest Outline/BlogVersion for the project.
        Returns the BlogVersion id.
        """
        project_id = state.get("project_id")
        if not project_id or not state.get("blog_content"):
            return 0

        async with AsyncSessionLocal() as db:
            # --- Outline (latest for project) ---
            outline_row = (
                await db.execute(
                    select(Outline)
                    .where(Outline.project_id == project_id)
                    .order_by(Outline.id.desc())
                )
            ).scalars().first()
            outline_data = state.get("outline") or {}
            if outline_row:
                outline_row.structure = outline_data
                outline_row.status = OutlineStatus.approved
            else:
                outline_row = Outline(
                    project_id=project_id,
                    structure=outline_data,
                    status=OutlineStatus.approved,
                )
                db.add(outline_row)
            await db.flush()

            # --- Blog version (latest for project) ---
            blog = (
                await db.execute(
                    select(BlogVersion)
                    .where(BlogVersion.project_id == project_id)
                    .order_by(BlogVersion.id.desc())
                )
            ).scalars().first()
            if blog:
                blog.content = state.get("blog_content")
                blog.outline_id = outline_row.id
                blog.status = BlogStatus.approved
            else:
                blog = BlogVersion(
                    project_id=project_id,
                    outline_id=outline_row.id,
                    content=state.get("blog_content"),
                    status=BlogStatus.approved,
                )
                db.add(blog)
            await db.flush()

            # --- SEO metadata (one per blog version) ---
            seo = state.get("seo_metadata") or {}
            seo_row = (
                await db.execute(
                    select(SEOMetadata).where(SEOMetadata.blog_version_id == blog.id)
                )
            ).scalars().first()
            seo_fields = {
                "title": seo.get("title"),
                "meta_description": seo.get("meta_description"),
                "keywords": seo.get("keyword_density"),
            }
            if seo_row:
                for field, value in seo_fields.items():
                    setattr(seo_row, field, value)
            else:
                db.add(SEOMetadata(blog_version_id=blog.id, **seo_fields))

            # --- Image generation (optional; only present if image agent ran) ---
            image = state.get("image_details") or {}
            if image.get("image_path"):
                img_row = (
                    await db.execute(
                        select(ImageGeneration).where(
                            ImageGeneration.blog_version_id == blog.id
                        )
                    )
                ).scalars().first()
                img_fields = {
                    "prompt": image.get("prompt"),
                    "image_path": image.get("image_path"),
                    "model_used": image.get("model_used"),
                }
                if img_row:
                    for field, value in img_fields.items():
                        setattr(img_row, field, value)
                else:
                    db.add(ImageGeneration(blog_version_id=blog.id, **img_fields))

            # --- Quality report ---
            quality = state.get("quality_report") or {}
            quality_row = (
                await db.execute(
                    select(QualityReport).where(QualityReport.blog_version_id == blog.id)
                )
            ).scalars().first()
            quality_fields = {
                "grammar_score": quality.get("grammar_score"),
                "readability_score": quality.get("readability_score"),
                "issues": quality.get("issues"),
            }
            if quality_row:
                for field, value in quality_fields.items():
                    setattr(quality_row, field, value)
            else:
                db.add(QualityReport(blog_version_id=blog.id, **quality_fields))

            # --- Fact verification report ---
            verification = state.get("fact_verification_report") or {}
            verification_row = (
                await db.execute(
                    select(FactVerificationReport).where(
                        FactVerificationReport.blog_version_id == blog.id
                    )
                )
            ).scalars().first()
            verification_fields = {
                "claims_verified": verification.get("claims_verified"),
                "sources": verification.get("sources"),
                "confidence_score": verification.get("confidence_score"),
            }
            if verification_row:
                for field, value in verification_fields.items():
                    setattr(verification_row, field, value)
            else:
                db.add(FactVerificationReport(blog_version_id=blog.id, **verification_fields))

            # --- Approval records (replace existing for idempotency) ---
            await db.execute(
                delete(Approval).where(Approval.blog_version_id == blog.id)
            )
            now = datetime.utcnow()
            db.add(
                Approval(
                    blog_version_id=blog.id,
                    stage=ApprovalStage.outline,
                    status=ApprovalStatus.approved,
                    approved_at=now,
                )
            )
            db.add(
                Approval(
                    blog_version_id=blog.id,
                    stage=ApprovalStage.final,
                    status=ApprovalStatus.approved,
                    approved_at=now,
                )
            )

            await db.commit()
            logger.info(
                f"Persisted workflow output for project {project_id}: "
                f"outline_id={outline_row.id}, blog_version_id={blog.id}"
            )
            return blog.id

    async def get_workflow_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get the current status of the workflow.
        """
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
            "blog_version_id": state.values.get("blog_version_id", 0) if state.values else 0,
        }


blog_generation_workflow = BlogGenerationWorkflow()
