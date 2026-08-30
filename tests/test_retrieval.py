"""
Retrieval layer tests.

These use an in-memory Chroma client and a forced hash-based embedding
fallback so they run fully offline and don't depend on downloading any
embedding model or calling a live API.
"""
import uuid

from app.retrieval.chroma_store import ChromaStore
from app.retrieval.embeddings import EmbeddingProvider
from app.schemas.evidence import DocumentChunk


def _make_store() -> ChromaStore:
    # Each test gets its own collection name so in-memory state never leaks
    # across tests that share the same underlying ephemeral Chroma system.
    return ChromaStore(
        in_memory=True,
        collection_name=f"test_{uuid.uuid4().hex[:8]}",
        embedding_provider=EmbeddingProvider(force_hash_fallback=True),
    )


def _sample_chunks():
    return [
        DocumentChunk(
            chunk_id="vendor_a::doc.pdf::p1::c0", vendor="Vendor A", document="doc.pdf",
            page_number=1, section="Pricing", chunk_index=0,
            text="The total cost for this project is 800000 rupees payable in three installments.",
        ),
        DocumentChunk(
            chunk_id="vendor_a::doc.pdf::p2::c0", vendor="Vendor A", document="doc.pdf",
            page_number=2, section="Support", chunk_index=1,
            text="Support is provided for eighteen months with a 99.5 percent uptime SLA.",
        ),
        DocumentChunk(
            chunk_id="vendor_b::doc.pdf::p1::c0", vendor="Vendor B", document="doc.pdf",
            page_number=1, section="Pricing", chunk_index=0,
            text="Our pricing is subject to change annually and additional seats cost extra.",
        ),
    ]


def test_insertion_and_count():
    store = _make_store()
    inserted = store.add_chunks(_sample_chunks())
    assert inserted == 3
    assert store.count() == 3


def test_query_returns_relevant_chunks_with_metadata():
    store = _make_store()
    store.add_chunks(_sample_chunks())
    results = store.query("total cost pricing", top_k=2)
    assert len(results) > 0
    for r in results:
        assert r.vendor in {"Vendor A", "Vendor B"}
        assert r.page_number is not None
        assert r.source_text


def test_vendor_filter_restricts_results():
    store = _make_store()
    store.add_chunks(_sample_chunks())
    results = store.query("pricing", top_k=5, vendor_filter="Vendor B")
    assert len(results) >= 1
    assert all(r.vendor == "Vendor B" for r in results)


def test_empty_store_returns_no_results():
    store = _make_store()
    results = store.query("anything", top_k=3)
    assert results == []


def test_metadata_preserved_section_and_page():
    store = _make_store()
    store.add_chunks(_sample_chunks())
    results = store.query("support SLA uptime", top_k=3, vendor_filter="Vendor A")
    assert any(r.section == "Support" for r in results)
