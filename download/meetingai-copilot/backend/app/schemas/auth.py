"""
Authentication schemas for the MeetingAI Copilot application.

Pydantic models for request/response validation of auth endpoints.
Uses Pydantic v2 field validators and common validation utilities.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validators import validate_password_strength, sanitize_text


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        email: User's email address (validated via Pydantic EmailStr).
        password: User's password (min 8 chars, max 128 chars, must contain
                  at least 1 uppercase letter, 1 lowercase letter, and 1 digit).
        full_name: User's display name (min 2 chars, max 100 chars, no XSS patterns).
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters and contain at least 1 uppercase letter, 1 lowercase letter, and 1 digit",
        examples=["SecurePass1"],
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the user (2-100 characters)",
        examples=["Jane Doe"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password meets minimum strength requirements.

        Delegates to the shared validate_password_strength utility which
        checks length bounds and character class requirements.
        """
        return validate_password_strength(v)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate full name: sanitize for XSS and enforce length.

        Strips leading/trailing whitespace, rejects content that matches
        known XSS patterns, and enforces the 2–100 character constraint.
        """
        sanitized = sanitize_text(v)
        if len(sanitized) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        if len(sanitized) > 100:
            raise ValueError("Full name must be at most 100 characters long")
        return sanitized


class UserLogin(BaseModel):
    """Schema for user login request.

    Attributes:
        email: User's email address.
        password: User's password.
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
    )


class UserResponse(BaseModel):
    """Schema for user data in API responses.

    Attributes:
        id: User's UUID as string.
        email: User's email address.
        full_name: User's display name.
        created_at: Timestamp of account creation.
        is_active: Whether the account is active.
        is_verified: Whether the account email has been verified.
    """

    id: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool
    is_verified: bool = False

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response (legacy, supports backward compatibility).

    Attributes:
        access_token: The JWT access token string.
        token_type: Token type, always "bearer".
    """

    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Schema for JWT token response with both access and refresh tokens.

    Attributes:
        access_token: The JWT access token string (short-lived).
        refresh_token: The JWT refresh token string (long-lived).
        token_type: Token type, always "bearer".
        expires_in: Access token expiration time in seconds.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[3600],
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request.

    Attributes:
        refresh_token: The refresh token string used to obtain a new access token.
    """

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="The refresh token to exchange for a new access token",
    )


class LogoutRequest(BaseModel):
    """Schema for logout request.

    Attributes:
        refresh_token: The refresh token to blacklist/revoked upon logout.
    """

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="The refresh token to revoke upon logout",
    )


class TokenData(BaseModel):
    """Schema for decoded JWT token payload.

    Attributes:
        user_id: The UUID string of the authenticated user.
        token_type: The type of token ('access' or 'refresh').
        jti: The unique JWT ID for blacklisting support.
    """

    user_id: Optional[str] = None
    token_type: Optional[str] = None
    jti: Optional[str] = None
