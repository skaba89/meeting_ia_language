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
    """Split a large audio file into smaller chunks using ffmpeg for clean cuts.

    Uses ffmpeg to split at silence boundaries or at regular intervals
    with proper audio frame alignment, preventing corrupted chunks.

    Args:
        file_path: Path to the audio file to split.
        chunk_size: Target maximum size of each chunk in bytes.

    Returns:
        List of file paths for the created chunks.
    """
    import subprocess

    file_size = os.path.getsize(file_path)
    if file_size <= chunk_size:
        return [file_path]

    # Get audio duration using ffprobe
    try:
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path,
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        if probe_result.returncode != 0:
            logger.warning("ffprobe failed, falling back to binary split")
            return _split_audio_binary(file_path, chunk_size)

        import json
        probe_data = json.loads(probe_result.stdout)
        duration = float(probe_data["format"]["duration"])
    except (subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("Failed to get audio duration with ffprobe: %s. Falling back to binary split.", exc)
        return _split_audio_binary(file_path, chunk_size)

    # Calculate number of chunks based on duration and file size
    num_chunks = max(2, int(file_size / chunk_size) + 1)
    chunk_duration = duration / num_chunks

    base_name, ext = os.path.splitext(file_path)
    chunk_paths = []

    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = f"{base_name}_chunk_{i}{ext}"

        # Use ffmpeg to split with proper audio frame alignment
        # Add 1 second overlap for continuity at boundaries
        cmd = [
            "ffmpeg", "-y",
            "-i", file_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration + 1.0),  # Extra second for overlap
            "-c", "copy",  # Stream copy - fast, no re-encoding
            chunk_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning("ffmpeg split failed for chunk %d: %s. Trying re-encode.", i, result.stderr[:200])
                # Fallback: re-encode instead of stream copy
                cmd_reencode = [
                    "ffmpeg", "-y",
                    "-i", file_path,
                    "-ss", str(start_time),
                    "-t", str(chunk_duration + 1.0),
                    "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
                    "-ac", "1",     # Mono
                    chunk_path,
                ]
                result = subprocess.run(cmd_reencode, capture_output=True, text=True, timeout=300)
                if result.returncode != 0:
                    logger.error("ffmpeg re-encode also failed for chunk %d: %s", i, result.stderr[:200])
                    continue

            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                chunk_paths.append(chunk_path)
            else:
                logger.warning("Chunk %d was not created or is empty", i)

        except subprocess.SubprocessError as exc:
            logger.error("ffmpeg subprocess error for chunk %d: %s", i, exc)
            continue

    if not chunk_paths:
        logger.warning("All ffmpeg splits failed, falling back to binary split")
        return _split_audio_binary(file_path, chunk_size)

    logger.info(
        "Split audio file %s into %d chunks using ffmpeg (duration: %.1fs, chunk_duration: %.1fs)",
        file_path, len(chunk_paths), duration, chunk_duration,
    )
    return chunk_paths


def _split_audio_binary(file_path: str, chunk_size: int = GROQ_WHISPER_MAX_FILE_SIZE) -> list[str]:
    """Fallback binary split for when ffmpeg is not available.

    Args:
        file_path: Path to the audio file to split.
        chunk_size: Maximum size of each chunk in bytes.

    Returns:
        List of file paths for the created chunks.
    """
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
        "Split audio file %s into %d chunks using binary split (fallback)",
        file_path, len(chunk_paths),
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
