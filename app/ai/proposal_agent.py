"""Read-only, evidence-grounded tool agent for questions about proposals.

The agent can choose from a deliberately small set of tools.  It has no
write access and never participates in requirement matching, scoring,
ranking, or vendor selection.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

from app.ai.groq_client import GroqClient, GroqClientError, GroqMalformedResponseError, parse_json_response
from app.retrieval.chroma_store import ChromaStore, RetrievalError
from app.schemas.analysis import VendorAnalysisResult
from app.schemas.evidence import EvidenceSnippet


PLANNER_SYSTEM_PROMPT = """You are the planning component of Vendorlens, a read-only procurement assistant.
Choose the smallest set of tools needed to answer the question. You may choose:
- search_evidence: semantic search over uploaded proposal excerpts; accepts query and optional vendor.
- calculate_total_cost: deterministic one-time, recurring and 3-year cost comparison; accepts optional vendor.
- check_requirements: reads existing deterministic requirement matches; accepts optional vendor.
- analyze_vendor_risks: reads existing deterministic and AI-assisted risk findings; accepts optional vendor.
- compare_vendors: reads the deterministic ranking and score totals; no arguments.

Return JSON only: {"tools": [{"name": string, "query": string?, "vendor": string?}]}. Use at most 3 tools.
Never request or invent a tool outside this list. The tools are read-only."""

ANSWER_SYSTEM_PROMPT = """You are Vendorlens Ask the Proposals, a careful procurement research assistant.
Answer only from the supplied deterministic analysis data and retrieved proposal evidence. Do not change,
recalculate, or second-guess scores, rankings, or vendor selection. Be concise, distinguish a proposal claim
from an evaluated result, and state when the evidence is insufficient. Cite source-backed claims inline as
[E1], [E2], and so on, using only IDs from the supplied evidence list. Do not fabricate citations.
Give a useful answer of at least 2-4 complete sentences when evidence is available; use more detail for a
multi-part question. Return JSON only: {"answer": string, "evidence_ids": [string, ...]}."""


@dataclass
class ProposalAnswer:
    """A safe response rendered by the Ask the Proposals page."""

    answer: str
    evidence: List[EvidenceSnippet] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    generated_by: str = "agent"
    tools_used: List[str] = field(default_factory=list)
    execution_details: List[dict[str, Any]] = field(default_factory=list)


def answer_proposal_question(
    client: Optional[GroqClient],
    question: str,
    results: Iterable[VendorAnalysisResult],
    store: ChromaStore,
    conversation_history: Optional[List[dict[str, str]]] = None,
    project_name: Optional[str] = None,
) -> ProposalAnswer:
    """Plan tool use, execute read-only tools, then create a cited answer.

    A deterministic evidence-only fallback keeps the page useful if Groq is
    unavailable. It never alters the existing evaluation state.
    """
    clean_question = question.strip()
    ranked = sorted(list(results), key=lambda item: item.score.total_score, reverse=True)
    if not clean_question:
        return ProposalAnswer("Enter a question about the uploaded proposals.", generated_by="fallback")

    # Project metadata belongs to the configured analysis, not vendor PDFs.
    # Answer it directly instead of sending an irrelevant Chroma search.
    question_lower = clean_question.lower()
    if project_name and ("project name" in question_lower or "name of the project" in question_lower):
        return ProposalAnswer(
            answer=(f"The current analysis project is named **{project_name}**. This name comes from the "
                    "configured analysis requirements, not from a vendor proposal, so no proposal citation is needed."),
            generated_by="fallback",
            tools_used=["inspect_project_context"],
            execution_details=[{"tool": "inspect_project_context", "status": "success", "input": {}, "output": "Read the configured analysis project name."}],
        )

    if client is None:
        return _fallback_answer(clean_question, ranked, store, "Groq is not configured.")

    try:
        plan = _plan_tools(client, clean_question, ranked, conversation_history or [])
        tool_data, evidence, tools_used, execution = _execute_tools(plan, clean_question, ranked, store)
        return _write_answer(client, clean_question, tool_data, evidence, tools_used, execution)
    except Exception:  # Never leave a submitted user message without a reply.
        return _fallback_answer(clean_question, ranked, store, "The AI agent is unavailable right now.")


def _plan_tools(client: GroqClient, question: str, results: List[VendorAnalysisResult], history: List[dict[str, str]]) -> List[dict[str, str]]:
    vendor_names = [item.vendor_name for item in results]
    raw = client.chat_json(
        PLANNER_SYSTEM_PROMPT,
        json.dumps({"question": question, "available_vendors": vendor_names, "conversation_context": history[-6:], "instruction": "Conversation context may resolve references such as 'it', but never treat earlier assistant answers as verified facts."}),
        temperature=0.0,
        max_tokens=450,
    )
    data = parse_json_response(raw)
    planned = data.get("tools", [])
    if not isinstance(planned, list):
        planned = []

    valid: List[dict[str, str]] = []
    for item in planned[:3]:
        if not isinstance(item, dict) or item.get("name") not in {
            "search_evidence", "calculate_total_cost", "check_requirements", "analyze_vendor_risks", "compare_vendors", "inspect_vendor_results"
        }:
            continue
        tool = {"name": str(item["name"])}
        if isinstance(item.get("query"), str):
            tool["query"] = item["query"].strip()
        if isinstance(item.get("vendor"), str) and item["vendor"].strip() in vendor_names:
            tool["vendor"] = item["vendor"].strip()
        valid.append(tool)

    # A valid plan with no tools would leave the answer ungrounded. Default
    # to evidence plus computed results rather than trusting that response.
    return valid or [
        {"name": "search_evidence", "query": question},
        {"name": "check_requirements"},
    ]


def _execute_tools(
    plan: List[dict[str, str]],
    question: str,
    results: List[VendorAnalysisResult],
    store: ChromaStore,
) -> tuple[List[dict[str, Any]], List[EvidenceSnippet], List[str], List[dict[str, Any]]]:
    tool_data: List[dict[str, Any]] = []
    evidence: List[EvidenceSnippet] = []
    tools_used: List[str] = []
    execution: List[dict[str, Any]] = []

    for tool in plan:
        name = tool["name"]
        if name == "search_evidence":
            query = tool.get("query") or question
            hits = search_evidence(store, query, tool.get("vendor"))
            evidence.extend(hits)
            tool_data.append({"tool": name, "query": query, "vendor": tool.get("vendor"), "hits": _evidence_payload(hits)})
            execution.append({"tool": name, "status": "success", "input": {"query": query, "vendor": tool.get("vendor")}, "output": f"Retrieved {len(hits)} proposal excerpt(s)."})
        elif name in {"check_requirements", "inspect_vendor_results"}:
            selected = [item for item in results if not tool.get("vendor") or item.vendor_name == tool["vendor"]]
            payload = check_requirements(selected)
            tool_data.append({"tool": "check_requirements", "vendors": payload})
            execution.append({"tool": "check_requirements", "status": "success", "input": {"vendor": tool.get("vendor")}, "output": f"Inspected requirement results for {len(payload)} vendor(s)."})
        elif name == "analyze_vendor_risks":
            selected = [item for item in results if not tool.get("vendor") or item.vendor_name == tool["vendor"]]
            payload = analyze_vendor_risks(selected)
            tool_data.append({"tool": name, "vendors": payload})
            execution.append({"tool": name, "status": "success", "input": {"vendor": tool.get("vendor")}, "output": f"Inspected risks for {len(payload)} vendor(s)."})
        elif name == "calculate_total_cost":
            selected = [item for item in results if not tool.get("vendor") or item.vendor_name == tool["vendor"]]
            payload = calculate_total_cost(selected)
            tool_data.append({"tool": name, "vendors": payload})
            execution.append({"tool": name, "status": "success", "input": {"vendor": tool.get("vendor")}, "output": f"Calculated comparable costs for {len(payload)} vendor(s); unknown charges were not assumed."})
        elif name == "compare_vendors":
            tool_data.append(
                {
                    "tool": name,
                    "ranking": compare_vendors(results),
                }
            )
            execution.append({"tool": name, "status": "success", "input": {}, "output": f"Compared {len(results)} existing evaluation result(s)."})
        tools_used.append(name)

    return tool_data, _deduplicate_evidence(evidence), tools_used, execution


def _write_answer(
    client: GroqClient,
    question: str,
    tool_data: List[dict[str, Any]],
    evidence: List[EvidenceSnippet],
    tools_used: List[str],
    execution: List[dict[str, Any]],
) -> ProposalAnswer:
    numbered_evidence = _evidence_payload(evidence)
    raw = client.chat_json(
        ANSWER_SYSTEM_PROMPT,
        json.dumps({"question": question, "tool_results": tool_data, "evidence": numbered_evidence}, default=str),
        temperature=0.1,
        max_tokens=900,
    )
    data = parse_json_response(raw)
    answer = str(data.get("answer", "")).strip()
    if not answer:
        raise GroqMalformedResponseError("The agent returned an empty answer.")

    allowed = {f"E{index}" for index in range(1, len(evidence) + 1)}
    cited_ids = [str(item) for item in data.get("evidence_ids", []) if str(item) in allowed]
    if answer.count(".") < 2:
        answer += " Review the cited proposal excerpts below to verify the commercial or contractual details before making a decision."
    return ProposalAnswer(answer, evidence, cited_ids, generated_by="agent", tools_used=tools_used, execution_details=execution)


def _fallback_answer(
    question: str,
    results: List[VendorAnalysisResult],
    store: ChromaStore,
    reason: str,
) -> ProposalAnswer:
    try:
        evidence = _deduplicate_evidence(store.query(question, top_k=4))
    except RetrievalError:
        evidence = []
    if results:
        leader = results[0]
        answer = (
            f"{reason} The current deterministic ranking places {leader.vendor_name} first with "
            f"{leader.score.total_score:.1f}/100. The retrieved proposal excerpts below may help answer your "
            "question, but the assistant cannot make an unsupported claim without clearer evidence."
        )
    else:
        answer = (
            f"{reason} Upload and analyze proposal PDFs before asking a proposal question. "
            "No vendor result or source evidence is currently available for a reliable answer."
        )
    return ProposalAnswer(
        answer=answer,
        evidence=evidence,
        evidence_ids=[f"E{index}" for index in range(1, len(evidence) + 1)],
        generated_by="fallback",
        tools_used=["search_evidence"],
        execution_details=[{"tool": "search_evidence", "status": "fallback", "input": {"query": question}, "output": f"Retrieved {len(evidence)} proposal excerpt(s)."}],
    )


def _result_payload(result: VendorAnalysisResult) -> dict[str, Any]:
    return {
        "vendor": result.vendor_name,
        "score": result.score.total_score,
        "mandatory_failure": result.has_mandatory_failure,
        "requirement_statuses": [{"requirement": item.label, "status": item.status.value} for item in result.requirement_results],
        "risks": [{"category": risk.category, "severity": risk.severity.value} for risk in result.risks],
        "missing_information": result.missing_information,
    }


# Public read-only tools. They deliberately call existing state-derived data
# and never mutate the procurement evaluation.
def search_evidence(store: ChromaStore, query: str, vendor: Optional[str] = None) -> List[EvidenceSnippet]:
    return store.query(query, top_k=5, vendor_filter=vendor)


def calculate_total_cost(results: List[VendorAnalysisResult]) -> List[dict[str, Any]]:
    return [_cost_payload(result) for result in results]


def check_requirements(results: List[VendorAnalysisResult]) -> List[dict[str, Any]]:
    return [_result_payload(result) for result in results]


def analyze_vendor_risks(results: List[VendorAnalysisResult]) -> List[dict[str, Any]]:
    return [
        {"vendor": result.vendor_name, "risks": [{"category": risk.category, "severity": risk.severity.value, "description": risk.description} for risk in result.risks], "missing_information": result.missing_information}
        for result in results
    ]


def compare_vendors(results: List[VendorAnalysisResult]) -> List[dict[str, Any]]:
    return [{"vendor": result.vendor_name, "score": result.score.total_score, "mandatory_failure": result.has_mandatory_failure} for result in results]


def _cost_payload(result: VendorAnalysisResult) -> dict[str, Any]:
    """Deterministic cost calculation; unknown prices and charges stay unknown."""
    proposal = result.proposal
    initial = proposal.total_cost
    recurring = proposal.recurring_cost
    frequency = (proposal.recurring_cost_frequency or "").lower().strip()
    annual = recurring if frequency in {"annual", "yearly", "per year", "year"} else (recurring * 12 if frequency in {"monthly", "month", "per month"} else None)
    three_year = initial + annual * 3 if initial is not None and annual is not None else None
    missing = []
    if initial is None:
        missing.append("initial or one-time cost")
    if recurring is None:
        missing.append("recurring cost")
    elif annual is None:
        missing.append("recurring-cost frequency")
    return {
        "vendor": result.vendor_name,
        "currency": proposal.currency,
        "quoted_initial_cost": initial,
        "quoted_recurring_cost": recurring,
        "recurring_frequency": proposal.recurring_cost_frequency,
        "calculated_annual_recurring_cost": annual,
        "calculated_three_year_tco": three_year,
        "assumption": "Three-year TCO = quoted one-time cost + (annual recurring cost × 3). It excludes unquantified additional charges, penalties, termination fees, and taxes.",
        "pricing_conditions": proposal.pricing_conditions,
        "contract_terms": proposal.contract_terms,
        "exclusions": proposal.exclusions,
        "missing_information": missing,
    }


def _evidence_payload(evidence: List[EvidenceSnippet]) -> List[dict[str, Any]]:
    return [
        {
            "id": f"E{index}",
            "vendor": item.vendor,
            "document": item.document,
            "page": item.page_number,
            "section": item.section,
            "text": item.source_text[:900],
        }
        for index, item in enumerate(evidence, start=1)
    ]


def _deduplicate_evidence(items: List[EvidenceSnippet]) -> List[EvidenceSnippet]:
    unique: List[EvidenceSnippet] = []
    seen = set()
    for item in items:
        key = (item.vendor, item.document, item.page_number, item.source_text[:120])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:8]
