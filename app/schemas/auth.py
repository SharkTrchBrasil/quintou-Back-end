from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class AcceptTermsRequest(BaseModel):
    version: str
    ip_address: Optional[str] = None
