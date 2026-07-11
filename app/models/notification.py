import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class NotificationType(str, enum.Enum):
    BOOKING_REQUEST = "BOOKING_REQUEST"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    REVIEW_RECEIVED = "REVIEW_RECEIVED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    data = Column(JSONB, nullable=True) # Dados extras para deep link no app
    
    is_read = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    user = relationship("User")
