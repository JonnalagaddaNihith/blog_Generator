from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_current_db
from app.models import BlogVersion, SEOMetadata, ImageGeneration
from app.services.pdf_generator import pdf_generator
from app.storage.file_manager import file_manager
from app.models.blog import BlogStatus
from app.utils.logger import logger
import os

router = APIRouter()


@router.post("/blogs/{blog_id}/export/pdf")
async def export_pdf(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog as PDF. Rejects if not approved."""
    # Get blog version with related data
    result = await db.execute(
        select(BlogVersion)
        .options(
            selectinload(BlogVersion.seo_metadata),
            selectinload(BlogVersion.image_generation),
        )
        .where(BlogVersion.id == blog_id)
    )
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Check if approved
    if blog.status != BlogStatus.approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot export PDF: blog version is not approved"
        )

    try:
        # Get SEO metadata
        title = "Blog Post"
        meta_description = ""
        image_path = None

        if blog.seo_metadata:
            title = blog.seo_metadata.title or title
            meta_description = blog.seo_metadata.meta_description or ""

        if blog.image_generation:
            image_path = blog.image_generation.image_path

        # Use blog content or project topic as fallback
        if not blog.content:
            raise HTTPException(status_code=400, detail="Blog content is empty")

        # Generate PDF filename
        pdf_filename = file_manager.generate_pdf_filename(prefix="blog")
        pdf_path = file_manager.get_pdf_path(pdf_filename)

        # Generate PDF
        pdf_generator.generate_pdf(
            output_path=pdf_path,
            title=title,
            content=blog.content or "",
            author="Blog Generator",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": "PDF generated successfully",
            "blog_id": blog_id,
            "pdf_filename": pdf_filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/pdf/{pdf_filename}",
        }

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@router.get("/blogs/{blog_id}/export/pdf/{filename}")
async def download_pdf(
    blog_id: int,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a generated PDF."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Verify PDF exists
    pdf_path = file_manager.get_pdf_path(filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf",
    )
