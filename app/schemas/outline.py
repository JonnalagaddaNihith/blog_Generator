from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, Literal
from datetime import datetime


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
    status: Literal["draft", "approved", "rejected"]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
