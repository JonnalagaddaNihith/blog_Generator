from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from datetime import datetime


class ApprovalBase(BaseModel):
    blog_version_id: int
    stage: Literal["outline", "final"]
    status: Literal["pending", "approved", "rejected"] = "pending"
    approver: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalUpdate(BaseModel):
    status: Literal["approved", "rejected"]
    approver: Optional[str] = None


class ApprovalResponse(ApprovalBase):
    id: int
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
