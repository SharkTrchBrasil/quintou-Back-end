from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.services.firebase_service import FirebaseService

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_notification(self, user_id: UUID, n_type: NotificationType, title: str, body: str, data: dict = None) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=n_type,
            title=title,
            body=body,
            data=data or {}
        )
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        
        # Load user to get fcm_token
        user = await self.db.get(User, user_id)
        if user and user.fcm_token:
            FirebaseService.send_push_notification(
                fcm_token=user.fcm_token,
                title=title,
                body=body,
                data=data or {}
            )
            
        return notif

    async def list_notifications(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: UUID, user_id: UUID):
        query = select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        result = await self.db.execute(query)
        notif = result.scalars().first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        notif.is_read = True
        await self.db.commit()

    async def mark_all_read(self, user_id: UUID):
        stmt = update(Notification).where(
            Notification.user_id == user_id, 
            Notification.is_read == False
        ).values(is_read=True)
        await self.db.execute(stmt)
        await self.db.commit()
