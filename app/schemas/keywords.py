from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class KeywordBase(BaseModel):
    project_id: int
    primary_keywords: Optional[List[str]] = None
    secondary_keywords: Optional[List[str]] = None
    long_tail_keywords: Optional[List[str]] = None


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    primary_keywords: Optional[List[str]] = None
    secondary_keywords: Optional[List[str]] = None
    long_tail_keywords: Optional[List[str]] = None


class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
