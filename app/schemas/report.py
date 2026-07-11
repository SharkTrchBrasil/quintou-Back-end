from typing import Optional
from uuid import UUID
from datetime import datetime
from app.schemas.common import BaseSchema
from app.models.report import ReportReason, ReportStatus
from app.schemas.user import UserSummary

class ReportCreate(BaseSchema):
    reported_user_id: Optional[UUID] = None
    reported_space_id: Optional[UUID] = None
    reason: ReportReason
    description: str

class ReportResponse(BaseSchema):
    id: UUID
    reporter_id: UUID
    reported_user_id: Optional[UUID]
    reported_space_id: Optional[UUID]
    reason: ReportReason
    description: str
    status: ReportStatus
    created_at: datetime
    resolved_at: Optional[datetime]
