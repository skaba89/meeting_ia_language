"""Common validation utilities for MeetingAI Copilot."""
import re
from typing import Optional

# Supported languages for transcription and translation
SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "sv": "Swedish",
}

# Allowed audio file extensions
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".mp4"}

# Maximum file size (100 MB)
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

# XSS patterns to detect
XSS_PATTERNS = [
    re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<embed[^>]*>", re.IGNORECASE),
    re.compile(r"eval\s*\(", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
]


def validate_language_code(code: str) -> str:
    """Validate that a language code is supported."""
    code = code.lower().strip()
    if code not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language code '{code}'. "
            f"Supported: {', '.join(f'{k} ({v})' for k, v in SUPPORTED_LANGUAGES.items())}"
        )
    return code


def validate_file_extension(filename: str) -> str:
    """Validate that a file has an allowed audio extension."""
    if not filename:
        raise ValueError("Filename is required")

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
        )
    return filename


def validate_file_size(size_bytes: int, max_bytes: int = MAX_FILE_SIZE_BYTES) -> int:
    """Validate that a file size is within allowed limits."""
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise ValueError(f"File size ({actual_mb:.1f}MB) exceeds maximum ({max_mb:.0f}MB)")
    return size_bytes


def sanitize_text(text: str) -> str:
    """Sanitize text input to prevent XSS attacks."""
    if not text:
        return text

    for pattern in XSS_PATTERNS:
        if pattern.search(text):
            raise ValueError("Input contains potentially dangerous content")

    return text.strip()


def validate_password_strength(password: str) -> str:
    """Validate password meets minimum strength requirements."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    return password


def validate_email(email: str) -> str:
    """Validate email format."""
    email = email.strip().lower()
    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    if not pattern.match(email):
        raise ValueError("Invalid email format")
    if len(email) > 254:
        raise ValueError("Email address is too long")
    return email
