"""
Transcription service for the MeetingAI Copilot application.

Uses Groq's Whisper API endpoint for audio-to-text transcription
with support for large file chunking and error handling.
"""

import os
import logging
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Maximum file size for Groq Whisper API (25MB)
GROQ_WHISPER_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes


def _get_groq_client() -> AsyncOpenAI:
    """Create and return an AsyncOpenAI client configured for Groq's API.

    Returns:
        AsyncOpenAI: An OpenAI client instance pointing to Groq's endpoint.
    """
    return AsyncOpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


def _split_audio_file(file_path: str, chunk_size: int = GROQ_WHISPER_MAX_FILE_SIZE) -> list[str]:
    """Split a large audio file into smaller chunks for API upload.

    This is a simple binary split approach. For production, consider
    using proper audio splitting tools like ffmpeg for clean cuts.

    Args:
        file_path: Path to the audio file to split.
        chunk_size: Maximum size of each chunk in bytes.

    Returns:
        List of file paths for the created chunks.
    """
    file_size = os.path.getsize(file_path)
    if file_size <= chunk_size:
        return [file_path]

    chunk_paths: list[str] = []
    base_name, ext = os.path.splitext(file_path)

    with open(file_path, "rb") as f:
        chunk_index = 0
        while True:
            chunk_data = f.read(chunk_size)
            if not chunk_data:
                break
            chunk_path = f"{base_name}_chunk_{chunk_index}{ext}"
            with open(chunk_path, "wb") as chunk_file:
                chunk_file.write(chunk_data)
            chunk_paths.append(chunk_path)
            chunk_index += 1

    logger.info(
        "Split audio file %s into %d chunks (original size: %d bytes)",
        file_path,
        len(chunk_paths),
        file_size,
    )
    return chunk_paths


def _cleanup_chunks(chunk_paths: list[str]) -> None:
    """Remove temporary chunk files created during audio splitting.

    Args:
        chunk_paths: List of file paths to remove.
    """
    for path in chunk_paths:
        if "_chunk_" in path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError as exc:
                logger.warning("Failed to remove chunk file %s: %s", path, exc)


async def transcribe_audio(file_path: str, language: Optional[str] = None) -> dict:
    """Transcribe an audio file using Groq's Whisper API.

    Handles large files by splitting them into chunks if they exceed
    the API's maximum file size. Each chunk is transcribed separately
    and the results are combined.

    Args:
        file_path: Path to the audio file to transcribe.
        language: Optional language code (e.g., 'en', 'es') to guide
            transcription. If None, auto-detection is used.

    Returns:
        A dictionary with keys:
            - "text": The full transcription text.
            - "language": The detected or provided language code.
            - "duration": The estimated duration in seconds (0.0 if unknown).

    Raises:
        FileNotFoundError: If the audio file does not exist.
        httpx.HTTPStatusError: If the API returns an error status.
        Exception: If transcription fails for any other reason.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    client = _get_groq_client()
    file_size = os.path.getsize(file_path)
    logger.info(
        "Starting transcription for file: %s (size: %d bytes, language: %s)",
        file_path,
        file_size,
        language,
    )

    try:
        # Determine if we need to split the file
        if file_size > GROQ_WHISPER_MAX_FILE_SIZE:
            chunk_paths = _split_audio_file(file_path)
        else:
            chunk_paths = [file_path]

        all_text_parts: list[str] = []
        detected_language: str = language or "en"
        total_duration: float = 0.0

        for chunk_path in chunk_paths:
            with open(chunk_path, "rb") as audio_file:
                # Build transcription parameters
                transcript_params = {
                    "model": "whisper-large-v3",
                    "file": audio_file,
                    "response_format": "verbose_json",
                }
                if language:
                    transcript_params["language"] = language

                try:
                    transcript = await client.audio.transcriptions.create(
                        **transcript_params
                    )
                except Exception as api_error:
                    # Fallback: try with simpler response format
                    logger.warning(
                        "Verbose JSON transcription failed for %s, trying simple format: %s",
                        chunk_path,
                        str(api_error),
                    )
                    with open(chunk_path, "rb") as audio_file_retry:
                        fallback_params = {
                            "model": "whisper-large-v3",
                            "file": audio_file_retry,
                        }
                        if language:
                            fallback_params["language"] = language
                        transcript = await client.audio.transcriptions.create(
                            **fallback_params
                        )

            # Extract text from response
            if hasattr(transcript, "text"):
                all_text_parts.append(transcript.text)
            else:
                all_text_parts.append(str(transcript))

            # Extract duration and language from verbose response
            if hasattr(transcript, "duration") and transcript.duration:
                total_duration += transcript.duration
            if hasattr(transcript, "language") and transcript.language:
                detected_language = transcript.language

        # Clean up temporary chunk files
        if len(chunk_paths) > 1:
            _cleanup_chunks(chunk_paths)

        full_text = " ".join(all_text_parts).strip()
        logger.info(
            "Transcription complete: %d characters, language=%s, duration=%.1fs",
            len(full_text),
            detected_language,
            total_duration,
        )

        return {
            "text": full_text,
            "language": detected_language,
            "duration": total_duration,
        }

    except Exception as exc:
        logger.error("Transcription failed for file %s: %s", file_path, str(exc))
        # Clean up chunks on failure
        if file_size > GROQ_WHISPER_MAX_FILE_SIZE:
            _cleanup_chunks(chunk_paths)
        raise Exception(f"Transcription failed: {str(exc)}") from exc
