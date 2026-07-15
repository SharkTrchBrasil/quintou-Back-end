import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class CategoryAmenity(Base):
    __tablename__ = "category_amenities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    name = Column(String, nullable=False)        # "Piscina Aquecida"
    icon = Column(String, nullable=True)         # "🏊" ou "pool"
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    category = relationship("Category", back_populates="amenities_config")
