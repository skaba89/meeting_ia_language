"""
Translation service for the MeetingAI Copilot application.

Translates text between languages using Groq or OpenRouter LLM APIs.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _call_groq_translate(source_lang: str, target_lang: str, text: str) -> str:
    """Call the Groq API for text translation.

    Args:
        source_lang: Source language code.
        target_lang: Target language code.
        text: Text to translate.

    Returns:
        Translated text string.

    Raises:
        httpx.HTTPStatusError: If the API returns an error status.
        Exception: If the translation call fails.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        f"You are a professional translator. Translate the following text "
        f"from {source_lang} to {target_lang}. Return only the translated text, "
        f"no explanations, no notes, no markdown formatting."
    )
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content: str = data["choices"][0]["message"]["content"]
        return content.strip()


async def _call_openrouter_translate(source_lang: str, target_lang: str, text: str) -> str:
    """Call the OpenRouter API for text translation.

    Args:
        source_lang: Source language code.
        target_lang: Target language code.
        text: Text to translate.

    Returns:
        Translated text string.

    Raises:
        httpx.HTTPStatusError: If the API returns an error status.
        Exception: If the translation call fails.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://meetingai-copilot.app",
        "X-Title": "MeetingAI Copilot",
    }
    system_prompt = (
        f"You are a professional translator. Translate the following text "
        f"from {source_lang} to {target_lang}. Return only the translated text, "
        f"no explanations, no notes, no markdown formatting."
    )
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content: str = data["choices"][0]["message"]["content"]
        return content.strip()


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text from source language to target language using LLM.

    Routes the translation request to either the Groq or OpenRouter API
    based on the LLM_PROVIDER configuration setting.

    Args:
        text: The text content to translate.
        source_lang: The source language code (e.g., 'en', 'es', 'fr').
        target_lang: The target language code for the translation.

    Returns:
        The translated text string.

    Raises:
        ValueError: If source_lang and target_lang are the same.
        httpx.HTTPStatusError: If the API returns an error status.
        Exception: If the translation fails for any reason.
    """
    if not text or not text.strip():
        return ""

    if source_lang == target_lang:
        logger.warning(
            "Source and target languages are the same (%s). Returning original text.",
            source_lang,
        )
        return text

    logger.info(
        "Translating text from %s to %s using %s provider (text length: %d chars)",
        source_lang,
        target_lang,
        settings.LLM_PROVIDER,
        len(text),
    )

    try:
        if settings.LLM_PROVIDER == "openrouter":
            translated = await _call_openrouter_translate(source_lang, target_lang, text)
        else:
            translated = await _call_groq_translate(source_lang, target_lang, text)

        logger.info(
            "Translation complete: %d chars -> %d chars",
            len(text),
            len(translated),
        )

        return translated

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Translation API error: %d - %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
        raise Exception(
            f"Translation API error: {exc.response.status_code}"
        ) from exc
    except Exception as exc:
        logger.error("Translation failed: %s", str(exc))
        raise Exception(f"Translation failed: {str(exc)}") from exc
