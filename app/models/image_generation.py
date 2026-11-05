from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ImageGeneration(Base):
    __tablename__ = "image_generations"

    id = Column(Integer, primary_key=True, index=True)
    blog_version_id = Column(Integer, ForeignKey("blog_versions.id"), nullable=False)
    prompt = Column(String(2000), nullable=True)
    image_path = Column(String(500), nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blog_version = relationship("BlogVersion", back_populates="image_generation")
