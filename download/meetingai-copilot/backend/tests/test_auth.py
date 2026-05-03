"""
Tests for authentication API endpoints.

Covers user registration, login, and profile retrieval scenarios
including validation errors and authentication failures.
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

    async def test_register_duplicate_email(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Register with an email that is already taken, expect 400."""
        user_data = {
            "email": test_user["email"],
            "password": "Anotherpassword123",
            "full_name": "Another User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_register_invalid_email(self, async_client: AsyncClient) -> None:
        """Register with an invalid email format, expect 422 Unprocessable."""
        user_data = {
            "email": "not-an-email",
            "password": "Securepassword123",
            "full_name": "Bad Email User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422

    async def test_register_short_password(self, async_client: AsyncClient) -> None:
        """Register with a password shorter than 8 characters, expect 422."""
        user_data = {
            "email": "shortpw@example.com",
            "password": "short",
            "full_name": "Short PW User",
        }
        response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)

        assert response.status_code == 422


class TestLogin:
    """Tests for the POST /api/v1/auth/login endpoint."""

    async def test_login_success(
        self, async_client: AsyncClient, test_user: dict
    ) -> None:
        """Login with correct credentials, expect 200 and a JWT token."""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"],
        }
        response = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"

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
        """Get /auth/me without providing a token, expect 403 Forbidden.

        FastAPI's HTTPBearer security scheme returns 403 when no
        credentials are provided (not 401, per Starlette implementation).
        """
        response = await async_client.get(f"{API_PREFIX}/auth/me")

        assert response.status_code == 403
