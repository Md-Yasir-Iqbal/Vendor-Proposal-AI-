"""Schemas for traceable evidence snippets pulled from the vector store."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A chunk of proposal text, ready for embedding and storage in Chroma."""

    chunk_id: str
    vendor: str
    document: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    chunk_index: int = 0
    text: str


class EvidenceSnippet(BaseModel):
    """A retrieved (or rule-derived) piece of evidence backing a claim."""

    vendor: str
    document: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    source_text: str
    evidence_type: str = Field(
        "retrieval", description="retrieval | rule_based | extraction"
    )
    relevance_score: Optional[float] = None
