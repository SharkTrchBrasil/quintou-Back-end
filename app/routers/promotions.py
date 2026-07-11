from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.promotion import SpacePromotionCreate, SpacePromotionUpdate, SpacePromotionResponse
from app.models.user import User
from app.dependencies import get_current_host
from app.services.promotion_service import PromotionService

router = APIRouter(prefix="/promotions", tags=["Promoções"])

@router.post("/space/{space_id}", response_model=SpacePromotionResponse, status_code=201)
async def create_promotion(
    space_id: UUID,
    promo_in: SpacePromotionCreate,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    promo_service = PromotionService(db)
    return await promo_service.create_promotion(space_id, current_host.id, promo_in)

@router.put("/{promo_id}", response_model=SpacePromotionResponse)
async def update_promotion(
    promo_id: UUID,
    promo_in: SpacePromotionUpdate,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    promo_service = PromotionService(db)
    return await promo_service.update_promotion(promo_id, current_host.id, promo_in)

@router.delete("/{promo_id}", status_code=204)
async def delete_promotion(
    promo_id: UUID,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    promo_service = PromotionService(db)
    await promo_service.delete_promotion(promo_id, current_host.id)
