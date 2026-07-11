from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import BaseSchema

class UserBase(BaseSchema):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    cpf: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=8)
    is_host: bool = False

class UserLogin(BaseSchema):
    email: EmailStr
    password: str

class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    document_type: Optional[str] = None
    document_url: Optional[str] = None
    selfie_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    is_host: bool
    is_active: bool
    email_verified: bool
    phone_verified: bool
    kyc_status: str
    is_verified_host: bool
    is_pro_host: bool
    hosting_since: Optional[datetime] = None
    avg_response_time_minutes: Optional[int] = None
    average_rating: float
    total_reviews: int
    last_seen_at: Optional[datetime] = None
    is_online: bool = False # Idealmente isso seria calculado com base no last_seen_at na hora da resposta
    created_at: datetime
    
class UserSummary(BaseSchema):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    is_verified_host: bool
    is_pro_host: bool
    average_rating: float
    total_reviews: int

class Token(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
