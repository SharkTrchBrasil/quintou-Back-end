from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Usuários"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.update(current_user.id, user_in)

@router.put("/me/become-host", response_model=UserResponse)
async def become_host(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.become_host(current_user.id)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService(db)
    return await user_service.get(user_id)
