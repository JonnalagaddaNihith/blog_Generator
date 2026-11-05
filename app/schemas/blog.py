from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from datetime import datetime


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
    status: Literal["draft", "approved", "rejected"]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
