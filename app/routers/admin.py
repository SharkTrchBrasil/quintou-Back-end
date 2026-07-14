import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_admin
from app.schemas.admin import DashboardStats
from app.services.admin_service import AdminService
from app.schemas.space import SpaceResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/admin", tags=["Administração"])

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna os KPIs gerais da plataforma para o painel de administração.
    """
    admin_service = AdminService(db)
    return await admin_service.get_dashboard_stats()

@router.put("/spaces/{space_id}/approve", response_model=SpaceResponse)
async def approve_space(
    space_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Aprova um espaço que estava pendente, tornando-o visível no app.
    """
    admin_service = AdminService(db)
    return await admin_service.approve_space(space_id)

@router.put("/users/{user_id}/ban", response_model=UserResponse)
async def ban_user(
    user_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Bane um usuário, impedindo-o de logar.
    """
    admin_service = AdminService(db)
    return await admin_service.ban_user(user_id)
