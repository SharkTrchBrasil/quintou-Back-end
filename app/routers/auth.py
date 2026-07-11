from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.auth import RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService
from pydantic import BaseModel
import httpx
from app.config import settings

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
    
    if not settings.CPFHUB_API_KEY:
        # Simulação se a chave não estiver configurada
        return CpfLookupResponse(is_valid=True, real_name="Usuário Teste", birth_date="1990-05-15")
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.cpfhub.io/cpf/{cpf_clean}",
                headers={"x-api-key": settings.CPFHUB_API_KEY},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return CpfLookupResponse(is_valid=True, real_name=data.get("nome", "Usuário Visitante"))
            return CpfLookupResponse(is_valid=False, error_message="CPF não encontrado")
    except Exception:
        return CpfLookupResponse(is_valid=False, error_message="Falha na comunicação com o servidor de CPF")

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
