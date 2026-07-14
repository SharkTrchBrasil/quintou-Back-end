from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.wallet import TransactionType, TransactionStatus

class TransactionBase(BaseModel):
    type: TransactionType
    amount: float
    status: TransactionStatus
    reference_id: Optional[str] = None
    description: Optional[str] = None

class TransactionOut(TransactionBase):
    id: UUID
    wallet_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WalletBase(BaseModel):
    available_balance: float
    pending_balance: float
    total_earned: float
    currency: str

class WalletOut(WalletBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PayoutRequest(BaseModel):
    amount: float
