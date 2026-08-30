"""Text cleaning for raw PDF-extracted text before chunking / LLM extraction."""
from __future__ import annotations

import re

_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_BLANK_LINES = re.compile(r"\n{3,}")
_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")
_PAGE_NUM_LINE = re.compile(r"^\s*(page\s*)?\d{1,4}\s*(of\s*\d{1,4})?\s*$", re.IGNORECASE)
_BULLET_NORMALIZE = re.compile(r"^[\u2022\u25cf\u25aa\u2013o\*]\s*", re.MULTILINE)


def clean_text(text: str) -> str:
    """Normalize whitespace, de-hyphenate wrapped words, strip page-number lines."""
    if not text:
        return ""

    # Re-join words split across a line break by a hyphen, e.g. "imple-\nmentation".
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if _PAGE_NUM_LINE.match(stripped):
            continue
        cleaned_lines.append(line.rstrip())
    text = "\n".join(cleaned_lines)

    text = _BULLET_NORMALIZE.sub("- ", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def remove_repeated_headers_footers(page_texts: list[str], min_repeats: int = 3) -> list[str]:
    """
    Detect lines that repeat identically across many pages (typical running
    headers/footers, e.g. a company letterhead line) and strip them out.
    Only applied when there are enough pages to make repetition meaningful.
    """
    if len(page_texts) < min_repeats:
        return page_texts

    from collections import Counter

    line_counts: Counter[str] = Counter()
    for text in page_texts:
        first_last = set()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            first_last.add(lines[0])
        if len(lines) > 1:
            first_last.add(lines[-1])
        for l in first_last:
            if 3 <= len(l) <= 90:
                line_counts[l] += 1

    repeated = {line for line, count in line_counts.items() if count >= min_repeats}
    if not repeated:
        return page_texts

    cleaned_pages = []
    for text in page_texts:
        lines = [l for l in text.split("\n") if l.strip() not in repeated]
        cleaned_pages.append("\n".join(lines))
    return cleaned_pages
