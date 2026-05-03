"""
MeetingAI Copilot — FastAPI Application Entry Point
Initializes the FastAPI app with CORS, database, and all API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.meetings import router as meetings_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: initialize database tables
    init_db()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} — API ready")
    print(f"📡 Whisper mode: {settings.WHISPER_MODE}")
    print(f"🤖 LLM model: {settings.LLM_MODEL}")
    yield
    # Shutdown: cleanup if needed
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent meeting assistant — transcription, summary, and translation",
    lifespan=lifespan,
)

# ── CORS Middleware ──────────────────────────────────────────────────
# Allow all origins in development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ─────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(meetings_router)


# ── Health Check ────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Basic health check endpoint for monitoring and Docker health checks."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"])
def detailed_health():
    """Detailed health check including service configuration status."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "whisper_mode": settings.WHISPER_MODE,
        "llm_configured": bool(settings.LLM_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "database": "sqlite" if settings.resolved_database_url.startswith("sqlite") else "postgresql",
    }
