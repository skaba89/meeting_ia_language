"""
Authentication API routes for the MeetingAI Copilot application.

Provides endpoints for user registration, login, and profile retrieval.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

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
        HTTPException: 400 if the email is already registered.
    """
    # Check if user with this email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        logger.warning("Registration attempt with existing email: %s", user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
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
    response_model=Token,
    summary="Login user",
    description="Authenticate a user and return a JWT access token.",
)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    """Authenticate a user and return a JWT access token.

    Verifies the user's credentials and generates a signed JWT token
    with the user's ID as the subject claim.

    Args:
        login_data: The login credentials (email, password).
        db: The async database session.

    Returns:
        Token containing the access_token and token_type.

    Raises:
        HTTPException: 401 if the credentials are invalid.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning("Login attempt with non-existent email: %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        logger.warning("Failed login attempt for email: %s", login_data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning("Login attempt by inactive user: %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info("User logged in: %s (id: %s)", user.email, user.id)
    return Token(access_token=access_token, token_type="bearer")


@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve the profile of the currently authenticated user.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get the profile of the currently authenticated user.

    This endpoint is protected and requires a valid JWT token
    in the Authorization header.

    Args:
        current_user: The authenticated user injected by the dependency.

    Returns:
        The authenticated User model instance.
    """
    return current_user
