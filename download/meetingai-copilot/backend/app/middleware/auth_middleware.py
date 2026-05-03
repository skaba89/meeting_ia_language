"""
Authentication middleware for the MeetingAI Copilot application.

Provides the get_current_user dependency for protecting API endpoints
with JWT Bearer token authentication.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData
from app.services.auth_service import decode_access_token

logger = logging.getLogger(__name__)

# Bearer token scheme for extracting Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts and validates the current user from a JWT token.

    Extracts the Bearer token from the Authorization header, decodes it,
    and retrieves the corresponding user from the database.

    Args:
        credentials: The HTTP Bearer credentials extracted by FastAPI.
        db: The async database session injected by FastAPI.

    Returns:
        The authenticated User model instance.

    Raises:
        HTTPException: 401 if the token is missing, invalid, expired,
            or the user does not exist / is inactive.
    """
    token = credentials.credentials

    try:
        token_data: TokenData = decode_access_token(token)
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if token_data.user_id is None:
        logger.warning("Token decoded but user_id is None")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query the user from the database
    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        logger.warning("User not found for token user_id: %s", token_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("Inactive user attempted access: %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
