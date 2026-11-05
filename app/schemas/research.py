from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime


class ResearchBase(BaseModel):
    project_id: int
    query: str
    results: Optional[Dict[str, Any]] = None


class ResearchCreate(ResearchBase):
    pass


class ResearchResponse(ResearchBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
