import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True, nullable=False)
    payer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), nullable=False)
    host_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="BRL")
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_transfer_id = Column(String, nullable=True)
    
    paid_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    booking = relationship("Booking", back_populates="payment")
    payer = relationship("User")
