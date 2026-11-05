from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api.dependencies import get_current_db
from app.schemas import ApprovalCreate, ApprovalUpdate, ApprovalResponse
from app.models import Approval, BlogVersion
from app.models.approval import ApprovalStatus

router = APIRouter()


@router.get("/blogs/{blog_id}/approvals", response_model=List[ApprovalResponse])
async def list_approvals(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """List all approvals for a blog version."""
    # Verify blog version exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    result = await db.execute(select(Approval).where(Approval.blog_version_id == blog_id))
    approvals = result.scalars().all()
    return approvals


@router.post("/blogs/{blog_id}/approvals", response_model=ApprovalResponse)
async def create_approval(
    blog_id: int,
    approval: ApprovalCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create an approval record for a blog version."""
    # Verify blog version exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    db_approval = Approval(**approval.model_dump())
    db.add(db_approval)
    await db.commit()
    await db.refresh(db_approval)
    return db_approval


@router.put("/approvals/{approval_id}", response_model=ApprovalResponse)
async def update_approval(
    approval_id: int,
    approval_update: ApprovalUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    """Update an approval (approve or reject)."""
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    update_data = approval_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(approval, field, value)

    # Set approved_at if approving
    if approval.status == ApprovalStatus.approved and not approval.approved_at:
        from datetime import datetime
        approval.approved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(approval)
    return approval
