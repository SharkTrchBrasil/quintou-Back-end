from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.common import BaseSchema

class CategoryAmenityResponse(BaseSchema):
    id: UUID
    name: str
    icon: Optional[str] = None

class CategoryResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    icon: str
    description: Optional[str] = None
    parent_group: Optional[str] = None
    listing_type: str
    order: int
    is_active: bool
    amenities_config: List[CategoryAmenityResponse] = []
