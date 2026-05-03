"""
Tests for service layer functions.

Unit tests for password hashing, JWT token creation/decoding,
and JSON extraction from LLM responses. These do not require a
database or HTTP client.
"""

from datetime import timedelta

import pytest
from jose import JWTError

from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.summary_service import _extract_json_from_response


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_and_verify_password(self) -> None:
        """Hash a password then verify it with the correct plaintext."""
        plain = "my_secure_password123"
        hashed = hash_password(plain)

        # The hash should differ from the plaintext
        assert hashed != plain
        # Verification should succeed with the correct password
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self) -> None:
        """Verify a wrong password against a hash, expect False."""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_and_decode_token(self) -> None:
        """Create a JWT token and decode it, expect matching user_id."""
        user_id = "test-user-123"
        token = create_access_token(data={"sub": user_id})
        token_data = decode_access_token(token)

        assert token_data.user_id == user_id

    def test_decode_expired_token(self) -> None:
        """Create an already-expired token and decode it, expect JWTError."""
        token = create_access_token(
            data={"sub": "expired-user"},
            expires_delta=timedelta(seconds=-10),
        )
        with pytest.raises(JWTError):
            decode_access_token(token)


class TestJsonExtraction:
    """Tests for JSON extraction from LLM responses."""

    def test_extract_json_from_response(self) -> None:
        """Extract JSON from a markdown code-block-wrapped LLM response."""
        response = (
            "Here is the summary:\n"
            "```json\n"
            '{"summary": "Meeting about Q4 goals", "key_decisions": ["Increase budget"], '
            '"action_items": ["Prepare report"], "participants": ["Alice", "Bob"]}\n'
            "```"
        )
        result = _extract_json_from_response(response)

        assert result["summary"] == "Meeting about Q4 goals"
        assert result["key_decisions"] == ["Increase budget"]
        assert result["action_items"] == ["Prepare report"]
        assert result["participants"] == ["Alice", "Bob"]

    def test_extract_json_plain(self) -> None:
        """Extract JSON from a plain JSON response (no markdown wrapping)."""
        response = (
            '{"summary": "Quick sync meeting", "key_decisions": [], '
            '"action_items": [], "participants": []}'
        )
        result = _extract_json_from_response(response)

        assert result["summary"] == "Quick sync meeting"
        assert result["key_decisions"] == []
        assert result["action_items"] == []
        assert result["participants"] == []
