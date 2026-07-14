"""
Payment schemas
"""
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional


class PaymentIntentCreate(BaseModel):
    """Request para criar PaymentIntent"""
    booking_id: UUID


class PaymentIntentResponse(BaseModel):
    """Response com client_secret do Stripe"""
    client_secret: str
    amount: Decimal
    currency: str = "brl"


class PaymentResponse(BaseModel):
    """Payment completo"""
    id: UUID
    booking_id: UUID
    payer_id: UUID
    amount: Decimal
    platform_fee: Decimal
    host_amount: Decimal
    currency: str
    status: str
    stripe_payment_intent_id: Optional[str] = None
    stripe_transfer_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WebhookEvent(BaseModel):
    """Stripe webhook event"""
    type: str
    data: dict
