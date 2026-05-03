"""
Meeting schemas for the MeetingAI Copilot application.

Pydantic models for request/response validation of meeting endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SummarySchema(BaseModel):
    """Schema for structured meeting summary.

    Attributes:
        summary: A concise textual summary of the meeting.
        key_decisions: List of key decisions made during the meeting.
        action_items: List of action items identified in the meeting.
        participants: Optional list of participants mentioned in the meeting.
    """

    summary: str = Field(..., description="Concise summary of the meeting")
    key_decisions: list[str] = Field(
        default_factory=list,
        description="Key decisions made during the meeting",
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Action items identified in the meeting",
    )
    participants: list[str] = Field(
        default_factory=list,
        description="Participants mentioned in the meeting",
    )


class MeetingCreate(BaseModel):
    """Schema for creating a new meeting.

    Attributes:
        title: Title of the meeting.
        target_language: Optional target language for translation.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Meeting title")
    target_language: Optional[str] = Field(
        None,
        max_length=10,
        description="Target language code for translation (e.g., 'es', 'fr')",
    )


class MeetingResponse(BaseModel):
    """Schema for meeting data in list/response endpoints.

    Attributes:
        id: Meeting UUID as string.
        title: Meeting title.
        audio_filename: Original audio filename.
        language: Detected language of the audio.
        status: Current processing status.
        created_at: Timestamp of meeting creation.
        updated_at: Timestamp of last update.
    """

    id: str
    title: str
    audio_filename: Optional[str] = None
    language: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MeetingDetail(BaseModel):
    """Schema for detailed meeting data including full content.

    Attributes:
        id: Meeting UUID as string.
        title: Meeting title.
        audio_filename: Original audio filename.
        language: Detected language of the audio.
        status: Current processing status.
        transcription_text: Full transcription text.
        summary_json: Structured summary data.
        translation_text: Translated transcription text.
        target_language: Target language for translation.
        audio_duration: Duration of audio in seconds.
        created_at: Timestamp of meeting creation.
        updated_at: Timestamp of last update.
    """

    id: str
    title: str
    audio_filename: Optional[str] = None
    language: Optional[str] = None
    status: str
    transcription_text: Optional[str] = None
    summary_json: Optional[dict] = None
    translation_text: Optional[str] = None
    target_language: Optional[str] = None
    audio_duration: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
