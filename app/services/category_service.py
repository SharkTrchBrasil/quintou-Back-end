from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from app.models.category import Category
from app.utils.i18n import _

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self, active_only: bool = True, city: str = None) -> list[Category]:
        from app.models.space import Space
        from sqlalchemy import func
        query = select(Category).options(selectinload(Category.amenities_config))
        if active_only:
            query = query.where(Category.is_active == True)
            
        if city:
            # Ensure category has at least one active space in the city
            query = query.join(Space, Space.category_id == Category.id)
            query = query.where(Space.is_active == True)
            query = query.where(func.lower(Space.city) == func.lower(city))
            query = query.distinct()
            
        query = query.order_by(Category.order)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category:
        query = select(Category).options(selectinload(Category.amenities_config)).where(Category.slug == slug)
        result = await self.db.execute(query)
        category = result.scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail=_("category_not_found"))
        return category
