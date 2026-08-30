"""
Structured extraction of vendor proposal fields using the LLM, validated
through Pydantic. This is the only place where free-text proposal content
is turned into the structured VendorProposal object used by the rest of the
pipeline.
"""
from __future__ import annotations

from typing import Optional

from pydantic import ValidationError

from app.ai.groq_client import (
    GroqClient,
    GroqClientError,
    GroqMalformedResponseError,
    parse_json_response,
)
from app.ai.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_TEMPLATE
from app.schemas.vendor import VendorProposal
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("extractor")


class ExtractionError(Exception):
    """Raised when a vendor proposal could not be turned into a valid VendorProposal."""


def _prepare_text_for_extraction(full_text: str, max_chars: Optional[int] = None) -> str:
    """
    Truncate very large documents to a safe size for a single extraction call.
    We keep the beginning of the document (title/overview/pricing usually
    appear early) plus a slice from further in the document to increase the
    chance of catching terms/support/compliance sections that appear later.
    Full-document coverage for evidence purposes is still provided separately
    via the chunk-based vector store (RAG), independent of this truncation.
    """
    settings = get_settings()
    limit = max_chars or settings.max_extraction_chars
    if len(full_text) <= limit:
        return full_text

    head_len = int(limit * 0.65)
    tail_len = limit - head_len
    head = full_text[:head_len]
    tail = full_text[-tail_len:]
    return head + "\n\n[... middle of document omitted for length ...]\n\n" + tail


def extract_vendor_proposal(client: GroqClient, full_text: str, filename_hint: Optional[str] = None) -> VendorProposal:
    """
    Run structured extraction on a single vendor's cleaned proposal text.

    Raises:
        ExtractionError: wrapping any GroqClientError or a persistent
            validation failure, so the caller can mark just this vendor
            as failed without crashing the whole pipeline.
    """
    text_for_prompt = _prepare_text_for_extraction(full_text)
    user_prompt = EXTRACTION_USER_TEMPLATE.format(proposal_text=text_for_prompt)

    raw = _call_with_repair(client, user_prompt)

    try:
        data = parse_json_response(raw)
    except GroqMalformedResponseError as exc:
        logger.warning("Malformed JSON on first attempt for %s: %s", filename_hint, exc)
        # One repair attempt: ask the model to return corrected, valid JSON.
        try:
            raw_repaired = _request_json_repair(client, user_prompt, str(exc))
            data = parse_json_response(raw_repaired)
        except (GroqClientError, GroqMalformedResponseError) as repair_exc:
            raise ExtractionError(
                f"Model returned malformed JSON for '{filename_hint}' and repair failed: {repair_exc}"
            ) from repair_exc

    try:
        proposal = VendorProposal.model_validate(data)
    except ValidationError as exc:
        logger.warning("Validation failed on first attempt for %s: %s", filename_hint, exc)
        # One repair attempt: ask the model to fix the schema violations.
        try:
            proposal = _attempt_validation_repair(client, data, exc, user_prompt)
        except (GroqClientError, ValidationError, GroqMalformedResponseError) as repair_exc:
            raise ExtractionError(
                f"Extracted data for '{filename_hint}' failed schema validation and could not be repaired: {repair_exc}"
            ) from repair_exc

    if not proposal.vendor_name and filename_hint:
        # Never invent a name; just fall back to a filename-derived label for display.
        stem = filename_hint.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
        proposal.vendor_name = stem.title() if stem else None

    return proposal


def _call_with_repair(client: GroqClient, user_prompt: str) -> str:
    try:
        return client.chat_json(EXTRACTION_SYSTEM_PROMPT, user_prompt, temperature=0.1, max_tokens=2200)
    except GroqClientError:
        raise


def _request_json_repair(client: GroqClient, original_prompt: str, issue: str) -> str:
    """Ask the model to return corrected, syntactically valid JSON."""
    repair_prompt = (
        original_prompt
        + "\n\nYour previous response could not be parsed as JSON: "
        + issue
        + "\n\nReturn ONLY a corrected, syntactically valid JSON object following the schema exactly. "
        "No markdown, no commentary."
    )
    return client.chat_json(EXTRACTION_SYSTEM_PROMPT, repair_prompt, temperature=0.0, max_tokens=2200)


def _attempt_validation_repair(client: GroqClient, bad_data: dict, error: ValidationError, original_prompt: str) -> VendorProposal:
    """Ask the model to fix its own output once, given the validation errors."""
    repair_prompt = (
        original_prompt
        + "\n\nYour previous JSON response failed schema validation with these errors:\n"
        + str(error)
        + "\n\nReturn a corrected JSON object only, following the schema exactly."
    )
    raw = client.chat_json(EXTRACTION_SYSTEM_PROMPT, repair_prompt, temperature=0.0, max_tokens=2200)
    data = parse_json_response(raw)
    return VendorProposal.model_validate(data)
