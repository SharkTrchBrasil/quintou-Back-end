import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class PromotionType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

class SpacePromotion(Base):
    __tablename__ = "space_promotions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    
    name = Column(String, nullable=False) # Ex: "Grand Opening Discount"
    description = Column(String, nullable=True)
    
    type = Column(Enum(PromotionType), nullable=False)
    value = Column(Numeric(10, 2), nullable=False) # Ex: 20 (se percentage), 50.00 (se fixed)
    
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Condições opcionais
    min_hours = Column(Integer, nullable=True)
    min_guests = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    space = relationship("Space", back_populates="promotions")
