"""API endpoints for Custom SQL website connections and publishing."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_current_db
from app.models import BlogVersion, SqlPublication, SqlWebsite
from app.models.blog import BlogStatus
from app.sql_connector.client import SsrfError
from app.sql_connector.schemas import (
    SqlPublishRequest,
    SqlPublishResponse,
    SqlPublicationResponse,
    SqlSchemaResponse,
    SqlWebsiteCreate,
    SqlWebsiteResponse,
    SqlWebsiteTestResponse,
    SqlWebsiteUpdate,
)
from app.sql_connector.services import SqlPublishService, SqlWebsiteService

router = APIRouter()


def _handle_value_error(e: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(e))


# --- Website connection management (scoped under companies) ---

@router.get("/companies/{company_id}/sql-websites", response_model=List[SqlWebsiteResponse])
async def list_sql_websites(
    company_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """List custom SQL website connections for a company."""
    service = SqlWebsiteService(db)
    try:
        return await service.list_for_company(company_id)
    except ValueError as e:
        raise _handle_value_error(e)


@router.post("/companies/{company_id}/sql-websites", response_model=SqlWebsiteResponse)
async def create_sql_website(
    company_id: int,
    data: SqlWebsiteCreate,
    db: AsyncSession = Depends(get_current_db),
):
    """Create a custom SQL website connection (optionally testing it first)."""
    if data.company_id != company_id:
        raise HTTPException(status_code=400, detail="company_id in body must match the path")
    service = SqlWebsiteService(db)
    try:
        return await service.create(data)
    except SsrfError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise _handle_value_error(e)


# --- Website connection management (by id) ---

@router.get("/sql-websites/{website_id}", response_model=SqlWebsiteResponse)
async def get_sql_website(
    website_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    service = SqlWebsiteService(db)
    try:
        return await service.get(website_id)
    except ValueError as e:
        raise _handle_value_error(e)


@router.put("/sql-websites/{website_id}", response_model=SqlWebsiteResponse)
async def update_sql_website(
    website_id: int,
    data: SqlWebsiteUpdate,
    db: AsyncSession = Depends(get_current_db),
):
    service = SqlWebsiteService(db)
    try:
        return await service.update(website_id, data)
    except SsrfError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise _handle_value_error(e)


@router.delete("/sql-websites/{website_id}")
async def delete_sql_website(
    website_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    service = SqlWebsiteService(db)
    try:
        await service.delete(website_id)
        return {"message": "SQL website connection deleted"}
    except ValueError as e:
        raise _handle_value_error(e)


@router.post("/sql-websites/{website_id}/test", response_model=SqlWebsiteTestResponse)
async def test_sql_website(
    website_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Test the connector connection and refresh the stored status."""
    service = SqlWebsiteService(db)
    try:
        return await service.test_connection(website_id)
    except ValueError as e:
        raise _handle_value_error(e)


@router.get("/sql-websites/{website_id}/schema", response_model=SqlSchemaResponse)
async def get_sql_website_schema(
    website_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Fetch authorized tables and columns from the customer connector."""
    service = SqlWebsiteService(db)
    try:
        return await service.get_schema(website_id)
    except ValueError as e:
        raise _handle_value_error(e)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Connector request failed: {e}")


# --- Publishing ---

@router.get("/blogs/{blog_id}/sql-publications", response_model=List[SqlPublicationResponse])
async def list_sql_publications(
    blog_id: int,
    db: AsyncSession = Depends(get_current_db),
):
    """Publishing history for a blog across all custom SQL websites."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Blog version not found")

    rows = await SqlPublishService(db).list_publications(blog_id)
    responses = []
    for publication, website_name in rows:
        resp = SqlPublicationResponse.model_validate(publication)
        resp.website_name = website_name
        responses.append(resp)
    return responses


@router.post("/blogs/{blog_id}/export/sql/{website_id}", response_model=SqlPublishResponse)
async def export_blog_to_sql(
    blog_id: int,
    website_id: int,
    publish_request: SqlPublishRequest,
    db: AsyncSession = Depends(get_current_db),
):
    """Push an approved blog into a custom website's SQL table."""
    result = await db.execute(select(BlogVersion).where(BlogVersion.id == blog_id))
    blog = result.scalar_one_or_none()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog version not found")
    if blog.status != BlogStatus.approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot publish to SQL website: blog version is not approved",
        )

    try:
        service = SqlPublishService(db)
        return await service.publish_blog(
            blog_version_id=blog_id,
            website_id=website_id,
            status=publish_request.status,
        )
    except ValueError as e:
        raise _handle_value_error(e)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to publish to SQL website: {e}")
