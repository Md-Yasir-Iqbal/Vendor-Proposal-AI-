"""
Contextual chunking of a parsed, cleaned document.

Goals:
- Keep chunks aligned to page boundaries so we can always cite a page number.
- Split within a page along paragraph boundaries (not arbitrary character
  cuts) so retrieved evidence reads coherently.
- Tag each chunk with the nearest preceding section heading, when detected,
  so evidence can say "Vendor A, Page 6, Pricing Terms".
- Add a small character overlap between consecutive chunks on the same page
  so context (e.g. a clause split across a chunk boundary) isn't lost.
"""
from __future__ import annotations

from typing import List, Optional

from app.document_processing.cleaner import clean_text
from app.document_processing.pdf_parser import ParsedDocument
from app.schemas.evidence import DocumentChunk
from app.utils.helpers import looks_like_heading


def _split_into_paragraphs(text: str) -> List[str]:
    raw_paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in raw_paragraphs if p]


def _pack_paragraphs(paragraphs: List[str], max_chars: int, overlap: int) -> List[str]:
    """Greedily pack paragraphs into chunks of at most max_chars, with overlap."""
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            # Very long paragraph (e.g. a dense terms block): hard-split it.
            # Pieces are sized to (max_chars - overlap) here because the final
            # overlap pass below adds `overlap` extra characters to each chunk.
            step = max(1, max_chars - overlap)
            for i in range(0, len(para), step):
                piece = para[i : i + step]
                if current and len(current) + len(piece) + 1 <= max_chars:
                    current = (current + "\n" + piece).strip()
                else:
                    if current:
                        chunks.append(current)
                    current = piece
            continue

        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    # Apply overlap: prepend the tail of the previous chunk to the next one.
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            overlapped.append((tail + "\n" + chunks[i]).strip())
        chunks = overlapped

    return chunks


def chunk_document(
    parsed: ParsedDocument,
    vendor: str,
    document_name: str,
    max_chunk_chars: int = 1200,
    overlap_chars: int = 150,
) -> List[DocumentChunk]:
    """Turn a ParsedDocument into a list of DocumentChunk ready for embedding."""
    chunks: List[DocumentChunk] = []
    current_section: Optional[str] = None
    chunk_index = 0

    for page in parsed.pages:
        page_text = clean_text(page.text)
        if not page_text:
            continue

        # Track the last heading-like line seen, to tag subsequent chunks.
        for line in page_text.split("\n"):
            if looks_like_heading(line):
                current_section = line.strip()
                break  # only need the first heading found on the page for tagging

        paragraphs = _split_into_paragraphs(page_text)
        packed = _pack_paragraphs(paragraphs, max_chunk_chars, overlap_chars)

        for piece in packed:
            if not piece.strip():
                continue
            chunk_id = f"{vendor}::{document_name}::p{page.page_number}::c{chunk_index}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    vendor=vendor,
                    document=document_name,
                    page_number=page.page_number,
                    section=current_section,
                    chunk_index=chunk_index,
                    text=piece,
                )
            )
            chunk_index += 1

    return chunks
