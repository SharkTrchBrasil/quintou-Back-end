from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from fastapi import HTTPException
from app.models.space import Space, SpaceImage, AvailabilityRule, SpacePricingTier, SpaceAddon, BlockedDate, AvailabilityException, CustomPricing
from app.models.category import Category
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
            selectinload(Space.category).selectinload(Category.amenities_config),
            selectinload(Space.host),
            selectinload(Space.blocked_dates),
            selectinload(Space.availability_exceptions),
            selectinload(Space.custom_pricing)
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

        space_data = space_in.model_dump(exclude={
            "availability_rules", "pricing_tiers", "addons", 
            "blocked_dates", "availability_exceptions", "custom_pricing",
            "latitude", "longitude"
        })
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
            
        for bd in space_in.blocked_dates:
            self.db.add(BlockedDate(**bd.model_dump(), space_id=db_space.id))

        for ae in space_in.availability_exceptions:
            self.db.add(AvailabilityException(**ae.model_dump(), space_id=db_space.id))

        for cp in space_in.custom_pricing:
            self.db.add(CustomPricing(**cp.model_dump(), space_id=db_space.id))
            
        await self.db.commit()
        await self.db.refresh(db_space)
        return await self.get(db_space.id)

    async def list_spaces(
        self, limit: int = 20, offset: int = 0, 
        city: str = None, category_id: UUID = None, 
        min_price: float = None, max_price: float = None,
        lat: float = None, lng: float = None, radius_km: float = 50.0,
        search_query: str = None, min_rating: float = None,
        # Filtros avançados
        min_guests: int = None, instant_book: bool = None,
        allows_smoking: bool = None, allows_alcohol: bool = None,
        allows_loud_music: bool = None, allows_parties: bool = None,
        allows_pets: bool = None, allows_children: bool = None,
        has_restroom: bool = None, has_parking: bool = None,
        is_outdoor: bool = None, is_ada_friendly: bool = None,
        cancellation_policy: str = None, amenities: list = None,
        sort_by: str = None,
    ) -> list[Space]:
        query = select(Space).options(
            selectinload(Space.images),
            selectinload(Space.category).selectinload(Category.amenities_config),
            selectinload(Space.availability_rules),
            selectinload(Space.pricing_tiers),
            selectinload(Space.addons),
            selectinload(Space.host),
            selectinload(Space.blocked_dates),
            selectinload(Space.availability_exceptions),
            selectinload(Space.custom_pricing)
        ).where(Space.is_active == True)
        
        if city:
            query = query.where(Space.city.ilike(f"{city}%"))
        
        if category_id:
            query = query.where(Space.category_id == category_id)
            
        if min_price is not None:
            query = query.where(Space.price >= min_price)
            
        if max_price is not None:
            query = query.where(Space.price <= max_price)
            
        if min_rating is not None:
            query = query.where(Space.average_rating >= min_rating)
            
        if search_query:
            # Busca textual simples usando ILIKE (no título e descrição)
            # Obs: Para bases gigantescas, o ideal é usar tsvector. Mas o ilike resolve para MVPs/fases iniciais
            search_term = f"%{search_query}%"
            query = query.where(
                (Space.title.ilike(search_term)) | 
                (Space.description.ilike(search_term)) |
                (Space.city.ilike(search_term)) |
                (Space.neighborhood.ilike(search_term))
            )
        
        # Capacidade mínima de convidados
        if min_guests is not None:
            query = query.where(Space.max_guests >= min_guests)
        
        # Instant Book (sem aprovação)
        if instant_book is not None:
            query = query.where(Space.requires_approval == (not instant_book))
        
        # House Rules
        if allows_smoking is not None:
            query = query.where(Space.allows_smoking == allows_smoking)
        if allows_alcohol is not None:
            query = query.where(Space.allows_alcohol == allows_alcohol)
        if allows_loud_music is not None:
            query = query.where(Space.allows_loud_music == allows_loud_music)
        if allows_parties is not None:
            query = query.where(Space.allows_parties == allows_parties)
        if allows_pets is not None:
            query = query.where(Space.allows_pets == allows_pets)
        if allows_children is not None:
            query = query.where(Space.allows_children == allows_children)
        
        # Infraestrutura
        if has_restroom is not None:
            query = query.where(Space.has_restroom == has_restroom)
        if has_parking is not None:
            query = query.where(Space.has_parking == has_parking)
        if is_outdoor is not None:
            query = query.where(Space.is_outdoor == is_outdoor)
        if is_ada_friendly is not None:
            query = query.where(Space.is_ada_friendly == is_ada_friendly)
        
        # Política de cancelamento
        if cancellation_policy is not None:
            query = query.where(Space.cancellation_policy == cancellation_policy)
        
        # Amenities (JSONB contains)
        if amenities:
            for amenity in amenities:
                query = query.where(Space.amenities.contains([amenity]))
            
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
            query = query.where((Space.latitude.is_(None)) | (distance <= radius_km))
            if sort_by is None:
                query = query.order_by(distance)
        
        # Ordenação
        if sort_by == "price_asc":
            query = query.order_by(Space.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Space.price.desc())
        elif sort_by == "rating":
            query = query.order_by(Space.average_rating.desc())
        elif sort_by == "newest":
            query = query.order_by(Space.created_at.desc())
            
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_host_spaces(self, host_id: UUID, limit: int = 20, offset: int = 0) -> list[Space]:
        query = select(Space).options(
            selectinload(Space.images),
            selectinload(Space.category).selectinload(Category.amenities_config),
            selectinload(Space.availability_rules),
            selectinload(Space.pricing_tiers),
            selectinload(Space.addons),
            selectinload(Space.host),
            selectinload(Space.blocked_dates),
            selectinload(Space.availability_exceptions),
            selectinload(Space.custom_pricing)
        ).where(Space.host_id == host_id).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def autocomplete_spaces(self, query_str: str, limit: int = 5) -> list[dict]:
        """
        Retorna sugestões rápidas baseadas no nome da cidade ou título do espaço.
        """
        search_term = f"%{query_str}%"
        query = select(Space.id, Space.title, Space.city, Space.state).where(
            Space.is_active == True,
            Space.is_approved == True,
            (Space.title.ilike(search_term)) | (Space.city.ilike(search_term))
        ).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        return [{"id": str(r.id), "title": r.title, "city": r.city, "state": r.state} for r in rows]

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

    async def increment_views(self, space_id: UUID):
        query = select(Space).where(Space.id == space_id)
        result = await self.db.execute(query)
        space = result.scalars().first()
        if not space:
            raise HTTPException(status_code=404, detail=_("space_not_found"))
        space.total_views = (space.total_views or 0) + 1
        await self.db.commit()
        return {"total_views": space.total_views}

    async def get_host_dashboard(self, host_id: UUID) -> dict:
        from app.models.booking import Booking, BookingStatus
        from sqlalchemy import cast, Date
        from datetime import datetime, timedelta

        # Buscar todos os espaços do host
        spaces_query = select(Space).where(Space.host_id == host_id, Space.is_active == True)
        spaces_result = await self.db.execute(spaces_query)
        spaces = list(spaces_result.scalars().all())
        space_ids = [s.id for s in spaces]

        total_views = sum(s.total_views or 0 for s in spaces)
        total_listings = len(spaces)

        if not space_ids:
            return {
                "total_revenue": 0.0,
                "pending_bookings": 0,
                "total_views": total_views,
                "total_listings": total_listings,
                "chart_data": [0.0] * 7,
            }

        # Receita total (bookings COMPLETED)
        revenue_query = select(func.coalesce(func.sum(Booking.host_payout), 0)).where(
            Booking.space_id.in_(space_ids),
            Booking.status == BookingStatus.COMPLETED,
        )
        revenue_result = await self.db.execute(revenue_query)
        total_revenue = float(revenue_result.scalar() or 0)

        # Reservas pendentes
        pending_query = select(func.count()).where(
            Booking.space_id.in_(space_ids),
            Booking.status == BookingStatus.PENDING,
        )
        pending_result = await self.db.execute(pending_query)
        pending_bookings = pending_result.scalar() or 0

        # Dados do gráfico: receita dos últimos 7 dias
        today = datetime.utcnow().date()
        chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_query = select(func.coalesce(func.sum(Booking.host_payout), 0)).where(
                Booking.space_id.in_(space_ids),
                Booking.status == BookingStatus.COMPLETED,
                cast(Booking.created_at, Date) == day,
            )
            day_result = await self.db.execute(day_query)
            chart_data.append(float(day_result.scalar() or 0))

        return {
            "total_revenue": total_revenue,
            "pending_bookings": pending_bookings,
            "total_views": total_views,
            "total_listings": total_listings,
            "chart_data": chart_data,
        }

