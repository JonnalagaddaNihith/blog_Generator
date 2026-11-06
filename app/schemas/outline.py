from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.outline import OutlineStatus


class OutlineBase(BaseModel):
    project_id: int
    structure: Optional[Dict[str, Any]] = None
    version: int = 1


class OutlineCreate(OutlineBase):
    pass


class OutlineUpdate(BaseModel):
    structure: Optional[Dict[str, Any]] = None


class OutlineResponse(OutlineBase):
    id: int
    status: OutlineStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
