import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class ReviewType(str, enum.Enum):
    GUEST_TO_HOST = "GUEST_TO_HOST"
    HOST_TO_GUEST = "HOST_TO_GUEST"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reviewee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=True)
    
    type = Column(Enum(ReviewType), nullable=False)
    rating = Column(Integer, nullable=False) # 1 a 5
    comment = Column(Text, nullable=True)
    event_type = Column(String, nullable=True) # Ex: "Friend hangout"
    
    # Avaliações detalhadas (apenas para GUEST_TO_HOST)
    cleanliness_rating = Column(Integer, nullable=True)
    accuracy_rating = Column(Integer, nullable=True)
    communication_rating = Column(Integer, nullable=True)
    value_rating = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamentos
    booking = relationship("Booking", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])
    space = relationship("Space")
