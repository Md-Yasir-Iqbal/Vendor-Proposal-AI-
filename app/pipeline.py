"""
Orchestrates the full pipeline for one uploaded proposal:

  PDF bytes -> parse -> clean -> chunk -> [store in Chroma] + [LLM extraction]
      -> Pydantic validation -> requirement matching -> risk detection
      -> scoring -> VendorAnalysisResult

A failure processing one vendor's document is isolated: it is recorded on
that vendor's result/metadata and does not prevent other vendors from being
analyzed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.ai.extractor import ExtractionError, extract_vendor_proposal
from app.ai.groq_client import GroqClient, GroqClientError
from app.ai.risk_analyzer import analyze_ambiguous_risks
from app.business_logic.matching import has_mandatory_failure, match_requirements, missing_information_summary
from app.business_logic.risk_rules import detect_rule_based_risks
from app.business_logic.scoring import compute_score
from app.document_processing.chunker import chunk_document
from app.document_processing.pdf_parser import PDFProcessingError, ParsedDocument, guess_vendor_name_from_text, parse_pdf
from app.retrieval.chroma_store import ChromaStore, RetrievalError
from app.retrieval.retriever import get_chunks_for_vendor
from app.schemas.analysis import VendorAnalysisResult
from app.schemas.evidence import DocumentChunk
from app.schemas.requirements import RequirementsConfig
from app.schemas.vendor import VendorDocumentMeta, VendorProposal
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("pipeline")


@dataclass
class ProcessedDocument:
    meta: VendorDocumentMeta
    parsed: Optional[ParsedDocument]
    chunks: List[DocumentChunk]
    proposal: Optional[VendorProposal]


def process_uploaded_pdf(
    file_bytes: bytes,
    filename: str,
    store: ChromaStore,
    client: Optional[GroqClient],
) -> ProcessedDocument:
    """Run parsing, cleaning, chunking, storage, and LLM extraction for one file."""
    meta = VendorDocumentMeta(filename=filename)

    try:
        parsed = parse_pdf(file_bytes, filename)
    except PDFProcessingError as exc:
        meta.status = "failed"
        meta.error_message = str(exc)
        return ProcessedDocument(meta=meta, parsed=None, chunks=[], proposal=None)

    meta.num_pages = parsed.num_pages
    meta.warnings.extend(parsed.warnings)
    if parsed.likely_scanned:
        meta.status = "scanned_warning"

    vendor_name_guess = guess_vendor_name_from_text(parsed.full_text, filename) or filename

    settings = get_settings()
    chunks = chunk_document(
        parsed,
        vendor=vendor_name_guess,
        document_name=filename,
        max_chunk_chars=settings.chunk_max_chars,
        overlap_chars=settings.chunk_overlap_chars,
    )
    meta.num_chunks = len(chunks)

    if chunks:
        try:
            store.add_chunks(chunks)
        except RetrievalError as exc:
            meta.warnings.append(f"Could not store chunks for semantic search: {exc}")

    proposal: Optional[VendorProposal] = None
    if not parsed.full_text.strip():
        meta.status = "failed"
        meta.error_message = "No extractable text was found in this document."
        return ProcessedDocument(meta=meta, parsed=parsed, chunks=chunks, proposal=None)

    if client is None:
        meta.status = "failed"
        meta.error_message = "Groq API is not configured (missing GROQ_API_KEY/GROQ_MODEL)."
        return ProcessedDocument(meta=meta, parsed=parsed, chunks=chunks, proposal=None)

    try:
        proposal = extract_vendor_proposal(client, parsed.full_text, filename_hint=filename)
        meta.detected_vendor_name = proposal.vendor_name or vendor_name_guess
        if meta.status not in ("scanned_warning",):
            meta.status = "processed"
    except (ExtractionError, GroqClientError) as exc:
        meta.status = "failed"
        meta.error_message = str(exc)
        meta.detected_vendor_name = vendor_name_guess

    return ProcessedDocument(meta=meta, parsed=parsed, chunks=chunks, proposal=proposal)


def analyze_vendor(
    vendor_name: str,
    proposal: VendorProposal,
    source_documents: List[str],
    requirements: RequirementsConfig,
    all_chunks: List[DocumentChunk],
    client: Optional[GroqClient],
    use_ai_risk_analysis: bool = True,
) -> VendorAnalysisResult:
    """Run matching, risk detection, and scoring for one already-extracted vendor."""
    requirement_results = match_requirements(proposal, requirements)
    mandatory_fail = has_mandatory_failure(requirement_results)
    missing = missing_information_summary(requirement_results, proposal)

    risks = detect_rule_based_risks(proposal, requirements)

    if use_ai_risk_analysis and client is not None:
        try:
            vendor_chunks = get_chunks_for_vendor(None, vendor_name, all_chunks)  # store unused here
            ai_risks = analyze_ambiguous_risks(client, vendor_name, vendor_chunks)
            risks.extend(ai_risks)
        except Exception as exc:  # noqa: BLE001 - AI risk layer must never break the pipeline
            logger.info("AI risk analysis skipped for %s due to error: %s", vendor_name, exc)

    score = compute_score(proposal, requirement_results, risks, requirements)

    return VendorAnalysisResult(
        vendor_name=vendor_name,
        source_documents=source_documents,
        proposal=proposal,
        requirement_results=requirement_results,
        risks=risks,
        missing_information=missing,
        score=score,
        has_mandatory_failure=mandatory_fail,
        extraction_failed=False,
    )


def build_failed_vendor_result(vendor_name: str, filename: str, error_message: str) -> VendorAnalysisResult:
    """Represents a vendor whose document could not be processed at all."""
    from app.schemas.analysis import ScoreBreakdown

    return VendorAnalysisResult(
        vendor_name=vendor_name,
        source_documents=[filename],
        proposal=VendorProposal(vendor_name=vendor_name),
        requirement_results=[],
        risks=[],
        missing_information=[f"Processing failed: {error_message}"],
        score=ScoreBreakdown(),
        has_mandatory_failure=True,
        extraction_failed=True,
        extraction_error=error_message,
    )
