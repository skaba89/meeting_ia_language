"""
Transcription service using OpenAI Whisper API.
Supports both API-based transcription (default) and local Whisper model.
"""

import os
from typing import Optional

import httpx
from app.core.config import get_settings

settings = get_settings()


async def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe an audio file using Whisper.

    Returns:
        dict with keys:
            - text: Full transcription text
            - language: Detected language code (e.g., "en", "fr")
            - duration: Audio duration in seconds (if available)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if settings.WHISPER_MODE == "api":
        return await _transcribe_via_api(audio_path)
    else:
        return await _transcribe_local(audio_path)


async def _transcribe_via_api(audio_path: str) -> dict:
    """
    Transcribe using the OpenAI Whisper API.
    Requires OPENAI_API_KEY to be set in environment variables.
    This is the recommended approach for the MVP as it provides
    fast, high-quality transcriptions without local GPU requirements.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        # If no API key, return a placeholder for demo purposes
        return {
            "text": "[Demo mode] Transcription requires OPENAI_API_KEY. "
                    "Please set it in your .env file to enable Whisper transcription. "
                    "In production, this would contain the full meeting transcript.",
            "language": "en",
            "duration": None,
        }

    url = "https://api.openai.com/v1/audio/transcriptions"

    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(audio_path, "rb") as audio_file:
            filename = os.path.basename(audio_path)
            files = {"file": (filename, audio_file)}
            data = {
                "model": "whisper-1",
                "response_format": "verbose_json",
                "language": None,  # Auto-detect
            }
            headers = {"Authorization": f"Bearer {api_key}"}

            response = await client.post(url, files=files, data=data, headers=headers)
            response.raise_for_status()

    result = response.json()
    return {
        "text": result.get("text", ""),
        "language": result.get("language", "unknown"),
        "duration": result.get("duration"),
    }


async def _transcribe_local(audio_path: str) -> dict:
    """
    Transcribe using a local Whisper model.
    Requires the `openai-whisper` Python package and benefits from GPU acceleration.
    Falls back to CPU if no CUDA device is available (slower but functional).

    Note: For the MVP, local transcription is optional and may require
    significant compute resources. The API mode is recommended for production.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "Local Whisper mode requires the 'openai-whisper' package. "
            "Install it with: pip install openai-whisper"
        )

    # Use base model for speed; can be upgraded to "small", "medium", "large"
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)

    return {
        "text": result["text"],
        "language": result.get("language", "unknown"),
        "duration": result.get("segments", [{}])[-1].get("end") if result.get("segments") else None,
    }
