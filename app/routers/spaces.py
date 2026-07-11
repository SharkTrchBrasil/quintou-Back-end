from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.space import SpaceCreate, SpaceUpdate, SpaceResponse, SpaceSummary, SpaceImageCreate, SpaceImageResponse
from app.models.user import User
from app.dependencies import get_current_user, get_current_host
from app.services.space_service import SpaceService

router = APIRouter(prefix="/spaces", tags=["Espaços"])

@router.post("", response_model=SpaceResponse, status_code=201)
async def create_space(
    space_in: SpaceCreate,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    return await space_service.create(current_host.id, space_in)

@router.get("", response_model=List[SpaceResponse]) # Na v2: PaginatedResponse[SpaceSummary]
async def list_spaces(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    city: str = None,
    category_id: UUID = None,
    min_price: float = None,
    max_price: float = None,
    lat: float = None,
    lng: float = None,
    radius_km: float = Query(50.0, ge=1.0),
    # Filtros avançados
    min_guests: int = None,
    instant_book: bool = None,
    # House Rules
    allows_smoking: bool = None,
    allows_alcohol: bool = None,
    allows_loud_music: bool = None,
    allows_parties: bool = None,
    allows_pets: bool = None,
    allows_children: bool = None,
    # Infraestrutura
    has_restroom: bool = None,
    has_parking: bool = None,
    is_outdoor: bool = None,
    is_ada_friendly: bool = None,
    # Cancelamento
    cancellation_policy: str = None,
    # Amenities (comma-separated)
    amenities: str = None,
    # Ordenação
    sort_by: str = None,
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    amenities_list = [a.strip() for a in amenities.split(",")] if amenities else None
    return await space_service.list_spaces(
        limit=limit, offset=offset, city=city, category_id=category_id, 
        min_price=min_price, max_price=max_price, lat=lat, lng=lng, radius_km=radius_km,
        min_guests=min_guests, instant_book=instant_book,
        allows_smoking=allows_smoking, allows_alcohol=allows_alcohol,
        allows_loud_music=allows_loud_music, allows_parties=allows_parties,
        allows_pets=allows_pets, allows_children=allows_children,
        has_restroom=has_restroom, has_parking=has_parking,
        is_outdoor=is_outdoor, is_ada_friendly=is_ada_friendly,
        cancellation_policy=cancellation_policy, amenities=amenities_list,
        sort_by=sort_by,
    )

@router.get("/my", response_model=List[SpaceResponse])
async def list_my_spaces(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    return await space_service.list_host_spaces(current_host.id, limit=limit, offset=offset)

@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(space_id: UUID, db: AsyncSession = Depends(get_db)):
    space_service = SpaceService(db)
    return await space_service.get(space_id)

@router.put("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: UUID,
    space_in: SpaceUpdate,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    return await space_service.update(space_id, current_host.id, space_in)

@router.delete("/{space_id}", status_code=204)
async def delete_space(
    space_id: UUID,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    await space_service.delete(space_id, current_host.id)

@router.post("/{space_id}/images", response_model=SpaceImageResponse, status_code=201)
async def add_space_image(
    space_id: UUID,
    image_in: SpaceImageCreate,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    return await space_service.add_image(space_id, current_host.id, image_in.model_dump())

@router.delete("/{space_id}/images/{image_id}", status_code=204)
async def remove_space_image(
    space_id: UUID,
    image_id: UUID,
    current_host: User = Depends(get_current_host),
    db: AsyncSession = Depends(get_db)
):
    space_service = SpaceService(db)
    await space_service.remove_image(space_id, current_host.id, image_id)
