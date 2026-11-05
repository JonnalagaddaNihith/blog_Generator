from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class FactVerificationReport(Base):
    __tablename__ = "fact_verification_reports"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False)
    claims_verified = Column(Integer, nullable=True)
    sources = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blog_version = relationship("BlogVersion", back_populates="fact_verification_report")
