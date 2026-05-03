"""
Comprehensive tests for core validation utilities.

Covers language code validation, password strength checks, email validation,
text sanitization (XSS detection), file extension validation, and file
size validation.
"""

import pytest

from app.core.validators import (
    SUPPORTED_LANGUAGES,
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    validate_language_code,
    validate_password_strength,
    validate_email,
    sanitize_text,
    validate_file_extension,
    validate_file_size,
)


class TestValidateLanguageCode:
    """Tests for the validate_language_code function."""

    def test_validate_language_code_valid(self) -> None:
        """Test valid language codes are accepted and returned lowercased."""
        assert validate_language_code("en") == "en"
        assert validate_language_code("fr") == "fr"
        assert validate_language_code("ES") == "es"
        assert validate_language_code("De") == "de"
        assert validate_language_code("zh") == "zh"
        assert validate_language_code("ja") == "ja"

    def test_validate_language_code_valid_all_supported(self) -> None:
        """Test all supported language codes are accepted."""
        for code in SUPPORTED_LANGUAGES:
            assert validate_language_code(code) == code

    def test_validate_language_code_invalid(self) -> None:
        """Test invalid language codes raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported language code"):
            validate_language_code("xx")

        with pytest.raises(ValueError, match="Unsupported language code"):
            validate_language_code("abc")

        with pytest.raises(ValueError, match="Unsupported language code"):
            validate_language_code("")

    def test_validate_language_code_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from language codes."""
        assert validate_language_code("  en  ") == "en"
        assert validate_language_code(" fr ") == "fr"


class TestValidatePasswordStrength:
    """Tests for the validate_password_strength function."""

    def test_validate_password_strength_valid(self) -> None:
        """Test valid passwords pass validation."""
        assert validate_password_strength("TestPass123") == "TestPass123"
        assert validate_password_strength("SecureP4ss") == "SecureP4ss"
        assert validate_password_strength("MyP@ssw0rd") == "MyP@ssw0rd"

    def test_validate_password_strength_too_short(self) -> None:
        """Test passwords shorter than 8 characters are rejected."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_strength("Short1")

    def test_validate_password_strength_no_uppercase(self) -> None:
        """Test passwords without uppercase letters are rejected."""
        with pytest.raises(ValueError, match="uppercase letter"):
            validate_password_strength("lowercase123")

    def test_validate_password_strength_no_lowercase(self) -> None:
        """Test passwords without lowercase letters are rejected."""
        with pytest.raises(ValueError, match="lowercase letter"):
            validate_password_strength("UPPERCASE123")

    def test_validate_password_strength_no_digit(self) -> None:
        """Test passwords without digits are rejected."""
        with pytest.raises(ValueError, match="digit"):
            validate_password_strength("NoDigitPassword")

    def test_validate_password_strength_too_long(self) -> None:
        """Test passwords longer than 128 characters are rejected."""
        long_pw = "A" * 129 + "a1"
        with pytest.raises(ValueError, match="at most 128 characters"):
            validate_password_strength(long_pw)

    def test_validate_password_strength_exactly_8_chars(self) -> None:
        """Test that a password of exactly 8 characters with all requirements is valid."""
        assert validate_password_strength("Abcd1234") == "Abcd1234"

    def test_validate_password_strength_exactly_128_chars(self) -> None:
        """Test that a password of exactly 128 characters is valid."""
        pw = "A" + "a" * 118 + "1" * 9  # 128 chars total: 1 uppercase, 118 lowercase, 9 digits
        assert len(pw) == 128
        assert validate_password_strength(pw) == pw


class TestValidateEmail:
    """Tests for the validate_email function."""

    def test_validate_email_valid(self) -> None:
        """Test valid emails pass validation and are lowercased."""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("User@Example.COM") == "user@example.com"
        assert validate_email("test.user+tag@domain.co") == "test.user+tag@domain.co"

    def test_validate_email_invalid(self) -> None:
        """Test invalid emails are rejected."""
        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("not-an-email")

        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("@domain.com")

        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("user@")

        with pytest.raises(ValueError, match="Invalid email format"):
            validate_email("user@.com")

    def test_validate_email_too_long(self) -> None:
        """Test emails longer than 254 characters are rejected."""
        # Create an email that passes the format check but exceeds 254 chars
        local_part = "a" * 243  # 243 + 1(@) + 1(b) + 1(.) + 7(abcdefg) = 253 (just under)
        long_email = local_part + "@b.abcdefg"  # 253 chars total - valid
        assert validate_email(long_email) == long_email

        # Now make it exceed 254 chars
        too_long_email = "a" * 245 + "@b.abcdefg"  # 256 chars total
        with pytest.raises(ValueError, match="too long|Invalid email"):
            validate_email(too_long_email)

    def test_validate_email_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from emails."""
        assert validate_email("  user@example.com  ") == "user@example.com"


class TestSanitizeText:
    """Tests for the sanitize_text function."""

    def test_sanitize_text_clean(self) -> None:
        """Test clean text passes sanitization unchanged (except whitespace stripping)."""
        assert sanitize_text("Hello World") == "Hello World"
        assert sanitize_text("Normal text with numbers 123") == "Normal text with numbers 123"

    def test_sanitize_text_xss_script_tag(self) -> None:
        """Test XSS script tags are detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("<script>alert('xss')</script>")

    def test_sanitize_text_xss_javascript_protocol(self) -> None:
        """Test javascript: protocol is detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("javascript:alert('xss')")

    def test_sanitize_text_xss_event_handler(self) -> None:
        """Test event handler attributes are detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("onclick=alert('xss')")

    def test_sanitize_text_xss_iframe(self) -> None:
        """Test iframe tags are detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("<iframe src='evil.com'></iframe>")

    def test_sanitize_text_xss_eval(self) -> None:
        """Test eval() calls are detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("eval('malicious code')")

    def test_sanitize_text_xss_expression(self) -> None:
        """Test CSS expression() calls are detected."""
        with pytest.raises(ValueError, match="dangerous content"):
            sanitize_text("expression(alert('xss'))")

    def test_sanitize_text_strips_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        assert sanitize_text("  hello  ") == "hello"

    def test_sanitize_text_empty(self) -> None:
        """Test empty string returns empty."""
        assert sanitize_text("") == ""
        assert sanitize_text(None) is None  # type: ignore[arg-type]


class TestValidateFileExtension:
    """Tests for the validate_file_extension function."""

    def test_validate_file_extension_valid(self) -> None:
        """Test valid audio file extensions are accepted."""
        assert validate_file_extension("meeting.mp3") == "meeting.mp3"
        assert validate_file_extension("meeting.wav") == "meeting.wav"
        assert validate_file_extension("meeting.m4a") == "meeting.m4a"
        assert validate_file_extension("meeting.ogg") == "meeting.ogg"
        assert validate_file_extension("meeting.flac") == "meeting.flac"
        assert validate_file_extension("meeting.webm") == "meeting.webm"
        assert validate_file_extension("meeting.mp4") == "meeting.mp4"

    def test_validate_file_extension_invalid(self) -> None:
        """Test invalid file extensions are rejected."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_extension("document.pdf")

        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_extension("image.png")

        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_extension("archive.zip")

        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_extension("data.csv")

    def test_validate_file_extension_no_extension(self) -> None:
        """Test files without extension are rejected."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_extension("noextension")

    def test_validate_file_extension_empty_filename(self) -> None:
        """Test empty filename raises ValueError."""
        with pytest.raises(ValueError, match="Filename is required"):
            validate_file_extension("")

    def test_validate_file_extension_case_insensitive(self) -> None:
        """Test file extensions are checked case-insensitively."""
        assert validate_file_extension("meeting.MP3") == "meeting.MP3"
        assert validate_file_extension("meeting.Wav") == "meeting.Wav"


class TestValidateFileSize:
    """Tests for the validate_file_size function."""

    def test_validate_file_size_valid(self) -> None:
        """Test file sizes within limits are accepted."""
        assert validate_file_size(0) == 0
        assert validate_file_size(1024) == 1024
        assert validate_file_size(50 * 1024 * 1024) == 50 * 1024 * 1024  # 50MB
        assert validate_file_size(MAX_FILE_SIZE_BYTES) == MAX_FILE_SIZE_BYTES

    def test_validate_file_size_too_large(self) -> None:
        """Test file sizes exceeding the limit are rejected."""
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_file_size(MAX_FILE_SIZE_BYTES + 1)

        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_file_size(200 * 1024 * 1024)  # 200MB

    def test_validate_file_size_custom_max(self) -> None:
        """Test file size validation with a custom maximum."""
        custom_max = 10 * 1024 * 1024  # 10MB
        assert validate_file_size(5 * 1024 * 1024, max_bytes=custom_max) == 5 * 1024 * 1024
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_file_size(15 * 1024 * 1024, max_bytes=custom_max)
