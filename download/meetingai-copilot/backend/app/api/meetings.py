"""
Meeting API routes for the MeetingAI Copilot application.

Provides endpoints for uploading audio, transcribing, generating summaries,
translating, listing, retrieving details, and deleting meetings.
"""

import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.user import User
from app.schemas.meeting import (
    MeetingResponse,
    MeetingDetail,
    SummarySchema,
)
from app.middleware.auth_middleware import get_current_user
from app.services.transcription_service import transcribe_audio
from app.services.summary_service import generate_summary
from app.services.translation_service import translate_text
from app.tasks import process_transcription, process_summary, process_translation

logger = logging.getLogger(__name__)

meetings_router = APIRouter(prefix="/meetings", tags=["Meetings"])

# Allowed audio MIME types
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".ogg"}


def _validate_audio_file(filename: Optional[str], content_type: Optional[str]) -> None:
    """Validate that an uploaded file is an allowed audio type.

    Args:
        filename: The original filename of the uploaded file.
        content_type: The MIME type reported by the upload.

    Raises:
        HTTPException: 400 if the file type is not allowed.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Check file extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check content type if provided
    if content_type and content_type not in ALLOWED_AUDIO_TYPES:
        # Some browsers send different content types, so we just warn
        logger.warning(
            "Unexpected content type '%s' for file '%s', but extension is allowed",
            content_type,
            filename,
        )


@meetings_router.post(
    "/upload",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio file",
    description="Upload an audio file and create a new meeting record.",
)
async def upload_meeting(
    audio: UploadFile = File(..., description="Audio file (mp3/wav/m4a/webm)"),
    title: str = Form(..., min_length=1, max_length=500, description="Meeting title"),
    target_language: Optional[str] = Form(None, max_length=10, description="Target language for translation"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Meeting:
    """Upload an audio file and create a meeting record."""
    # Validate the audio file type
    _validate_audio_file(audio.filename, audio.content_type)

    # Read the file content and check size
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await audio.read()

    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Generate a unique filename to avoid collisions
    file_extension = os.path.splitext(audio.filename)[1].lower() if audio.filename else ".mp3"
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Ensure upload directory exists
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_filename)

    # Save the file
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(
            "Audio file saved: %s (original: %s, size: %d bytes)",
            unique_filename,
            audio.filename,
            len(contents),
        )
    except OSError as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        ) from exc

    # Create the meeting record
    meeting = Meeting(
        title=title,
        audio_filename=audio.filename,
        audio_file_path=file_path,
        status=MeetingStatus.UPLOADED,
        target_language=target_language,
        user_id=current_user.id,
    )

    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)

    logger.info(
        "Meeting created: id=%s, title='%s', user=%s",
        meeting.id,
        meeting.title,
        current_user.id,
    )

    return meeting


@meetings_router.post(
    "/{meeting_id}/transcribe",
    response_model=MeetingDetail,
    summary="Transcribe meeting audio",
    description="Start transcription of the meeting's audio file using Groq Whisper API. "
    "Transcription runs asynchronously via Celery worker.",
)
async def transcribe_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Meeting:
    """Transcribe the audio file associated with a meeting (async via Celery)."""
    # Fetch the meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if not meeting.audio_file_path or not os.path.exists(meeting.audio_file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has no audio file or file was deleted",
        )

    # Update status to transcribing and dispatch Celery task
    meeting.status = MeetingStatus.TRANSCRIBING
    await db.flush()

    process_transcription.delay(meeting_id=str(meeting.id))

    await db.refresh(meeting)
    logger.info("Transcription task dispatched for meeting %s", meeting.id)

    return meeting


@meetings_router.post(
    "/{meeting_id}/summary",
    response_model=MeetingDetail,
    summary="Generate meeting summary",
    description="Generate a structured summary from the meeting transcription. "
    "Summarization runs asynchronously via Celery worker.",
)
async def summarize_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Meeting:
    """Generate a structured summary for a meeting's transcription (async via Celery)."""
    # Fetch the meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    if not meeting.transcription_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting has no transcription text. Transcribe the meeting first.",
        )

    # Update status to summarizing and dispatch Celery task
    meeting.status = MeetingStatus.SUMMARIZING
    await db.flush()

    process_summary.delay(meeting_id=str(meeting.id))

    await db.refresh(meeting)
    logger.info("Summary task dispatched for meeting %s", meeting.id)

    return meeting


@meetings_router.post(
    "/{meeting_id}/translate",
    response_model=MeetingDetail,
    summary="Translate meeting transcription",
    description="Translate the meeting transcription to a target language. "
    "Translation runs asynchronously via Celery worker.",
)
async def translate_meeting(
    meeting_id: str,
    target_language: str = Query(..., max_length=10, description="Target language code (e.g., 'fr', 'es')"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Meeting:
    """Translate a meeting's transcription to a target language (async via Celery)."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if not meeting.transcription_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting has no transcription. Transcribe first.")

    meeting.target_language = target_language
    await db.flush()
    await db.refresh(meeting)

    # Dispatch translation task
    process_translation.delay(meeting_id=str(meeting.id), target_language=target_language)

    logger.info("Translation task dispatched for meeting %s to %s", meeting.id, target_language)

    return meeting


@meetings_router.get(
    "/",
    response_model=list[MeetingResponse],
    summary="List meetings",
    description="List the current user's meetings, paginated and ordered by newest first.",
)
async def list_meetings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Meeting]:
    """List the authenticated user's meetings, newest first."""
    result = await db.execute(
        select(Meeting)
        .where(Meeting.user_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    meetings = list(result.scalars().all())
    return meetings


@meetings_router.get(
    "/{meeting_id}",
    response_model=MeetingDetail,
    summary="Get meeting detail",
    description="Retrieve full meeting details including transcription, summary, and translation.",
)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Meeting:
    """Retrieve the full details of a specific meeting."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    return meeting


@meetings_router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete meeting",
    description="Delete a meeting and its associated audio file.",
)
async def delete_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a meeting and its associated audio file."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    # Delete the audio file from the filesystem
    if meeting.audio_file_path and os.path.exists(meeting.audio_file_path):
        try:
            os.remove(meeting.audio_file_path)
            logger.info("Audio file deleted: %s", meeting.audio_file_path)
        except OSError as exc:
            logger.warning(
                "Failed to delete audio file %s: %s",
                meeting.audio_file_path,
                exc,
            )

    # Delete the meeting record from the database
    await db.delete(meeting)
    await db.flush()

    logger.info("Meeting deleted: id=%s, user=%s", meeting_id, current_user.id)
