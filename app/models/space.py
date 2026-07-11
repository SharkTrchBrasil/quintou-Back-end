import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, ForeignKey, Enum, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class AddonPricingType(str, enum.Enum):
    FLAT = "FLAT"
    PER_HOUR = "PER_HOUR"
    PER_UNIT = "PER_UNIT"

class ListingType(str, enum.Enum):
    SPACE = "SPACE"         # Espaço físico (piscina, quadra, chácara)
    EQUIPMENT = "EQUIPMENT" # Equipamento para aluguel (pula-pula, mesas)

class ListingPricingMode(str, enum.Enum):
    PER_HOUR = "PER_HOUR"   # Piscina: R$50/hr
    PER_DAY = "PER_DAY"     # Pula-pula: R$150/dia (diária)
    FIXED = "FIXED"         # DJ: R$1.500 o pacote


class CancellationPolicy(str, enum.Enum):
    FLEXIVEL = "FLEXIVEL"
    MODERADA = "MODERADA"
    RIGOROSA = "RIGOROSA"

class Space(Base):
    __tablename__ = "spaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    listing_type = Column(Enum(ListingType), default=ListingType.SPACE, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    
    # Localização
    address_line = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    neighborhood = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Preços
    pricing_mode = Column(Enum(ListingPricingMode), default=ListingPricingMode.PER_HOUR, nullable=False)
    price = Column(Numeric(10, 2), nullable=False) # Valor base (por hora, por dia, ou fixo)
    price_per_hour = Column(Numeric(10, 2), nullable=True) # Mantido para compatibilidade
    weekday_discount_percent = Column(Integer, default=0)
    
    # Entrega (para EQUIPMENT)
    delivery_available = Column(Boolean, default=False)
    delivery_fee = Column(Numeric(10, 2), default=0.0)
    delivery_radius_km = Column(Integer, nullable=True)
    delivery_description = Column(Text, nullable=True)
    
    # Detalhes do Espaço (About the pool)
    space_type = Column(String, nullable=True) # Chlorine, Salt, etc
    size_length = Column(Float, nullable=True)
    size_width = Column(Float, nullable=True)
    depth_min = Column(Float, nullable=True)
    depth_max = Column(Float, nullable=True)
    is_outdoor = Column(Boolean, default=True)
    is_ada_friendly = Column(Boolean, default=False)
    accessibility_description = Column(Text, nullable=True)
    
    # Detalhes extras (Courts/Studios)
    num_courts = Column(Integer, nullable=True)
    court_type = Column(String, nullable=True) # Ex: "Regulation", "Full court"
    area_sqft = Column(Integer, nullable=True)
    
    # House Rules (Booleans)
    allows_parties = Column(Boolean, default=False)
    allows_smoking = Column(Boolean, default=False)
    allows_alcohol = Column(Boolean, default=False)
    allows_loud_music = Column(Boolean, default=False)
    rules = Column(Text, nullable=True) # Regras em texto livre
    
    # Políticas e Limites
    min_hours = Column(Integer, default=2)
    max_hours = Column(Integer, default=12)
    max_guests = Column(Integer, nullable=False)
    allows_pets = Column(Boolean, default=False)
    pet_rules = Column(Text, nullable=True)
    allows_children = Column(Boolean, default=True)
    allows_infants = Column(Boolean, default=True)
    
    # Info adicional
    check_in_type = Column(String, nullable=True) # Ex: "Meet host", "Self check-in"
    has_restroom = Column(Boolean, default=False)
    restroom_description = Column(String, nullable=True)
    
    has_parking = Column(Boolean, default=False)
    parking_description = Column(String, nullable=True)
    parking_capacity = Column(Integer, nullable=True)
    has_street_parking = Column(Boolean, default=False)
    has_paid_parking = Column(Boolean, default=False)
    has_parking_lot = Column(Boolean, default=False)
    
    privacy_level = Column(String, nullable=True) # Ex: "Very Private"
    privacy_description = Column(Text, nullable=True)
    
    tour_360_url = Column(String, nullable=True)
    
    amenities = Column(JSONB, default=[])
    tags = Column(JSONB, default=[]) # Ex: ["Corporate events", "Parties"]
    badges = Column(JSONB, default=[]) # Ex: ["Swimply's Choice Award"]
    
    # Segurança & Moderação
    cancellation_policy = Column(Enum(CancellationPolicy), default=CancellationPolicy.FLEXIVEL)
    cancellation_hours_before = Column(Integer, default=24) # Ex: Full refund se cancelar 24h antes
    security_deposit = Column(Numeric(10, 2), default=0.0)
    requires_approval = Column(Boolean, default=True) # Se falso, é Instant Book
    
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_highly_rebooked = Column(Boolean, default=False)
    
    # Estatísticas
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_bookings = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    host = relationship("User", back_populates="spaces")
    category = relationship("Category")
    images = relationship("SpaceImage", back_populates="space", cascade="all, delete-orphan", order_by="SpaceImage.order")
    availability_rules = relationship("AvailabilityRule", back_populates="space", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="space", cascade="all, delete-orphan")
    pricing_tiers = relationship("SpacePricingTier", back_populates="space", cascade="all, delete-orphan", order_by="SpacePricingTier.min_guests")
    addons = relationship("SpaceAddon", back_populates="space", cascade="all, delete-orphan")
    promotions = relationship("SpacePromotion", back_populates="space", cascade="all, delete-orphan")

class SpacePricingTier(Base):
    __tablename__ = "space_pricing_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    min_guests = Column(Integer, nullable=False)
    max_guests = Column(Integer, nullable=False)
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)
    
    space = relationship("Space", back_populates="pricing_tiers")

class SpaceAddon(Base):
    __tablename__ = "space_addons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pricing_type = Column(Enum(AddonPricingType), default=AddonPricingType.FLAT, nullable=False)
    price = Column(Numeric(10, 2), nullable=False) # 0 = gratuito
    icon = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    space = relationship("Space", back_populates="addons")

class SpaceImage(Base):
    __tablename__ = "space_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    url = Column(String, nullable=False)
    media_type = Column(String, default="IMAGE") # IMAGE, VIDEO
    is_cover = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    space = relationship("Space", back_populates="images")

class AvailabilityRule(Base):
    __tablename__ = "availability_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(UUID(as_uuid=True), ForeignKey("spaces.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0 = Domingo, 6 = Sábado
    start_time = Column(String, nullable=False) # Ex: "08:00"
    end_time = Column(String, nullable=False)   # Ex: "22:00"
    is_available = Column(Boolean, default=True)
    price_override = Column(Numeric(10, 2), nullable=True) # Ex: Preço fds
    
    space = relationship("Space", back_populates="availability_rules")
