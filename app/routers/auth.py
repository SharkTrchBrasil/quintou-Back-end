from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.auth import RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest, AcceptTermsRequest
from app.services.auth_service import AuthService
from app.dependencies import get_current_user


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
    
    if not settings.CPFHUB_API_KEY or settings.CPFHUB_API_KEY == "mock":
        # Retorna um mock de sucesso para facilitar testes
        return CpfLookupResponse(
            is_valid=True,
            real_name="Usuário de Teste",
            birth_date="01/01/1990"
        )
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.cpfhub.io/cpf/{cpf_clean}",
                headers={"x-api-key": settings.CPFHUB_API_KEY},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                real_name = data.get("nome")
                if not real_name or real_name.strip() == "":
                    return CpfLookupResponse(is_valid=False, error_message="Não foi possível obter o nome vinculado a este CPF")
                return CpfLookupResponse(
                    is_valid=True,
                    real_name=real_name.strip(),
                    birth_date=data.get("data_nascimento"),
                )
            elif response.status_code == 404:
                return CpfLookupResponse(is_valid=False, error_message="CPF não encontrado na base da Receita Federal")
            else:
                return CpfLookupResponse(is_valid=False, error_message="Erro ao consultar CPF. Tente novamente.")
    except httpx.TimeoutException:
        return CpfLookupResponse(is_valid=False, error_message="Tempo de resposta esgotado. Tente novamente.")
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

@router.post("/accept-terms")
async def accept_terms(accept_in: AcceptTermsRequest, db: AsyncSession = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    auth_service = AuthService(db)
    return await auth_service.accept_terms(str(current_user.id), accept_in)
