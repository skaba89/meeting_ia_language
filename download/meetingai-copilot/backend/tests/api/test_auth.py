"""
Comprehensive tests for authentication API endpoints.

Covers user registration, login, token refresh, logout, and profile
retrieval scenarios including validation errors, authentication failures,
duplicate email handling, and token management.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import API_PREFIX


class TestRegister:
    """Tests for the POST /api/v1/auth/register endpoint."""

    async def test_register_success(self, async_client: AsyncClient) -> None:
        """Register a new user with valid data, expect 201 Created."""
        user_data = {
            "email": "newuser@example.com",
            "password": "Securepassword123",
            "full_name": "New User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data
        assert "password" not in data

    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Register with an email that is already taken, expect 409 Conflict."""
        user_data = {
            "email": test_user["email"],
            "password": "Anotherpassword123",
            "full_name": "Another User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        # The app raises ConflictError which maps to 409
        assert response.status_code == 409
        body = response.json()
        # The error handler wraps it in {"error": {"code": ..., "message": ...}}
        error = body.get("error", body)
        assert "already exists" in error.get("message", error.get("detail", ""))

    async def test_register_weak_password(self, async_client: AsyncClient) -> None:
        """Register with a weak password (no uppercase, no digit), expect 422."""
        user_data = {
            "email": "weakpw@example.com",
            "password": "weakpassword",
            "full_name": "Weak PW User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_invalid_email(self, async_client: AsyncClient) -> None:
        """Register with an invalid email format, expect 422 Unprocessable."""
        user_data = {
            "email": "not-an-email",
            "password": "Securepassword123",
            "full_name": "Bad Email User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_missing_fields(self, async_client: AsyncClient) -> None:
        """Register with missing required fields, expect 422."""
        response = await async_client.post(
            f"{API_PREFIX}/auth/register", json={"email": "only@email.com"}
        )

        assert response.status_code == 422

    async def test_register_short_full_name(self, async_client: AsyncClient) -> None:
        """Register with a full_name shorter than 2 chars, expect 422."""
        user_data = {
            "email": "shortname@example.com",
            "password": "Securepassword123",
            "full_name": "A",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_password_no_uppercase(self, async_client: AsyncClient) -> None:
        """Register with a password missing uppercase letters, expect 422."""
        user_data = {
            "email": "nouppercase@example.com",
            "password": "lowercase123",
            "full_name": "No Upper",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_password_no_digit(self, async_client: AsyncClient) -> None:
        """Register with a password missing digits, expect 422."""
        user_data = {
            "email": "nodigit@example.com",
            "password": "NoDigitPassword",
            "full_name": "No Digit",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422


class TestLogin:
    """Tests for the POST /api/v1/auth/login endpoint."""

    async def test_login_success(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Login with correct credentials, expect 200 and JWT tokens."""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"],
        }
        response = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        assert "refresh_token" in data
        assert len(data["refresh_token"]) > 0
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert isinstance(data["expires_in"], int)

    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Login with an incorrect password, expect 401."""
        login_data = {
            "email": test_user["email"],
            "password": "wrongpassword123",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_login_nonexistent_user(self, async_client: AsyncClient) -> None:
        """Login with an email that does not exist, expect 401."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword123",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)

        assert response.status_code == 401


class TestGetMe:
    """Tests for the GET /api/v1/auth/me endpoint."""

    async def test_get_me_authenticated(self, auth_client: AsyncClient) -> None:
        """Get /auth/me with a valid JWT token, expect 200 with user data."""
        response = await auth_client.get(f"{API_PREFIX}/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data
        assert data["is_active"] is True

    async def test_get_me_unauthenticated(self, async_client: AsyncClient) -> None:
        """Get /auth/me without providing a token, expect 401 Unauthorized.

        The custom AuthenticationError exception returns 401 when no
        credentials are provided or credentials are invalid.
        """
        response = await async_client.get(f"{API_PREFIX}/auth/me")

        assert response.status_code == 401


class TestRefreshToken:
    """Tests for the POST /api/v1/auth/refresh endpoint."""

    async def test_refresh_token(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Refresh an access token using a valid refresh token."""
        # First, login to get both tokens
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"],
        }
        login_resp = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        refresh_token = tokens["refresh_token"]

        # Now refresh using the refresh token
        response = await async_client.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        assert "refresh_token" in data
        assert len(data["refresh_token"]) > 0
        # New tokens should be different from the old ones
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != refresh_token

    async def test_refresh_with_invalid_token(self, async_client: AsyncClient) -> None:
        """Refresh with an invalid token string, expect 401."""
        response = await async_client.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": "invalid-token-string"},
        )

        assert response.status_code == 401

    async def test_refresh_with_access_token(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Refresh using an access token instead of a refresh token, expect 401."""
        # Login to get an access token
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"],
        }
        login_resp = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)
        tokens = login_resp.json()
        access_token = tokens["access_token"]

        # Try to refresh using the access token (wrong type)
        response = await async_client.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for the POST /api/v1/auth/logout endpoint."""

    async def test_logout(
        self, auth_client: AsyncClient, test_user: dict
    ) -> None:
        """Logout and verify the refresh token is blacklisted."""
        # Login first to get refresh token
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"],
        }
        login_resp = await auth_client.post(f"{API_PREFIX}/auth/login", json=login_data)
        tokens = login_resp.json()
        refresh_token = tokens["refresh_token"]

        # Logout using the refresh token
        response = await auth_client.post(
            f"{API_PREFIX}/auth/logout",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert "logged out" in data["detail"].lower()

        # Try to use the blacklisted refresh token — it should fail
        refresh_resp = await auth_client.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    async def test_logout_with_invalid_token(self, auth_client: AsyncClient) -> None:
        """Logout with an invalid refresh token, expect 422 validation error."""
        response = await auth_client.post(
            f"{API_PREFIX}/auth/logout",
            json={"refresh_token": "invalid-token-string"},
        )

        # The token_service.blacklist_token will raise JWTError which maps to ValidationError (422)
        assert response.status_code == 422
