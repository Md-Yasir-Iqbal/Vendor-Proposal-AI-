from __future__ import annotations

from app.schemas.evidence import DocumentChunk
from app.ui import review


def test_review_evidence_falls_back_to_source_document_and_value(monkeypatch):
    chunks = [
        DocumentChunk(
            chunk_id="c1", vendor="Perfect Fit", document="perfectfit_proposal.pdf",
            page_number=3, section="Commercials", chunk_index=0,
            text="Commercial proposal: total implementation cost is INR 1,030,000.00.",
        ),
        DocumentChunk(
            chunk_id="c2", vendor="Perfect Fit", document="perfectfit_proposal.pdf",
            page_number=5, section="Support", chunk_index=1,
            text="Support coverage is available after launch.",
        ),
    ]
    monkeypatch.setattr(review, "get_all_chunks", lambda: chunks)

    evidence = review._find_evidence(
        "PerfectFit Solutions", ["perfectfit_proposal.pdf"],
        ("price", "cost"), 1_030_000.0,
    )

    assert evidence[0].page_number == 3
    assert "1,030,000" in evidence[0].text
