import uuid
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from app.models.space import ListingType

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=False)
    listing_type = Column(Enum(ListingType), default=ListingType.SPACE, nullable=False)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
