"""
Database configuration module using SQLAlchemy async engine.

Provides async engine, session factory, and dependency injection
for PostgreSQL (production/Docker) or SQLite (local development) access.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import settings

# Build engine kwargs based on database type
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {
    "echo": False,
}

if _is_sqlite:
    # SQLite-specific configuration
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL-specific configuration
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True

async_engine = create_async_engine(
    settings.DATABASE_URL,
    **_engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Yields:
        AsyncSession: An async SQLAlchemy session instance.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables defined in the Base metadata.

    This is called during application startup to ensure
    all tables exist before the app starts serving requests.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
