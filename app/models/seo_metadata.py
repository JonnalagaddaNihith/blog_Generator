from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SEOMetadata(Base):
    __tablename__ = "seo_metadata"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False)
    title = Column(String(200), nullable=True)
    meta_description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    headings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    blog_version = relationship("BlogVersion", back_populates="seo_metadata")
