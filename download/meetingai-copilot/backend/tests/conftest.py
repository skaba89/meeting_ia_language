"""
Test configuration and fixtures for MeetingAI Copilot backend tests.

Provides async test client, test database (SQLite in-memory), test user,
authenticated client fixtures, and mock data for external services.
Overrides the production get_db dependency to use a test database for
full isolation.

NOTE: The production .env file is temporarily moved aside during the import
of app modules so that ``load_dotenv(override=True)`` in config.py cannot
overwrite our test environment variables. The .env file is always restored,
even if the import fails.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Ensure the backend directory is on sys.path so ``app`` is importable
# regardless of the working directory pytest is launched from.
# ---------------------------------------------------------------------------
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# ---------------------------------------------------------------------------
# Temporarily move the .env file aside so that the ``load_dotenv(override=True)``
# call in config.py does NOT overwrite our test env vars.  The .env file is
# always restored, even on import failure.
# ---------------------------------------------------------------------------
_env_file = _backend_dir / ".env"
_env_backup = _backend_dir / ".env._pytest_backup"
_env_moved = False

if _env_file.exists():
    shutil.move(str(_env_file), str(_env_backup))
    _env_moved = True

try:
    # Set test environment variables BEFORE importing any app modules.
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-2024"
    os.environ["GROQ_API_KEY"] = "fake-groq-key-for-testing"
    os.environ["OPENROUTER_API_KEY"] = "fake-openrouter-key-for-testing"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    # Use in-memory storage for rate limiting so tests don't need Redis
    os.environ["REDIS_URL"] = "memory://"

    # Import app modules — settings will reflect our test env vars because
    # the .env file is no longer present to override them.
    from app.config import settings  # noqa: E402

    # Also override the settings object directly as a safety measure, in case
    # pydantic-settings' own env_file handling picked up anything unexpected.
    settings.DATABASE_URL = "sqlite+aiosqlite://"
    settings.SECRET_KEY = "test-secret-key-for-testing-2024"
    settings.GROQ_API_KEY = "fake-groq-key-for-testing"
    settings.OPENROUTER_API_KEY = "fake-groq-key-for-testing"
    settings.REDIS_URL = "memory://"

    # Create a temporary upload directory for tests
    _test_upload_dir = tempfile.mkdtemp()
    settings.UPLOAD_DIR = _test_upload_dir

    from app.database import Base, get_db  # noqa: E402
    from app.main import app  # noqa: E402
    from app.models.meeting import Meeting  # noqa: E402
    from app.models.user import User  # noqa: E402

finally:
    # Always restore the .env file
    if _env_moved and _env_backup.exists():
        shutil.move(str(_env_backup), str(_env_file))

# ---------------------------------------------------------------------------
# Safety net: if the models were imported when DATABASE_URL still pointed at
# PostgreSQL, the column types will be PG_UUID. Patch them to String(36) so
# that SQLite can handle them.
# ---------------------------------------------------------------------------
for _model_cls in (User, Meeting):
    for _col in _model_cls.__table__.columns:
        if type(_col.type).__module__.startswith("sqlalchemy.dialects.postgresql"):
            _col.type = String(36)

# ---------------------------------------------------------------------------
# API prefix used by the versioned router in main.py
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

# ---------------------------------------------------------------------------
# Test database engine and session factory
# ---------------------------------------------------------------------------
# StaticPool shares a single connection so that in-memory SQLite data persists
# across sessions within the same test.
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency override that yields a test database session.

    Commits on success, rolls back on exception — mirrors the production
    get_db behaviour.
    """
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override the production get_db dependency globally for all tests.
app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after.

    Ensures full test isolation: every test starts with a clean database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client for making requests to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(async_client: AsyncClient) -> dict:
    """Create a test user via the registration endpoint.

    Returns:
        Dictionary with ``id``, ``email``, ``password``, and ``full_name``.
    """
    user_data = {
        "email": "testuser@example.com",
        "password": "Testpassword123",
        "full_name": "Test User",
    }
    response = await async_client.post(f"{API_PREFIX}/auth/register", json=user_data)
    assert response.status_code == 201
    user_info = response.json()
    return {
        "id": user_info["id"],
        "email": user_data["email"],
        "password": user_data["password"],
        "full_name": user_data["full_name"],
    }


@pytest_asyncio.fixture
async def auth_client(async_client: AsyncClient, test_user: dict) -> AsyncClient:
    """Provide an authenticated async HTTP test client with a valid JWT token.

    Logs in as the ``test_user`` and attaches the Bearer token to the
    ``Authorization`` header of the client.
    """
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"],
    }
    response = await async_client.post(f"{API_PREFIX}/auth/login", json=login_data)
    assert response.status_code == 200
    tokens = response.json()
    token = tokens["access_token"]
    async_client.headers["Authorization"] = f"Bearer {token}"
    # Also store the refresh_token on the client for tests that need it
    async_client._refresh_token = tokens["refresh_token"]  # type: ignore[attr-defined]
    return async_client


# ---------------------------------------------------------------------------
# Additional data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for registration tests."""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_login_data() -> dict:
    """Sample login data."""
    return {
        "email": "test@example.com",
        "password": "TestPass123",
    }


@pytest.fixture
def mock_groq_response() -> dict:
    """Mock response from Groq Whisper API."""
    return {
        "text": "This is a test transcription of a meeting.",
        "language": "en",
        "duration": 120.5,
    }


@pytest.fixture
def mock_llm_summary() -> dict:
    """Mock LLM summary response."""
    return {
        "summary": "The team discussed project timeline and deliverables.",
        "key_decisions": ["Launch date set for Q2", "Budget approved for hiring"],
        "action_items": ["John to prepare roadmap", "Jane to finalize budget"],
        "participants": ["John", "Jane", "Bob"],
    }
