"""
Summary and translation service using an LLM via OpenRouter / Groq / OpenAI-compatible API.
Generates structured meeting summaries with decisions, action items, and overview.
Optionally translates the summary into a target language.
"""

import json
from typing import Optional

import httpx
from app.core.config import get_settings

settings = get_settings()

SUMMARY_SYSTEM_PROMPT = """You are a professional meeting analyst. Your task is to analyze meeting transcripts and produce structured summaries.

You MUST respond with valid JSON only, following this exact schema:
{
  "decisions": "A clear, numbered list of all decisions made during the meeting. If no decisions were made, write 'No formal decisions were recorded.'",
  "actions": "A numbered list of action items with responsible persons and deadlines if mentioned. Format: '- [Action] (Owner, Deadline)'. If none, write 'No specific action items identified.'",
  "overview": "A comprehensive 3-5 paragraph summary of the meeting covering: key topics discussed, main arguments or perspectives, outcomes and next steps. Be specific and detailed."
}

Rules:
- Be specific: reference names, numbers, dates when they appear
- Use the same language as the transcript for the summary
- If the transcript is too short or unclear, note that in the overview
- Do not invent information that is not in the transcript
- Return ONLY valid JSON, no markdown or extra text"""

TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the following meeting summary into {target_lang}.
Maintain the professional tone and all specific details (names, numbers, dates).
Return only the translated text, preserving the original formatting."""


async def summarize_transcription(
    text: str,
    target_lang: Optional[str] = None,
) -> dict:
    """
    Generate a structured summary from a meeting transcription using an LLM.

    Args:
        text: The full transcription text
        target_lang: Optional target language for translation (e.g., "en", "fr", "es")

    Returns:
        dict with keys: decisions, actions, overview, raw, translation (optional)
    """
    api_key = settings.LLM_API_KEY
    if not api_key:
        # Demo mode: return placeholder summary
        return _demo_summary(text, target_lang)

    # Build messages for the LLM
    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"Please analyze this meeting transcript and provide a structured summary:\n\n{text}"},
    ]

    # Call LLM API
    llm_response = await _call_llm(messages)

    # Parse the structured JSON response
    summary = _parse_summary_response(llm_response)

    # Optionally translate
    translation = None
    if target_lang and settings.TRANSLATION_ENABLED:
        translation = await _translate_text(summary["overview"], target_lang)

    result = {
        "decisions": summary.get("decisions", ""),
        "actions": summary.get("actions", ""),
        "overview": summary.get("overview", ""),
        "raw": llm_response,
    }

    if translation:
        result["translation"] = translation

    return result


async def _call_llm(messages: list[dict]) -> str:
    """
    Call the configured LLM API (OpenRouter, Groq, or OpenAI-compatible).
    Uses the LLM_API_BASE and LLM_MODEL settings for configuration flexibility.
    """
    api_key = settings.LLM_API_KEY
    base_url = settings.LLM_API_BASE.rstrip("/")
    url = f"{base_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Add OpenRouter-specific headers if using OpenRouter
    if "openrouter" in base_url.lower():
        headers["HTTP-Referer"] = "https://meetingai.app"
        headers["X-Title"] = "MeetingAI Copilot"

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


async def _translate_text(text: str, target_lang: str) -> str:
    """Translate text into the target language using the LLM."""
    api_key = settings.LLM_API_KEY
    if not api_key:
        return "[Translation requires LLM_API_KEY]"

    lang_names = {
        "en": "English", "fr": "French", "es": "Spanish",
        "de": "German", "it": "Italian", "pt": "Portuguese",
        "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
        "ar": "Arabic", "ru": "Russian", "nl": "Dutch",
    }
    lang_name = lang_names.get(target_lang, target_lang)

    messages = [
        {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT.format(target_lang=lang_name)},
        {"role": "user", "content": text},
    ]

    return await _call_llm(messages)


def _parse_summary_response(response: str) -> dict:
    """
    Parse the LLM response into a structured summary.
    Attempts JSON extraction first, falls back to text parsing.
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON in the response (might be wrapped in markdown code block)
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(text)
        if isinstance(parsed, dict) and "decisions" in parsed and "actions" in parsed and "overview" in parsed:
            return parsed
    except (json.JSONDecodeError, IndexError):
        pass

    # Fallback: treat the entire response as the overview
    return {
        "decisions": "See overview for details.",
        "actions": "See overview for details.",
        "overview": response,
    }


def _demo_summary(text: str, target_lang: Optional[str] = None) -> dict:
    """
    Generate a demo summary when no LLM API key is configured.
    This allows the application to be tested without an API key.
    """
    word_count = len(text.split())
    preview = text[:200] + "..." if len(text) > 200 else text

    return {
        "decisions": (
            "1. Continue with the current project timeline\n"
            "2. Allocate additional resources for the next sprint\n"
            "3. Schedule a follow-up meeting for next week\n\n"
            "[Demo mode — set LLM_API_KEY for AI-generated summaries]"
        ),
        "actions": (
            "- [Review project milestones] (Team Lead, This week)\n"
            "- [Update documentation] (Engineering, By Friday)\n"
            "- [Send meeting notes to stakeholders] (PM, Tomorrow)\n\n"
            "[Demo mode — set LLM_API_KEY for AI-generated action items]"
        ),
        "overview": (
            f"This is a demo summary generated for a {word_count}-word transcript. "
            f"In production mode (with LLM_API_KEY configured), this section would contain "
            f"a detailed 3-5 paragraph analysis of the meeting covering key topics, "
            f"arguments, outcomes, and next steps.\n\n"
            f"Transcript preview: {preview}\n\n"
            f"[Demo mode — configure LLM_API_KEY in .env for real AI summaries]"
        ),
        "raw": f"[Demo summary for transcript of {word_count} words]",
        "translation": f"[Translation to {target_lang} would appear here in production mode]" if target_lang else None,
    }
