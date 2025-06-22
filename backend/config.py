# backend/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, HttpUrl
from typing import List, Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App Settings
    APP_NAME: str = "Flawless FastAPI Backend"
    APP_DESCRIPTION: str = "A production-ready FastAPI application"
    APP_VERSION: str = "0.1.0"
    APP_SECRET_KEY: SecretStr = Field(..., description="Secret key for general application security")

    # Database Settings (PostgreSQL)
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: SecretStr = Field(..., description="PostgreSQL database password")
    POSTGRES_DB: str = "flawless_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = Field(..., description="Full PostgreSQL connection URL")

    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[SecretStr] = None # Optional Redis password

    # Session Settings
    SESSION_SECRET_KEY: SecretStr = Field(..., description="Secret key for signing session cookies")
    SESSION_COOKIE_NAME: str = "flawless_session"
    SESSION_COOKIE_DOMAIN: Optional[str] = None # Set to your frontend domain in production
    SESSION_COOKIE_SAMESITE: str = "Lax" # 'Lax', 'Strict', 'None'
    SESSION_COOKIE_SECURE: bool = False # True in production (requires HTTPS)
    SESSION_COOKIE_HTTPONLY: bool = True # Always True for security
    SESSION_IDLE_TIMEOUT: int = 1800 # 30 minutes
    SESSION_ABSOLUTE_TIMEOUT: int = 86400 # 24 hours

    # CORS Settings
    CORS_ORIGINS: List[HttpUrl] = ["http://localhost:3000"] # Example: ["http://localhost:3000"]
    CORS_METHODS: List[str] = ["*"] # E.g., ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"] # E.g., ["Content-Type", "Authorization", "X-CSRF-Token"]


settings = Settings()