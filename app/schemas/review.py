from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.common import BaseSchema
from app.models.review import ReviewType

class ReviewBase(BaseSchema):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    event_type: Optional[str] = None

class ReviewCreate(ReviewBase):
    booking_id: UUID
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewResponse(ReviewBase):
    id: UUID
    booking_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    space_id: Optional[UUID]
    type: ReviewType
    cleanliness_rating: Optional[int]
    accuracy_rating: Optional[int]
    communication_rating: Optional[int]
    created_at: datetime
