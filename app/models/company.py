from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    
    # WordPress.com credentials (encrypted in database)
    wp_site = Column(String(500), nullable=True)
    wp_client_id = Column(String(255), nullable=True)
    wp_client_secret = Column(String(500), nullable=True)
    wp_token = Column(Text, nullable=True)
    wp_redirect_uri = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
