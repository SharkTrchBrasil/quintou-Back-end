from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.favorite import FavoriteResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/favorites", tags=["Favoritos"])

@router.post("/{space_id}", response_model=FavoriteResponse, status_code=201)
async def add_favorite(
    space_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    favorite_service = FavoriteService(db)
    return await favorite_service.add_favorite(current_user.id, space_id)

@router.delete("/{space_id}", status_code=204)
async def remove_favorite(
    space_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    favorite_service = FavoriteService(db)
    await favorite_service.remove_favorite(current_user.id, space_id)

@router.get("", response_model=List[FavoriteResponse])
async def list_favorites(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    favorite_service = FavoriteService(db)
    return await favorite_service.list_user_favorites(current_user.id, limit=limit, offset=offset)
