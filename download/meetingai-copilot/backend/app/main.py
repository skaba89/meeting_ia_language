"""
MeetingAI Copilot API - Main application module.

Creates and configures the FastAPI application with CORS middleware,
rate limiting, API versioning, structured logging with request IDs,
security headers, error handling, request logging, routers, lifespan
events, health check endpoint, and application metrics.
"""

import os
import uuid
import logging
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastapi import FastAPI, Depends, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import create_tables, async_engine, AsyncSessionLocal
from app.api.auth import auth_router
from app.api.meetings import meetings_router
from app.core import setup_logging, get_logger
from app.core.exceptions import MeetingAIError
from app.core.metrics import metrics as app_metrics
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.auth_middleware import get_current_user

# ---------------------------------------------------------------------------
# Structured logging – initialize early
# ---------------------------------------------------------------------------

setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (uses Redis when available, falls back to in-memory)
# ---------------------------------------------------------------------------

# Try Redis first; fall back to in-memory storage if Redis is unavailable
_storage_uri = settings.REDIS_URL
try:
    import redis as redis_lib  # noqa: F401
    _redis_client = redis_lib.from_url(settings.REDIS_URL)
    _redis_client.ping()
    logger.info("Rate limiter: Using Redis storage at %s", settings.REDIS_URL)
except Exception:
    _storage_uri = "memory://"
    logger.warning(
        "Redis unavailable at %s – falling back to in-memory rate limit storage",
        settings.REDIS_URL,
    )

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=_storage_uri,
)

# ---------------------------------------------------------------------------
# API versioning – wrap existing routers under /api/v1
# ---------------------------------------------------------------------------

from fastapi import APIRouter  # noqa: E402

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(meetings_router)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown.

    On startup:
    - Creates the uploads directory if it doesn't exist
    - Creates database tables if they don't exist

    On shutdown:
    - Performs any necessary cleanup
    """
    # Startup
    logger.info("Starting MeetingAI Copilot API...")

    # Create uploads directory
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    logger.info("Upload directory ensured: %s", upload_dir)

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables verified/created")
    except Exception as exc:
        logger.error("Failed to create database tables: %s", exc)
        # Don't crash on startup - tables might exist already or DB might be unavailable temporarily

    logger.info("MeetingAI Copilot API started successfully")

    yield  # Application is running

    # Shutdown
    logger.info("Shutting down MeetingAI Copilot API...")


# ---------------------------------------------------------------------------
# Create the FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MeetingAI Copilot API",
    version="1.0.0",
    description=(
        "Intelligent meeting assistant API that provides audio transcription, "
        "AI-powered summaries, and multi-language translation for your meetings."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: Request logging (outermost – logs every request with timing)
# ---------------------------------------------------------------------------

app.add_middleware(RequestLoggingMiddleware)

# ---------------------------------------------------------------------------
# Middleware: Error handler (catches MeetingAIError and unhandled exceptions)
# ---------------------------------------------------------------------------

app.add_middleware(ErrorHandlerMiddleware)

# ---------------------------------------------------------------------------
# Middleware: CORS (settings-based origins with specific methods/headers)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "Accept",
        "Origin",
    ],
    expose_headers=["X-Request-ID"],
)

# ---------------------------------------------------------------------------
# Middleware: Security headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security-related headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking – only same-origin framing allowed
        response.headers["X-Frame-Options"] = "DENY"
        # Enable browser XSS filtering (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Content Security Policy – restrict to same origin by default
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        # HSTS – enforce HTTPS for 1 year (include subdomains)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # Referrer policy – send origin only
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy – disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)

# ---------------------------------------------------------------------------
# Middleware: Rate limiting
# ---------------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ---------------------------------------------------------------------------
# Middleware: Request ID injection
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_id_middleware(request: FastAPIRequest, call_next):
    """Attach a unique request ID to every request and inject it into logs."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Temporarily set the request_id on the logger filter for this request
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        logging.setLogRecordFactory(old_factory)


@app.exception_handler(MeetingAIError)
async def meetingai_exception_handler(request: FastAPIRequest, exc: MeetingAIError):
    """Return a structured error response for MeetingAIError exceptions."""
    request_id = getattr(request.state, "request_id", "-")
    logger.warning(
        f"Application error: {exc.code} - {exc.message}",
        extra={"extra_data": {"code": exc.code, "details": exc.details, "request_id": request_id}},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def sanitized_exception_handler(request: FastAPIRequest, exc: Exception):
    """Return a generic error to the client; log the real detail server-side."""
    request_id = getattr(request.state, "request_id", "-")
    logger.exception(
        "Unhandled exception (request_id=%s): %s", request_id, exc
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "request_id": request_id}},
    )


# ---------------------------------------------------------------------------
# Include API routers (versioned)
# ---------------------------------------------------------------------------

app.include_router(api_v1_router)


# ---------------------------------------------------------------------------
# Health check – comprehensive health and dependency status
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    summary="Health check",
    description="Check the health status of the API, database, Redis, and AI service configuration.",
    tags=["Health"],
)
async def health_check() -> JSONResponse:
    """Comprehensive health check endpoint.

    Checks database connectivity, Redis availability, AI service configuration,
    and system resource usage. Returns a structured status response with
    per-component health information.

    Returns:
        JSONResponse with status, version, and per-component health info.
    """
    checks: dict = {
        "status": "healthy",
        "service": "MeetingAI Copilot API",
        "version": "1.0.0",
        "checks": {},
    }

    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_type = "postgresql" if "postgresql" in str(settings.DATABASE_URL) else "sqlite"
        checks["checks"]["database"] = {"status": "healthy", "type": db_type}
    except Exception as e:
        checks["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        checks["status"] = "degraded"

    # Check Redis (if configured)
    try:
        import redis as redis_lib
        r = redis_lib.from_url(str(settings.REDIS_URL), socket_timeout=2)
        r.ping()
        checks["checks"]["redis"] = {"status": "healthy"}
        r.close()
    except Exception:
        checks["checks"]["redis"] = {
            "status": "unavailable",
            "note": "Running without Redis (in-memory fallback)",
        }

    # Check AI services (just verify keys are set)
    checks["checks"]["groq_api"] = {
        "status": "configured" if settings.GROQ_API_KEY else "not_configured"
    }
    checks["checks"]["openrouter_api"] = {
        "status": "configured" if settings.OPENROUTER_API_KEY else "not_configured"
    }

    # System info (optional – only if psutil is available)
    try:
        import psutil
        checks["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        checks["system"] = {"note": "psutil not installed – system metrics unavailable"}

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)


# ---------------------------------------------------------------------------
# Metrics endpoint – application metrics (requires authentication)
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/metrics",
    summary="Application metrics",
    description="Retrieve application metrics including request counts, processing times, and business metrics. Requires authentication.",
    tags=["Monitoring"],
)
async def get_metrics(
    current_user=Depends(get_current_user),
) -> dict:
    """Retrieve collected application metrics.

    Returns counters, gauges, timer summaries, and uptime information.
    This endpoint requires a valid JWT access token.

    Args:
        current_user: The authenticated user (injected by dependency).

    Returns:
        Dictionary containing all collected metrics.
    """
    app_metrics.increment("metrics.endpoint_requests")
    return app_metrics.get_metrics()
