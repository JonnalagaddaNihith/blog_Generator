from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BlogStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class BlogVersion(Base):
    __tablename__ = "blog_versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    outline_id = Column(Integer, ForeignKey("outlines.id"), nullable=True)
    content = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    status = Column(Enum(BlogStatus), default=BlogStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="blog_versions")
    outline = relationship("Outline", back_populates="blog_versions")
    image_generation = relationship("ImageGeneration", back_populates="blog_version", uselist=False)
    seo_metadata = relationship("SEOMetadata", back_populates="blog_version", uselist=False)
    quality_report = relationship("QualityReport", back_populates="blog_version", uselist=False)
    fact_verification_report = relationship("FactVerificationReport", back_populates="blog_version", uselist=False)
    approvals = relationship("Approval", back_populates="blog_version")
