from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime
from pydantic import BaseModel, Field
from decimal import Decimal
from app.schemas.common import BaseSchema
from app.models.booking import BookingStatus
from app.schemas.user import UserSummary
from app.schemas.space import SpaceSummary

class BookingAddonBase(BaseSchema):
    addon_id: UUID
    quantity: int = Field(default=1, gt=0)

class BookingAddonCreate(BookingAddonBase):
    pass

class BookingAddonResponse(BookingAddonBase):
    id: UUID
    unit_price: Decimal
    total_price: Decimal

class BookingBase(BaseSchema):
    date: date
    start_time: time
    end_time: time
    num_guests: int = Field(gt=0)
    num_adults: int = Field(default=0, ge=0)
    num_children: int = Field(default=0, ge=0)
    num_infants: int = Field(default=0, ge=0)
    num_pets: int = Field(default=0, ge=0)
    guest_message: Optional[str] = None
    event_type: Optional[str] = None

class BookingCreate(BookingBase):
    space_id: UUID
    delivery_address: Optional[str] = None  # Obrigatório para listings tipo EQUIPMENT com entrega
    selected_addons: List[BookingAddonCreate] = []

class BookingUpdate(BaseSchema):
    status: Optional[BookingStatus] = None
    host_response: Optional[str] = None

class BookingCancel(BaseSchema):
    cancellation_reason: str

class BookingResponse(BookingBase):
    id: UUID
    space_id: UUID
    guest_id: UUID
    total_hours: int
    subtotal: Decimal
    addons_total: Decimal
    delivery_fee: Decimal = Decimal('0.00')
    service_fee: Decimal
    host_fee: Decimal
    total_price: Decimal
    host_payout: Decimal
    delivery_address: Optional[str] = None
    deposit_amount: Decimal
    deposit_status: str
    status: BookingStatus
    host_response: Optional[str] = None
    created_at: datetime
    
    addons: List[BookingAddonResponse] = []
    
    # Detalhes opcionais inclusos via join
    space: Optional[SpaceSummary] = None
    guest: Optional[UserSummary] = None
