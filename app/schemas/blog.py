from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.blog import BlogStatus


class BlogVersionBase(BaseModel):
    project_id: int
    outline_id: Optional[int] = None
    content: Optional[str] = None
    version: int = 1


class BlogVersionCreate(BlogVersionBase):
    pass


class BlogVersionUpdate(BaseModel):
    content: Optional[str] = None


class BlogVersionResponse(BlogVersionBase):
    id: int
    status: BlogStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
