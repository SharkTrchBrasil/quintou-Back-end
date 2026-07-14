from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReportCreate(BaseModel):
    reported_user_id: Optional[UUID] = None
    reported_space_id: Optional[UUID] = None
    reason: str
    description: str

class ReportResponse(BaseModel):
    id: UUID
    reporter_id: UUID
    reported_user_id: Optional[UUID] = None
    reported_space_id: Optional[UUID] = None
    reason: str
    description: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
