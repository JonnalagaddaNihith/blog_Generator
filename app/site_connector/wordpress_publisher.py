"""WordPress.com API client for publishing blog posts.

Based on the reference implementation adapted for this project.
"""

import hashlib
import httpx
from dataclasses import dataclass, replace
from typing import Optional, Dict, Any
from app.utils.logger import logger


class PublishingError(Exception):
    """Exception raised when WordPress publishing fails."""
    pass


@dataclass
class ApprovedBlog:
    """Represents a blog ready for publishing to WordPress."""
    id: str  # Source blog ID
    revision: int  # Current revision number
    approved_revision: int  # Revision that was approved
    approved_hash: str  # Hash of approved content
    approval_status: str  # "approved" or other
    title: str
    slug: str
    content_html: str
    excerpt: Optional[str] = None
    categories: Optional[list[int]] = None  # WordPress category IDs
    tags: Optional[list[int]] = None  # WordPress tag IDs
    featured_media: Optional[int] = None  # WordPress media ID for featured image

    def content_hash(self) -> str:
        """Compute SHA256 hash of the content for verification."""
        return hashlib.sha256(self.content_html.encode()).hexdigest()


class WordPressClient:
    """HTTP client for WordPress.com REST API."""
    
    def __init__(
        self,
        site: str,
        access_token: str,
        timeout: int = 20,
    ):
        """
        Initialize WordPress client.
        
        Args:
            site: WordPress.com site (e.g., "example.wordpress.com")
            access_token: OAuth access token
            timeout: HTTP request timeout in seconds
        """
        self.site = site
        self.site_domain = site.replace("https://", "").replace("http://", "").rstrip("/")
        self.access_token = access_token
        self.timeout = timeout
        # WordPress.com REST API v2 endpoint format
        # Use site_domain (extracted from site) for the URL path
        self.url = f"https://public-api.wordpress.com/wp/v2/sites/{self.site_domain}/posts"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        self.http = httpx.Client(timeout=timeout)
    
    def _api(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated API request to WordPress."""
        try:
            response = self.http.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    code = error_data.get("code") or error_data.get("error")
                    message = error_data.get("message") or error_data.get("error_description")
                    if code:
                        error_msg += f" ({code})"
                    if message:
                        error_msg += f": {message}"
            except Exception:
                pass
            raise PublishingError(error_msg)
        except httpx.RequestError as e:
            raise PublishingError(f"Network error: {type(e).__name__}")
    
    def posts_by_slug(self, slug: str, status: str = "any") -> list:
        """Look up posts by slug (including unpublished drafts)."""
        params = {"slug": slug, "status": status}
        return self._api("GET", self.url, params=params)
    
    def create_post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new WordPress post."""
        return self._api("POST", self.url, json=data)
    
    def update_post(self, post_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing WordPress post."""
        update_url = f"{self.url}/{post_id}"
        return self._api("POST", update_url, json=data)
    
    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a WordPress post by ID."""
        get_url = f"{self.url}/{post_id}"
        return self._api("GET", get_url)
    
    def close(self):
        """Close the HTTP client."""
        self.http.close()


def publish_approved_blog(
    blog: ApprovedBlog,
    client: WordPressClient,
    existing_wp_post_id: Optional[int] = None,
    status: str = "draft",
) -> Dict[str, Any]:
    """
    Publish an approved blog to WordPress with idempotency checks.
    
    Args:
        blog: The approved blog to publish
        client: WordPress API client
        existing_wp_post_id: Existing WordPress post ID if this is an update
        
    Returns:
        Dictionary with status, post_id, and url
        
    Raises:
        PublishingError: If publishing fails
    """
    # Verify approval status
    if blog.approval_status != "approved":
        raise PublishingError("Only an approved blog can be published")
    
    # Verify revision hasn't changed since approval
    if blog.revision != blog.approved_revision:
        raise PublishingError("Blog revision changed after approval")
    
    # Check for existing post by slug and reconcile with WordPress as the
    # source of truth. If a post with this slug already exists on the site
    # (e.g., created outside the ledger or the ledger record was lost),
    # update it instead of failing or creating a duplicate.
    existing = client.posts_by_slug(blog.slug)
    wp_post_id = existing_wp_post_id

    if existing:
        # Prefer the post tracked in our ledger; otherwise adopt the first
        # slug match on the site.
        match = next(
            (p for p in existing if p.get("id") == existing_wp_post_id),
            existing[0],
        )
        wp_post_id = match.get("id")
        logger.info(
            f"Found existing WordPress post {wp_post_id} with slug '{blog.slug}' "
            f"(tracked id was {existing_wp_post_id}); will update it"
        )
    
    # Prepare WordPress post data
    post_data = {
        "title": blog.title,
        "content": blog.content_html,
        "slug": blog.slug,
        "status": status,
    }
    
    if blog.excerpt:
        post_data["excerpt"] = blog.excerpt
    
    if blog.categories:
        post_data["categories"] = blog.categories
    
    if blog.tags:
        post_data["tags"] = blog.tags
    
    if blog.featured_media:
        post_data["featured_media"] = blog.featured_media
    
    # Create or update post
    if wp_post_id:
        logger.info(f"Updating existing WordPress post {wp_post_id}")
        result = client.update_post(wp_post_id, post_data)
    else:
        logger.info(f"Creating new WordPress post with slug '{blog.slug}'")
        result = client.create_post(post_data)
    
    # Verify the post was published
    post_id = result["id"]
    post_url = result.get("link", "")
    
    # Double-check status via GET
    verified = client.get_post(post_id)
    if verified.get("status") != status:
        raise PublishingError(f"Post created but status is '{verified.get('status')}', expected '{status}'")
    
    # Verify the URL belongs to the correct site
    if post_url and client.site_domain not in post_url:
        raise PublishingError(f"Post URL '{post_url}' does not belong to site '{client.site_domain}'")
    
    # Verify public accessibility
    try:
        public_check = httpx.get(post_url, timeout=10)
        if public_check.status_code != 200:
            logger.warning(f"Public URL returned HTTP {public_check.status_code}, but API says published")
    except Exception as e:
        logger.warning(f"Could not verify public URL: {e}")
    
    return {
        "status": status,
        "post_id": post_id,
        "url": post_url,
    }
