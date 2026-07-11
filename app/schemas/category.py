from uuid import UUID
from pydantic import BaseModel
from app.schemas.common import BaseSchema

class CategoryResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    icon: str
    listing_type: str
    order: int
    is_active: bool
