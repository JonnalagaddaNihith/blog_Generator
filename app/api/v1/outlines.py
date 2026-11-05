from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import OutlineCreate, OutlineUpdate, OutlineResponse
from app.models import Outline, Project
from app.models.outline import OutlineStatus

router = APIRouter()


@router.get("/projects/{project_id}/outlines", response_model=List[OutlineResponse])
async def list_outlines(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """List all outlines for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(select(Outline).where(Outline.project_id == project_id))
    outlines = result.scalars().all()
    return outlines


@router.get("/outlines/{outline_id}", response_model=OutlineResponse)
async def get_outline(
    outline_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get an outline by ID."""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return outline


@router.put("/outlines/{outline_id}", response_model=OutlineResponse)
async def update_outline(
    outline_id: int,
    outline_update: OutlineUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    """Update an outline (for editing after interrupt)."""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    # If editing, reset status to draft
    update_data = outline_update.model_dump(exclude_unset=True)
    if "structure" in update_data:
        outline.status = OutlineStatus.draft

    for field, value in update_data.items():
        setattr(outline, field, value)

    await db.commit()
    await db.refresh(outline)
    return outline


@router.post("/outlines/{outline_id}/approve", response_model=OutlineResponse)
async def approve_outline(
    outline_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Approve an outline."""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    outline.status = OutlineStatus.approved
    await db.commit()
    await db.refresh(outline)
    return outline


@router.post("/outlines/{outline_id}/reject", response_model=OutlineResponse)
async def reject_outline(
    outline_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Reject an outline."""
    result = await db.execute(select(Outline).where(Outline.id == outline_id))
    outline = result.scalar_one_or_none()
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")

    outline.status = OutlineStatus.rejected
    await db.commit()
    await db.refresh(outline)
    return outline
