import os
import secrets
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "campusconnect.db"


class Settings(BaseSettings):
    """Application Settings"""
    
    # App
    APP_NAME: str = os.getenv("APP_NAME", "CampusConnect")
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{DEFAULT_DB_PATH.as_posix()}"
    )
    DATABASE_ECHO: bool = DEBUG
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # MongoDB document store
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "campusconnect")
    MONGODB_ENABLED: bool = os.getenv("MONGODB_ENABLED", "True") == "True"
    
    # JWT
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    EXPOSE_RESET_OTP: bool = os.getenv("EXPOSE_RESET_OTP", "False") == "True"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_REDIRECT_URI: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/linkedin/callback")
    
    # Payment
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY: str = os.getenv("STRIPE_PUBLIC_KEY", "")
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TIMEOUT_SECONDS: float = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
    AI_RATE_LIMIT_PER_USER_PER_MINUTE: int = int(os.getenv("AI_RATE_LIMIT_PER_USER_PER_MINUTE", "20"))
    AI_RATE_LIMIT_GLOBAL_PER_MINUTE: int = int(os.getenv("AI_RATE_LIMIT_GLOBAL_PER_MINUTE", "300"))
    RESUME_MAX_CHARS: int = int(os.getenv("RESUME_MAX_CHARS", "20000"))
    RESUME_MAX_FILE_SIZE_BYTES: int = int(os.getenv("RESUME_MAX_FILE_SIZE_BYTES", str(2 * 1024 * 1024)))
    RESUME_ALLOWED_EXTENSIONS: str = os.getenv("RESUME_ALLOWED_EXTENSIONS", ".txt,.pdf,.doc,.docx")
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET_NAME: str = os.getenv("AWS_S3_BUCKET_NAME", "campusconnect")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Sentry
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    
    # CORS
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return configured browser origins as a normalized list."""
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Rate Limit
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Platform Commission
    PLATFORM_COMMISSION_MIN: float = 0.10
    PLATFORM_COMMISSION_MAX: float = 0.20
    PLATFORM_COMMISSION_DEFAULT: float = 0.15
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_production_like(self) -> bool:
        return self.ENVIRONMENT in {"production", "staging"}

    @property
    def resume_allowed_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.RESUME_ALLOWED_EXTENSIONS.split(",") if item.strip()}

    @model_validator(mode="after")
    def validate_security_configuration(self):
        placeholders = {
            "your-secret-key-change-in-production",
            "your-super-secret-key-change-this-in-production",
            "replace-with-a-random-long-secret-key",
            "replace-with-a-long-random-value",
            "change-me",
            "secret",
        }
        secret = (self.SECRET_KEY or "").strip()

        if not secret:
            if self.is_production_like:
                raise ValueError("SECRET_KEY must be configured for this environment")
            self.SECRET_KEY = secrets.token_urlsafe(64)
            return self

        if len(secret) < 32 or secret.lower() in placeholders:
            if self.is_production_like:
                raise ValueError("SECRET_KEY is not secure for this environment")
            self.SECRET_KEY = secrets.token_urlsafe(64)
            return self

        self.SECRET_KEY = secret
        return self


settings = Settings()
