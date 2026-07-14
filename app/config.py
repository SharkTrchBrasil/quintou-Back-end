from typing import List, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Quintou API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] | str = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str
    
    # JWT Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    FIREBASE_CREDENTIALS_JSON: str | None = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CPF Hub
    CPFHUB_API_KEY: str | None = None
    
    # Mapbox
    MAPBOX_ACCESS_TOKEN: str | None = None
    
    # Didit (KYC)
    DIDIT_API_KEY: str | None = None
    DIDIT_WEBHOOK_SECRET: str | None = None
    DIDIT_WORKFLOW_ID: str | None = None
    
    # Email Configuration
    EMAIL_FROM: str = "noreply@quintou.com"
    
    # SendGrid (recomendado para produção)
    SENDGRID_API_KEY: str | None = None
    
    # SMTP (alternativa)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    
    # Frontend URL (para links de reset de senha)
    FRONTEND_URL: str = "https://app.quintou.com"
    
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
