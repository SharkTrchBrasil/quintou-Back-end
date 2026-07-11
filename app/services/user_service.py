from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils.i18n import _

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get(self, user_id: UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail=_("user_not_found"))
        return user

    async def update(self, user_id: UUID, user_in: UserUpdate) -> User:
        user = await self.get(user_id)
        
        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
            
        await self.db.commit()
        await self.db.refresh(user)
        return user
        
    async def become_host(self, user_id: UUID) -> User:
        user = await self.get(user_id)
        user.is_host = True
        await self.db.commit()
        await self.db.refresh(user)
        return user
