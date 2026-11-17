"""Node implementations for the blog generation workflow."""
from typing import Dict, Any, Sequence
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
from app.config import settings
from app.utils.logger import logger


class WorkflowState(Dict[str, Any]):
    """Type alias for workflow state dictionary."""
    pass


async def web_research_node(state: WorkflowState) -> WorkflowState:
    """Execute web research agent."""
    logger.info("Executing web research node")
    result = await web_research_agent.execute(
        topic=state["topic"],
        company_description=state.get("company_description", ""),
    )
    state["research_results"] = result.get("results", [])
    state["current_stage"] = "web_research"
    return state


async def keyword_intelligence_node(state: WorkflowState) -> WorkflowState:
    """Execute keyword intelligence agent."""
    logger.info("Executing keyword intelligence node")
    result = await keyword_intelligence_agent.execute(
        topic=state["topic"],
        research_results=list(state["research_results"]),
    )
    state["keywords"] = result
    state["current_stage"] = "keyword_intelligence"
    return state


async def competitor_gap_node(state: WorkflowState) -> WorkflowState:
    """Execute competitor gap agent."""
    logger.info("Executing competitor gap node")
    result = await competitor_gap_agent.execute(
        topic=state["topic"],
        research_results=list(state["research_results"]),
    )
    state["competitor_analysis"] = result
    state["current_stage"] = "competitor_gap"
    return state


async def blog_strategy_node(state: WorkflowState) -> WorkflowState:
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


async def blog_writing_node(state: WorkflowState) -> WorkflowState:
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


async def seo_node(state: WorkflowState) -> WorkflowState:
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


async def image_node(state: WorkflowState) -> WorkflowState:
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


async def quality_node(state: WorkflowState) -> WorkflowState:
    """Execute quality agent."""
    logger.info("Executing quality node")
    result = await quality_agent.execute(
        content=state["blog_content"],
        use_cache=not state.get("bypass_llm_cache", False),
    )
    state["quality_report"] = result
    state["current_stage"] = "quality"
    return state


async def fact_verification_node(state: WorkflowState) -> WorkflowState:
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


async def blog_strategy_approval_node(state: WorkflowState) -> WorkflowState:
    """Check blog strategy approval status."""
    logger.info(f"Blog strategy approval status: {state.get('approval_status')}")
    state["current_stage"] = "blog_strategy_approval"
    return state


async def final_approval_node(state: WorkflowState) -> WorkflowState:
    """Check final approval status."""
    logger.info(f"Final approval status: {state.get('approval_status')}")
    state["current_stage"] = "final_approval"
    return state


async def regenerate_outline_node(state: WorkflowState) -> WorkflowState:
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


async def regenerate_seo_node(state: WorkflowState) -> WorkflowState:
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


async def regenerate_image_node(state: WorkflowState) -> WorkflowState:
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


async def regenerate_verification_node(state: WorkflowState) -> WorkflowState:
    """Re-run fact verification only, keeping all other outputs."""
    logger.info("Regenerating fact verification")
    state["current_stage"] = "regenerate_verification"
    # The fact_verification node reads this flag to skip the LLM cache.
    state["bypass_llm_cache"] = True
    state["fact_verification_report"] = {}
    return state


async def regenerate_all_node(state: WorkflowState) -> WorkflowState:
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