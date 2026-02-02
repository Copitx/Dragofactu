"""
Application configuration using Pydantic Settings.
Loads from environment variables or .env file.
"""
import warnings
import secrets
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List


# Default insecure key - NEVER use in production
_INSECURE_SECRET_KEY = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "Dragofactu API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database - SQLite for development, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./dragofactu_api.db"

    # Security
    SECRET_KEY: str = _INSECURE_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - Set specific origins in production
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Rate limiting
    LOGIN_RATE_LIMIT: int = 5  # attempts
    LOGIN_RATE_WINDOW: int = 300  # seconds (5 min)

    # Email (optional, for future use)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        """Warn if using insecure secret key."""
        if v == _INSECURE_SECRET_KEY:
            warnings.warn(
                "\n" + "="*60 + "\n"
                "⚠️  SECURITY WARNING: Using default SECRET_KEY!\n"
                "Set a secure SECRET_KEY environment variable in production.\n"
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                + "="*60,
                UserWarning
            )
        elif len(v) < 32:
            warnings.warn(
                "⚠️  SECRET_KEY should be at least 32 characters long",
                UserWarning
            )
        return v

    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_origins(cls, v):
        """Warn if allowing all origins."""
        if "*" in v:
            warnings.warn(
                "⚠️  CORS allows all origins (*). Set specific origins in production.",
                UserWarning
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Cache for settings
_settings = None


def get_settings() -> Settings:
    """Get settings instance (cached)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)
