from __future__ import annotations

from app.ai.groq_client import GroqClientError
from app.ai.proposal_agent import _cost_payload, answer_proposal_question
from app.retrieval.chroma_store import ChromaStore
from app.retrieval.embeddings import EmbeddingProvider
from app.schemas.analysis import ScoreBreakdown, VendorAnalysisResult
from app.schemas.evidence import DocumentChunk
from app.schemas.vendor import VendorProposal


class _FakeAgentClient:
    def __init__(self, responses):
        self.responses = iter(responses)

    def chat_json(self, *_args, **_kwargs):
        return next(self.responses)


class _FailingAgentClient:
    def chat_json(self, *_args, **_kwargs):
        raise GroqClientError("Service unavailable")


def _store() -> ChromaStore:
    store = ChromaStore(in_memory=True, collection_name="agent_test", embedding_provider=EmbeddingProvider(force_hash_fallback=True))
    store.add_chunks([
        DocumentChunk(
            chunk_id="a::proposal.pdf::p1::c1", vendor="Nexora", document="proposal.pdf", page_number=1,
            section="Support", text="Nexora provides support for six months after go-live.",
        )
    ])
    return store


def _result() -> VendorAnalysisResult:
    return VendorAnalysisResult(
        vendor_name="Nexora",
        proposal=VendorProposal(vendor_name="Nexora"),
        score=ScoreBreakdown(total_score=72.0),
    )


def test_agent_uses_selected_tools_and_returns_only_known_citations():
    client = _FakeAgentClient([
        '{"tools": [{"name": "search_evidence", "query": "support", "vendor": "Nexora"}, {"name": "inspect_vendor_results", "vendor": "Nexora"}]}',
        '{"answer": "Nexora offers six months of support [E1].", "evidence_ids": ["E1", "E999"]}',
    ])

    answer = answer_proposal_question(client, "Why does Nexora fail support?", [_result()], _store())

    assert answer.generated_by == "agent"
    assert answer.tools_used == ["search_evidence", "inspect_vendor_results"]
    assert answer.evidence_ids == ["E1"]
    assert len(answer.evidence) == 1


def test_agent_falls_back_without_changing_existing_ranking():
    answer = answer_proposal_question(_FailingAgentClient(), "What is the support period?", [_result()], _store())

    assert answer.generated_by == "fallback"
    assert "Nexora" in answer.answer


def test_three_year_cost_is_python_calculated_only_when_frequency_is_known():
    result = _result()
    result.proposal.total_cost = 1000
    result.proposal.recurring_cost = 100
    result.proposal.recurring_cost_frequency = "monthly"
    cost = _cost_payload(result)
    assert cost["calculated_annual_recurring_cost"] == 1200
    assert cost["calculated_three_year_tco"] == 4600
    result.proposal.recurring_cost_frequency = None
    assert _cost_payload(result)["calculated_three_year_tco"] is None


def test_project_name_question_reads_analysis_context_not_proposal_evidence():
    answer = answer_proposal_question(None, "What is the name of the project?", [_result()], _store(), project_name="Demo2")

    assert "Demo2" in answer.answer
    assert answer.tools_used == ["inspect_project_context"]
