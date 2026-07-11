from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from fastapi import HTTPException
from app.models.space import Space, SpaceImage, AvailabilityRule, SpacePricingTier, SpaceAddon
from app.schemas.space import SpaceCreate, SpaceUpdate
from app.utils.i18n import _
from app.utils.geocoding import get_lat_lng_from_address

class SpaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get(self, space_id: UUID) -> Space:
        query = select(Space).options(
            selectinload(Space.images),
            selectinload(Space.availability_rules),
            selectinload(Space.pricing_tiers),
            selectinload(Space.addons),
            selectinload(Space.category),
            selectinload(Space.host)
        ).where(Space.id == space_id)
        
        result = await self.db.execute(query)
        space = result.scalars().first()
        if not space:
            raise HTTPException(status_code=404, detail=_("space_not_found"))
        return space

    async def create(self, host_id: UUID, space_in: SpaceCreate) -> Space:
        lat = space_in.latitude
        lng = space_in.longitude
        if not lat or not lng:
            full_address = f"{space_in.address_line}, {space_in.neighborhood}, {space_in.city}, {space_in.state}, {space_in.zip_code}"
            coords = await get_lat_lng_from_address(full_address)
            if coords:
                lat, lng = coords

        space_data = space_in.model_dump(exclude={"availability_rules", "pricing_tiers", "addons", "latitude", "longitude"})
        db_space = Space(**space_data, host_id=host_id, latitude=lat, longitude=lng)
        
        self.db.add(db_space)
        await self.db.flush()
        
        for rule_in in space_in.availability_rules:
            db_rule = AvailabilityRule(**rule_in.model_dump(), space_id=db_space.id)
            self.db.add(db_rule)
            
        for tier_in in space_in.pricing_tiers:
            db_tier = SpacePricingTier(**tier_in.model_dump(), space_id=db_space.id)
            self.db.add(db_tier)
            
        for addon_in in space_in.addons:
            db_addon = SpaceAddon(**addon_in.model_dump(), space_id=db_space.id)
            self.db.add(db_addon)
            
        await self.db.commit()
        await self.db.refresh(db_space)
        return await self.get(db_space.id)

    async def list_spaces(
        self, limit: int = 20, offset: int = 0, 
        city: str = None, category_id: UUID = None, 
        min_price: float = None, max_price: float = None,
        lat: float = None, lng: float = None, radius_km: float = 50.0
    ) -> list[Space]:
        query = select(Space).options(
            selectinload(Space.images),
            selectinload(Space.category)
        ).where(Space.is_active == True)
        
        if city:
            # Bug fix: avoid wildcard interpolation if not needed or escape it
            query = query.where(Space.city.ilike(f"{city}%"))
        
        if category_id:
            query = query.where(Space.category_id == category_id)
            
        if min_price is not None:
            query = query.where(Space.price >= min_price)
            
        if max_price is not None:
            query = query.where(Space.price <= max_price)
            
        if lat is not None and lng is not None:
            # Haversine formula in KM
            distance = (
                6371 * func.acos(
                    func.cos(func.radians(lat)) * 
                    func.cos(func.radians(Space.latitude)) * 
                    func.cos(func.radians(Space.longitude) - func.radians(lng)) + 
                    func.sin(func.radians(lat)) * 
                    func.sin(func.radians(Space.latitude))
                )
            )
            query = query.where(distance <= radius_km)
            query = query.order_by(distance)
            
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_host_spaces(self, host_id: UUID, limit: int = 20, offset: int = 0) -> list[Space]:
        query = select(Space).options(
            selectinload(Space.images),
            selectinload(Space.category)
        ).where(Space.host_id == host_id).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, space_id: UUID, host_id: UUID, space_in: SpaceUpdate) -> Space:
        space = await self.get(space_id)
        if space.host_id != host_id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        update_data = space_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(space, field, value)
            
        await self.db.commit()
        return await self.get(space_id)

    async def delete(self, space_id: UUID, host_id: UUID):
        space = await self.get(space_id)
        if space.host_id != host_id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        # Hard delete or soft delete? We'll do soft delete
        space.is_active = False
        await self.db.commit()

    async def add_image(self, space_id: UUID, host_id: UUID, image_in: dict) -> SpaceImage:
        space = await self.get(space_id)
        if space.host_id != host_id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        db_image = SpaceImage(**image_in, space_id=space.id)
        self.db.add(db_image)
        await self.db.commit()
        await self.db.refresh(db_image)
        return db_image

    async def remove_image(self, space_id: UUID, host_id: UUID, image_id: UUID):
        space = await self.get(space_id)
        if space.host_id != host_id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        query = select(SpaceImage).where(SpaceImage.id == image_id, SpaceImage.space_id == space_id)
        result = await self.db.execute(query)
        image = result.scalars().first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
            
        await self.db.delete(image)
        await self.db.commit()
