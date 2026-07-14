from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    event_type: Optional[str] = None

class ReviewCreate(ReviewBase):
    booking_id: UUID
    # Optional detailed ratings (GUEST_TO_HOST only)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewResponse(ReviewBase):
    id: UUID
    booking_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    space_id: Optional[UUID] = None
    type: str
    
    cleanliness_rating: Optional[int] = None
    accuracy_rating: Optional[int] = None
    communication_rating: Optional[int] = None
    value_rating: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
