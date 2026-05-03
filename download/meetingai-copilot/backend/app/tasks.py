"""
Celery tasks for async AI processing.

Tasks for transcription, summarization, and translation that run
in the background via Celery workers.
"""

import logging
from app.celery_worker import celery_app
from app.database import AsyncSessionLocal
from app.models.meeting import Meeting, MeetingStatus
from app.services.transcription_service import transcribe_audio
from app.services.summary_service import generate_summary
from app.services.translation_service import translate_text
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.process_transcription", max_retries=3)
def process_transcription(self, meeting_id: str):
    """Transcribe audio for a meeting in the background.

    Args:
        meeting_id: UUID of the meeting to transcribe.
    """
    import asyncio
    asyncio.run(_process_transcription_async(meeting_id))


async def _process_transcription_async(meeting_id: str):
    """Async implementation of transcription task."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            meeting = result.scalar_one_or_none()
            if not meeting:
                logger.error("Meeting %s not found for transcription", meeting_id)
                return

            meeting.status = MeetingStatus.TRANSCRIBING
            await session.commit()

            transcription_result = await transcribe_audio(
                file_path=meeting.audio_file_path,
                language=None,
            )

            meeting.transcription_text = transcription_result["text"]
            meeting.language = transcription_result["language"]
            meeting.audio_duration = transcription_result["duration"]
            meeting.status = MeetingStatus.TRANSCRIBED
            await session.commit()

            logger.info("Transcription complete for meeting %s", meeting_id)

        except Exception as exc:
            logger.error("Transcription failed for meeting %s: %s", meeting_id, exc)
            # Try to update status to failed
            try:
                result = await session.execute(
                    select(Meeting).where(Meeting.id == meeting_id)
                )
                meeting = result.scalar_one_or_none()
                if meeting:
                    meeting.status = MeetingStatus.FAILED
                    await session.commit()
            except Exception:
                pass


@celery_app.task(bind=True, name="app.tasks.process_summary", max_retries=3)
def process_summary(self, meeting_id: str):
    """Generate summary for a meeting in the background."""
    import asyncio
    asyncio.run(_process_summary_async(meeting_id))


async def _process_summary_async(meeting_id: str):
    """Async implementation of summary task."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            meeting = result.scalar_one_or_none()
            if not meeting:
                logger.error("Meeting %s not found for summary", meeting_id)
                return

            if not meeting.transcription_text:
                logger.error("Meeting %s has no transcription for summary", meeting_id)
                return

            meeting.status = MeetingStatus.SUMMARIZING
            await session.commit()

            from app.schemas.meeting import SummarySchema
            summary: SummarySchema = await generate_summary(
                transcription_text=meeting.transcription_text,
                language=meeting.language or "en",
            )

            meeting.summary_json = summary.model_dump()

            # Auto-translate if target language is set
            if meeting.target_language and meeting.language and meeting.target_language != meeting.language:
                try:
                    translated_text = await translate_text(
                        text=meeting.transcription_text,
                        source_lang=meeting.language,
                        target_lang=meeting.target_language,
                    )
                    meeting.translation_text = translated_text
                except Exception as translation_exc:
                    logger.warning(
                        "Translation failed for meeting %s: %s",
                        meeting_id, translation_exc,
                    )

            meeting.status = MeetingStatus.COMPLETED
            await session.commit()

            logger.info("Summary complete for meeting %s", meeting_id)

        except Exception as exc:
            logger.error("Summary failed for meeting %s: %s", meeting_id, exc)
            try:
                result = await session.execute(
                    select(Meeting).where(Meeting.id == meeting_id)
                )
                meeting = result.scalar_one_or_none()
                if meeting:
                    meeting.status = MeetingStatus.FAILED
                    await session.commit()
            except Exception:
                pass


@celery_app.task(bind=True, name="app.tasks.process_translation", max_retries=3)
def process_translation(self, meeting_id: str, target_language: str):
    """Translate a meeting transcription in the background."""
    import asyncio
    asyncio.run(_process_translation_async(meeting_id, target_language))


async def _process_translation_async(meeting_id: str, target_language: str):
    """Async implementation of translation task."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            meeting = result.scalar_one_or_none()
            if not meeting:
                logger.error("Meeting %s not found for translation", meeting_id)
                return

            if not meeting.transcription_text:
                logger.error("Meeting %s has no transcription for translation", meeting_id)
                return

            translated_text = await translate_text(
                text=meeting.transcription_text,
                source_lang=meeting.language or "en",
                target_lang=target_language,
            )

            meeting.translation_text = translated_text
            meeting.target_language = target_language
            await session.commit()

            logger.info("Translation complete for meeting %s", meeting_id)

        except Exception as exc:
            logger.error("Translation failed for meeting %s: %s", meeting_id, exc)
