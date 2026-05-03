"""
MeetingAI Copilot API - Main application module.

Creates and configures the FastAPI application with CORS middleware,
routers, lifespan events, and health check endpoint.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.api.auth import auth_router
from app.api.meetings import meetings_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


# Create the FastAPI application
app = FastAPI(
    title="MeetingAI Copilot API",
    version="1.0.0",
    description=(
        "Intelligent meeting assistant API that provides audio transcription, "
        "AI-powered summaries, and multi-language translation for your meetings."
    ),
    lifespan=lifespan,
)

# Configure CORS middleware (development mode - allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(meetings_router)


@app.get(
    "/health",
    summary="Health check",
    description="Check the health status of the API.",
    tags=["Health"],
)
async def health_check() -> dict:
    """Health check endpoint.

    Returns a simple status response indicating the API is running.

    Returns:
        A dictionary with status and version information.
    """
    return {
        "status": "healthy",
        "service": "MeetingAI Copilot API",
        "version": "1.0.0",
    }
