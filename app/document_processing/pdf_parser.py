"""
PDF text extraction using PyMuPDF (fitz).

Design notes / known limitations:
- This module extracts embedded text only. It does NOT perform OCR.
  Scanned/image-only PDFs will yield little or no text; we detect this
  case and surface a clear warning rather than silently failing or
  fabricating content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pymupdf as fitz  # PyMuPDF (the 'pymupdf' import name is preferred over the legacy 'fitz' alias)

from app.utils.logging import get_logger

logger = get_logger("pdf_parser")


class PDFProcessingError(Exception):
    """Raised when a PDF cannot be opened or read at all."""


@dataclass
class PageContent:
    page_number: int  # 1-indexed
    text: str


@dataclass
class ParsedDocument:
    filename: str
    pages: List[PageContent] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    likely_scanned: bool = False

    @property
    def num_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @property
    def total_chars(self) -> int:
        return sum(len(p.text) for p in self.pages)


MIN_CHARS_PER_PAGE_NOT_SCANNED = 20


def parse_pdf(file_bytes: bytes, filename: str) -> ParsedDocument:
    """
    Extract text from a PDF's bytes.

    Raises:
        PDFProcessingError: if the file cannot be opened as a PDF at all
            (corrupted, not a PDF, encrypted without password, zero pages).
    """
    if not file_bytes:
        raise PDFProcessingError(f"'{filename}' is empty (0 bytes).")

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises its own exception types
        raise PDFProcessingError(f"'{filename}' could not be opened as a PDF: {exc}") from exc

    try:
        if doc.is_encrypted:
            # Try an empty password (common for "restricted, not really locked" PDFs).
            if not doc.authenticate(""):
                doc.close()
                raise PDFProcessingError(f"'{filename}' is password-protected and could not be opened.")

        if doc.page_count == 0:
            doc.close()
            raise PDFProcessingError(f"'{filename}' contains no pages.")

        pages: List[PageContent] = []
        chars_per_page = []
        for i in range(doc.page_count):
            try:
                page = doc.load_page(i)
                text = page.get_text("text") or ""
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to extract page %s of %s: %s", i + 1, filename, exc)
                text = ""
            text = text.strip()
            pages.append(PageContent(page_number=i + 1, text=text))
            chars_per_page.append(len(text))

        doc.close()

    except PDFProcessingError:
        raise
    except Exception as exc:
        raise PDFProcessingError(f"Unexpected error while reading '{filename}': {exc}") from exc

    warnings: List[str] = []
    total_chars = sum(chars_per_page)
    avg_chars = total_chars / max(1, len(pages))
    likely_scanned = avg_chars < MIN_CHARS_PER_PAGE_NOT_SCANNED

    if likely_scanned:
        warnings.append(
            "This document appears to contain little or no extractable text "
            "(it may be a scanned/image-only PDF). OCR is not implemented in "
            "this version, so analysis for this document may be incomplete."
        )
    elif total_chars == 0:
        warnings.append("No text could be extracted from this document.")

    return ParsedDocument(filename=filename, pages=pages, warnings=warnings, likely_scanned=likely_scanned)


def guess_vendor_name_from_text(text: str, filename: str) -> Optional[str]:
    """
    Very lightweight heuristic to pre-fill a vendor name before LLM extraction
    runs (used for immediate UI feedback during upload). The LLM-extracted
    name (from structured extraction) is treated as authoritative later.
    """
    import re

    candidates = []
    for line in text.splitlines()[:40]:
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if re.search(r"\b(proposal|prepared by|submitted by|vendor|from)\b", line, re.IGNORECASE):
            m = re.search(r"(?:prepared by|submitted by|from|vendor)[:\-]?\s*(.+)", line, re.IGNORECASE)
            if m and m.group(1).strip():
                candidates.append(m.group(1).strip())
    if candidates:
        return candidates[0][:80]

    # Fall back to filename without extension, lightly formatted.
    stem = filename.rsplit(".", 1)[0]
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return stem[:80] if stem else None
