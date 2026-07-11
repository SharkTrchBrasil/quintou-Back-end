from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.category import Category
from app.utils.i18n import _

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_categories(self, active_only: bool = True) -> list[Category]:
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        query = query.order_by(Category.order)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Category:
        query = select(Category).where(Category.slug == slug)
        result = await self.db.execute(query)
        category = result.scalars().first()
        if not category:
            raise HTTPException(status_code=404, detail=_("category_not_found"))
        return category
