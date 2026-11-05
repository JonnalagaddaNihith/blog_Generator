from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class QualityReportBase(BaseModel):
    blog_version_id: int
    grammar_score: Optional[float] = None
    readability_score: Optional[float] = None
    issues: Optional[List[Dict[str, Any]]] = None


class QualityReportCreate(QualityReportBase):
    pass


class QualityReportResponse(QualityReportBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FactVerificationReportBase(BaseModel):
    blog_version_id: int
    claims_verified: Optional[int] = None
    sources: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None


class FactVerificationReportCreate(FactVerificationReportBase):
    pass


class FactVerificationReportResponse(FactVerificationReportBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
