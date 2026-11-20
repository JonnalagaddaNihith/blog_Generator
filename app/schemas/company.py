from pydantic import BaseModel, HttpUrl, ConfigDict, Field
from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None


class CompanyCreate(CompanyBase):
    # WordPress credentials (optional)
    wp_site: Optional[str] = None
    wp_client_id: Optional[str] = None
    wp_client_secret: Optional[str] = None
    wp_redirect_uri: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    # WordPress credentials (optional)
    wp_site: Optional[str] = None
    wp_client_id: Optional[str] = None
    wp_client_secret: Optional[str] = None
    wp_token: Optional[str] = None
    wp_redirect_uri: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # WordPress site only - sensitive credentials are not exposed
    wp_site: Optional[str] = None
    wp_configured: bool = Field(default=False, description="Whether WordPress credentials are configured")

    model_config = ConfigDict(from_attributes=True)
