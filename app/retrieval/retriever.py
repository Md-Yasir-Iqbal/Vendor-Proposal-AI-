"""High-level retrieval helpers built on top of ChromaStore."""
from __future__ import annotations

from typing import Dict, List, Optional

from app.retrieval.chroma_store import ChromaStore
from app.schemas.evidence import DocumentChunk, EvidenceSnippet

# Standard topics we retrieve evidence for when building risk/recommendation views.
EVIDENCE_TOPICS = [
    "pricing and total cost",
    "recurring or additional costs",
    "implementation timeline",
    "support and SLA terms",
    "certifications and compliance",
    "contract terms and exclusions",
]


def get_chunks_for_vendor(store: ChromaStore, vendor: str, all_chunks: List[DocumentChunk]) -> List[DocumentChunk]:
    """Convenience helper: filter the in-memory chunk list for a vendor
    (used to feed the AI risk analyzer without an extra round-trip)."""
    return [c for c in all_chunks if c.vendor == vendor]


def get_evidence_for_topic(store: ChromaStore, topic: str, vendor: str, top_k: int = 3) -> List[EvidenceSnippet]:
    return store.query(query_text=topic, top_k=top_k, vendor_filter=vendor)


def get_key_evidence_for_vendor(
    store: ChromaStore,
    vendor: str,
    top_k_per_topic: int = 1,
    source_documents: Optional[List[str]] = None,
) -> List[EvidenceSnippet]:
    """Gather one strong evidence snippet per key topic for a vendor, deduplicated."""
    collected: List[EvidenceSnippet] = []
    seen_texts = set()
    for topic in EVIDENCE_TOPICS:
        try:
            hits = get_evidence_for_topic(store, topic, vendor, top_k=top_k_per_topic)
        except Exception:  # noqa: BLE001
            hits = []
        for hit in hits:
            key = (hit.page_number, hit.source_text[:80])
            if key in seen_texts:
                continue
            seen_texts.add(key)
            collected.append(hit)
    # Chunks are indexed before LLM extraction, so their vendor metadata can
    # contain a filename-derived name while the evaluated result has the LLM's
    # canonical vendor name. When the exact vendor filter has no hits, use the
    # known source documents as a safe, analysis-owned alias bridge.
    if not collected and source_documents:
        allowed_documents = set(source_documents)
        for topic in EVIDENCE_TOPICS:
            try:
                hits = store.query(query_text=topic, top_k=max(8, top_k_per_topic))
            except Exception:  # noqa: BLE001
                hits = []
            for hit in hits:
                if hit.document not in allowed_documents:
                    continue
                key = (hit.page_number, hit.source_text[:80])
                if key not in seen_texts:
                    seen_texts.add(key)
                    collected.append(hit)
    return collected


def get_recommendation_evidence(
    store: ChromaStore, recommended_vendor: str, top_k: int = 4, source_documents: Optional[List[str]] = None
) -> List[EvidenceSnippet]:
    return get_key_evidence_for_vendor(
        store, recommended_vendor, top_k_per_topic=1, source_documents=source_documents
    )[:top_k]
