import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    cpf = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    is_host = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verificações & Segurança (KYC)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    document_type = Column(String, nullable=True) # "RG" ou "CNH"
    document_url = Column(String, nullable=True)
    selfie_url = Column(String, nullable=True)
    kyc_status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Badges de Host
    is_verified_host = Column(Boolean, default=False)
    is_pro_host = Column(Boolean, default=False)
    hosting_since = Column(DateTime(timezone=True), nullable=True)
    avg_response_time_minutes = Column(Integer, nullable=True)
    
    stripe_account_id = Column(String, nullable=True)
    
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    spaces = relationship("Space", back_populates="host", cascade="all, delete-orphan")
    bookings_as_guest = relationship("Booking", back_populates="guest", cascade="all, delete-orphan")
    # reviews e chats serão definidos nos respectivos arquivos usando back_populates
