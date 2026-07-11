from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal
from app.schemas.common import BaseSchema
from app.models.payment import PaymentStatus

class PaymentIntentCreate(BaseSchema):
    booking_id: UUID

class PaymentIntentResponse(BaseSchema):
    client_secret: str
    amount: Decimal
    currency: str

class PaymentResponse(BaseSchema):
    id: UUID
    booking_id: UUID
    payer_id: UUID
    amount: Decimal
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime
