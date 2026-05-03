"""
Authentication middleware for the MeetingAI Copilot application.

Provides the get_current_user dependency for protecting API endpoints
with JWT Bearer token authentication. Supports both access and refresh
token types with proper validation and error messages.
"""

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData
from app.services.token_service import TokenService
from app.core.logging import get_logger
from app.core.exceptions import AuthenticationError

logger = get_logger(__name__)

# Bearer token scheme for extracting Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts and validates the current user from a JWT access token.

    Extracts the Bearer token from the Authorization header, decodes it
    as an access token, and retrieves the corresponding user from the database.

    Args:
        credentials: The HTTP Bearer credentials extracted by FastAPI.
        db: The async database session injected by FastAPI.

    Returns:
        The authenticated User model instance.

    Raises:
        AuthenticationError: If the token is missing, invalid, expired,
            wrong type, revoked, or the user does not exist / is inactive.
    """
    token = credentials.credentials

    try:
        token_data: TokenData = TokenService.decode_token(token, expected_type="access")
    except ExpiredSignatureError:
        logger.warning("Expired access token presented")
        raise AuthenticationError(
            message="Access token has expired. Please refresh your token or log in again.",
        )
    except JWTError as exc:
        error_msg = str(exc)
        # Provide specific error messages based on the JWTError content
        if "Invalid token type" in error_msg:
            logger.warning("Wrong token type used: %s", error_msg)
            raise AuthenticationError(
                message="Invalid token type. An access token is required for this endpoint.",
            ) from exc
        if "revoked" in error_msg.lower():
            logger.warning("Revoked token used: %s", error_msg)
            raise AuthenticationError(
                message="Token has been revoked. Please log in again.",
            ) from exc
        logger.warning("JWT decode failed: %s", exc)
        raise AuthenticationError(
            message="Could not validate credentials. Please log in again.",
        ) from exc

    if token_data.user_id is None:
        logger.warning("Token decoded but user_id is None")
        raise AuthenticationError(
            message="Invalid token: missing user identifier.",
        )

    # Query the user from the database
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        logger.warning("User not found for token user_id: %s", token_data.user_id)
        raise AuthenticationError(
            message="User not found.",
        )

    if not user.is_active:
        logger.warning("Inactive user attempted access: %s", user.id)
        raise AuthenticationError(
            message="User account is inactive. Please contact support.",
        )

    return user


async def validate_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """FastAPI dependency that validates a refresh token from the Authorization header.

    This is used for the /auth/refresh endpoint where a refresh token
    (not an access token) is expected.

    Args:
        credentials: The HTTP Bearer credentials extracted by FastAPI.

    Returns:
        TokenData containing the decoded token information.

    Raises:
        AuthenticationError: If the token is invalid, expired, wrong type, or revoked.
    """
    token = credentials.credentials

    try:
        token_data: TokenData = TokenService.decode_token(token, expected_type="refresh")
    except ExpiredSignatureError:
        logger.warning("Expired refresh token presented")
        raise AuthenticationError(
            message="Refresh token has expired. Please log in again.",
        )
    except JWTError as exc:
        error_msg = str(exc)
        if "Invalid token type" in error_msg:
            logger.warning("Wrong token type used for refresh: %s", error_msg)
            raise AuthenticationError(
                message="Invalid token type. A refresh token is required for this endpoint.",
            ) from exc
        if "revoked" in error_msg.lower():
            logger.warning("Revoked refresh token used: %s", error_msg)
            raise AuthenticationError(
                message="Refresh token has been revoked. Please log in again.",
            ) from exc
        logger.warning("Refresh token decode failed: %s", exc)
        raise AuthenticationError(
            message="Could not validate refresh token. Please log in again.",
        ) from exc

    return token_data
