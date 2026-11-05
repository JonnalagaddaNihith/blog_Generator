from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class OutlineStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class Outline(Base):
    __tablename__ = "outlines"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    structure = Column(JSON, nullable=True)
    version = Column(Integer, default=1)
    status = Column(Enum(OutlineStatus), default=OutlineStatus.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="outlines")
    blog_versions = relationship("BlogVersion", back_populates="outline")
