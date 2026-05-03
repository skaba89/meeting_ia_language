"""Core utilities for MeetingAI Copilot."""
from .logging import setup_logging, get_logger
from .exceptions import (
    MeetingAIError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from .validators import (
    SUPPORTED_LANGUAGES,
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    validate_language_code,
    validate_file_extension,
    validate_file_size,
    sanitize_text,
    validate_password_strength,
    validate_email,
)
from .metrics import metrics, MetricsCollector, TimerContext

__all__ = [
    "setup_logging",
    "get_logger",
    "MeetingAIError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ExternalServiceError",
    "FileTooLargeError",
    "UnsupportedFileTypeError",
    "SUPPORTED_LANGUAGES",
    "ALLOWED_AUDIO_EXTENSIONS",
    "MAX_FILE_SIZE_BYTES",
    "validate_language_code",
    "validate_file_extension",
    "validate_file_size",
    "sanitize_text",
    "validate_password_strength",
    "validate_email",
    "metrics",
    "MetricsCollector",
    "TimerContext",
]
