"""Services for Custom SQL website connections and blog publishing."""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import markdown
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import BlogVersion, Company, SqlPublication, SqlWebsite
from app.models.blog import BlogStatus
from app.models.sql_website import SqlDatabaseType, SqlPublicationStatus, SqlWebsiteStatus
from app.site_connector.encryption import decrypt, encrypt
from app.sql_connector.client import SqlConnectorClient, SqlConnectorError, validate_connector_url
from app.sql_connector.schemas import (
    BLOG_FIELDS,
    SqlPublishResponse,
    SqlWebsiteCreate,
    SqlWebsiteResponse,
    SqlWebsiteTestResponse,
    SqlWebsiteUpdate,
)
from app.utils.logger import logger


SUPPORTED_DATABASE_TYPES = {t.value for t in SqlDatabaseType}


def _validate_database_type(value: str) -> str:
    if value not in SUPPORTED_DATABASE_TYPES:
        raise ValueError(
            f"Unsupported database type '{value}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_DATABASE_TYPES))}"
        )
    return value


def _validate_mapping(mapping: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Validate a blog-field -> column mapping. Keys must be known blog fields."""
    if mapping is None:
        return None
    if not isinstance(mapping, dict):
        raise ValueError("column_mapping must be an object of {field: column}")
    cleaned = {}
    for field, column in mapping.items():
        if field not in BLOG_FIELDS:
            raise ValueError(f"Unknown blog field '{field}'. Supported: {', '.join(BLOG_FIELDS)}")
        if not isinstance(column, str) or not column.strip():
            raise ValueError(f"Column for field '{field}' must be a non-empty string")
        cleaned[field] = column.strip()
    return cleaned or None


class SqlWebsiteService:
    """CRUD + connection testing for custom SQL website connections."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_response(self, website: SqlWebsite) -> SqlWebsiteResponse:
        response = SqlWebsiteResponse.model_validate(website)
        response.has_api_token = bool(website.api_token)
        return response

    async def _get_website(self, website_id: int) -> SqlWebsite:
        result = await self.db.execute(select(SqlWebsite).where(SqlWebsite.id == website_id))
        website = result.scalar_one_or_none()
        if not website:
            raise ValueError(f"SQL website {website_id} not found")
        return website

    async def _get_company(self, company_id: int) -> Company:
        result = await self.db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        return company

    def _make_client(self, website: SqlWebsite) -> SqlConnectorClient:
        return SqlConnectorClient(
            connector_url=website.connector_url,
            api_token=decrypt(website.api_token),
            allow_private=settings.sql_connector_allow_private,
        )

    async def create(self, data: SqlWebsiteCreate) -> SqlWebsiteResponse:
        await self._get_company(data.company_id)
        database_type = _validate_database_type(data.database_type)
        column_mapping = _validate_mapping(data.column_mapping)
        # Validate URL early (SSRF guard) before persisting
        validate_connector_url(
            data.connector_url,
            allow_private=settings.sql_connector_allow_private,
        )

        website = SqlWebsite(
            company_id=data.company_id,
            name=data.name.strip(),
            website_url=data.website_url,
            database_type=database_type,
            connector_url=data.connector_url.strip().rstrip("/"),
            api_token=encrypt(data.api_token),
            table_name=data.table_name,
            column_mapping=column_mapping,
            status=SqlWebsiteStatus.untested.value,
        )
        self.db.add(website)
        await self.db.flush()

        test_message = None
        if data.test_connection:
            test = await self.test_connection(website.id, commit=False)
            test_message = test.message
        await self.db.commit()
        await self.db.refresh(website)

        response = self._to_response(website)
        if test_message:
            response.last_test_message = test_message
        return response

    async def update(self, website_id: int, data: SqlWebsiteUpdate) -> SqlWebsiteResponse:
        website = await self._get_website(website_id)
        update_data = data.model_dump(exclude_unset=True)

        for required in ("name", "connector_url"):
            if required in update_data and not (update_data[required] or "").strip():
                raise ValueError(f"{required} cannot be empty")
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()

        if "database_type" in update_data and update_data["database_type"]:
            update_data["database_type"] = _validate_database_type(update_data["database_type"])
        if "column_mapping" in update_data:
            update_data["column_mapping"] = _validate_mapping(update_data["column_mapping"])
        if "connector_url" in update_data and update_data["connector_url"]:
            update_data["connector_url"] = update_data["connector_url"].strip().rstrip("/")
            validate_connector_url(
                update_data["connector_url"],
                allow_private=settings.sql_connector_allow_private,
            )
            # Connector or token may have changed -> reset test status
            website.status = SqlWebsiteStatus.untested.value
        if update_data.get("api_token"):
            update_data["api_token"] = encrypt(update_data["api_token"])
            website.status = SqlWebsiteStatus.untested.value
        else:
            # api_token=None (or empty) means "keep the stored token"
            update_data.pop("api_token", None)

        for field, value in update_data.items():
            setattr(website, field, value)

        await self.db.commit()
        await self.db.refresh(website)
        return self._to_response(website)

    async def delete(self, website_id: int) -> None:
        website = await self._get_website(website_id)
        await self.db.delete(website)
        await self.db.commit()

    async def list_for_company(self, company_id: int) -> List[SqlWebsiteResponse]:
        result = await self.db.execute(
            select(SqlWebsite).where(SqlWebsite.company_id == company_id).order_by(SqlWebsite.id)
        )
        return [self._to_response(w) for w in result.scalars().all()]

    async def get(self, website_id: int) -> SqlWebsiteResponse:
        return self._to_response(await self._get_website(website_id))

    async def test_connection(self, website_id: int, commit: bool = True) -> SqlWebsiteTestResponse:
        website = await self._get_website(website_id)
        try:
            client = self._make_client(website)
            try:
                health = client.health()
            finally:
                client.close()
        except Exception as e:
            website.status = SqlWebsiteStatus.error.value
            website.last_tested_at = datetime.utcnow()
            website.last_test_message = str(e)
            if commit:
                await self.db.commit()
                await self.db.refresh(website)
            return SqlWebsiteTestResponse(success=False, message=str(e))

        tables = health.get("tables") or []
        message = health.get("message") or "Connection successful"
        website.status = SqlWebsiteStatus.connected.value
        website.last_tested_at = datetime.utcnow()
        website.last_test_message = message
        if commit:
            await self.db.commit()
            await self.db.refresh(website)

        return SqlWebsiteTestResponse(
            success=True,
            message=message,
            database_type=health.get("database_type") or website.database_type,
            connector_version=health.get("version"),
            tables=tables,
        )

    async def get_schema(self, website_id: int) -> Dict[str, Any]:
        """Fetch authorized tables and columns from the connector."""
        website = await self._get_website(website_id)
        client = self._make_client(website)
        try:
            tables = client.list_tables()
        finally:
            client.close()
        return {"tables": tables}


class SqlPublishService:
    """Publish approved blogs to custom SQL websites via their connectors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_website(self, website_id: int) -> SqlWebsite:
        result = await self.db.execute(select(SqlWebsite).where(SqlWebsite.id == website_id))
        website = result.scalar_one_or_none()
        if not website:
            raise ValueError(f"SQL website {website_id} not found")
        return website

    async def _get_existing_publication(
        self, blog_version_id: int, website_id: int
    ) -> Optional[SqlPublication]:
        result = await self.db.execute(
            select(SqlPublication).where(
                SqlPublication.blog_version_id == blog_version_id,
                SqlPublication.sql_website_id == website_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_publications(self, blog_version_id: int) -> List[Tuple[SqlPublication, str]]:
        result = await self.db.execute(
            select(SqlPublication, SqlWebsite.name)
            .join(SqlWebsite, SqlPublication.sql_website_id == SqlWebsite.id)
            .where(SqlPublication.blog_version_id == blog_version_id)
            .order_by(SqlPublication.id)
        )
        publications = []
        for publication, website_name in result.all():
            publications.append((publication, website_name))
        return publications

    def _build_record(
        self,
        blog: BlogVersion,
        status: str,
    ) -> Dict[str, Any]:
        """Build the full blog field payload (pre-mapping)."""
        seo = blog.seo_metadata
        title = (seo.title if seo and seo.title else None) or "Blog Post"
        content_html = markdown.markdown(
            blog.content or "",
            extensions=[
                "markdown.extensions.extra",
                "markdown.extensions.codehilite",
                "markdown.extensions.toc",
            ],
        )
        slug = self._generate_slug(title)

        image_url = None
        if blog.image_generation and blog.image_generation.image_path:
            if settings.public_api_url:
                image_url = (
                    f"{settings.public_api_url.rstrip('/')}"
                    f"/api/v1/projects/{blog.project_id}/workflow/image"
                )
            else:
                image_url = blog.image_generation.image_path

        keywords = None
        if seo and seo.keywords:
            keywords = ", ".join(seo.keywords) if isinstance(seo.keywords, list) else str(seo.keywords)

        return {
            "title": title,
            "slug": slug,
            "content_html": content_html,
            "excerpt": (seo.meta_description if seo else None),
            "meta_title": (seo.title if seo else None),
            "meta_description": (seo.meta_description if seo else None),
            "image_url": image_url,
            "status": status,
            "keywords": keywords,
            "categories": None,
            "tags": None,
        }

    def _generate_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "-", slug)
        return slug.strip("-")

    async def publish_blog(
        self,
        blog_version_id: int,
        website_id: int,
        status: str = "draft",
    ) -> SqlPublishResponse:
        """Push an approved blog into a custom website's SQL table."""
        if status not in ("draft", "publish"):
            raise ValueError("status must be 'draft' or 'publish'")

        result = await self.db.execute(
            select(BlogVersion)
            .options(
                selectinload(BlogVersion.seo_metadata),
                selectinload(BlogVersion.image_generation),
                selectinload(BlogVersion.project),
            )
            .where(BlogVersion.id == blog_version_id)
        )
        blog = result.scalar_one_or_none()
        if not blog:
            raise ValueError(f"Blog version {blog_version_id} not found")
        if blog.status != BlogStatus.approved:
            raise ValueError(f"Blog version {blog_version_id} is not approved (status: {blog.status})")
        if not blog.project:
            raise ValueError(f"Blog version {blog_version_id} has no associated project")

        website = await self._get_website(website_id)
        if website.company_id != blog.project.company_id:
            raise ValueError("SQL website does not belong to this blog's company")
        if not website.table_name:
            raise ValueError("No table configured for this SQL website")
        if not website.column_mapping:
            raise ValueError("No column mapping configured for this SQL website")

        record = self._build_record(blog, status)
        mapping = website.column_mapping or {}

        # Apply mapping: only mapped fields are sent to the connector
        mapped_record = {
            field: record[field]
            for field, column in mapping.items()
            if field in record and record[field] is not None
        }
        # Status column may need an explicit value even if 'status' field unmapped
        status_column = mapping.get("status")

        content_hash = hashlib.sha256(
            (record["title"] + "\n" + record["content_html"] + "\n" + status).encode()
        ).hexdigest()

        existing = await self._get_existing_publication(blog_version_id, website_id)

        # If the tracked remote record vanished, allow the connector to
        # re-dedupe by the slug column.
        dedupe_column = mapping.get("slug")

        client = SqlConnectorClient(
            connector_url=website.connector_url,
            api_token=decrypt(website.api_token),
            allow_private=settings.sql_connector_allow_private,
        )
        try:
            result_data = client.upsert_blog({
                "table": website.table_name,
                "column_mapping": mapping,
                "record": mapped_record,
                "dedupe_column": dedupe_column,
                "external_id": existing.external_id if existing else None,
                "status_column": status_column,
                "status_value": record["status"],
            })
        except SqlConnectorError as e:
            logger.error(f"SQL connector publish failed for blog {blog_version_id}: {e}")
            if existing:
                existing.status = SqlPublicationStatus.needs_reconciliation.value
                await self.db.commit()
            raise
        finally:
            client.close()

        action = result_data.get("action", "upserted")
        external_id = (
            result_data.get("external_id")
            or result_data.get("record_id")
            or (str(existing.external_id) if existing and existing.external_id else None)
        )
        external_url = result_data.get("url") or website.website_url

        now = datetime.utcnow()
        publication_status = (
            SqlPublicationStatus.published.value
            if status == "publish"
            else SqlPublicationStatus.draft.value
        )

        if existing:
            if existing.source_hash == content_hash and existing.external_id == external_id:
                existing.status = publication_status
                await self.db.commit()
                return SqlPublishResponse(
                    status="already_published",
                    action="unchanged",
                    external_id=str(external_id) if external_id else None,
                    url=external_url,
                    message="Blog already published with identical content",
                )
            existing.source_revision = blog.version
            existing.source_hash = content_hash
            existing.external_id = str(external_id) if external_id else None
            existing.external_url = external_url
            existing.status = publication_status
            existing.published_at = now
        else:
            publication = SqlPublication(
                blog_version_id=blog_version_id,
                sql_website_id=website_id,
                source_revision=blog.version,
                source_hash=content_hash,
                external_id=str(external_id) if external_id else None,
                external_url=external_url,
                status=publication_status,
                published_at=now,
            )
            self.db.add(publication)

        await self.db.commit()

        return SqlPublishResponse(
            status=publication_status,
            action=action,
            external_id=str(external_id) if external_id else None,
            url=external_url,
            message=f"Blog {action} in custom website database",
        )
