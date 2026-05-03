"""
Comprehensive tests for the TokenService.

Covers access token creation, refresh token creation, token verification,
expired token handling, invalid token handling, and token blacklisting.
"""

from datetime import timedelta

import pytest
from jose import JWTError

from app.services.token_service import TokenService
from app.schemas.auth import TokenData


class TestCreateAccessToken:
    """Tests for TokenService.create_access_token."""

    def test_create_access_token(self) -> None:
        """Create an access token and verify it can be decoded."""
        user_id = "test-user-123"
        token = TokenService.create_access_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        token_data = TokenService.decode_token(token, expected_type="access")
        assert token_data.user_id == user_id
        assert token_data.token_type == "access"
        assert token_data.jti is not None

    def test_create_access_token_with_custom_expiry(self) -> None:
        """Create an access token with a custom expiration delta."""
        user_id = "test-user-456"
        token = TokenService.create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=2),
        )

        token_data = TokenService.decode_token(token, expected_type="access")
        assert token_data.user_id == user_id

    def test_create_access_token_type_is_access(self) -> None:
        """Verify that the token type claim is 'access'."""
        token = TokenService.create_access_token(data={"sub": "user"})
        token_data = TokenService.decode_token(token, expected_type="access")
        assert token_data.token_type == "access"

    def test_create_access_token_has_jti(self) -> None:
        """Verify that each access token gets a unique JTI."""
        token1 = TokenService.create_access_token(data={"sub": "user1"})
        token2 = TokenService.create_access_token(data={"sub": "user1"})

        data1 = TokenService.decode_token(token1, expected_type="access")
        data2 = TokenService.decode_token(token2, expected_type="access")

        assert data1.jti is not None
        assert data2.jti is not None
        assert data1.jti != data2.jti


class TestCreateRefreshToken:
    """Tests for TokenService.create_refresh_token."""

    def test_create_refresh_token(self) -> None:
        """Create a refresh token and verify it can be decoded."""
        user_id = "test-user-789"
        token = TokenService.create_refresh_token(data={"sub": user_id})

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        token_data = TokenService.decode_token(token, expected_type="refresh")
        assert token_data.user_id == user_id
        assert token_data.token_type == "refresh"
        assert token_data.jti is not None

    def test_create_refresh_token_with_custom_expiry(self) -> None:
        """Create a refresh token with a custom expiration delta."""
        user_id = "test-user-999"
        token = TokenService.create_refresh_token(
            data={"sub": user_id},
            expires_delta=timedelta(days=14),
        )

        token_data = TokenService.decode_token(token, expected_type="refresh")
        assert token_data.user_id == user_id

    def test_create_refresh_token_type_is_refresh(self) -> None:
        """Verify that the token type claim is 'refresh'."""
        token = TokenService.create_refresh_token(data={"sub": "user"})
        token_data = TokenService.decode_token(token, expected_type="refresh")
        assert token_data.token_type == "refresh"

    def test_refresh_token_rejected_as_access(self) -> None:
        """Verify that a refresh token is rejected when expecting an access token."""
        token = TokenService.create_refresh_token(data={"sub": "user"})

        with pytest.raises(JWTError, match="Invalid token type"):
            TokenService.decode_token(token, expected_type="access")

    def test_access_token_rejected_as_refresh(self) -> None:
        """Verify that an access token is rejected when expecting a refresh token."""
        token = TokenService.create_access_token(data={"sub": "user"})

        with pytest.raises(JWTError, match="Invalid token type"):
            TokenService.decode_token(token, expected_type="refresh")


class TestVerifyExpiredToken:
    """Tests for verifying expired tokens."""

    def test_verify_expired_token(self) -> None:
        """Verify that an expired token raises JWTError."""
        # Create a token that expired 10 seconds ago
        token = TokenService.create_access_token(
            data={"sub": "expired-user"},
            expires_delta=timedelta(seconds=-10),
        )

        with pytest.raises(JWTError):
            TokenService.decode_token(token)

    def test_verify_expired_refresh_token(self) -> None:
        """Verify that an expired refresh token raises JWTError."""
        token = TokenService.create_refresh_token(
            data={"sub": "expired-user"},
            expires_delta=timedelta(seconds=-10),
        )

        with pytest.raises(JWTError):
            TokenService.decode_token(token, expected_type="refresh")


class TestVerifyInvalidToken:
    """Tests for verifying invalid tokens."""

    def test_verify_invalid_token(self) -> None:
        """Verify that an invalid token string raises JWTError."""
        with pytest.raises(JWTError):
            TokenService.decode_token("invalid-token-string")

    def test_verify_empty_token(self) -> None:
        """Verify that an empty token string raises JWTError."""
        with pytest.raises(JWTError):
            TokenService.decode_token("")

    def test_verify_tampered_token(self) -> None:
        """Verify that a tampered token raises JWTError."""
        token = TokenService.create_access_token(data={"sub": "user"})
        tampered = token + "tampered"

        with pytest.raises(JWTError):
            TokenService.decode_token(tampered)

    def test_decode_without_expected_type(self) -> None:
        """Verify that decoding without specifying expected_type works for any valid token."""
        access_token = TokenService.create_access_token(data={"sub": "user1"})
        refresh_token = TokenService.create_refresh_token(data={"sub": "user2"})

        # Both should decode successfully without type validation
        access_data = TokenService.decode_token(access_token)
        refresh_data = TokenService.decode_token(refresh_token)

        assert access_data.user_id == "user1"
        assert refresh_data.user_id == "user2"


class TestBlacklistToken:
    """Tests for TokenService.blacklist_token."""

    def test_blacklist_token(self) -> None:
        """Blacklist a token and verify it's rejected on decode."""
        token = TokenService.create_refresh_token(data={"sub": "user-to-blacklist"})

        # Token should be valid before blacklisting
        token_data = TokenService.decode_token(token, expected_type="refresh")
        assert token_data.user_id == "user-to-blacklist"

        # Blacklist the token
        TokenService.blacklist_token(token)

        # Token should now be rejected
        with pytest.raises(JWTError, match="revoked"):
            TokenService.decode_token(token, expected_type="refresh")

    def test_blacklist_access_token(self) -> None:
        """Blacklist an access token and verify it's rejected."""
        token = TokenService.create_access_token(data={"sub": "user-to-blacklist"})

        # Valid before blacklisting
        TokenService.decode_token(token, expected_type="access")

        # Blacklist
        TokenService.blacklist_token(token)

        # Rejected after blacklisting
        with pytest.raises(JWTError, match="revoked"):
            TokenService.decode_token(token, expected_type="access")

    def test_blacklist_invalid_token_raises(self) -> None:
        """Blacklisting an invalid token string raises JWTError."""
        with pytest.raises(JWTError):
            TokenService.blacklist_token("invalid-token-string")

    def test_non_blacklisted_token_still_works(self) -> None:
        """Verify that non-blacklisted tokens continue to work."""
        token1 = TokenService.create_access_token(data={"sub": "user1"})
        token2 = TokenService.create_access_token(data={"sub": "user2"})

        # Blacklist only token1
        TokenService.blacklist_token(token1)

        # token1 should be rejected
        with pytest.raises(JWTError):
            TokenService.decode_token(token1)

        # token2 should still work
        token_data = TokenService.decode_token(token2, expected_type="access")
        assert token_data.user_id == "user2"


class TestRefreshAccessToken:
    """Tests for TokenService.refresh_access_token."""

    def test_refresh_access_token(self) -> None:
        """Create a new access token from a valid refresh token."""
        user_id = "refresh-test-user"
        refresh_token = TokenService.create_refresh_token(data={"sub": user_id})

        new_access_token, returned_user_id = TokenService.refresh_access_token(
            refresh_token
        )

        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 0
        assert returned_user_id == user_id

        # Verify the new access token is valid
        token_data = TokenService.decode_token(new_access_token, expected_type="access")
        assert token_data.user_id == user_id

    def test_refresh_with_blacklisted_token(self) -> None:
        """Refresh with a blacklisted token raises JWTError."""
        refresh_token = TokenService.create_refresh_token(data={"sub": "user"})
        TokenService.blacklist_token(refresh_token)

        with pytest.raises(JWTError):
            TokenService.refresh_access_token(refresh_token)

    def test_refresh_with_access_token_fails(self) -> None:
        """Trying to refresh with an access token (wrong type) raises JWTError."""
        access_token = TokenService.create_access_token(data={"sub": "user"})

        with pytest.raises(JWTError):
            TokenService.refresh_access_token(access_token)
