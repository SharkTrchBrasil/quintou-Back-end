from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryService
from fastapi_cache.decorator import cache
from app.services.wizard_config import WIZARD_STEPS_CONFIG, WIZARD_LABELS

router = APIRouter(prefix="/categories", tags=["Categorias"])

@router.get("", response_model=List[CategoryResponse])
async def list_categories(city: str = None, active_only: bool = False, db: AsyncSession = Depends(get_db)):
    category_service = CategoryService(db)
    return await category_service.list_categories(active_only=active_only, city=city)

@router.get("/{slug}", response_model=CategoryResponse)
@cache(expire=3600)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    category_service = CategoryService(db)
    return await category_service.get_by_slug(slug)

@router.get("/{slug}/wizard-config")
@cache(expire=3600)
async def get_wizard_config(slug: str, db: AsyncSession = Depends(get_db)):
    """Retorna configuração dinâmica do wizard para esta categoria."""
    category = await CategoryService(db).get_by_slug(slug)
    
    steps_config = WIZARD_STEPS_CONFIG.get(category.listing_type.value, WIZARD_STEPS_CONFIG["SPACE"])
    
    return {
        "category": CategoryResponse.model_validate(category),
        "steps": steps_config,
        "amenities": [{"id": str(a.id), "name": a.name, "icon": a.icon} for a in category.amenities_config],
        "labels": WIZARD_LABELS.get(category.listing_type.value, WIZARD_LABELS["SPACE"]),
    }
