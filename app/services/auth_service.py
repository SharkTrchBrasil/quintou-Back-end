from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from datetime import datetime, timezone
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
        
        # Verifica CPF único
        if user_in.cpf:
            cpf_check = await self.db.execute(
                select(User).where(User.cpf == user_in.cpf)
            )
            if cpf_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado no sistema."
                )
        
        # Verifica telefone único
        if user_in.phone:
            phone_check = await self.db.execute(
                select(User).where(User.phone == user_in.phone)
            )
            if phone_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telefone já cadastrado no sistema."
                )
            
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            phone=user_in.phone,
            cpf=user_in.cpf,
            is_host=user_in.is_host
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
        
        # Importa o modelo e serviço
        from app.models.password_reset import PasswordResetToken
        from app.services.email_service import EmailService
        
        # Invalida tokens antigos do usuário
        old_tokens = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None)
            )
        )
        for old_token in old_tokens.scalars().all():
            old_token.used_at = datetime.now(timezone.utc)
        
        # Gera novo token
        token_str = PasswordResetToken.generate_token()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=PasswordResetToken.get_expiration_time()
        )
        self.db.add(reset_token)
        await self.db.commit()
        
        # Gera link de reset (URL do frontend/app)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token_str}"
        
        # Envia email
        email_service = EmailService()
        await email_service.send_password_reset(
            to_email=user.email,
            reset_link=reset_link,
            user_name=user.full_name
        )
        
        return {"message": "If an account exists, a reset link was sent."}

    async def reset_password(self, reset_in: ResetPasswordRequest):
        from app.models.password_reset import PasswordResetToken
        from datetime import datetime, timezone
        
        # Busca token
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == reset_in.token)
        )
        reset_token = result.scalars().first()
        
        if not reset_token:
            raise HTTPException(
                status_code=400, 
                detail="Token de reset inválido."
            )
        
        # Valida token
        if reset_token.is_used:
            raise HTTPException(
                status_code=400, 
                detail="Este token já foi utilizado."
            )
        
        if reset_token.is_expired:
            raise HTTPException(
                status_code=400, 
                detail="Este token expirou. Solicite um novo reset de senha."
            )
        
        # Busca usuário
        user = await self.db.get(User, reset_token.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        # Atualiza senha
        user.hashed_password = get_password_hash(reset_in.new_password)
        
        # Marca token como usado
        reset_token.used_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        return {"message": "Senha redefinida com sucesso."}
