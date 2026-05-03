"""
Meeting model for the MeetingAI Copilot application.

Defines the SQLAlchemy ORM model for meeting records including
audio file metadata, transcription data, summaries, and translations.
Compatible with both PostgreSQL (UUID type) and SQLite (String type).
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base

# Use PostgreSQL UUID type when connected to PostgreSQL,
# otherwise use String(36) for SQLite compatibility
_is_postgres = "postgresql" in settings.DATABASE_URL


class MeetingStatus(str, enum.Enum):
    """Enum representing the lifecycle stages of a meeting processing pipeline.

    Attributes:
        UPLOADED: Audio file has been uploaded but not yet processed.
        TRANSCRIBING: Audio is currently being transcribed.
        TRANSCRIBED: Transcription is complete, summary pending.
        SUMMARIZING: Summary is currently being generated.
        COMPLETED: All processing is complete.
        FAILED: Processing failed at some stage.
    """

    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    TRANSCRIBED = "transcribed"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


class Meeting(Base):
    """SQLAlchemy model for the meetings table.

    Attributes:
        id: UUID primary key.
        title: Meeting title provided by the user.
        audio_filename: Original filename of the uploaded audio.
        audio_file_path: Server filesystem path to the saved audio file.
        audio_duration: Duration of the audio in seconds.
        language: Detected or specified language of the audio.
        status: Current processing status of the meeting.
        transcription_text: Full transcription text from the audio.
        summary_json: Structured summary data (JSON).
        translation_text: Translated version of the transcription.
        target_language: Target language for translation (optional).
        user_id: Foreign key referencing the owning user.
        created_at: Timestamp of meeting creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True) if _is_postgres else String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    audio_filename: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    audio_file_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    audio_duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus),
        nullable=False,
        default=MeetingStatus.UPLOADED,
    )
    transcription_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    summary_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    translation_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    target_language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=True) if _is_postgres else String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to User model
    user: Mapped["User"] = relationship(
        "User",
        backref="meetings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation of the Meeting."""
        return f"<Meeting(id={self.id}, title={self.title}, status={self.status})>"
