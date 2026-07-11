from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal
from app.schemas.common import BaseSchema
from app.models.promotion import PromotionType

class SpacePromotionBase(BaseSchema):
    name: str
    description: Optional[str] = None
    type: PromotionType
    value: Decimal
    is_active: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_hours: Optional[int] = None
    min_guests: Optional[int] = None

class SpacePromotionCreate(SpacePromotionBase):
    pass

class SpacePromotionUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None

class SpacePromotionResponse(SpacePromotionBase):
    id: UUID
    space_id: UUID
    created_at: datetime
