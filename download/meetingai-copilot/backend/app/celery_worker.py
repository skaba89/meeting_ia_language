"""
Celery worker configuration for MeetingAI Copilot.

Handles async processing of transcription, summarization, and translation tasks.
"""

import os
import logging
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "meetingai_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Queue configuration
    task_routes={
        "app.tasks.process_transcription": {"queue": "ai_processing"},
        "app.tasks.process_summary": {"queue": "ai_processing"},
        "app.tasks.process_translation": {"queue": "ai_processing"},
    },
    # Retry policy
    task_default_retry_delay=60,
    task_max_retries=3,
)

if __name__ == "__main__":
    celery_app.start()
