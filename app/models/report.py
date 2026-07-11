import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class ReportReason(str, enum.Enum):
    FAKE_LISTING = "FAKE_LISTING"
    HARASSMENT = "HARASSMENT"
    DAMAGE = "DAMAGE"
    FRAUD = "FRAUD"
    INAPPROPRIATE = "INAPPROPRIATE"
    OTHER = "OTHER"

class ReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Pode denunciar um usuário ou um espaço
    reported_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reported_space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=True)
    
    reason = Column(Enum(ReportReason), nullable=False)
    description = Column(Text, nullable=False)
    
    status = Column(Enum(ReportStatus), default=ReportStatus.OPEN)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    reported_space = relationship("Space")
