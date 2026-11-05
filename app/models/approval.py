from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ApprovalStage(str, enum.Enum):
    outline = "outline"
    final = "final"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False)
    stage = Column(Enum(ApprovalStage), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.pending)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approver = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    blog_version = relationship("BlogVersion", back_populates="approvals")
