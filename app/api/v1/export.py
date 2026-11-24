from typing import Any, Dict

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
from app.site_connector.services import WordPressPublishService
from app.site_connector.schemas import WordPressPublishRequest, WordPressPublishResponse
import os

router = APIRouter()

EXPORT_FORMATS: Dict[str, Dict[str, Any]] = {
    "pdf": {
        "generator": pdf_generator,
        "generate_filename": file_manager.generate_pdf_filename,
        "get_path": file_manager.get_pdf_path,
        "media_type": "application/pdf",
        "label": "PDF",
    },
    "docx": {
        "generator": docx_generator,
        "generate_filename": file_manager.generate_docx_filename,
        "get_path": file_manager.get_docx_path,
        "media_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "label": "DOCX",
    },
    "txt": {
        "generator": txt_generator,
        "generate_filename": file_manager.generate_txt_filename,
        "get_path": file_manager.get_txt_path,
        "media_type": "text/plain",
        "label": "TXT",
    },
    "html": {
        "generator": html_generator,
        "generate_filename": file_manager.generate_html_filename,
        "get_path": file_manager.get_html_path,
        "media_type": "text/html",
        "label": "HTML",
    },
    "md": {
        "generator": md_generator,
        "generate_filename": file_manager.generate_md_filename,
        "get_path": file_manager.get_md_path,
        "media_type": "text/markdown",
        "label": "MD",
    },
}


async def _get_approved_blog(blog_id: int, db: AsyncSession, format_label: str) -> BlogVersion:
    """Fetch a blog version with SEO/image relations, requiring approved status."""
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
    if blog.status != BlogStatus.approved:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot export {format_label}: blog version is not approved"
        )
    if not blog.content:
        raise HTTPException(status_code=400, detail="Blog content is empty")
    return blog


# WordPress Export
@router.post("/blogs/{blog_id}/export/wordpress", response_model=WordPressPublishResponse)
async def export_wordpress(
    blog_id: int,
    publish_request: WordPressPublishRequest,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog to WordPress.com. Rejects if not approved."""
    # Verify blog exists
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    # Check if approved
    if blog.status != BlogStatus.approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot export to WordPress: blog version is not approved"
        )

    try:
        service = WordPressPublishService(db)
        result = await service.publish_blog_to_wordpress(
            blog_version_id=blog_id,
            status=publish_request.status,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing to WordPress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish to WordPress: {str(e)}")


@router.post("/blogs/{blog_id}/export/{file_format}")
async def export_blog(
    blog_id: int,
    file_format: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Export an approved blog in the requested format (pdf, docx, txt, html, md)."""
    config = EXPORT_FORMATS.get(file_format)
    if not config:
        raise HTTPException(status_code=404, detail=f"Unsupported export format: {file_format}")
    label = config["label"]

    blog = await _get_approved_blog(blog_id, db, label)

    try:
        title = "Blog Post"
        meta_description = ""
        image_path = None

        if blog.seo_metadata:
            title = blog.seo_metadata.title or title
            meta_description = blog.seo_metadata.meta_description or ""

        if blog.image_generation:
            image_path = blog.image_generation.image_path

        filename = config["generate_filename"](prefix="blog")
        output_path = config["get_path"](filename)

        generate_fn = getattr(config["generator"], f"generate_{file_format}")
        generate_fn(
            output_path=output_path,
            title=title,
            content=blog.content or "",
            author="Jonnalagadda Nihit",
            image_path=image_path,
            meta_description=meta_description,
        )

        return {
            "message": f"{label} generated successfully",
            "blog_id": blog_id,
            f"{file_format}_filename": filename,
            "download_url": f"/api/v1/blogs/{blog_id}/export/{file_format}/{filename}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating {label}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate {label}: {str(e)}")


@router.get("/blogs/{blog_id}/export/{file_format}/{filename}")
async def download_export(
    blog_id: int,
    file_format: str,
    filename: str,
    db: AsyncSession = Depends(get_current_db),
):
    """Download a previously generated export file."""
    config = EXPORT_FORMATS.get(file_format)
    if not config:
        raise HTTPException(status_code=404, detail=f"Unsupported export format: {file_format}")

    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")

    file_path = config["get_path"](filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"{config['label']} file not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=config["media_type"],
    )


