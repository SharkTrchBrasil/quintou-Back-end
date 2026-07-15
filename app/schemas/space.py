from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from decimal import Decimal
from app.schemas.common import BaseSchema
from app.models.space import CancellationPolicy, AddonPricingType, ListingType, ListingPricingMode
from app.schemas.user import UserSummary
from app.schemas.category import CategoryResponse

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

class BlockedDateBase(BaseSchema):
    date: str
    reason: Optional[str] = None

class BlockedDateCreate(BlockedDateBase):
    pass

class BlockedDateResponse(BlockedDateBase):
    id: UUID

class AvailabilityExceptionBase(BaseSchema):
    date: str
    start_time: str
    end_time: str
    is_available: bool = True
    reason: Optional[str] = None

class AvailabilityExceptionCreate(AvailabilityExceptionBase):
    pass

class AvailabilityExceptionResponse(AvailabilityExceptionBase):
    id: UUID

class CustomPricingBase(BaseSchema):
    date: str
    price_per_hour: Decimal

class CustomPricingCreate(CustomPricingBase):
    pass

class CustomPricingResponse(CustomPricingBase):
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
    category_id: UUID
    
    # Location
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    neighborhood: Optional[str] = None
    
    # Pricing
    pricing_mode: ListingPricingMode = ListingPricingMode.PER_HOUR
    price: Decimal  # Valor base (interpretação depende do pricing_mode)
    price_per_hour: Optional[Decimal] = None  # Compat: usado se pricing_mode == PER_HOUR
    price_per_hour_weekend: Optional[Decimal] = None
    price_per_hour_holiday: Optional[Decimal] = None
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
    allows_commercial: bool = False
    has_heated_pool: bool = False
    has_hot_tub: bool = False
    rules: Optional[str] = None
    
    # Limits
    min_hours: int = 2
    max_hours: int = 12
    buffer_minutes: int = 0
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
    
    # SERVICE fields
    service_area_description: Optional[str] = None
    years_experience: Optional[int] = None
    portfolio_url: Optional[str] = None
    
    # VEHICLE fields
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_length_ft: Optional[float] = None
    engine_hp: Optional[int] = None
    has_captain: Optional[bool] = False
    requires_license: Optional[bool] = False
    embark_location: Optional[str] = None
    
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
    blocked_dates: List[BlockedDateCreate] = []
    availability_exceptions: List[AvailabilityExceptionCreate] = []
    custom_pricing: List[CustomPricingCreate] = []

    @model_validator(mode='after')
    def validate_by_listing_type(self):
        lt = self.listing_type
        if lt == ListingType.SPACE:
            if not self.max_guests:
                raise ValueError("max_guests é obrigatório para SPACE")
            if not self.address_line:
                raise ValueError("Endereço é obrigatório para SPACE")
        elif lt == ListingType.SERVICE:
            if not self.service_area_description and not self.address_line:
                raise ValueError("Informe a área de atuação ou endereço")
        elif lt == ListingType.VEHICLE:
            if not self.max_guests:
                raise ValueError("Capacidade de passageiros é obrigatória para veículos")
        return self

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
    # SERVICE fields
    service_area_description: Optional[str] = None
    years_experience: Optional[int] = None
    portfolio_url: Optional[str] = None
    # VEHICLE fields
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_length_ft: Optional[float] = None
    engine_hp: Optional[int] = None
    has_captain: Optional[bool] = None
    requires_license: Optional[bool] = None
    embark_location: Optional[str] = None

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
    total_views: int
    images: List[SpaceImageResponse]
    availability_rules: List[AvailabilityRuleResponse]
    pricing_tiers: List[SpacePricingTierResponse]
    addons: List[SpaceAddonResponse]
    blocked_dates: List[BlockedDateResponse] = []
    availability_exceptions: List[AvailabilityExceptionResponse] = []
    custom_pricing: List[CustomPricingResponse] = []
    host: UserSummary
    category: CategoryResponse
    created_at: datetime

class SpaceSummary(BaseSchema):
    id: UUID
    listing_type: ListingType = ListingType.SPACE
    title: str
    category: CategoryResponse
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
