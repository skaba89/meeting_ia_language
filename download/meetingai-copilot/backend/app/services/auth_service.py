"""
Authentication service for the MeetingAI Copilot application.

Provides password hashing/verification and JWT token creation/decoding.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas.auth import TokenData

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The bcrypt hash to verify against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with an expiration time.

    Args:
        data: The payload data to encode in the token.
            Should contain a "sub" key with the user ID.
        expires_delta: Optional custom expiration timedelta.
            Defaults to ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        The encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT token string to decode.

    Returns:
        TokenData containing the user_id extracted from the token.

    Raises:
        JWTError: If the token is invalid, expired, or cannot be decoded.
    """
    try:
        payload: dict = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise JWTError("Token payload missing 'sub' claim")
        return TokenData(user_id=user_id_str)
    except (JWTError, ValueError) as exc:
        raise JWTError(f"Could not validate credentials: {exc}") from exc
