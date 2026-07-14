from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import RefreshTokenRequest, ForgotPasswordRequest, ResetPasswordRequest, AcceptTermsRequest
from app.utils.validators import validate_password_strength, validate_cpf, validate_phone_br, sanitize_cpf, sanitize_phone
from jose import jwt, JWTError
from app.config import settings
from app.utils.i18n import _
from app.models.user import Blacklist, DeviceFingerprint

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def register(self, user_in: UserCreate) -> User:
        # Valida força da senha
        is_valid_pwd, pwd_error = validate_password_strength(user_in.password)
        if not is_valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=pwd_error
            )
        
        # Verifica se já existe
        existing = await self.get_user_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_("email_already_exists")
            )
            
        # Verifica Blacklist
        blacklist_check = await self.db.execute(
            select(Blacklist).where(Blacklist.value.in_([user_in.email, user_in.cpf, user_in.phone, user_in.device_id]))
        )
        if blacklist_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registro bloqueado por violação dos termos de segurança."
            )
        
        # Verifica CPF único e valida
        if user_in.cpf:
            cpf_clean = sanitize_cpf(user_in.cpf)
            
            # Valida CPF
            is_valid_cpf, cpf_error = validate_cpf(cpf_clean)
            if not is_valid_cpf:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=cpf_error
                )
            
            # Verifica se CPF já está cadastrado
            cpf_check = await self.db.execute(
                select(User).where(User.cpf == cpf_clean)
            )
            if cpf_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado no sistema."
                )
            
            user_in.cpf = cpf_clean  # Salva CPF limpo
        
        # Verifica telefone único e valida
        if user_in.phone:
            phone_clean = sanitize_phone(user_in.phone)
            
            # Valida telefone
            is_valid_phone, phone_error = validate_phone_br(phone_clean)
            if not is_valid_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=phone_error
                )
            
            phone_check = await self.db.execute(
                select(User).where(User.phone == phone_clean)
            )
            if phone_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telefone já cadastrado no sistema."
                )
            
            user_in.phone = phone_clean  # Salva telefone limpo
            
        if user_in.device_id:
            # Verifica se dispositivo está associado a conta banida
            banned_check = await self.db.execute(
                select(User).where(
                    User.last_device_id == user_in.device_id,
                    User.is_active == False
                )
            )
            if banned_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Dispositivo bloqueado por violação dos termos de uso."
                )
            
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            phone=user_in.phone,
            cpf=user_in.cpf,
            is_host=user_in.is_host,
            last_device_id=user_in.device_id
        )
        self.db.add(db_user)
        await self.db.flush()
        
        if user_in.device_id:
            device = DeviceFingerprint(
                user_id=db_user.id,
                device_id=user_in.device_id,
                device_model=user_in.device_model,
                os_version=user_in.os_version,
                app_version=user_in.app_version,
                is_primary=True
            )
            self.db.add(device)
            
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
        
    async def authenticate(self, user_in: UserLogin) -> Token:
        # Verifica Blacklist antes de autenticar
        blacklist_check = await self.db.execute(
            select(Blacklist).where(Blacklist.value.in_([user_in.email, user_in.device_id]))
        )
        if blacklist_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Login bloqueado por violação dos termos de segurança."
            )
            
        user = await self.get_user_by_email(user_in.email)
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_("invalid_credentials")
            )
            
        if user_in.device_id:
            # Verifica se dispositivo está associado a conta banida
            banned_check = await self.db.execute(
                select(User).where(
                    User.last_device_id == user_in.device_id,
                    User.is_active == False
                )
            )
            if banned_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Dispositivo bloqueado por violação dos termos de uso."
                )

            user.last_device_id = user_in.device_id
            
            # Atualiza ou cria fingerprint
            device_check = await self.db.execute(
                select(DeviceFingerprint).where(
                    DeviceFingerprint.user_id == user.id,
                    DeviceFingerprint.device_id == user_in.device_id
                )
            )
            device = device_check.scalars().first()
            if device:
                device.device_model = user_in.device_model or device.device_model
                device.os_version = user_in.os_version or device.os_version
                device.app_version = user_in.app_version or device.app_version
            else:
                new_device = DeviceFingerprint(
                    user_id=user.id,
                    device_id=user_in.device_id,
                    device_model=user_in.device_model,
                    os_version=user_in.os_version,
                    app_version=user_in.app_version
                )
                self.db.add(new_device)
                
            await self.db.commit()
            
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
        
        # Valida força da nova senha
        is_valid_pwd, pwd_error = validate_password_strength(reset_in.new_password)
        if not is_valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=pwd_error
            )
        
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

    async def accept_terms(self, user_id: str, accept_in: AcceptTermsRequest):
        from app.models.user import TermsAcceptance
        
        acceptance = TermsAcceptance(
            user_id=user_id,
            version=accept_in.version,
            ip_address=accept_in.ip_address
        )
        self.db.add(acceptance)
        await self.db.commit()
        return {"message": "Termos aceitos com sucesso."}
