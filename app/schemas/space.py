from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal
from app.schemas.common import BaseSchema
from app.models.space import SpaceCategory, CancellationPolicy, AddonPricingType, ListingType, ListingPricingMode
from app.schemas.user import UserSummary

class AvailabilityRuleBase(BaseSchema):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str
    is_available: bool = True
    price_override: Optional[Decimal] = None

class AvailabilityRuleCreate(AvailabilityRuleBase):
    pass

class AvailabilityRuleResponse(AvailabilityRuleBase):
    id: UUID

class SpacePricingTierBase(BaseSchema):
    min_guests: int
    max_guests: int
    price_per_hour: Decimal
    original_price: Optional[Decimal] = None

class SpacePricingTierCreate(SpacePricingTierBase):
    pass

class SpacePricingTierResponse(SpacePricingTierBase):
    id: UUID

class SpaceAddonBase(BaseSchema):
    name: str
    description: Optional[str] = None
    pricing_type: AddonPricingType = AddonPricingType.FLAT
    price: Decimal
    icon: Optional[str] = None

class SpaceAddonCreate(SpaceAddonBase):
    pass

class SpaceAddonResponse(SpaceAddonBase):
    id: UUID
    is_active: bool

class SpaceImageBase(BaseSchema):
    url: str
    media_type: str = "IMAGE"
    is_cover: bool = False
    order: int = 0

class SpaceImageCreate(SpaceImageBase):
    pass

class SpaceImageResponse(SpaceImageBase):
    id: UUID

class SpaceBase(BaseSchema):
    listing_type: ListingType = ListingType.SPACE
    title: str
    description: str
    category: SpaceCategory
    
    # Location
    address_line: str
    city: str
    state: str
    zip_code: str
    neighborhood: str
    
    # Pricing
    pricing_mode: ListingPricingMode = ListingPricingMode.PER_HOUR
    price: Decimal  # Valor base (interpretação depende do pricing_mode)
    price_per_hour: Optional[Decimal] = None  # Compat: usado se pricing_mode == PER_HOUR
    weekday_discount_percent: int = 0
    
    # Entrega (para EQUIPMENT)
    delivery_available: bool = False
    delivery_fee: Decimal = Decimal('0.00')
    delivery_radius_km: Optional[int] = None
    delivery_description: Optional[str] = None
    
    # Details
    space_type: Optional[str] = None
    size_length: Optional[float] = None
    size_width: Optional[float] = None
    depth_min: Optional[float] = None
    depth_max: Optional[float] = None
    is_outdoor: bool = True
    is_ada_friendly: bool = False
    accessibility_description: Optional[str] = None
    num_courts: Optional[int] = None
    court_type: Optional[str] = None
    area_sqft: Optional[int] = None
    
    # Rules
    allows_parties: bool = False
    allows_smoking: bool = False
    allows_alcohol: bool = False
    allows_loud_music: bool = False
    rules: Optional[str] = None
    
    # Limits
    min_hours: int = 2
    max_hours: int = 12
    max_guests: Optional[int] = None  # Opcional para equipamentos
    allows_pets: bool = False
    pet_rules: Optional[str] = None
    allows_children: bool = True
    allows_infants: bool = True
    
    # Additional Info
    check_in_type: Optional[str] = None
    has_restroom: bool = False
    restroom_description: Optional[str] = None
    
    has_parking: bool = False
    parking_description: Optional[str] = None
    parking_capacity: Optional[int] = None
    has_street_parking: bool = False
    has_paid_parking: bool = False
    has_parking_lot: bool = False
    
    privacy_level: Optional[str] = None
    privacy_description: Optional[str] = None
    tour_360_url: Optional[str] = None
    
    amenities: List[str] = []
    tags: List[str] = []
    
    cancellation_policy: CancellationPolicy = CancellationPolicy.FLEXIVEL
    cancellation_hours_before: int = 24
    security_deposit: Decimal = Decimal('0.00')
    requires_approval: bool = True

class SpaceCreate(SpaceBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability_rules: List[AvailabilityRuleCreate] = []
    pricing_tiers: List[SpacePricingTierCreate] = []
    addons: List[SpaceAddonCreate] = []

class SpaceUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    pricing_mode: Optional[ListingPricingMode] = None
    price: Optional[Decimal] = None
    price_per_hour: Optional[Decimal] = None
    delivery_available: Optional[bool] = None
    delivery_fee: Optional[Decimal] = None
    max_guests: Optional[int] = None
    amenities: Optional[List[str]] = None
    rules: Optional[str] = None
    is_active: Optional[bool] = None

class SpaceResponse(SpaceBase):
    id: UUID
    host_id: UUID
    latitude: Optional[float]
    longitude: Optional[float]
    badges: List[str]
    is_active: bool
    is_approved: bool
    is_featured: bool
    is_highly_rebooked: bool
    average_rating: float
    total_reviews: int
    images: List[SpaceImageResponse]
    availability_rules: List[AvailabilityRuleResponse]
    pricing_tiers: List[SpacePricingTierResponse]
    addons: List[SpaceAddonResponse]
    host: UserSummary
    created_at: datetime

class SpaceSummary(BaseSchema):
    id: UUID
    listing_type: ListingType = ListingType.SPACE
    title: str
    category: SpaceCategory
    city: str
    state: str
    neighborhood: str
    pricing_mode: ListingPricingMode = ListingPricingMode.PER_HOUR
    price: Decimal
    price_per_hour: Optional[Decimal] = None
    max_guests: Optional[int] = None
    average_rating: float
    total_reviews: int
    is_featured: bool
    is_highly_rebooked: bool
    delivery_available: bool = False
    cover_image: Optional[SpaceImageResponse] = None
    distance_km: Optional[float] = None # Para buscas geográficas
