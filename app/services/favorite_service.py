from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.favorite import Favorite
from app.models.space import Space
from app.utils.i18n import _

class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _load_favorite_with_space(self, favorite_id: UUID) -> Favorite:
        """Load a favorite with its space and images eagerly loaded."""
        query = select(Favorite).options(
            selectinload(Favorite.space).selectinload(Space.images)
        ).where(Favorite.id == favorite_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add_favorite(self, user_id: UUID, space_id: UUID) -> Favorite:
        # Check if space exists
        query_space = select(Space).where(Space.id == space_id)
        result_space = await self.db.execute(query_space)
        space = result_space.scalars().first()
        if not space:
            raise HTTPException(status_code=404, detail=_("space_not_found"))

        # Check if already favorited
        query_fav = select(Favorite).where(Favorite.user_id == user_id, Favorite.space_id == space_id)
        result_fav = await self.db.execute(query_fav)
        existing = result_fav.scalars().first()
        
        if existing:
            return await self._load_favorite_with_space(existing.id)

        favorite = Favorite(user_id=user_id, space_id=space_id)
        self.db.add(favorite)
        await self.db.commit()
        
        return await self._load_favorite_with_space(favorite.id)

    async def remove_favorite(self, user_id: UUID, space_id: UUID):
        query = select(Favorite).where(Favorite.user_id == user_id, Favorite.space_id == space_id)
        result = await self.db.execute(query)
        favorite = result.scalars().first()
        
        if favorite:
            await self.db.delete(favorite)
            await self.db.commit()

    async def list_user_favorites(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[Favorite]:
        query = select(Favorite).options(
            selectinload(Favorite.space).selectinload(Space.images)
        ).where(Favorite.user_id == user_id).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
