"""WordPress publishing service for integrating with the blog generator."""

import hashlib
import markdown
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, Any

from app.models import BlogVersion, Company, Project, WordPressPublication
from app.models.wordpress_publication import PublicationStatus
from app.site_connector.encryption import decrypt
from app.site_connector.wordpress_publisher import WordPressClient, PublishingError, ApprovedBlog, publish_approved_blog
from app.site_connector.schemas import WordPressPublishResponse
from app.utils.logger import logger


class WordPressPublishService:
    """Service for publishing blogs to WordPress.com."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def publish_blog_to_wordpress(
        self,
        blog_version_id: int,
        status: str = "publish",
    ) -> WordPressPublishResponse:
        """
        Publish an approved blog to WordPress.
        
        Args:
            blog_version_id: ID of the blog version to publish
            status: WordPress post status (draft or publish)
            
        Returns:
            WordPressPublishResponse with publication results
            
        Raises:
            PublishingError: If publishing fails
            ValueError: If blog is not approved or credentials are missing
        """
        # Get blog version with related data
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
        
        # Check if approved
        from app.models.blog import BlogStatus
        if blog.status != BlogStatus.approved:
            raise ValueError(f"Blog version {blog_version_id} is not approved (status: {blog.status})")
        
        # Get company and project
        project = blog.project
        if not project:
            raise ValueError(f"Blog version {blog_version_id} has no associated project")
        
        result = await self.db.execute(
            select(Company).where(Company.id == project.company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            raise ValueError(f"Company {project.company_id} not found")
        
        # Check WordPress credentials
        if not all([company.wp_site, company.wp_client_id, company.wp_client_secret, company.wp_token]):
            raise ValueError("WordPress credentials not configured for this company")
        
        # Decrypt credentials
        try:
            # Ensure site is just the domain, not full URL
            wp_site = company.wp_site.replace("https://", "").replace("http://", "").rstrip("/")
            wp_client_id = decrypt(company.wp_client_id)
            wp_client_secret = decrypt(company.wp_client_secret)
            wp_token = decrypt(company.wp_token)
        except Exception as e:
            logger.error(f"Failed to decrypt WordPress credentials: {e}")
            raise ValueError("Failed to decrypt WordPress credentials")
        
        # Convert Markdown to HTML
        content_html = self._markdown_to_html(blog.content or "")
        
        # Get SEO metadata for title and excerpt
        title = "Blog Post"
        excerpt = None
        
        if blog.seo_metadata:
            title = blog.seo_metadata.title or title
            excerpt = blog.seo_metadata.meta_description
        
        # Generate slug from title
        slug = self._generate_slug(title)
        
        # Check for existing publication
        existing_publication = await self._get_existing_publication(blog_version_id)
        existing_wp_post_id = existing_publication.wp_post_id if existing_publication else None
        
        # Prepare ApprovedBlog dataclass
        approved_blog = ApprovedBlog(
            id=str(blog_version_id),
            revision=blog.version,
            approved_revision=blog.version,  # Assuming current version is approved
            approved_hash=hashlib.sha256(content_html.encode()).hexdigest(),
            approval_status="approved",
            title=title,
            slug=slug,
            content_html=content_html,
            excerpt=excerpt,
            # TODO: Add categories, tags, featured_media mapping in future
            categories=None,
            tags=None,
            featured_media=None,
        )
        
        # Create WordPress client
        client = WordPressClient(
            site=wp_site,
            access_token=wp_token,
        )

        try:
            # Check idempotency if existing publication
            if existing_publication:
                if existing_publication.source_hash == approved_blog.content_hash():
                    # Verify the post still exists on WordPress before
                    # reporting it as already published (it may have been
                    # deleted or trashed manually on the site).
                    post_still_exists = False
                    try:
                        client.get_post(existing_publication.wp_post_id)
                        post_still_exists = True
                    except PublishingError:
                        post_still_exists = False

                    if post_still_exists:
                        logger.info(f"Blog {blog_version_id} already published with same content")
                        return WordPressPublishResponse(
                            status="already_published",
                            post_id=existing_publication.wp_post_id,
                            url=existing_publication.wp_url,
                            message="Blog already published with identical content",
                        )
                    logger.info(
                        f"Tracked post {existing_publication.wp_post_id} no longer exists "
                        f"on WordPress; republishing blog {blog_version_id}"
                    )
                # Content changed or post missing, will update/create

            # Publish to WordPress
            result = publish_approved_blog(
                blog=approved_blog,
                client=client,
                existing_wp_post_id=existing_wp_post_id,
                status=status,
            )
            
            # Update or create publication record
            # Track whether the WordPress post is draft or published
            publication_status = PublicationStatus.published if status == "publish" else PublicationStatus.draft
            
            if existing_publication:
                existing_publication.wp_post_id = result["post_id"]
                existing_publication.wp_url = result["url"]
                existing_publication.source_revision = blog.version
                existing_publication.source_hash = approved_blog.content_hash()
                existing_publication.status = publication_status
                from datetime import datetime
                existing_publication.published_at = datetime.utcnow()
            else:
                from datetime import datetime
                publication = WordPressPublication(
                    blog_version_id=blog_version_id,
                    source_revision=blog.version,
                    source_hash=approved_blog.content_hash(),
                    wp_post_id=result["post_id"],
                    wp_url=result["url"],
                    status=publication_status,
                    published_at=datetime.utcnow(),
                )
                self.db.add(publication)
            
            await self.db.commit()
            
            return WordPressPublishResponse(
                status=result["status"],
                post_id=result["post_id"],
                url=result["url"],
                message="Successfully published to WordPress",
            )
            
        except PublishingError as e:
            logger.error(f"WordPress publishing failed: {e}")
            
            # Update publication status to needs_reconciliation if it exists
            if existing_publication:
                existing_publication.status = PublicationStatus.needs_reconciliation
                await self.db.commit()
            
            raise
        finally:
            client.close()
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown content to HTML."""
        return markdown.markdown(
            markdown_content,
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
            ]
        )
    
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from title."""
        import re
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    async def _get_existing_publication(self, blog_version_id: int) -> Optional[WordPressPublication]:
        """Get existing WordPress publication record for a blog version."""
        result = await self.db.execute(
            select(WordPressPublication)
            .where(WordPressPublication.blog_version_id == blog_version_id)
        )
        return result.scalar_one_or_none()
