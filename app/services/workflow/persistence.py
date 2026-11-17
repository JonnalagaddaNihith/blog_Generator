"""Database persistence operations for workflow output."""
from typing import Dict, Any, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
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
from app.utils.logger import logger


async def upsert_entity(
    db: AsyncSession,
    model_class,
    where_condition,
    field_updates: Dict[str, Any],
) -> Any:
    """Generic upsert helper for any model.
    
    Args:
        db: Database session
        model_class: The SQLAlchemy model class
        where_condition: SQLAlchemy where clause for finding existing record
        field_updates: Dictionary of field names to values to update/set
        
    Returns:
        The upserted model instance
    """
    result = await db.execute(select(model_class).where(where_condition))
    instance = result.scalars().first()
    
    if instance:
        for field, value in field_updates.items():
            setattr(instance, field, value)
    else:
        instance = model_class(**field_updates)
        db.add(instance)
    
    await db.flush()
    return instance


async def persist_outline(
    db: AsyncSession,
    project_id: int,
    outline_data: Dict[str, Any],
) -> Outline:
    """Persist or update outline for a project."""
    outline_row = (
        await db.execute(
            select(Outline)
            .where(Outline.project_id == project_id)
            .order_by(Outline.id.desc())
        )
    ).scalars().first()
    
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
    return outline_row


async def persist_blog_version(
    db: AsyncSession,
    project_id: int,
    outline_id: int,
    blog_content: str,
) -> BlogVersion:
    """Persist or update blog version for a project."""
    blog = (
        await db.execute(
            select(BlogVersion)
            .where(BlogVersion.project_id == project_id)
            .order_by(BlogVersion.id.desc())
        )
    ).scalars().first()
    
    if blog:
        blog.content = blog_content
        blog.outline_id = outline_id
        blog.status = BlogStatus.approved
    else:
        blog = BlogVersion(
            project_id=project_id,
            outline_id=outline_id,
            content=blog_content,
            status=BlogStatus.approved,
        )
        db.add(blog)
    
    await db.flush()
    return blog


async def persist_seo_metadata(
    db: AsyncSession,
    blog_version_id: int,
    seo_data: Dict[str, Any],
) -> Optional[SEOMetadata]:
    """Persist or update SEO metadata for a blog version."""
    if not seo_data:
        return None
    
    seo_fields = {
        "blog_version_id": blog_version_id,
        "title": seo_data.get("title"),
        "meta_description": seo_data.get("meta_description"),
        "keywords": seo_data.get("keyword_density"),
    }
    
    return await upsert_entity(
        db,
        SEOMetadata,
        SEOMetadata.blog_version_id == blog_version_id,
        seo_fields,
    )


async def persist_image_generation(
    db: AsyncSession,
    blog_version_id: int,
    image_data: Dict[str, Any],
) -> Optional[ImageGeneration]:
    """Persist or update image generation for a blog version."""
    if not image_data or not image_data.get("image_path"):
        return None
    
    img_fields = {
        "blog_version_id": blog_version_id,
        "prompt": image_data.get("prompt"),
        "image_path": image_data.get("image_path"),
        "model_used": image_data.get("model_used"),
    }
    
    return await upsert_entity(
        db,
        ImageGeneration,
        ImageGeneration.blog_version_id == blog_version_id,
        img_fields,
    )


async def persist_quality_report(
    db: AsyncSession,
    blog_version_id: int,
    quality_data: Dict[str, Any],
) -> Optional[QualityReport]:
    """Persist or update quality report for a blog version."""
    if not quality_data:
        return None
    
    quality_fields = {
        "blog_version_id": blog_version_id,
        "grammar_score": quality_data.get("grammar_score"),
        "readability_score": quality_data.get("readability_score"),
        "issues": quality_data.get("issues"),
    }
    
    return await upsert_entity(
        db,
        QualityReport,
        QualityReport.blog_version_id == blog_version_id,
        quality_fields,
    )


async def persist_fact_verification_report(
    db: AsyncSession,
    blog_version_id: int,
    verification_data: Dict[str, Any],
) -> Optional[FactVerificationReport]:
    """Persist or update fact verification report for a blog version."""
    if not verification_data:
        return None
    
    verification_fields = {
        "blog_version_id": blog_version_id,
        "claims_verified": verification_data.get("claims_verified"),
        "sources": verification_data.get("sources"),
        "confidence_score": verification_data.get("confidence_score"),
    }
    
    return await upsert_entity(
        db,
        FactVerificationReport,
        FactVerificationReport.blog_version_id == blog_version_id,
        verification_fields,
    )


async def persist_approvals(
    db: AsyncSession,
    blog_version_id: int,
) -> None:
    """Persist approval records for a blog version.
    
    Replaces existing approvals for idempotency.
    """
    # Delete existing approvals
    await db.execute(
        delete(Approval).where(Approval.blog_version_id == blog_version_id)
    )
    
    # Add new approvals
    now = datetime.utcnow()
    db.add(
        Approval(
            blog_version_id=blog_version_id,
            stage=ApprovalStage.outline,
            status=ApprovalStatus.approved,
            approved_at=now,
        )
    )
    db.add(
        Approval(
            blog_version_id=blog_version_id,
            stage=ApprovalStage.final,
            status=ApprovalStatus.approved,
            approved_at=now,
        )
    )


async def persist_workflow_output(
    db: AsyncSession,
    state: Dict[str, Any],
) -> int:
    """
    Save final workflow output to the database so the REST APIs
    (blogs, SEO metadata, reports, approvals, PDF export) work.
    Upserts the latest Outline/BlogVersion for the project.
    Returns the BlogVersion id.
    """
    project_id = state.get("project_id")
    if not project_id or not state.get("blog_content"):
        return 0

    # Persist outline
    outline_data = state.get("outline") or {}
    outline_row = await persist_outline(db, project_id, outline_data)

    # Persist blog version
    blog = await persist_blog_version(
        db,
        project_id,
        outline_row.id,
        state.get("blog_content"),
    )

    # Persist SEO metadata
    await persist_seo_metadata(db, blog.id, state.get("seo_metadata") or {})

    # Persist image generation (optional)
    await persist_image_generation(db, blog.id, state.get("image_details") or {})

    # Persist quality report
    await persist_quality_report(db, blog.id, state.get("quality_report") or {})

    # Persist fact verification report
    await persist_fact_verification_report(
        db, blog.id, state.get("fact_verification_report") or {}
    )

    # Persist approval records
    await persist_approvals(db, blog.id)

    await db.commit()
    logger.info(
        f"Persisted workflow output for project {project_id}: "
        f"outline_id={outline_row.id}, blog_version_id={blog.id}"
    )
    return blog.id