"""
Application configuration module using pydantic-settings.

Loads environment variables from .env file with override priority
and provides type-safe configuration access throughout the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Load .env file with override=True so that .env values take precedence
# over system environment variables that may conflict (e.g., DATABASE_URL
# from a parent project's environment).
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=True)

# Insecure default values that must not be used in production
_INSECURE_SECRET_KEYS = {
    "meetingai-super-secret-key-change-in-production-2024",
    "meetingai-prod-secret-key-2026-please-change-me",
    "secret",
    "changeme",
    "change-me",
    "change_in_production",
    "change-me-to-a-very-long-random-secret-key-at-least-32-chars",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string (asyncpg driver).
        SECRET_KEY: Secret key for JWT token signing (required, no insecure defaults).
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token expiration time in minutes.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token expiration time in days.
        GROQ_API_KEY: API key for Groq services.
        OPENROUTER_API_KEY: API key for OpenRouter services.
        WHISPER_MODEL_SIZE: Whisper model size for transcription.
        LLM_PROVIDER: Preferred LLM provider ('groq' or 'openrouter').
        UPLOAD_DIR: Directory for uploaded audio files.
        MAX_UPLOAD_SIZE_MB: Maximum upload file size in megabytes.
        CORS_ORIGINS: Comma-separated list of allowed CORS origins.
        REDIS_URL: Redis connection URL for rate limiting and caching.
        RATE_LIMIT_PER_MINUTE: Maximum number of requests per minute per client.
        GROQ_MODEL: Model name for Groq API calls.
        OPENROUTER_MODEL: Model name for OpenRouter API calls.
        LOG_LEVEL: Logging level for the application.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/meetingai"
    SECRET_KEY: str  # Required - no default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    WHISPER_MODEL_SIZE: str = "base"
    LLM_PROVIDER: str = "groq"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    CORS_ORIGINS: str = "http://localhost:3000"
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 60
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    LOG_LEVEL: str = "INFO"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Reject insecure or well-known default SECRET_KEY values.

        Validates that the SECRET_KEY is not a known insecure default
        and meets the minimum length requirement of 32 characters.
        """
        if v.strip().lower() in _INSECURE_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY is set to a known insecure default. "
                "Please set a strong, unique SECRET_KEY in your environment or .env file."
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long. "
                "Please use a cryptographically strong random key."
            )
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that LOG_LEVEL is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.strip().upper()
        if upper not in valid_levels:
            raise ValueError(
                f"LOG_LEVEL must be one of {valid_levels}, got '{v}'"
            )
        return upper

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
