"""WordPress publication ledger model for tracking published posts."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PublicationStatus(str, enum.Enum):
    """Status of a WordPress publication."""
    published = "published"
    draft = "draft"
    needs_reconciliation = "needs_reconciliation"
    verify_pending = "verify_pending"
    already_published = "already_published"


class WordPressPublication(Base):
    """Ledger for tracking WordPress blog publications to ensure idempotency."""
    __tablename__ = "wordpress_publications"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False, index=True)
    source_revision = Column(Integer, nullable=False)  # The blog version number published
    source_hash = Column(String(64), nullable=False)  # Hash of published content for verification
    wp_post_id = Column(Integer, nullable=True)  # WordPress post ID
    wp_url = Column(String(500), nullable=True)  # WordPress post URL
    status = Column(Enum(PublicationStatus), default=PublicationStatus.published, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    blog_version = relationship("BlogVersion", backref="wordpress_publications")
