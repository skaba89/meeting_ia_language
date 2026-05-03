"""
Authentication API routes for the MeetingAI Copilot application.

Provides endpoints for user registration, login, token refresh,
logout (token revocation), and profile retrieval.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    TokenData,
)
from app.services.auth_service import hash_password, verify_password
from app.services.token_service import TokenService
from app.middleware.auth_middleware import get_current_user, validate_refresh_token
from app.core.logging import get_logger
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
)

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user account.

    Validates that the email is not already registered, hashes the password,
    and creates a new user record in the database.

    Args:
        user_data: The user registration data (email, password, full_name).
        db: The async database session.

    Returns:
        The newly created User model instance.

    Raises:
        ConflictError: If the email is already registered.
    """
    # Check if user with this email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        logger.warning("Registration attempt with existing email: %s", user_data.email)
        raise ConflictError(
            message="A user with this email already exists",
            details={"email": user_data.email},
        )

    # Hash the password and create the user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )

    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    logger.info("New user registered: %s (id: %s)", new_user.email, new_user.id)
    return new_user


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate a user and return both access and refresh JWT tokens.",
)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return JWT access and refresh tokens.

    Verifies the user's credentials, checks for account lockout,
    updates failed login attempts, and generates signed JWT tokens.

    Args:
        login_data: The login credentials (email, password).
        db: The async database session.

    Returns:
        TokenResponse containing access_token, refresh_token, token_type, and expires_in.

    Raises:
        AuthenticationError: If the credentials are invalid or the account is locked.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("Login attempt with non-existent email: %s", login_data.email)
        raise AuthenticationError(
            message="Invalid email or password",
            details={"email": login_data.email},
        )

    # Check if account is locked
    if user.locked_until is not None and user.locked_until > datetime.now(timezone.utc):
        logger.warning("Login attempt on locked account: %s (locked until %s)", user.id, user.locked_until)
        raise AuthenticationError(
            message=f"Account is temporarily locked due to too many failed login attempts. Try again after {user.locked_until.isoformat()}",
            details={"locked_until": user.locked_until.isoformat()},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning("Login attempt by inactive user: %s", user.id)
        raise AuthenticationError(
            message="User account is inactive",
            details={"user_id": str(user.id)},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + __import__("datetime").timedelta(minutes=30)
            logger.warning(
                "Account locked for user %s after %d failed attempts",
                user.id, user.failed_login_attempts,
            )
            await db.flush()
            raise AuthenticationError(
                message="Account locked due to too many failed login attempts. Please try again later.",
                details={"failed_attempts": user.failed_login_attempts},
            )

        await db.flush()
        logger.warning("Failed login attempt for email: %s (attempts: %d)", login_data.email, user.failed_login_attempts)
        raise AuthenticationError(
            message="Invalid email or password",
            details={"failed_attempts": user.failed_login_attempts},
        )

    # Reset failed login attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    # Generate JWT tokens
    access_token = TokenService.create_access_token(data={"sub": str(user.id)})
    refresh_token = TokenService.create_refresh_token(data={"sub": str(user.id)})

    await db.flush()

    logger.info("User logged in: %s (id: %s)", user.email, user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token and refresh token pair.",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    Validates the provided refresh token, blacklists the old refresh token
    to prevent reuse, and issues a new access/refresh token pair.

    Args:
        request: The refresh token request containing the refresh_token.
        db: The async database session.

    Returns:
        TokenResponse containing new access_token, refresh_token, token_type, and expires_in.

    Raises:
        AuthenticationError: If the refresh token is invalid, expired, or revoked.
    """
    try:
        # Validate and decode the refresh token
        new_access_token, user_id = TokenService.refresh_access_token(request.refresh_token)
    except JWTError as exc:
        logger.warning("Token refresh failed: %s", exc)
        raise AuthenticationError(
            message="Invalid or expired refresh token. Please log in again.",
        ) from exc

    # Blacklist the old refresh token to prevent reuse (refresh token rotation)
    try:
        TokenService.blacklist_token(request.refresh_token)
    except JWTError:
        # If blacklisting fails, we still want to issue the new token
        logger.warning("Failed to blacklist old refresh token during rotation")

    # Verify the user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None or not user.is_active:
        logger.warning("Token refresh for inactive/missing user: %s", user_id)
        raise AuthenticationError(
            message="User account is no longer active. Please log in again.",
        )

    # Issue a new refresh token (rotation)
    new_refresh_token = TokenService.create_refresh_token(data={"sub": str(user_id)})

    logger.info("Tokens refreshed for user_id: %s", user_id)
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@auth_router.post(
    "/logout",
    summary="Logout user",
    description="Blacklist the refresh token to prevent further use.",
)
async def logout(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Logout by blacklisting the refresh token.

    Validates the current user's access token (via dependency), then
    blacklists the provided refresh token so it can no longer be used
    to obtain new access tokens.

    Args:
        request: The logout request containing the refresh_token to revoke.
        current_user: The authenticated user (validated by access token).

    Returns:
        A confirmation message dictionary.

    Raises:
        ValidationError: If the refresh token cannot be blacklisted.
    """
    try:
        TokenService.blacklist_token(request.refresh_token)
    except JWTError as exc:
        logger.warning("Logout blacklist failed for user %s: %s", current_user.id, exc)
        raise ValidationError(
            message="Failed to revoke refresh token. It may already be invalid.",
        ) from exc

    logger.info("User logged out: %s (id: %s)", current_user.email, current_user.id)
    return {"detail": "Successfully logged out"}


@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve the profile of the currently authenticated user.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get the profile of the currently authenticated user.

    This endpoint is protected and requires a valid JWT access token
    in the Authorization header.

    Args:
        current_user: The authenticated user injected by the dependency.

    Returns:
        The authenticated User model instance.
    """
    return current_user
