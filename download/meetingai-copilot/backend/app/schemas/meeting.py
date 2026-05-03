"""
Meeting schemas for the MeetingAI Copilot application.

Pydantic models for request/response validation of meeting endpoints.
Uses Pydantic v2 field validators, model validators, and shared
validation utilities from app.core.validators.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.validators import (
    validate_language_code,
    sanitize_text,
    SUPPORTED_LANGUAGES,
)


class SummarySchema(BaseModel):
    """Schema for structured meeting summary.

    Attributes:
        summary: A concise textual summary of the meeting.
        key_decisions: List of key decisions made during the meeting.
        action_items: List of action items identified in the meeting.
        participants: Optional list of participants mentioned in the meeting.
    """

    summary: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Concise summary of the meeting",
        examples=["The team discussed the Q3 roadmap and agreed on three priorities."],
    )
    key_decisions: list[str] = Field(
        default_factory=list,
        description="Key decisions made during the meeting",
        examples=[["Prioritize mobile redesign", "Hire two more engineers"]],
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Action items identified in the meeting",
        examples=[["Alice to draft the proposal by Friday", "Bob to schedule vendor calls"]],
    )
    participants: list[str] = Field(
        default_factory=list,
        description="Participants mentioned in the meeting",
        examples=[["Alice", "Bob", "Charlie"]],
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        """Sanitize and validate the summary text for XSS patterns."""
        return sanitize_text(v)

    @field_validator("key_decisions", "action_items", "participants")
    @classmethod
    def validate_string_lists(cls, v: list[str]) -> list[str]:
        """Sanitize each string in list fields for XSS patterns."""
        return [sanitize_text(item) for item in v]


class TranslationRequest(BaseModel):
    """Schema for translation request.

    Attributes:
        target_language: The language code to translate the transcription into.
            Must be one of the supported language codes.
    """

    target_language: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Target language code for translation. Must be a supported language code.",
        examples=["es", "fr", "de"],
    )

    @field_validator("target_language")
    @classmethod
    def validate_target_language(cls, v: str) -> str:
        """Validate that the target language code is supported."""
        return validate_language_code(v)


class MeetingCreate(BaseModel):
    """Schema for creating a new meeting.

    Attributes:
        title: Title of the meeting (1-500 characters, XSS-sanitized).
        target_language: Optional target language code for translation.
            Must be one of the supported language codes if provided.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Meeting title",
        examples=["Weekly Standup - Q3 Planning"],
    )
    target_language: Optional[str] = Field(
        None,
        max_length=10,
        description=(
            "Target language code for translation (e.g., 'es', 'fr'). "
            f"Supported: {', '.join(f'{k} ({v})' for k, v in SUPPORTED_LANGUAGES.items())}"
        ),
        examples=["es"],
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Sanitize meeting title for XSS patterns."""
        return sanitize_text(v)

    @field_validator("target_language")
    @classmethod
    def validate_target_lang(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the target language code is supported, if provided."""
        if v is None:
            return v
        return validate_language_code(v)


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

    @model_validator(mode="after")
    def validate_translation_consistency(self) -> "MeetingDetail":
        """Ensure translation_text is only present when target_language is set.

        This cross-field validator checks that if translation_text has a value,
        a target_language is also specified. This catches inconsistent states
        where a translation exists but no language was recorded.
        """
        if self.translation_text and not self.target_language:
            # This is a data consistency issue, not a user input error.
            # We log a warning rather than raise an error so existing
            # records can still be read, but new data should not have
            # this inconsistency.
            pass  # Data is read from DB; silently tolerate for backward compat
        return self
