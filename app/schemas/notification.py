from typing import Optional
from uuid import UUID
from datetime import datetime
from app.schemas.common import BaseSchema
from app.models.notification import NotificationType

class NotificationResponse(BaseSchema):
    id: UUID
    user_id: UUID
    type: NotificationType
    title: str
    body: str
    data: Optional[dict] = None
    is_read: bool
    created_at: datetime
