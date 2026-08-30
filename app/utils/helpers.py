"""Small, reusable, dependency-free helper functions used across the app."""
from __future__ import annotations

import re
import uuid
from typing import Optional

NOT_SPECIFIED = "Not specified"

# Common section-heading patterns found in vendor proposals. Used by the
# chunker (to tag chunks with a section name) and by the cleaner.
_HEADING_PATTERNS = [
    re.compile(r"^\s*\d+(\.\d+)*\s+[A-Z][A-Za-z0-9 &/\-]{2,60}$"),  # "3.2 Pricing Details"
    re.compile(r"^[A-Z][A-Z0-9 &/\-]{3,60}$"),  # ALL CAPS HEADING
    re.compile(r"^\s*(Section|Article)\s+\d+.*$", re.IGNORECASE),
]


def looks_like_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80:
        return False
    return any(p.match(line) for p in _HEADING_PATTERNS)


def generate_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def format_currency(amount: Optional[float], symbol: str = "\u20b9") -> str:
    """Format a number as Indian-style currency, e.g. Rs. 8,00,000."""
    if amount is None:
        return NOT_SPECIFIED
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return NOT_SPECIFIED
    is_negative = amount < 0
    amount = abs(amount)
    whole = int(round(amount))
    s = str(whole)
    if len(s) <= 3:
        grouped = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts) + "," + last3
    return f"{'-' if is_negative else ''}{symbol}{grouped}"


def truncate_text(text: Optional[str], max_chars: int = 220) -> str:
    if not text:
        return NOT_SPECIFIED
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "\u2026"


def status_icon(status: str) -> str:
    mapping = {
        "PASS": "\u2713",
        "FAIL": "\u2717",
        "NOT_SPECIFIED": "\u2013",
        "REQUIRES_REVIEW": "\u26a0",
    }
    return mapping.get(status, "?")


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def is_unspecified(value) -> bool:
    """True if a value should be treated as 'not provided' by the model."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {
        "",
        "not specified",
        "n/a",
        "na",
        "none",
        "unknown",
        "not mentioned",
        "not provided",
    }:
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False
