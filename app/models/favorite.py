import uuid
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'space_id', name='uq_user_space_favorite'),
    )
    
    # Relacionamentos
    user = relationship("User")
    space = relationship("Space")
