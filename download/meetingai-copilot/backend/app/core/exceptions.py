"""
Custom exception classes for MeetingAI Copilot.
Provides a hierarchy of exceptions that map to HTTP status codes.
"""
from typing import Any, Optional


class MeetingAIError(Exception):
    """Base exception for all MeetingAI errors."""
    
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(MeetingAIError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message, code="AUTHENTICATION_ERROR", status_code=401, details=details)


class AuthorizationError(MeetingAIError):
    """Raised when user lacks permissions."""
    def __init__(self, message: str = "Permission denied", details: Optional[dict] = None):
        super().__init__(message, code="AUTHORIZATION_ERROR", status_code=403, details=details)


class ValidationError(MeetingAIError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error", details: Optional[dict] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class NotFoundError(MeetingAIError):
    """Raised when a resource is not found."""
    def __init__(self, resource: str = "Resource", resource_id: Any = None, details: Optional[dict] = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(msg, code="NOT_FOUND", status_code=404, details=details)


class ConflictError(MeetingAIError):
    """Raised when a conflict occurs (e.g., duplicate email)."""
    def __init__(self, message: str = "Conflict", details: Optional[dict] = None):
        super().__init__(message, code="CONFLICT", status_code=409, details=details)


class RateLimitError(MeetingAIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[dict] = None):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429, details=details)


class ExternalServiceError(MeetingAIError):
    """Raised when an external service (Groq, OpenRouter) fails."""
    def __init__(self, service: str, message: str = "External service error", details: Optional[dict] = None):
        msg = f"{service}: {message}"
        super().__init__(msg, code="EXTERNAL_SERVICE_ERROR", status_code=502, details=details)


class FileTooLargeError(MeetingAIError):
    """Raised when uploaded file exceeds size limit."""
    def __init__(self, max_size_mb: int = 100, details: Optional[dict] = None):
        super().__init__(
            f"File too large. Maximum size is {max_size_mb}MB",
            code="FILE_TOO_LARGE",
            status_code=413,
            details=details,
        )


class UnsupportedFileTypeError(MeetingAIError):
    """Raised when uploaded file type is not supported."""
    def __init__(self, allowed: list = None, details: Optional[dict] = None):
        allowed = allowed or [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"]
        super().__init__(
            f"Unsupported file type. Allowed: {', '.join(allowed)}",
            code="UNSUPPORTED_FILE_TYPE",
            status_code=415,
            details=details,
        )
