"""
PDF processing tests.

These tests build small PDFs on the fly with PyMuPDF, so they don't
depend on the sample data files and run anywhere.
"""
import pymupdf as fitz
import pytest

from app.document_processing.pdf_parser import PDFProcessingError, parse_pdf


def _make_pdf_bytes(text: str | None = "Hello, this is a proposal with some text.") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def test_valid_pdf_extracts_text():
    pdf_bytes = _make_pdf_bytes("Total Cost: 500000. Timeline: 6 weeks.")
    parsed = parse_pdf(pdf_bytes, "valid.pdf")
    assert parsed.num_pages == 1
    assert "Total Cost" in parsed.full_text
    assert not parsed.likely_scanned


def test_truncated_corrupt_pdf_raises():
    # A real PDF's bytes, truncated halfway, should fail to open cleanly.
    good_bytes = _make_pdf_bytes("Some content that will never be reached.")
    corrupted = good_bytes[: len(good_bytes) // 2]
    with pytest.raises(PDFProcessingError):
        parse_pdf(corrupted, "corrupted.pdf")


def test_zero_byte_file_raises():
    with pytest.raises(PDFProcessingError):
        parse_pdf(b"", "zero_bytes.pdf")


def test_invalid_pdf_bytes_raise():
    with pytest.raises(PDFProcessingError):
        parse_pdf(b"this is not a real pdf file", "corrupt.pdf")


def test_image_only_pdf_flagged_as_likely_scanned():
    # A page with no inserted text should have ~0 extractable characters.
    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    # A page with 0 chars but 1 page is still "0 pages" edge case avoided by having 1 page.
    parsed = parse_pdf(data, "scanned.pdf")
    assert parsed.likely_scanned is True
    assert any("scanned" in w.lower() for w in parsed.warnings)
