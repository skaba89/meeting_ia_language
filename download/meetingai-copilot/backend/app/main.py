"""
MeetingAI Copilot API - Main application module.

Creates and configures the FastAPI application with CORS middleware,
rate limiting, API versioning, structured logging with request IDs,
routers, lifespan events, and health check endpoint.
"""

import os
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import create_tables, async_engine
from app.api.auth import auth_router
from app.api.meetings import meetings_router

# ---------------------------------------------------------------------------
# Structured logging with request ID support
# ---------------------------------------------------------------------------

class RequestIdFilter(logging.Filter):
    """Logging filter that injects the current request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


# Set up root logger first with a safe default format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Add request ID filter to all handlers
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [request_id=%(request_id)s] - %(message)s"
    ))
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter (uses Redis when available, falls back to in-memory)
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
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
# Middleware: CORS (settings-based origins)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Middleware: Rate limiting
# ---------------------------------------------------------------------------

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ---------------------------------------------------------------------------
# Middleware: Request ID injection + error sanitization
# ---------------------------------------------------------------------------

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
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


@app.exception_handler(Exception)
async def sanitized_exception_handler(request: Request, exc: Exception):
    """Return a generic error to the client; log the real detail server-side."""
    request_id = getattr(request.state, "request_id", "-")
    logger.exception(
        "Unhandled exception (request_id=%s): %s", request_id, exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


# ---------------------------------------------------------------------------
# Include API routers (versioned)
# ---------------------------------------------------------------------------

app.include_router(api_v1_router)


# ---------------------------------------------------------------------------
# Health check – tests DB connectivity
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    summary="Health check",
    description="Check the health status of the API and database connectivity.",
    tags=["Health"],
)
async def health_check() -> dict:
    """Health check endpoint.

    Returns a status response indicating the API is running and can
    reach the database.

    Returns:
        A dictionary with status, version, and database connectivity info.
    """
    db_status = "unknown"
    try:
        async with async_engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        db_status = "healthy"
    except Exception as exc:
        logger.error("Health check – DB connection failed: %s", exc)
        db_status = "unhealthy"

    overall = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall,
        "service": "MeetingAI Copilot API",
        "version": "1.0.0",
        "database": db_status,
    }
