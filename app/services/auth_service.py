from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest
from jose import jwt, JWTError
from app.config import settings
from app.utils.i18n import _

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def register(self, user_in: UserCreate) -> User:
        # Verifica se já existe
        existing = await self.get_user_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("email_already_exists")
            )
            
        # TODO: Adicionar verificação de CPF e Telefone únicos aqui
            
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            phone=user_in.phone,
            cpf=user_in.cpf
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
        
    async def authenticate(self, user_in: UserLogin) -> Token:
        user = await self.get_user_by_email(user_in.email)
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_("invalid_credentials")
            )
            
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )

    async def refresh_token(self, refresh_in: RefreshTokenRequest) -> Token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(refresh_in.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if user is None or not user.is_active:
            raise credentials_exception
            
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )

    async def forgot_password(self, forgot_in: ForgotPasswordRequest):
        user = await self.get_user_by_email(forgot_in.email)
        if not user:
            # Avoid user enumeration by returning generic success
            return {"message": "If an account exists, a reset link was sent."}
            
        # TODO: Generate reset token and send email
        return {"message": "If an account exists, a reset link was sent."}

    async def reset_password(self, reset_in: ResetPasswordRequest):
        # TODO: Validate reset token, get user, update password
        # This is a stub since we don't have email/token sending implemented yet
        raise HTTPException(status_code=501, detail="Not implemented")
