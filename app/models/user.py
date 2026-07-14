import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class UserRole(str, enum.Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"

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
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verificações & Segurança (KYC)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    document_type = Column(String, nullable=True) # "RG" ou "CNH"
    document_url = Column(String, nullable=True)
    selfie_url = Column(String, nullable=True)
    address_proof_url = Column(String, nullable=True)
    last_device_id = Column(String, nullable=True)
    kyc_status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Badges de Host
    is_verified_host = Column(Boolean, default=False)
    is_pro_host = Column(Boolean, default=False)
    hosting_since = Column(DateTime(timezone=True), nullable=True)
    avg_response_time_minutes = Column(Integer, nullable=True)
    
    stripe_account_id = Column(String, nullable=True, unique=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_account_status = Column(String, default="pending")
    stripe_onboarding_complete = Column(Boolean, default=False)
    
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    firebase_token = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    spaces = relationship("Space", back_populates="host", cascade="all, delete-orphan")
    bookings_as_guest = relationship("Booking", back_populates="guest", cascade="all, delete-orphan")
    devices = relationship("DeviceFingerprint", back_populates="user", cascade="all, delete-orphan")
    terms_acceptances = relationship("TermsAcceptance", back_populates="user", cascade="all, delete-orphan")
    # reviews e chats serão definidos nos respectivos arquivos usando back_populates

class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False, index=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    app_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_primary = Column(Boolean, default=False)

    user = relationship("User", back_populates="devices")

class Blacklist(Base):
    __tablename__ = "blacklists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False, index=True) # "EMAIL", "PHONE", "DEVICE", "IP"
    value = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TermsAcceptance(Base):
    __tablename__ = "terms_acceptances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    version = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="terms_acceptances")
