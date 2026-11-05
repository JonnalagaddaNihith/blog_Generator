from pydantic import BaseModel, Field, HttpUrl, field_serializer, ConfigDict
from typing import Optional, Literal, Any
from datetime import datetime
from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    company_id: int
    topic: str
    target_word_count: int = Field(..., ge=100, le=10000)
    audience: Optional[str] = None
    tone: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    topic: Optional[str] = None
    target_word_count: Optional[int] = Field(None, ge=100, le=10000)
    audience: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[Literal["draft", "in_progress", "completed", "failed"]] = None


class ProjectResponse(ProjectBase):
    id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_serializer('status')
    @classmethod
    def serialize_status(cls, v: ProjectStatus) -> str:
        """Serialize enum to string."""
        return v.value if hasattr(v, 'value') else str(v)

    model_config = ConfigDict(from_attributes=True)
