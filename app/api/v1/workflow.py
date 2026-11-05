from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_current_db
from app.models import Project
from app.services.langgraph_workflow import blog_generation_workflow
from app.utils.logger import logger

router = APIRouter()


class WorkflowApprovalRequest(BaseModel):
    action: str  # "approve", "reject", or "regenerate"
    updated_outline: dict = None
    regenerate_section: str = None  # "outline", "blog_content", "seo", "image", "verification", or "all"


@router.post("/projects/{project_id}/workflow/start")
async def start_workflow(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Start the blog generation workflow for a project."""
    # Verify project exists and load company
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.company))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        thread_id = await blog_generation_workflow.start_workflow(
            project_id=project.id,
            topic=project.topic,
            target_word_count=project.target_word_count,
            audience=project.audience or "",
            tone=project.tone or "",
            company_description=project.company.description if project.company else "",
            company_website=project.company.website if project.company else "",
        )

        return {
            "message": "Workflow started successfully",
            "project_id": project_id,
            "thread_id": thread_id,
        }
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.post("/projects/{project_id}/workflow/approve")
async def approve_workflow(
    project_id: int,
    request: WorkflowApprovalRequest,
    db: AsyncSession = Depends(get_current_db),
):
    """Approve, reject, or regenerate workflow at current stage."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        final_state = await blog_generation_workflow.resume_workflow(
            project_id=project_id,
            action=request.action,
            updated_outline=request.updated_outline,
            regenerate_section=request.regenerate_section,
        )

        return {
            "message": f"Workflow {request.action} successfully",
            "project_id": project_id,
            "current_stage": final_state.get("current_stage"),
        }
    except Exception as e:
        logger.error(f"Error approving workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve workflow: {str(e)}")


@router.put("/projects/{project_id}/workflow/outline")
async def update_workflow_outline(
    project_id: int,
    updated_outline: dict,
    db: AsyncSession = Depends(get_current_db),
):
    """Update the outline in the workflow state (for manual editing)."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Get current workflow state
        status = await blog_generation_workflow.get_workflow_status(project_id=project_id)
        
        # Update outline in state
        graph = await blog_generation_workflow.build_graph()
        thread_id = str(project_id)
        config = {"configurable": {"thread_id": thread_id}}
        current_state = await graph.aget_state(config)
        
        if current_state.values:
            current_state.values["outline"] = updated_outline
            # Save the updated state
            await graph.aupdate_state(config, current_state.values)
        
        return {
            "message": "Outline updated successfully",
            "project_id": project_id,
        }
    except Exception as e:
        logger.error(f"Error updating outline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update outline: {str(e)}")


@router.get("/projects/{project_id}/workflow/status")
async def get_workflow_status(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get the current status of the workflow."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        status = await blog_generation_workflow.get_workflow_status(project_id=project_id)
        return status
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")
