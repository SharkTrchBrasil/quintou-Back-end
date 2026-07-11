from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.promotion import SpacePromotion
from app.models.space import Space
from app.schemas.promotion import SpacePromotionCreate, SpacePromotionUpdate

class PromotionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_host(self, space_id: UUID, host_id: UUID):
        space = await self.db.get(Space, space_id)
        if not space:
            raise HTTPException(status_code=404, detail="Space not found")
        if space.host_id != host_id:
            raise HTTPException(status_code=403, detail="Not authorized")

    async def create_promotion(self, space_id: UUID, host_id: UUID, promo_in: SpacePromotionCreate) -> SpacePromotion:
        await self._check_host(space_id, host_id)
        
        promo = SpacePromotion(**promo_in.model_dump(), space_id=space_id)
        self.db.add(promo)
        await self.db.commit()
        await self.db.refresh(promo)
        return promo

    async def update_promotion(self, promo_id: UUID, host_id: UUID, promo_in: SpacePromotionUpdate) -> SpacePromotion:
        promo = await self.db.get(SpacePromotion, promo_id)
        if not promo:
            raise HTTPException(status_code=404, detail="Promotion not found")
            
        await self._check_host(promo.space_id, host_id)
        
        update_data = promo_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(promo, field, value)
            
        await self.db.commit()
        await self.db.refresh(promo)
        return promo

    async def delete_promotion(self, promo_id: UUID, host_id: UUID):
        promo = await self.db.get(SpacePromotion, promo_id)
        if not promo:
            raise HTTPException(status_code=404, detail="Promotion not found")
            
        await self._check_host(promo.space_id, host_id)
        
        await self.db.delete(promo)
        await self.db.commit()
