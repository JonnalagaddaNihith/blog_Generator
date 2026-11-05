from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import BlogVersionCreate, BlogVersionUpdate, BlogVersionResponse
from app.models import BlogVersion, Project
from app.models.blog import BlogStatus

router = APIRouter()


@router.get("/projects/{project_id}/blogs", response_model=List[BlogVersionResponse])
async def list_blogs(
    project_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """List all blog versions for a project."""
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(select(BlogVersion).where(BlogVersion.project_id == project_id))
    blogs = result.scalars().all()
    return blogs


@router.get("/blogs/{blog_id}", response_model=BlogVersionResponse)
async def get_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Get a blog version by ID."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")
    return blog


@router.put("/blogs/{blog_id}", response_model=BlogVersionResponse)
async def update_blog(
    blog_id: int,
    blog_update: BlogVersionUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    """Update a blog version."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # If editing content, reset status to draft and increment version
    update_data = blog_update.model_dump(exclude_unset=True)
    if "content" in update_data:
        blog.status = BlogStatus.draft
        blog.version += 1

    for field, value in update_data.items():
        setattr(blog, field, value)

    await db.commit()
    await db.refresh(blog)
    return blog


@router.post("/blogs/{blog_id}/approve", response_model=BlogVersionResponse)
async def approve_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Approve a final blog version."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    blog.status = BlogStatus.approved
    await db.commit()
    await db.refresh(blog)
    return blog


@router.post("/blogs/{blog_id}/reject", response_model=BlogVersionResponse)
async def reject_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Reject a final blog version."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    blog.status = BlogStatus.rejected
    await db.commit()
    await db.refresh(blog)
    return blog
