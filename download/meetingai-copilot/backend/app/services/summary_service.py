"""
Summary service for the MeetingAI Copilot application.

Generates structured meeting summaries using the shared LLM client.
Returns parsed JSON with summary, key decisions, action items, and participants.
"""

import json
import logging
import re
from typing import Optional

from app.config import settings
from app.schemas.meeting import SummarySchema
from app.services.llm_client import chat_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert meeting analyst. Analyze the following meeting transcription "
    "and provide a structured summary. You MUST respond with valid JSON only, "
    "no markdown, no code blocks, no extra text. The JSON must have exactly these keys:\n"
    '- "summary": A concise summary of the meeting (string)\n'
    '- "key_decisions": An array of key decisions made (array of strings)\n'
    '- "action_items": An array of action items identified (array of strings)\n'
    '- "participants": An array of participant names mentioned (array of strings, can be empty)\n\n'
    "Example response format:\n"
    '{"summary": "The team discussed...", "key_decisions": ["Decision 1"], '
    '"action_items": ["Action 1"], "participants": ["Alice", "Bob"]}'
)


def _extract_json_from_response(text: str) -> dict:
    """Extract and parse JSON from an LLM response that may contain markdown.

    Handles responses wrapped in markdown code blocks (```json ... ```)
    as well as plain JSON responses.

    Args:
        text: Raw text response from the LLM.

    Returns:
        Parsed JSON dictionary.

    Raises:
        ValueError: If no valid JSON can be extracted from the response.
    """
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = text.strip()

    # Try to find JSON object boundaries
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = json_str[first_brace : last_brace + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from LLM response: %s\nResponse: %s", exc, text[:500])
        raise ValueError(f"Invalid JSON in LLM response: {exc}") from exc


async def generate_summary(
    transcription_text: str,
    language: str = "en",
) -> SummarySchema:
    """Generate a structured summary from a meeting transcription.

    Uses the shared LLM client with automatic provider fallback.

    Args:
        transcription_text: The full transcription text to summarize.
        language: Language code of the transcription (used for context).

    Returns:
        SummarySchema containing parsed summary, key decisions,
        action items, and participants.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
        RuntimeError: If all LLM providers fail.
        Exception: If the summary generation fails.
    """
    if not transcription_text or not transcription_text.strip():
        return SummarySchema(
            summary="No transcription text provided.",
            key_decisions=[],
            action_items=[],
            participants=[],
        )

    logger.info(
        "Generating summary using %s provider (transcription length: %d chars)",
        settings.LLM_PROVIDER,
        len(transcription_text),
    )

    try:
        # Use shared LLM client with JSON response format on Groq
        raw_response = await chat_completion(
            system_prompt=SYSTEM_PROMPT,
            user_content=transcription_text,
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        # Parse the JSON response
        parsed = _extract_json_from_response(raw_response)

        # Build and validate the SummarySchema
        summary = SummarySchema(
            summary=parsed.get("summary", ""),
            key_decisions=parsed.get("key_decisions", []),
            action_items=parsed.get("action_items", []),
            participants=parsed.get("participants", []),
        )

        logger.info(
            "Summary generated successfully: %d decisions, %d action items, %d participants",
            len(summary.key_decisions),
            len(summary.action_items),
            len(summary.participants),
        )

        return summary

    except ValueError as exc:
        logger.error("Failed to parse summary JSON: %s", exc)
        # Return a fallback summary with the raw text
        return SummarySchema(
            summary="Summary generation produced invalid format. Raw response saved.",
            key_decisions=[],
            action_items=[],
            participants=[],
        )
    except Exception as exc:
        logger.error("Summary generation failed: %s", exc)
        raise RuntimeError(f"Summary generation failed: {exc}") from exc
