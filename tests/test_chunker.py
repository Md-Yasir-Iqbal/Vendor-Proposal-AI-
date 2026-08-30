"""Chunking tests: page alignment, section tagging, size limits."""
from app.document_processing.chunker import chunk_document
from app.document_processing.pdf_parser import PageContent, ParsedDocument


def test_chunks_stay_within_max_size():
    long_para = "This is a sentence about pricing terms. " * 60
    parsed = ParsedDocument(filename="doc.pdf", pages=[PageContent(page_number=1, text=long_para)])
    chunks = chunk_document(parsed, vendor="Vendor X", document_name="doc.pdf", max_chunk_chars=500, overlap_chars=50)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.text) <= 500 + 50  # allow for overlap prefix


def test_chunks_preserve_page_numbers():
    pages = [
        PageContent(page_number=1, text="PRICING\nThe cost is 500000."),
        PageContent(page_number=2, text="SUPPORT\nSupport is 12 months."),
    ]
    parsed = ParsedDocument(filename="doc.pdf", pages=pages)
    chunks = chunk_document(parsed, vendor="Vendor X", document_name="doc.pdf")
    page_numbers = {c.page_number for c in chunks}
    assert page_numbers == {1, 2}


def test_section_heading_detected_and_tagged():
    pages = [PageContent(page_number=1, text="PRICING DETAILS\n\nThe total cost is 500000 rupees.")]
    parsed = ParsedDocument(filename="doc.pdf", pages=pages)
    chunks = chunk_document(parsed, vendor="Vendor X", document_name="doc.pdf")
    assert any(c.section and "PRICING" in c.section for c in chunks)


def test_empty_page_produces_no_chunks():
    pages = [PageContent(page_number=1, text="")]
    parsed = ParsedDocument(filename="doc.pdf", pages=pages)
    chunks = chunk_document(parsed, vendor="Vendor X", document_name="doc.pdf")
    assert chunks == []
