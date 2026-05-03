"""
Application configuration module using pydantic-settings.

Loads environment variables from .env file and provides
type-safe configuration access throughout the application.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        DATABASE_URL: PostgreSQL connection string (asyncpg driver).
        SECRET_KEY: Secret key for JWT token signing.
        ALGORITHM: JWT signing algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes.
        GROQ_API_KEY: API key for Groq services.
        OPENROUTER_API_KEY: API key for OpenRouter services.
        WHISPER_MODEL_SIZE: Whisper model size for transcription.
        LLM_PROVIDER: Preferred LLM provider ('groq' or 'openrouter').
        UPLOAD_DIR: Directory for uploaded audio files.
        MAX_UPLOAD_SIZE_MB: Maximum upload file size in megabytes.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/meetingai"
    SECRET_KEY: str = "meetingai-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    WHISPER_MODEL_SIZE: str = "base"
    LLM_PROVIDER: str = "groq"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 100

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
