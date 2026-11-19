# """Graph building and routing logic for the blog generation workflow."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.services.workflow.nodes import (
    web_research_node,
    keyword_intelligence_node,
    competitor_gap_node,
    blog_strategy_node,
    blog_writing_node,
    seo_node,
    image_node,
    quality_node,
    fact_verification_node,
    blog_strategy_approval_node,
    final_approval_node,
    regenerate_outline_node,
    regenerate_seo_node,
    regenerate_image_node,
    regenerate_verification_node,
    regenerate_all_node,
    regenerate_quality_node,
)
from app.utils.logger import logger


class WorkflowState(Dict[str, Any]):
    """Type alias for workflow state dictionary."""
    pass


def check_blog_strategy_approval(state: WorkflowState) -> str:
    """Determine next step based on blog strategy approval."""
    approval = state.get("approval_status", "pending")
    if approval == "approved":
        return "approved"
    elif approval == "regenerate":
        return "regenerate"
    else:
        return "pending"


def check_final_approval(state: WorkflowState) -> str:
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


def build_workflow_graph(workflow: StateGraph, enable_image_generation: bool = False) -> StateGraph:
    """Build the LangGraph workflow graph structure.
    
    Args:
        workflow: A StateGraph instance to configure
        enable_image_generation: Whether to include image generation nodes
        
    Returns:
        Configured StateGraph ready for compilation
    """
    # Add nodes for each agent
    workflow.add_node("web_research", web_research_node)
    workflow.add_node("keyword_intelligence", keyword_intelligence_node)
    workflow.add_node("competitor_gap", competitor_gap_node)
    workflow.add_node("blog_strategy", blog_strategy_node)
    workflow.add_node("blog_writing", blog_writing_node)
    workflow.add_node("seo", seo_node)
    
    if enable_image_generation:
        workflow.add_node("image", image_node)
    
    workflow.add_node("quality", quality_node)
    workflow.add_node("fact_verification", fact_verification_node)

    # Add conditional routing nodes
    workflow.add_node("blog_strategy_approval", blog_strategy_approval_node)
    workflow.add_node("final_approval", final_approval_node)
    workflow.add_node("regenerate_outline", regenerate_outline_node)
    workflow.add_node("regenerate_seo", regenerate_seo_node)
    
    if enable_image_generation:
        workflow.add_node("regenerate_image", regenerate_image_node)
    
    workflow.add_node("regenerate_all", regenerate_all_node)
    workflow.add_node("regenerate_verification", regenerate_verification_node)
    workflow.add_node("regenerate_quality", regenerate_quality_node)

    # Stage 1: Research to Outline
    workflow.set_entry_point("web_research")
    workflow.add_edge("web_research", "keyword_intelligence")
    workflow.add_edge("keyword_intelligence", "competitor_gap")
    workflow.add_edge("competitor_gap", "blog_strategy")

    # Blog Strategy approval checkpoint
    workflow.add_edge("blog_strategy", "blog_strategy_approval")
    workflow.add_conditional_edges(
        "blog_strategy_approval",
        check_blog_strategy_approval,
        {
            "approved": "blog_writing",
            "regenerate": "regenerate_outline",
            "pending": END  # Wait for human approval
        }
    )

    # Stage 2: Writing to Final Verification
    workflow.add_edge("blog_writing", "seo")
    
    if enable_image_generation:
        workflow.add_edge("seo", "image")
        workflow.add_edge("image", "quality")
    else:
        workflow.add_edge("seo", "quality")
    
    workflow.add_edge("quality", "fact_verification")

    # Final approval checkpoint
    workflow.add_edge("fact_verification", "final_approval")
    
    final_approval_routes = {
        "approved": END,
        "regenerate_outline": "regenerate_outline",
        "regenerate_seo": "regenerate_seo",
        "regenerate_verification": "regenerate_verification",
        "regenerate_all": "regenerate_all",
        "regenerate_quality": "regenerate_quality",
        "pending": END  # Wait for human approval
    }
    
    if enable_image_generation:
        final_approval_routes["regenerate_image"] = "regenerate_image"
    
    workflow.add_conditional_edges(
        "final_approval",
        check_final_approval,
        final_approval_routes
    )

    # Regeneration loops: each re-runs only its own node, then returns to
    # the final approval checkpoint. State (outline, content, keywords,
    # research) is read from the checkpoint — nothing upstream re-runs.
    workflow.add_edge("regenerate_seo", "final_approval")
    
    if enable_image_generation:
        workflow.add_edge("regenerate_image", "final_approval")
    
    workflow.add_edge("regenerate_verification", "fact_verification")
    # regenerate_all already produces blog+seo+image; continue to quality
    # and fact verification so reports stay consistent (avoids re-running
    # blog_writing/seo/image a second time).
    workflow.add_edge("regenerate_all", "quality")
    # regenerate_quality revises content for non-grammar quality issues and
    # refreshes SEO inline; it rejoins at quality so the report, fact
    # verification and final approval all re-run on the revised content.
    workflow.add_edge("regenerate_quality", "quality")

    # Regenerate outline is reachable from both approval checkpoints and
    # always returns to the first approval gate: a new outline invalidates
    # any downstream content, so the user must approve the outline again
    # before blog content, SEO, etc. are generated.
    workflow.add_edge("regenerate_outline", "blog_strategy_approval")

    logger.info("LangGraph workflow graph structure built successfully")
    return workflow
