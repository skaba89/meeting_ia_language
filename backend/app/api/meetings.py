"""
Meeting management endpoints: upload, list, transcribe, summarize, delete.
All routes require JWT authentication.
"""

import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.schemas import (
    UserORM,
    MeetingORM,
    MeetingOut,
    MeetingListOut,
    MeetingUpdate,
    TranscribeRequest,
    SummaryRequest,
    MessageResponse,
)
from app.services.transcription import transcribe_audio
from app.services.summary import summarize_transcription

settings = get_settings()
router = APIRouter(prefix="/meetings", tags=["Meetings"])


def _get_user_meeting(meeting_id: str, user_id: str, db: Session) -> MeetingORM:
    """Helper: fetch a meeting owned by the current user, or 404."""
    meeting = (
        db.query(MeetingORM)
        .filter(MeetingORM.id == meeting_id, MeetingORM.owner_id == user_id)
        .first()
    )
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


# ── Upload Audio ────────────────────────────────────────────────────

@router.post("/upload", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(..., description="Audio file (mp3, wav, m4a, ogg, flac, webm)"),
    title: str = Form(default="Untitled Meeting"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Upload an audio file and create a new meeting record.
    The file is stored locally in the uploads directory.
    Supported formats: mp3, wav, m4a, ogg, flac, webm.
    """
    # Validate file extension
    original_name = file.filename or "audio.mp3"
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}",
        )

    # Validate file size
    contents = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file with unique name
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create meeting record
    meeting = MeetingORM(
        title=title,
        audio_filename=original_name,
        audio_path=file_path,
        status="uploaded",
        owner_id=user_id,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


# ── List Meetings ───────────────────────────────────────────────────

@router.get("/", response_model=List[MeetingListOut])
def list_meetings(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    List all meetings for the authenticated user, ordered by most recent first.
    Returns a lightweight representation without transcription/summary content.
    """
    meetings = (
        db.query(MeetingORM)
        .filter(MeetingORM.owner_id == user_id)
        .order_by(MeetingORM.created_at.desc())
        .all()
    )
    return meetings


# ── Get Meeting Detail ──────────────────────────────────────────────

@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(
    meeting_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Retrieve full meeting details including transcription and summary.
    """
    return _get_user_meeting(meeting_id, user_id, db)


# ── Transcribe Meeting ─────────────────────────────────────────────

@router.post("/transcribe", response_model=MeetingOut)
async def transcribe_meeting(
    request: TranscribeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Transcribe an uploaded audio file using Whisper.
    Updates the meeting record with the transcription text and detected language.
    """
    meeting = _get_user_meeting(request.meeting_id, user_id, db)

    if meeting.status not in ("uploaded", "error"):
        if meeting.status == "transcribed" or meeting.status == "completed":
            return meeting  # Already transcribed
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Meeting is currently being processed (status: {meeting.status})",
        )

    # Update status to processing
    meeting.status = "transcribing"
    db.commit()

    try:
        # Run transcription
        result = await transcribe_audio(meeting.audio_path)

        meeting.transcription = result["text"]
        meeting.language = result.get("language", "unknown")
        meeting.audio_duration_sec = result.get("duration")
        meeting.status = "transcribed"
        db.commit()
        db.refresh(meeting)

    except Exception as e:
        meeting.status = "error"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )

    return meeting


# ── Summarize Meeting ──────────────────────────────────────────────

@router.post("/summary", response_model=MeetingOut)
async def summarize_meeting(
    request: SummaryRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Generate a structured summary from a transcription using an LLM.
    The summary includes: decisions, action items, and a general overview.
    Optionally translates the summary into a target language.
    """
    meeting = _get_user_meeting(request.meeting_id, user_id, db)

    if not meeting.transcription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meeting must be transcribed before summarizing",
        )

    if meeting.status == "summarizing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Summary is already being generated",
        )

    # Update status
    meeting.status = "summarizing"
    db.commit()

    try:
        # Generate summary
        summary_result = await summarize_transcription(
            text=meeting.transcription,
            target_lang=request.target_lang,
        )

        meeting.summary_decisions = summary_result.get("decisions", "")
        meeting.summary_actions = summary_result.get("actions", "")
        meeting.summary_overview = summary_result.get("overview", "")
        meeting.summary_raw = summary_result.get("raw", "")

        # Translation if requested
        if request.target_lang and settings.TRANSLATION_ENABLED:
            meeting.translation = summary_result.get("translation", "")
            meeting.translation_lang = request.target_lang

        meeting.status = "completed"
        db.commit()
        db.refresh(meeting)

    except Exception as e:
        meeting.status = "transcribed"  # Revert to transcribed state
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}",
        )

    return meeting


# ── Update Meeting ──────────────────────────────────────────────────

@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting(
    meeting_id: str,
    update_data: MeetingUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update meeting metadata (e.g., title)."""
    meeting = _get_user_meeting(meeting_id, user_id, db)

    if update_data.title is not None:
        meeting.title = update_data.title

    db.commit()
    db.refresh(meeting)
    return meeting


# ── Delete Meeting ──────────────────────────────────────────────────

@router.delete("/{meeting_id}", response_model=MessageResponse)
def delete_meeting(
    meeting_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a meeting and its associated audio file."""
    meeting = _get_user_meeting(meeting_id, user_id, db)

    # Remove audio file from disk
    if meeting.audio_path and os.path.exists(meeting.audio_path):
        os.remove(meeting.audio_path)

    db.delete(meeting)
    db.commit()

    return MessageResponse(message="Meeting deleted successfully")
