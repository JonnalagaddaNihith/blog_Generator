from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.api.dependencies import get_current_db
from app.models import BlogVersion
from app.services.file_generators import pdf_generator, docx_generator, txt_generator, html_generator, md_generator
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
            author="Jonnalagadda Nihit",
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


# DOCX Export
@router.post("/blogs/{blog_id}/export/docx")
async def export_docx(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog as DOCX. Rejects if not approved."""
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
            detail="Cannot export DOCX: blog version is not approved"
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

        # Generate DOCX filename
        docx_filename = file_manager.generate_docx_filename(prefix="blog")
        docx_path = file_manager.get_docx_path(docx_filename)

        # Generate DOCX
        docx_generator.generate_docx(
            output_path=docx_path,
            title=title,
            content=blog.content or "",
            author="Blog Generator",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": "DOCX generated successfully",
            "blog_id": blog_id,
            "docx_filename": docx_filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/docx/{docx_filename}",
        }

    except Exception as e:
        logger.error(f"Error generating DOCX: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate DOCX: {str(e)}")


@router.get("/blogs/{blog_id}/export/docx/{filename}")
async def download_docx(
    blog_id: int,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a generated DOCX."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Verify DOCX exists
    docx_path = file_manager.get_docx_path(filename)
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="DOCX file not found")

    return FileResponse(
        path=docx_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# TXT Export
@router.post("/blogs/{blog_id}/export/txt")
async def export_txt(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog as TXT. Rejects if not approved."""
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
            detail="Cannot export TXT: blog version is not approved"
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

        # Generate TXT filename
        txt_filename = file_manager.generate_txt_filename(prefix="blog")
        txt_path = file_manager.get_txt_path(txt_filename)

        # Generate TXT
        txt_generator.generate_txt(
            output_path=txt_path,
            title=title,
            content=blog.content or "",
            author="Blog Generator",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": "TXT generated successfully",
            "blog_id": blog_id,
            "txt_filename": txt_filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/txt/{txt_filename}",
        }

    except Exception as e:
        logger.error(f"Error generating TXT: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate TXT: {str(e)}")


@router.get("/blogs/{blog_id}/export/txt/{filename}")
async def download_txt(
    blog_id: int,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a generated TXT."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Verify TXT exists
    txt_path = file_manager.get_txt_path(filename)
    if not os.path.exists(txt_path):
        raise HTTPException(status_code=404, detail="TXT file not found")

    return FileResponse(
        path=txt_path,
        filename=filename,
        media_type="text/plain",
    )


# HTML Export
@router.post("/blogs/{blog_id}/export/html")
async def export_html(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog as HTML. Rejects if not approved."""
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
            detail="Cannot export HTML: blog version is not approved"
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

        # Generate HTML filename
        html_filename = file_manager.generate_html_filename(prefix="blog")
        html_path = file_manager.get_html_path(html_filename)

        # Generate HTML
        html_generator.generate_html(
            output_path=html_path,
            title=title,
            content=blog.content or "",
            author="Blog Generator",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": "HTML generated successfully",
            "blog_id": blog_id,
            "html_filename": html_filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/html/{html_filename}",
        }

    except Exception as e:
        logger.error(f"Error generating HTML: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate HTML: {str(e)}")


@router.get("/blogs/{blog_id}/export/html/{filename}")
async def download_html(
    blog_id: int,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a generated HTML."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Verify HTML exists
    html_path = file_manager.get_html_path(filename)
    if not os.path.exists(html_path):
        raise HTTPException(status_code=404, detail="HTML file not found")

    return FileResponse(
        path=html_path,
        filename=filename,
        media_type="text/html",
    )


# MD Export
@router.post("/blogs/{blog_id}/export/md")
async def export_md(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog as MD. Rejects if not approved."""
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
            detail="Cannot export MD: blog version is not approved"
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

        # Generate MD filename
        md_filename = file_manager.generate_md_filename(prefix="blog")
        md_path = file_manager.get_md_path(md_filename)

        # Generate MD
        md_generator.generate_md(
            output_path=md_path,
            title=title,
            content=blog.content or "",
            author="Blog Generator",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": "MD generated successfully",
            "blog_id": blog_id,
            "md_filename": md_filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/md/{md_filename}",
        }

    except Exception as e:
        logger.error(f"Error generating MD: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate MD: {str(e)}")


@router.get("/blogs/{blog_id}/export/md/{filename}")
async def download_md(
    blog_id: int,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a generated MD."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Verify MD exists
    md_path = file_manager.get_md_path(filename)
    if not os.path.exists(md_path):
        raise HTTPException(status_code=404, detail="MD file not found")

    return FileResponse(
        path=md_path,
        filename=filename,
        media_type="text/markdown",
    )
