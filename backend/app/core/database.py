"""
SQLAlchemy database engine and session management.
Automatically switches between SQLite (local) and PostgreSQL (Docker) based on DATABASE_URL.
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import get_settings

settings = get_settings()

# Resolve the database URL (handles empty default)
db_url = settings.resolved_database_url

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# SQLite needs check_same_thread=False for FastAPI async-like usage
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables — used on application startup."""
    Base.metadata.create_all(bind=engine)
