"""
AI-assisted risk identification.

This complements the deterministic rules in
`app.business_logic.risk_rules` (which handle clear-cut numeric/boolean
checks). Here, the LLM is used for what it's good at: spotting ambiguous
or vague language across several excerpts. Every AI-identified risk must
be grounded in a quote that is verified to actually appear in the
supplied source text -- if it doesn't, the risk is discarded rather than
trusted blindly.
"""
from __future__ import annotations

from typing import List

from app.ai.groq_client import GroqClient, GroqClientError, GroqMalformedResponseError, parse_json_response
from app.ai.prompts import RISK_ANALYSIS_SYSTEM_PROMPT, RISK_ANALYSIS_USER_TEMPLATE
from app.schemas.analysis import RiskItem, RiskSeverity
from app.schemas.evidence import DocumentChunk, EvidenceSnippet
from app.utils.logging import get_logger

logger = get_logger("risk_analyzer")

_VALID_SEVERITIES = {s.value for s in RiskSeverity}


def analyze_ambiguous_risks(client: GroqClient, vendor_name: str, chunks: List[DocumentChunk]) -> List[RiskItem]:
    """
    Ask the LLM to identify ambiguous/vague/potentially unfavorable language
    in the given chunks. Returns an empty list (never raises to the caller)
    if the LLM is unavailable or the response can't be used -- AI-assisted
    risk detection is a bonus layer on top of deterministic rules, not a
    hard dependency of the pipeline.
    """
    if not chunks:
        return []

    excerpt_text = "\n\n".join(
        f"[Page {c.page_number or '?'}] {c.text[:900]}" for c in chunks[:8]
    )

    prompt = RISK_ANALYSIS_USER_TEMPLATE.format(vendor_name=vendor_name, excerpts=excerpt_text)

    try:
        raw = client.chat_json(RISK_ANALYSIS_SYSTEM_PROMPT, prompt, temperature=0.2, max_tokens=1200)
        data = parse_json_response(raw)
    except (GroqClientError, GroqMalformedResponseError) as exc:
        logger.info("AI risk analysis skipped for %s: %s", vendor_name, exc)
        return []

    risks_raw = data.get("risks", []) if isinstance(data, dict) else []
    combined_source = "\n".join(c.text for c in chunks)

    results: List[RiskItem] = []
    for item in risks_raw:
        try:
            quote = str(item.get("quote", "")).strip()
            severity_raw = str(item.get("severity", "")).strip()
            description = str(item.get("description", "")).strip()
            category = str(item.get("category", "Ambiguous Language")).strip()
            page_number = item.get("page_number")

            if not quote or not description:
                continue
            if severity_raw not in _VALID_SEVERITIES:
                severity_raw = RiskSeverity.REVIEW.value
            # Groundedness check: the quote must actually appear (loosely) in the source.
            if quote.lower()[:40] not in combined_source.lower():
                logger.info("Discarding ungrounded AI risk quote for %s", vendor_name)
                continue

            evidence = EvidenceSnippet(
                vendor=vendor_name,
                document=chunks[0].document if chunks else None,
                page_number=page_number if isinstance(page_number, int) else None,
                section=None,
                source_text=quote,
                evidence_type="retrieval",
            )
            results.append(
                RiskItem(
                    category=category,
                    severity=RiskSeverity(severity_raw),
                    description=description,
                    related_field=None,
                    source="ai_identified",
                    evidence=evidence,
                )
            )
        except Exception as exc:  # noqa: BLE001 - never let one bad item break the batch
            logger.warning("Skipping malformed AI risk item for %s: %s", vendor_name, exc)
            continue

    return results
