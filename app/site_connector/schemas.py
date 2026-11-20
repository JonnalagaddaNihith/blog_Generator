"""Pydantic schemas for WordPress connector configuration and responses."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WordPressConfig(BaseModel):
    """WordPress configuration for a company."""
    wp_site: str = Field(..., description="WordPress.com site URL (e.g., example.wordpress.com)")
    wp_client_id: str = Field(..., description="OAuth client ID")
    wp_client_secret: str = Field(..., description="OAuth client secret")
    wp_redirect_uri: str = Field(default="http://127.0.0.1:8765/callback", description="OAuth redirect URI")


class WordPressOAuthRequest(BaseModel):
    """Request to initiate OAuth flow for a company."""
    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:8765/callback"


class WordPressPublishRequest(BaseModel):
    """Request to publish a blog to WordPress."""
    status: str = Field(default="draft", description="WordPress post status (draft or publish)")


class WordPressPublishResponse(BaseModel):
    """Response from WordPress publishing."""
    status: str
    post_id: Optional[int] = None
    url: Optional[str] = None
    message: Optional[str] = None


class WordPressPublicationStatus(BaseModel):
    """Status of a WordPress publication."""
    blog_version_id: int
    wp_post_id: Optional[int] = None
    wp_url: Optional[str] = None
    publication_status: str
    published_at: Optional[str] = None


class WordPressOAuthUrlResponse(BaseModel):
    """Response with OAuth authorization URL."""
    authorization_url: str
    state: str


class WordPressOAuthCallbackRequest(BaseModel):
    """Request to exchange OAuth code for token."""
    code: str
    state: str
