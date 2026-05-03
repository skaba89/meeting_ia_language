"""
Input validation middleware for the MeetingAI Copilot application.

Provides file upload validation (size, extension), SQL injection detection
in string inputs, and XSS sanitization for text fields.
"""

import logging
import re
from typing import Optional, Set

from fastapi import HTTPException, status, UploadFile
from pydantic import field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File upload validation
# ---------------------------------------------------------------------------

# Maximum allowed file size in bytes (default: 100 MB)
MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024

# Allowed audio file extensions (with leading dot)
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4",
}

# Allowed MIME types for audio files
ALLOWED_MIME_TYPES: Set[str] = {
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/ogg",
    "audio/flac",
    "audio/x-flac",
    "audio/webm",
    "video/mp4",
    "video/webm",
}


def validate_file_upload(
    file: UploadFile,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    allowed_extensions: Optional[Set[str]] = None,
    allowed_mime_types: Optional[Set[str]] = None,
) -> None:
    """Validate an uploaded file's extension, MIME type, and size.

    Args:
        file: The FastAPI UploadFile to validate.
        max_size_bytes: Maximum allowed file size in bytes.
        allowed_extensions: Set of allowed file extensions (with dots).
            Defaults to ALLOWED_AUDIO_EXTENSIONS.
        allowed_mime_types: Set of allowed MIME types.
            Defaults to ALLOWED_MIME_TYPES.

    Raises:
        HTTPException: 400 if the file extension is not allowed.
        HTTPException: 413 if the file exceeds the maximum size.
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_AUDIO_EXTENSIONS
    if allowed_mime_types is None:
        allowed_mime_types = ALLOWED_MIME_TYPES

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    # Extract and validate extension
    filename = file.filename.lower()
    ext = _get_file_extension(filename)
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File extension '{ext}' is not allowed. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    # Validate MIME type if available
    if file.content_type and file.content_type not in allowed_mime_types:
        # Be permissive: some clients send generic MIME types
        # Only reject clearly wrong types (e.g., application/executable)
        dangerous_mime_prefixes = {
            "application/x-executable",
            "application/x-dosexec",
            "application/x-msdownload",
            "application/x-sh",
            "application/x-bat",
        }
        if file.content_type in dangerous_mime_prefixes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type '{file.content_type}' is not allowed for audio uploads.",
            )

    # Validate file size (check Content-Length header first, then read if needed)
    # Note: Content-Length may not always be accurate; this is a preliminary check
    content_length = file.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
            if size > max_size_bytes:
                max_mb = max_size_bytes // (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds the maximum allowed size of {max_mb}MB",
                )
        except ValueError:
            pass  # Ignore invalid Content-Length headers


async def validate_file_size_by_read(
    file: UploadFile,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
) -> bytes:
    """Read and validate file content size.

    Reads the entire file content to verify the size constraint.
    Use this when Content-Length header is not reliable.

    Args:
        file: The FastAPI UploadFile to read and validate.
        max_size_bytes: Maximum allowed file size in bytes.

    Returns:
        The file content as bytes.

    Raises:
        HTTPException: 413 if the file exceeds the maximum size.
    """
    content = await file.read()
    if len(content) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum allowed size of {max_mb}MB",
        )
    # Reset file position so it can be read again downstream
    await file.seek(0)
    return content


def _get_file_extension(filename: str) -> str:
    """Extract the file extension from a filename, including the dot.

    Args:
        filename: The filename to extract the extension from.

    Returns:
        The lowercase extension including the dot (e.g., '.mp3'),
        or an empty string if no extension.
    """
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


# ---------------------------------------------------------------------------
# SQL injection detection
# ---------------------------------------------------------------------------

# Common SQL injection patterns (case-insensitive)
_SQL_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"(\b|\')(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b", re.IGNORECASE),
    re.compile(r"(\b|\')(UNION\s+(ALL\s+)?SELECT)\b", re.IGNORECASE),
    re.compile(r"(--\s*$|/\*|\*/)", re.IGNORECASE),
    re.compile(r"(\b|\')(OR|AND)\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"(\b|\')(OR|AND)\s+['\"]\w+[\"']\s*=\s*['\"]\w+[\"']", re.IGNORECASE),
    re.compile(r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)", re.IGNORECASE),
    re.compile(r"(\b|\')(WAITFOR\s+DELAY|BENCHMARK|SLEEP)\s*\(", re.IGNORECASE),
    re.compile(r"(\b|\')(CHAR|CONCAT|GROUP_CONCAT|LOAD_FILE|INTO\s+(OUT|DUMP)FILE)\s*\(", re.IGNORECASE),
]

# Fields that are exempt from SQL injection checks (e.g., passwords which may
# legitimately contain special characters)
_SQL_INJECTION_EXEMPT_FIELDS: Set[str] = {"password", "hashed_password"}


def detect_sql_injection(value: str, field_name: str = "") -> bool:
    """Detect potential SQL injection patterns in a string value.

    Args:
        value: The string value to check for SQL injection patterns.
        field_name: The name of the field being checked (used for exemptions).

    Returns:
        True if a potential SQL injection pattern is detected, False otherwise.
    """
    if field_name.lower() in _SQL_INJECTION_EXEMPT_FIELDS:
        return False

    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            logger.warning(
                "Potential SQL injection detected in field '%s': pattern matched '%s'",
                field_name,
                pattern.pattern,
            )
            return True

    return False


def validate_string_input(value: str, field_name: str = "") -> str:
    """Validate a string input for SQL injection patterns.

    Args:
        value: The string value to validate.
        field_name: The name of the field being validated.

    Returns:
        The validated string value (unchanged if no issues).

    Raises:
        HTTPException: 400 if SQL injection patterns are detected.
    """
    if detect_sql_injection(value, field_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input contains potentially dangerous content. Please review your input.",
        )
    return value


# ---------------------------------------------------------------------------
# XSS sanitization
# ---------------------------------------------------------------------------

# HTML/XSS patterns to strip or escape
_XSS_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Script tags (opening and closing)
    (re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL), ""),
    # Script opening tag (self-closing or unclosed)
    (re.compile(r"<\s*script[^>]*/?\s*>", re.IGNORECASE), ""),
    # Event handler attributes (onclick, onload, onerror, etc.)
    (re.compile(r'\bon\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE), ""),
    # javascript: protocol in href/src attributes
    (re.compile(r'((?:href|src|action|data|formaction)\s*=\s*["\'])\s*javascript:', re.IGNORECASE), r"\1#"),
    # data: protocol with text/html
    (re.compile(r'data\s*:\s*text/html', re.IGNORECASE), "data:text/plain"),
    # iframe, object, embed, applet tags
    (re.compile(r"<\s*/?\s*(iframe|object|embed|applet|form|input|textarea|button|link|meta|base)[^>]*>", re.IGNORECASE), ""),
    # SVG with event handlers
    (re.compile(r"<\s*svg[^>]*on\w+\s*=", re.IGNORECASE), ""),
]

# Fields exempt from XSS sanitization
_XSS_EXEMPT_FIELDS: Set[str] = {"password", "hashed_password"}


def sanitize_xss(value: str, field_name: str = "") -> str:
    """Sanitize a string value by removing or neutralizing XSS patterns.

    Strips potentially dangerous HTML tags, event handler attributes,
    and javascript: protocols while preserving safe content.

    Args:
        value: The string value to sanitize.
        field_name: The name of the field being sanitized (used for exemptions).

    Returns:
        The sanitized string value.
    """
    if field_name.lower() in _XSS_EXEMPT_FIELDS:
        return value

    sanitized = value
    for pattern, replacement in _XSS_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    if sanitized != value:
        logger.info(
            "XSS content sanitized in field '%s' (original length: %d, sanitized length: %d)",
            field_name,
            len(value),
            len(sanitized),
        )

    return sanitized


def sanitize_and_validate_input(value: str, field_name: str = "") -> str:
    """Apply both XSS sanitization and SQL injection validation to a string.

    First sanitizes the value for XSS, then checks the sanitized value
    for SQL injection patterns.

    Args:
        value: The string value to sanitize and validate.
        field_name: The name of the field being processed.

    Returns:
        The sanitized and validated string value.

    Raises:
        HTTPException: 400 if SQL injection patterns are detected after sanitization.
    """
    sanitized = sanitize_xss(value, field_name)
    validate_string_input(sanitized, field_name)
    return sanitized
