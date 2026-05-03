"""
Application configuration loaded from environment variables.
Supports both local SQLite development and Docker PostgreSQL deployment.
Uses API_DATABASE_URL to avoid conflict with the system DATABASE_URL used by Prisma.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the MeetingAI Copilot backend."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "MeetingAI Copilot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PORT: int = 8000

    # ── Database ─────────────────────────────────────────────────
    # Using API_DATABASE_URL to avoid conflict with system DATABASE_URL (Prisma)
    API_DATABASE_URL: str = ""

    @property
    def resolved_database_url(self) -> str:
        """Resolve database URL with sensible defaults."""
        if self.API_DATABASE_URL:
            return self.API_DATABASE_URL
        # Default to SQLite in the app directory
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "meetingai.db")
        return f"sqlite:///{db_path}"

    # ── JWT Authentication ───────────────────────────────────────
    SECRET_KEY: str = "meetingai-dev-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── AI Services ──────────────────────────────────────────────
    # OpenRouter / Groq / OpenAI compatible endpoint
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "openai/gpt-3.5-turbo"

    # Whisper configuration: "local" uses openai-whisper, "api" uses OpenAI API
    WHISPER_MODE: str = "api"
    OPENAI_API_KEY: str = ""

    # ── File Upload ──────────────────────────────────────────────
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_AUDIO_EXTENSIONS: list[str] = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"]

    # ── Translation ──────────────────────────────────────────────
    TRANSLATION_ENABLED: bool = True
    DEFAULT_TARGET_LANG: str = "en"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — loaded once per process."""
    return Settings()
