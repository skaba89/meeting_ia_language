"""
Shared LLM client for the MeetingAI Copilot application.

Provides a unified interface for calling Groq and OpenRouter chat completion
APIs with connection pooling, retry logic, and automatic fallback between
providers.
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

_GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

_INSECURE_KEYS = {"", None}

# ---------------------------------------------------------------------------
# Singleton async HTTP client with connection pooling
# ---------------------------------------------------------------------------

_client: Optional[httpx.AsyncClient] = None


async def _get_client() -> httpx.AsyncClient:
    """Return (and lazily create) the shared httpx.AsyncClient singleton."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
            ),
        )
    return _client


async def close_client() -> None:
    """Gracefully close the shared HTTP client (call on app shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


# ---------------------------------------------------------------------------
# Low-level provider calls
# ---------------------------------------------------------------------------

async def _call_groq(
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    response_format: Optional[dict[str, Any]] = None,
) -> str:
    """Call the Groq chat completion API.

    Args:
        system_prompt: The system-level instruction.
        user_content: The user message content.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.
        response_format: Optional response format dict (e.g. {"type": "json_object"}).

    Returns:
        The assistant's content string.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        RuntimeError: If GROQ_API_KEY is not configured.
    """
    if settings.GROQ_API_KEY in _INSECURE_KEYS:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = await _get_client()
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    response = await client.post(_GROQ_BASE_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


async def _call_openrouter(
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Call the OpenRouter chat completion API.

    Args:
        system_prompt: The system-level instruction.
        user_content: The user message content.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.

    Returns:
        The assistant's content string.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        RuntimeError: If OPENROUTER_API_KEY is not configured.
    """
    if settings.OPENROUTER_API_KEY in _INSECURE_KEYS:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    client = await _get_client()
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://meetingai-copilot.app",
        "X-Title": "MeetingAI Copilot",
    }
    payload: dict[str, Any] = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    response = await client.post(_OPENROUTER_BASE_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Retry logic with exponential backoff
# ---------------------------------------------------------------------------

_MAX_RETRIES = 3
_BASE_DELAY_SECONDS = 1.0


async def _retry_with_backoff(coro_factory, *args, **kwargs) -> str:
    """Execute an async callable with exponential-backoff retries.

    Args:
        coro_factory: An async callable (e.g. _call_groq or _call_openrouter).
        *args: Positional arguments forwarded to the callable.
        **kwargs: Keyword arguments forwarded to the callable.

    Returns:
        The string result from the successful call.

    Raises:
        The last exception encountered after all retries are exhausted.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return await coro_factory(*args, **kwargs)
        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                delay = _BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "LLM call attempt %d/%d failed (%s). Retrying in %.1fs…",
                    attempt,
                    _MAX_RETRIES,
                    type(exc).__name__,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "LLM call failed after %d attempts: %s", _MAX_RETRIES, exc
                )
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def chat_completion(
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    response_format: Optional[dict[str, Any]] = None,
    provider: Optional[str] = None,
) -> str:
    """Send a chat completion request with automatic provider fallback.

    Uses the configured LLM_PROVIDER as the primary provider and falls back
    to the alternative if the primary fails.

    Args:
        system_prompt: The system-level instruction for the LLM.
        user_content: The user message content.
        temperature: Sampling temperature (0.0 – 2.0).
        max_tokens: Maximum number of tokens in the response.
        response_format: Optional response format dict (Groq only, e.g. {"type": "json_object"}).
        provider: Force a specific provider ("groq" or "openrouter").
                  If None, uses the LLM_PROVIDER setting.

    Returns:
        The assistant's content string from the LLM.

    Raises:
        RuntimeError: If neither provider has a configured API key.
        httpx.HTTPStatusError: If both providers return error statuses.
    """
    primary = provider or settings.LLM_PROVIDER
    secondary = "openrouter" if primary == "groq" else "groq"

    # Build call kwargs
    primary_kwargs: dict[str, Any] = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    secondary_kwargs: dict[str, Any] = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Only Groq supports response_format
    if primary == "groq" and response_format is not None:
        primary_kwargs["response_format"] = response_format
    elif secondary == "groq" and response_format is not None:
        secondary_kwargs["response_format"] = response_format

    # Select coro factories
    primary_fn = _call_groq if primary == "groq" else _call_openrouter
    secondary_fn = _call_groq if secondary == "groq" else _call_openrouter

    # Try primary provider
    try:
        result = await _retry_with_backoff(
            primary_fn, system_prompt, user_content, **primary_kwargs
        )
        logger.debug("LLM call succeeded via primary provider (%s)", primary)
        return result
    except Exception as primary_exc:
        logger.warning(
            "Primary provider (%s) failed: %s. Falling back to %s…",
            primary,
            primary_exc,
            secondary,
        )

    # Try fallback provider
    try:
        result = await _retry_with_backoff(
            secondary_fn, system_prompt, user_content, **secondary_kwargs
        )
        logger.debug("LLM call succeeded via fallback provider (%s)", secondary)
        return result
    except Exception as fallback_exc:
        logger.error(
            "Both LLM providers failed. Primary: %s | Fallback: %s",
            primary_exc,
            fallback_exc,
        )
        raise RuntimeError(
            f"All LLM providers failed. Primary error: {primary_exc}; "
            f"Fallback error: {fallback_exc}"
        ) from fallback_exc
