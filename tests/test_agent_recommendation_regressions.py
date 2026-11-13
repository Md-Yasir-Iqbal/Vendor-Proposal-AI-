"""Regression tests reproducing saved-analysis agent and evidence issues."""
from __future__ import annotations

from app.ai.proposal_agent import answer_proposal_question
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.retriever import get_recommendation_evidence
from app.schemas.analysis import ScoreBreakdown, VendorAnalysisResult
from app.schemas.evidence import DocumentChunk
from app.schemas.requirements import RequirementsConfig, ScoringWeights
from app.schemas.vendor import VendorProposal


def _store() -> ChromaStore:
    return ChromaStore(in_memory=True, collection_name="regression_evidence", embedding_provider=EmbeddingProvider(force_hash_fallback=True))


def _result(vendor: str = "Nexora Solutions") -> VendorAnalysisResult:
    return VendorAnalysisResult(
        vendor_name=vendor,
        source_documents=["nexora_proposal.pdf"],
        proposal=VendorProposal(vendor_name=vendor),
        score=ScoreBreakdown(total_score=91.0),
    )


def test_project_context_question_should_include_name_and_budget():
    """BUG A: the old API only passed the project name, losing thresholds."""
    answer = answer_proposal_question(
        None,
        "How much is this project maximum budget? What is this project name?",
        [_result()],
        _store(),
        project_name="Demo2",
        project_requirements=RequirementsConfig(
            project_name="Demo2",
            max_budget=1_500_000,
            max_timeline_weeks=10,
            min_support_months=15,
            api_integration_required=True,
            sla_required=True,
            iso27001_required=True,
            gdpr_required=True,
            scoring_weights=ScoringWeights(technical_fit=30, budget=25, delivery_timeline=20, support_sla=15, risk=10),
        ),
    )

    assert "Demo2" in answer.answer
    assert "1,500,000" in answer.answer


def test_recommendation_evidence_falls_back_to_source_document_when_vendor_names_differ():
    """BUG B: chunks were indexed before extraction under a filename-derived name."""
    store = _store()
    store.add_chunks([
        DocumentChunk(
            chunk_id="nexora_file_guess::nexora_proposal.pdf::p2::c0",
            vendor="Nexora Proposal",  # Pre-extraction/file-derived name.
            document="nexora_proposal.pdf",
            page_number=2,
            section="Pricing",
            chunk_index=0,
            text="The quoted implementation price is 1200000 and annual support is included.",
        )
    ])

    evidence = get_recommendation_evidence(
        store, "Nexora Solutions", top_k=4, source_documents=["nexora_proposal.pdf"]
    )

    assert evidence
    assert evidence[0].vendor == "Nexora Proposal"
    assert evidence[0].document == "nexora_proposal.pdf"
    assert evidence[0].page_number == 2
    assert evidence[0].section == "Pricing"


def test_empty_store_still_returns_no_recommendation_evidence():
    assert get_recommendation_evidence(_store(), "Nexora Solutions", top_k=4) == []


def test_project_requirement_question_includes_numeric_thresholds():
    requirements = RequirementsConfig(
        project_name="Demo2", max_budget=1_500_000, max_timeline_weeks=10, min_support_months=15
    )
    answer = answer_proposal_question(
        None, "What is the requirement for this project?", [_result()], _store(), project_requirements=requirements
    )

    assert "1,500,000" in answer.answer
    assert "10 weeks" in answer.answer
    assert "15 months" in answer.answer
