from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Reservas"])

@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    booking_service = BookingService(db)
    return await booking_service.create(current_user.id, booking_in)

@router.get("/my", response_model=list[BookingResponse])
async def list_my_bookings(
    limit: int = 20, offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    booking_service = BookingService(db)
    return await booking_service.list_guest_bookings(current_user.id, limit, offset)

@router.get("/host", response_model=list[BookingResponse])
async def list_host_bookings(
    limit: int = 20, offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    booking_service = BookingService(db)
    return await booking_service.list_host_bookings(current_user.id, limit, offset)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    booking_service = BookingService(db)
    return await booking_service.get(booking_id, current_user.id)

@router.put("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.booking import BookingStatus
    booking_service = BookingService(db)
    return await booking_service.update_status(booking_id, current_user.id, BookingStatus.CONFIRMED)

@router.put("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.booking import BookingStatus
    booking_service = BookingService(db)
    return await booking_service.update_status(booking_id, current_user.id, BookingStatus.CANCELLED_BY_HOST, "Rejected by host")

@router.put("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.booking import BookingStatus
    booking_service = BookingService(db)
    return await booking_service.update_status(booking_id, current_user.id, BookingStatus.CANCELLED_BY_GUEST, reason)

@router.put("/{booking_id}/complete", response_model=BookingResponse)
async def complete_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.models.booking import BookingStatus
    booking_service = BookingService(db)
    return await booking_service.update_status(booking_id, current_user.id, BookingStatus.COMPLETED)
