"""
User model for the MeetingAI Copilot application.

Defines the SQLAlchemy ORM model for user accounts with
UUID primary keys and authentication-related fields.
Compatible with both PostgreSQL (UUID type) and SQLite (String type).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base

# Use PostgreSQL UUID type when connected to PostgreSQL,
# otherwise use String(36) for SQLite compatibility
_is_postgres = "postgresql" in settings.DATABASE_URL


class User(Base):
    """SQLAlchemy model for the users table.

    Attributes:
        id: UUID primary key.
        email: Unique email address for the user.
        hashed_password: Bcrypt-hashed password string.
        full_name: User's display name.
        created_at: Timestamp of account creation.
        is_active: Whether the user account is active.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True) if _is_postgres else String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        """Return string representation of the User."""
        return f"<User(id={self.id}, email={self.email})>"
