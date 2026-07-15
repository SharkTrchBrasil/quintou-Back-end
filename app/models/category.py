import uuid
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.space import ListingType

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_group = Column(String, nullable=True)
    listing_type = Column(Enum(ListingType), default=ListingType.SPACE, nullable=False)
    requires_address_proof = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    amenities_config = relationship("CategoryAmenity", back_populates="category", order_by="CategoryAmenity.order", cascade="all, delete-orphan")
