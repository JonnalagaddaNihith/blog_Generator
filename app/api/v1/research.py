from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import ResearchCreate, ResearchResponse
from app.models import Research, Project

router = APIRouter()


@router.get("/projects/{project_id}/research", response_model=List[ResearchResponse])
async def get_research(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get all research data for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(select(Research).where(Research.project_id == project_id))
    research_data = result.scalars().all()
    return research_data


@router.post("/projects/{project_id}/research", response_model=ResearchResponse)
async def create_research(
    project_id: int,
    research: ResearchCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create research data for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_research = Research(**research.model_dump())
    db.add(db_research)
    await db.commit()
    await db.refresh(db_research)
    return db_research
