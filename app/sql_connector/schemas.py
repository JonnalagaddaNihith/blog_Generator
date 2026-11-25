"""Pydantic schemas for Custom SQL website connections and publishing."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# Blog fields that can be mapped to SQL columns
BLOG_FIELDS = [
    "title",
    "slug",
    "content_html",
    "excerpt",
    "meta_title",
    "meta_description",
    "image_url",
    "status",
    "keywords",
    "categories",
    "tags",
]


class SqlWebsiteCreate(BaseModel):
    """Create a custom SQL website connection."""
    company_id: int
    name: str = Field(..., min_length=1, max_length=255)
    website_url: Optional[str] = Field(default=None, description="Public website URL used for 'view live' links")
    database_type: str = Field(..., description="One of: mysql, postgresql, mariadb, sqlite, mssql")
    connector_url: str = Field(..., description="Base URL of the customer-side publishing connector")
    api_token: str = Field(..., min_length=1, description="Bearer token for the connector API")
    table_name: Optional[str] = None
    column_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Map of blog field -> SQL column name",
    )
    test_connection: bool = Field(default=False, description="Test the connector before saving")


class SqlWebsiteUpdate(BaseModel):
    """Update a custom SQL website connection. api_token=None keeps the stored token."""
    name: Optional[str] = None
    website_url: Optional[str] = None
    database_type: Optional[str] = None
    connector_url: Optional[str] = None
    api_token: Optional[str] = None
    table_name: Optional[str] = None
    column_mapping: Optional[Dict[str, str]] = None


class SqlWebsiteResponse(BaseModel):
    id: int
    company_id: int
    name: str
    website_url: Optional[str] = None
    database_type: str
    connector_url: str
    table_name: Optional[str] = None
    column_mapping: Optional[Dict[str, str]] = None
    status: str
    last_tested_at: Optional[datetime] = None
    last_test_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_api_token: bool = True

    model_config = {"from_attributes": True}


class SqlWebsiteTestResponse(BaseModel):
    success: bool
    message: str
    database_type: Optional[str] = None
    connector_version: Optional[str] = None
    tables: Optional[List[str]] = None


class SqlColumnInfo(BaseModel):
    name: str
    type: Optional[str] = None
    nullable: Optional[bool] = None


class SqlTableInfo(BaseModel):
    name: str
    columns: List[SqlColumnInfo]


class SqlSchemaResponse(BaseModel):
    tables: List[SqlTableInfo]


class SqlPublishRequest(BaseModel):
    """Publish a blog to a custom SQL website."""
    status: str = Field(default="draft", description="'draft' or 'publish'")


class SqlPublishResponse(BaseModel):
    status: str
    action: Optional[str] = None  # "inserted" | "updated" | "unchanged"
    external_id: Optional[str] = None
    url: Optional[str] = None
    message: Optional[str] = None


class SqlPublicationResponse(BaseModel):
    id: int
    blog_version_id: int
    sql_website_id: int
    website_name: Optional[str] = None
    source_revision: int
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
