from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.models import Project, Company
from app.services.langgraph_workflow import blog_generation_workflow
from app.services.project_cleanup import delete_project_artifacts, delete_project

router = APIRouter()

# Fields that feed into blog generation — changing any of them invalidates
# previously generated artifacts.
GENERATION_FIELDS = {"topic", "target_word_count", "audience", "tone"}


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create a new project."""
    # Verify company exists
    result = await db.execute(select(Company).where(Company.id == project.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    company_id: int = None,
    db: AsyncSession = Depends(get_current_db),
):
    """List all projects, optionally filtered by company."""
    query = select(Project).offset(skip).limit(limit)
    if company_id:
        query = query.where(Project.company_id == company_id)

    result = await db.execute(query)
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get a project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    """Update a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Completed projects (workflow ran to final approval) are read-only.
    # is_complete is also true for never-started workflows, so require an
    # approved final state as well.
    wf_status = await blog_generation_workflow.get_workflow_status(project_id)
    if (
        wf_status.get("is_complete")
        and wf_status.get("approval_status") == "approved"
        and wf_status.get("current_stage") not in ("not_started", "unknown")
    ):
        raise HTTPException(
            status_code=400,
            detail="Cannot edit a completed project",
        )

    update_data = project_update.model_dump(exclude_unset=True)
    inputs_changed = any(
        field in update_data and getattr(project, field) != update_data[field]
        for field in GENERATION_FIELDS
    )

    for field, value in update_data.items():
        setattr(project, field, value)

    if inputs_changed:
        # Generation inputs changed — drop stale artifacts and checkpoint
        # state so the next workflow run starts from scratch.
        await delete_project_artifacts(db, project_id)
        await blog_generation_workflow.reset_workflow(project_id)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project_endpoint(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Delete a project and all of its generated artifacts."""
    if not await delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    await blog_generation_workflow.reset_workflow(project_id)
    await db.commit()
    return {"message": "Project deleted successfully"}
