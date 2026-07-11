import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Numeric, Date, Time, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED_BY_GUEST = "CANCELLED_BY_GUEST"
    CANCELLED_BY_HOST = "CANCELLED_BY_HOST"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    total_hours = Column(Integer, nullable=False)
    
    # Guest breakdown
    num_guests = Column(Integer, nullable=False) # Total
    num_adults = Column(Integer, default=0)
    num_children = Column(Integer, default=0)
    num_infants = Column(Integer, default=0)
    num_pets = Column(Integer, default=0)
    
    # Valores
    subtotal = Column(Numeric(10, 2), nullable=False)
    addons_total = Column(Numeric(10, 2), default=0.0)
    delivery_fee = Column(Numeric(10, 2), default=0.0)
    service_fee = Column(Numeric(10, 2), nullable=False)
    host_fee = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False) # subtotal + addons + delivery + service_fee
    host_payout = Column(Numeric(10, 2), nullable=False) # subtotal + addons + delivery - host_fee
    
    # Endereço de entrega (para EQUIPMENT)
    delivery_address = Column(String, nullable=True)
    
    # Depósito de Segurança (Caução)
    deposit_amount = Column(Numeric(10, 2), default=0.0)
    deposit_status = Column(String, default="NONE") # NONE, HELD, RELEASED, CLAIMED
    
    event_type = Column(String, nullable=True) # Ex: "Birthday Party"
    
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    
    guest_message = Column(Text, nullable=True)
    host_response = Column(Text, nullable=True)
    
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    space = relationship("Space", back_populates="bookings")
    guest = relationship("User", back_populates="bookings_as_guest")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="booking", cascade="all, delete-orphan")
    addons = relationship("BookingAddon", back_populates="booking", cascade="all, delete-orphan")

class BookingAddon(Base):
    __tablename__ = "booking_addons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    addon_id = Column(UUID(as_uuid=True), ForeignKey("space_addons.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    booking = relationship("Booking", back_populates="addons")
    addon = relationship("SpaceAddon")
