"""
SQLAlchemy ORM models and Pydantic schemas for the MeetingAI Copilot API.
All database models and their corresponding serialization schemas live here.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


# ── SQLAlchemy ORM Models ──────────────────────────────────────────

class UserORM(Base):
    """Represents a registered user in the system."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meetings = relationship("MeetingORM", back_populates="owner", cascade="all, delete-orphan")


class MeetingORM(Base):
    """Represents a meeting with its audio file, transcription, and summary."""
    __tablename__ = "meetings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="Untitled Meeting")
    audio_filename = Column(String, nullable=False)
    audio_path = Column(String, nullable=False)
    audio_duration_sec = Column(Float, nullable=True)
    status = Column(String, default="uploaded")  # uploaded | transcribing | transcribed | summarizing | completed | error
    language = Column(String, nullable=True)

    # Transcription
    transcription = Column(Text, nullable=True)

    # Summary sections
    summary_decisions = Column(Text, nullable=True)
    summary_actions = Column(Text, nullable=True)
    summary_overview = Column(Text, nullable=True)
    summary_raw = Column(Text, nullable=True)

    # Translation
    translation = Column(Text, nullable=True)
    translation_lang = Column(String, nullable=True)

    # Metadata
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("UserORM", back_populates="meetings")


# ── Pydantic Schemas ───────────────────────────────────────────────

from pydantic import BaseModel, EmailStr, Field


# Auth schemas
class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    name: str = Field(default="", description="Display name")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# Meeting schemas
class MeetingOut(BaseModel):
    id: str
    title: str
    audio_filename: str
    status: str
    language: Optional[str] = None
    transcription: Optional[str] = None
    summary_decisions: Optional[str] = None
    summary_actions: Optional[str] = None
    summary_overview: Optional[str] = None
    translation: Optional[str] = None
    translation_lang: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingListOut(BaseModel):
    id: str
    title: str
    audio_filename: str
    status: str
    language: Optional[str] = None
    audio_duration_sec: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingUpdate(BaseModel):
    title: Optional[str] = None


class TranscribeRequest(BaseModel):
    meeting_id: str


class SummaryRequest(BaseModel):
    meeting_id: str
    target_lang: Optional[str] = None  # Optional translation language


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
