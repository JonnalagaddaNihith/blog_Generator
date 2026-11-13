from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models import (
    Project,
    BlogVersion,
    Outline,
    Research,
    Keyword,
    CompetitorGap,
    SEOMetadata,
    QualityReport,
    FactVerificationReport,
    ImageGeneration,
    Approval,
)


async def delete_project_artifacts(db: AsyncSession, project_id: int) -> None:
    """Remove all generated artifacts for a project (workflow outputs)."""
    blog_ids = (
        await db.execute(select(BlogVersion.id).where(BlogVersion.project_id == project_id))
    ).scalars().all()
    if blog_ids:
        for model in (Approval, SEOMetadata, QualityReport, FactVerificationReport, ImageGeneration):
            await db.execute(delete(model).where(model.blog_version_id.in_(blog_ids)))
    await db.execute(delete(BlogVersion).where(BlogVersion.project_id == project_id))
    await db.execute(delete(Outline).where(Outline.project_id == project_id))
    await db.execute(delete(Research).where(Research.project_id == project_id))
    await db.execute(delete(Keyword).where(Keyword.project_id == project_id))
    await db.execute(delete(CompetitorGap).where(CompetitorGap.project_id == project_id))


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Delete a project and all of its generated artifacts. Returns False if not found."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        return False

    await delete_project_artifacts(db, project_id)
    await db.delete(project)
    return True
