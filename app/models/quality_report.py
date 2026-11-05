from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False)
    grammar_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    issues = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blog_version = relationship("BlogVersion", back_populates="quality_report")
