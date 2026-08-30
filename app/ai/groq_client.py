"""
Thin, isolated wrapper around the Groq API.

Every other module in this application talks to the LLM only through
`GroqClient.chat_json(...)`. If the LLM provider ever needs to change,
this is the only file that should require edits.
"""
from __future__ import annotations

import json
import time
from typing import Optional

from app.utils.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger("groq_client")


# ---------------------------------------------------------------------------
# Error hierarchy — callers can catch these without importing the Groq SDK.
# ---------------------------------------------------------------------------
class GroqClientError(Exception):
    """Base class for all LLM-related errors surfaced by this application."""


class GroqNotConfiguredError(GroqClientError):
    """Raised when no API key / model is configured at all."""


class GroqAuthenticationError(GroqClientError):
    """Invalid or revoked API key."""


class GroqRateLimitError(GroqClientError):
    """Rate limit exceeded."""


class GroqTimeoutError(GroqClientError):
    """Request timed out."""


class GroqServiceError(GroqClientError):
    """Groq API unavailable / 5xx / connection error."""


class GroqInvalidModelError(GroqClientError):
    """The configured model name is invalid or unsupported."""


class GroqMalformedResponseError(GroqClientError):
    """The model responded, but not with valid/parseable content."""


class GroqClient:
    """Wraps the Groq SDK (OpenAI-compatible chat completions API)."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client = None  # lazily constructed

    # ------------------------------------------------------------------ setup
    def _ensure_client(self):
        if not self.settings.is_groq_configured():
            raise GroqNotConfiguredError(
                "GROQ_API_KEY and/or GROQ_MODEL are not set. Add them to your .env file."
            )
        if self._client is None:
            try:
                from groq import Groq  # imported lazily so tests can run without the package's network calls
            except ImportError as exc:  # pragma: no cover
                raise GroqClientError(
                    "The 'groq' package is not installed. Run: pip install groq"
                ) from exc
            self._client = Groq(api_key=self.settings.groq_api_key, timeout=self.settings.groq_timeout_seconds)
        return self._client

    # ------------------------------------------------------------------ core call
    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a chat completion request and return the raw text content.
        Raises one of the GroqClientError subclasses on failure; never
        returns None and never raises a raw SDK exception.
        """
        client = self._ensure_client()

        # Imported here so module import doesn't hard-fail if 'groq' isn't installed
        # (e.g. while running non-AI unit tests).
        try:
            import groq as groq_sdk
        except ImportError:  # pragma: no cover
            groq_sdk = None

        last_exc: Optional[Exception] = None
        attempts = max(1, self.settings.groq_max_retries + 1)

        for attempt in range(1, attempts + 1):
            try:
                response = client.chat.completions.create(
                    model=self.settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise GroqMalformedResponseError("The model returned an empty response.")
                return content
            except GroqMalformedResponseError:
                raise
            except Exception as exc:  # noqa: BLE001 - we deliberately branch on type below
                last_exc = exc
                classified = self._classify_exception(exc, groq_sdk)
                # Only retry on transient classes.
                if classified in (GroqRateLimitError, GroqTimeoutError, GroqServiceError) and attempt < attempts:
                    wait = 1.5 * attempt
                    logger.warning("Groq call failed (%s), retrying in %.1fs (attempt %d/%d)",
                                   classified.__name__, wait, attempt, attempts)
                    time.sleep(wait)
                    continue
                raise classified(self._error_message(classified, exc)) from exc

        # Should not be reached, but keeps type checkers happy.
        raise GroqServiceError(f"Groq request failed after {attempts} attempts: {last_exc}")

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _classify_exception(exc: Exception, groq_sdk) -> type:
        name = type(exc).__name__.lower()
        message = str(exc).lower()

        if groq_sdk is not None:
            if isinstance(exc, getattr(groq_sdk, "AuthenticationError", ())):
                return GroqAuthenticationError
            if isinstance(exc, getattr(groq_sdk, "RateLimitError", ())):
                return GroqRateLimitError
            if isinstance(exc, getattr(groq_sdk, "APITimeoutError", ())):
                return GroqTimeoutError
            if isinstance(exc, getattr(groq_sdk, "APIConnectionError", ())):
                return GroqServiceError
            if isinstance(exc, getattr(groq_sdk, "NotFoundError", ())):
                return GroqInvalidModelError
            if isinstance(exc, getattr(groq_sdk, "APIStatusError", ())):
                status = getattr(exc, "status_code", None)
                if status == 401:
                    return GroqAuthenticationError
                if status == 404:
                    return GroqInvalidModelError
                if status == 429:
                    return GroqRateLimitError
                if status and status >= 500:
                    return GroqServiceError

        # Fallback: classify by message content.
        if "auth" in message or "api key" in name or "401" in message:
            return GroqAuthenticationError
        if "rate" in message and "limit" in message:
            return GroqRateLimitError
        if "timeout" in message or "timed out" in message:
            return GroqTimeoutError
        if "model" in message and ("not found" in message or "does not exist" in message or "invalid" in message):
            return GroqInvalidModelError
        return GroqServiceError

    @staticmethod
    def _error_message(classified: type, exc: Exception) -> str:
        friendly = {
            GroqAuthenticationError: "Groq API key is invalid or was rejected. Check GROQ_API_KEY in your .env file.",
            GroqRateLimitError: "Groq API rate limit reached. Please wait a moment and try again.",
            GroqTimeoutError: "The request to Groq timed out. Please try again.",
            GroqServiceError: "The Groq API is currently unavailable or unreachable.",
            GroqInvalidModelError: "The configured GROQ_MODEL is invalid or not available to your account.",
        }
        base = friendly.get(classified, "An unexpected error occurred while calling the Groq API.")
        return f"{base} (details: {exc})"


def parse_json_response(raw_text: str) -> dict:
    """
    Parse a JSON object out of raw LLM text, tolerating common formatting
    issues (markdown code fences, leading/trailing prose).
    Raises GroqMalformedResponseError if no valid JSON object can be found.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the outermost { ... } block.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise GroqMalformedResponseError(f"Model response was not valid JSON: {exc}") from exc

    raise GroqMalformedResponseError("Model response did not contain a parseable JSON object.")
