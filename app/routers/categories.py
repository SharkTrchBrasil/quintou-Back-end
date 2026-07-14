from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryService
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/categories", tags=["Categorias"])

@router.get("", response_model=List[CategoryResponse])
@cache(expire=3600)
async def list_categories(db: AsyncSession = Depends(get_db)):
    category_service = CategoryService(db)
    return await category_service.list_categories(active_only=True)

@router.get("/{slug}", response_model=CategoryResponse)
@cache(expire=3600)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    category_service = CategoryService(db)
    return await category_service.get_by_slug(slug)
