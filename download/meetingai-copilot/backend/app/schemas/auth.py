"""
Authentication schemas for the MeetingAI Copilot application.

Pydantic models for request/response validation of auth endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        email: User's email address.
        password: User's password (minimum 8 characters).
        full_name: User's display name.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of the user")


class UserLogin(BaseModel):
    """Schema for user login request.

    Attributes:
        email: User's email address.
        password: User's password.
    """

    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")


class UserResponse(BaseModel):
    """Schema for user data in API responses.

    Attributes:
        id: User's UUID.
        email: User's email address.
        full_name: User's display name.
        created_at: Timestamp of account creation.
        is_active: Whether the account is active.
    """

    id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for JWT token response.

    Attributes:
        access_token: The JWT access token string.
        token_type: Token type, always "bearer".
    """

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token payload.

    Attributes:
        user_id: The UUID of the authenticated user.
    """

    user_id: Optional[uuid.UUID] = None
