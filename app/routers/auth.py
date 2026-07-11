from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.auth import RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService
from pydantic import BaseModel

class CpfLookupRequest(BaseModel):
    cpf: str

class CpfLookupResponse(BaseModel):
    is_valid: bool
    real_name: str | None = None
    birth_date: str | None = None
    error_message: str | None = None

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/lookup-cpf", response_model=CpfLookupResponse)
async def lookup_cpf(request: CpfLookupRequest):
    cpf_clean = ''.join(filter(str.isdigit, request.cpf))
    if len(cpf_clean) != 11:
        return CpfLookupResponse(is_valid=False, error_message="CPF inválido")
    
    # Simulação da consulta na Receita Federal
    return CpfLookupResponse(is_valid=True, real_name="João Silva Pereira", birth_date="1990-05-15")

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.register(user_in)

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.authenticate(user_in)

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.refresh_token(refresh_in)

@router.post("/forgot-password")
async def forgot_password(forgot_in: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.forgot_password(forgot_in)

@router.post("/reset-password")
async def reset_password(reset_in: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.reset_password(reset_in)
