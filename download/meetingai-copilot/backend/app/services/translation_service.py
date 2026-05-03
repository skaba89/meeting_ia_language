"""
Translation service for the MeetingAI Copilot application.

Translates text between languages using the shared LLM client.
"""

from app.config import settings
from app.services.llm_client import chat_completion
from app.core.logging import get_logger
from app.core.exceptions import ExternalServiceError

logger = get_logger(__name__)


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text from source language to target language using LLM.

    Uses the shared LLM client with automatic provider fallback.

    Args:
        text: The text content to translate.
        source_lang: The source language code (e.g., 'en', 'es', 'fr').
        target_lang: The target language code for the translation.

    Returns:
        The translated text string.

    Raises:
        ValueError: If source_lang and target_lang are the same.
        RuntimeError: If all LLM providers fail.
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

    system_prompt = (
        f"You are a professional translator. Translate the following text "
        f"from {source_lang} to {target_lang}. Return only the translated text, "
        f"no explanations, no notes, no markdown formatting."
    )

    try:
        translated = await chat_completion(
            system_prompt=system_prompt,
            user_content=text,
            temperature=0.3,
            max_tokens=8192,
        )

        translated = translated.strip()

        logger.info(
            "Translation complete: %d chars -> %d chars",
            len(text),
            len(translated),
        )

        return translated

    except ExternalServiceError:
        raise
    except Exception as exc:
        logger.error("Translation failed: %s", str(exc))
        raise ExternalServiceError(
            service="LLM Translation",
            message=f"Translation failed: {exc}",
        ) from exc
