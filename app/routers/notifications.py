from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.notification import NotificationResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notificações"])

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notification_service = NotificationService(db)
    return await notification_service.list_notifications(current_user.id, limit=limit, offset=offset)

@router.put("/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notification_service = NotificationService(db)
    await notification_service.mark_as_read(notification_id, current_user.id)

@router.put("/read-all", status_code=204)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    notification_service = NotificationService(db)
    await notification_service.mark_all_read(current_user.id)
