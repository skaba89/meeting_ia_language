"""
Token service for the MeetingAI Copilot application.

Provides TokenService class for creating, verifying, and managing both
access tokens (short-lived) and refresh tokens (long-lived), with
token blacklisting support via Redis (and in-memory fallback).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings
from app.schemas.auth import TokenData
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Blacklist backend: Redis with in-memory fallback
# ---------------------------------------------------------------------------

# In-memory fallback for token blacklisting when Redis is unavailable
_memory_blacklist: dict[str, float] = {}  # token_jti -> expiry_timestamp

_redis_client: Optional[object] = None

try:
    import redis as redis_lib  # noqa: F811
    _redis_client = redis_lib.from_url(settings.REDIS_URL)
    _redis_client.ping()
    logger.info("Token blacklist: Using Redis at %s", settings.REDIS_URL)
except Exception:
    _redis_client = None
    logger.warning(
        "Token blacklist: Redis unavailable – using in-memory fallback"
    )


def _is_blacklisted(jti: str) -> bool:
    """Check if a token's JTI is in the blacklist.

    Args:
        jti: The unique JWT ID to check.

    Returns:
        True if the token is blacklisted, False otherwise.
    """
    if _redis_client is not None:
        try:
            return bool(_redis_client.exists(f"blacklist:{jti}"))
        except Exception as exc:
            logger.warning("Redis blacklist check failed: %s – checking memory", exc)

    # Fallback to in-memory blacklist
    import time
    expiry = _memory_blacklist.get(jti)
    if expiry is None:
        return False
    if time.time() > expiry:
        # Token has expired naturally – remove from memory blacklist
        del _memory_blacklist[jti]
        return False
    return True


def _add_to_blacklist(jti: str, ttl_seconds: int) -> None:
    """Add a token's JTI to the blacklist.

    Args:
        jti: The unique JWT ID to blacklist.
        ttl_seconds: Time-to-live in seconds (should match token expiry).
    """
    if _redis_client is not None:
        try:
            _redis_client.setex(f"blacklist:{jti}", ttl_seconds, "1")
            return
        except Exception as exc:
            logger.warning("Redis blacklist add failed: %s – using memory", exc)

    # Fallback to in-memory blacklist
    import time
    _memory_blacklist[jti] = time.time() + ttl_seconds


# ---------------------------------------------------------------------------
# TokenService
# ---------------------------------------------------------------------------


class TokenService:
    """Service for creating and managing JWT access and refresh tokens.

    Access tokens are short-lived (default 60 minutes) and used for API
    authentication. Refresh tokens are long-lived (default 7 days) and
    used to obtain new access tokens without re-authentication.

    Both token types include a 'type' claim ('access' or 'refresh') and
    a unique 'jti' (JWT ID) claim for blacklisting support.
    """

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a short-lived JWT access token.

        Args:
            data: The payload data to encode. Should contain a "sub" key
                with the user ID.
            expires_delta: Optional custom expiration timedelta. Defaults to
                ACCESS_TOKEN_EXPIRE_MINUTES from settings.

        Returns:
            The encoded JWT access token string.
        """
        import uuid as _uuid

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({
            "exp": expire,
            "type": "access",
            "jti": str(_uuid.uuid4()),
        })
        encoded_jwt: str = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a long-lived JWT refresh token.

        Args:
            data: The payload data to encode. Should contain a "sub" key
                with the user ID.
            expires_delta: Optional custom expiration timedelta. Defaults to
                REFRESH_TOKEN_EXPIRE_DAYS from settings.

        Returns:
            The encoded JWT refresh token string.
        """
        import uuid as _uuid

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": str(_uuid.uuid4()),
        })
        encoded_jwt: str = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str, expected_type: Optional[str] = None) -> TokenData:
        """Decode and validate a JWT token.

        Args:
            token: The JWT token string to decode.
            expected_type: If provided, validates that the token type matches
                ('access' or 'refresh'). Raises JWTError on mismatch.

        Returns:
            TokenData containing the user_id and metadata extracted from the token.

        Raises:
            JWTError: If the token is invalid, expired, blacklisted, or
                the type does not match expected_type.
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

            token_type: Optional[str] = payload.get("type")
            jti: Optional[str] = payload.get("jti")

            # Validate token type if specified
            if expected_type is not None and token_type != expected_type:
                raise JWTError(
                    f"Invalid token type: expected '{expected_type}', got '{token_type}'"
                )

            # Check if token is blacklisted
            if jti is not None and _is_blacklisted(jti):
                raise JWTError("Token has been revoked")

            return TokenData(
                user_id=user_id_str,
                token_type=token_type,
                jti=jti,
            )
        except (JWTError, ValueError) as exc:
            raise JWTError(f"Could not validate credentials: {exc}") from exc

    @staticmethod
    def refresh_access_token(refresh_token: str) -> tuple[str, str]:
        """Create a new access token from a valid refresh token.

        Validates the refresh token, then issues a new access token
        for the same user.

        Args:
            refresh_token: The refresh token string.

        Returns:
            A tuple of (new_access_token, user_id).

        Raises:
            JWTError: If the refresh token is invalid, expired, or blacklisted.
        """
        token_data = TokenService.decode_token(refresh_token, expected_type="refresh")

        if token_data.user_id is None:
            raise JWTError("Refresh token payload missing user ID")

        new_access_token = TokenService.create_access_token(
            data={"sub": token_data.user_id}
        )

        logger.info("Access token refreshed for user_id: %s", token_data.user_id)
        return new_access_token, token_data.user_id

    @staticmethod
    def blacklist_token(token: str) -> None:
        """Blacklist a token so it can no longer be used.

        Extracts the JTI and expiry from the token and adds it to
        the blacklist with a matching TTL.

        Args:
            token: The JWT token string to blacklist.

        Raises:
            JWTError: If the token cannot be decoded.
        """
        try:
            payload: dict = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except (JWTError, ValueError) as exc:
            raise JWTError(f"Cannot blacklist invalid token: {exc}") from exc

        jti = payload.get("jti")
        if jti is None:
            raise JWTError("Token missing 'jti' claim – cannot blacklist")

        # Calculate remaining TTL based on token expiry
        exp = payload.get("exp")
        if exp is not None:
            remaining = int(exp - datetime.now(timezone.utc).timestamp())
            ttl_seconds = max(remaining, 0)
        else:
            # Fallback: use a generous TTL
            ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        _add_to_blacklist(jti, ttl_seconds)
        logger.info("Token blacklisted (jti: %s, ttl: %ds)", jti, ttl_seconds)
