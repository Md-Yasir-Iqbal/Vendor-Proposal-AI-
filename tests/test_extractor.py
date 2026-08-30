"""
Extraction pipeline tests.

None of these tests call the real Groq API -- GroqClient.chat_json is
mocked/monkeypatched throughout. This file is safe to run without any
API key configured.
"""
import json

import pytest

from app.ai.extractor import ExtractionError, extract_vendor_proposal
from app.ai.groq_client import GroqClient, GroqMalformedResponseError


class _FakeClient(GroqClient):
    """A GroqClient stand-in that returns canned responses instead of calling the network."""

    def __init__(self, responses):
        # Intentionally skip GroqClient.__init__ (no real settings/client needed).
        self._responses = list(responses)
        self.calls = []

    def chat_json(self, system_prompt, user_prompt, temperature=0.2, max_tokens=2000):
        self.calls.append((system_prompt, user_prompt))
        if not self._responses:
            raise GroqMalformedResponseError("No more canned responses.")
        return self._responses.pop(0)


VALID_JSON = json.dumps({
    "vendor_name": "Vendor A", "total_cost": 800000, "recurring_cost": 45000,
    "recurring_cost_frequency": "monthly", "currency": "INR", "payment_terms": "40/40/20",
    "pricing_conditions": None, "implementation_timeline_weeks": 6, "implementation_timeline_raw": "6 weeks",
    "support_duration_months": 18, "sla": "99.5% uptime", "warranty": None,
    "features": ["Ticketing"], "technical_capabilities": ["REST API"],
    "api_integration_supported": True, "certifications": ["ISO 27001"],
    "iso27001_certified": True, "gdpr_compliant": True, "security_information": None,
    "contract_terms": None, "exclusions": [], "other_clauses": [],
})


def test_valid_extraction_produces_validated_proposal():
    client = _FakeClient([VALID_JSON])
    proposal = extract_vendor_proposal(client, "some proposal text " * 50, filename_hint="vendor_a.pdf")
    assert proposal.vendor_name == "Vendor A"
    assert proposal.total_cost == 800000
    assert proposal.api_integration_supported is True


def test_malformed_json_raises_extraction_error():
    client = _FakeClient(["this is not json at all"])
    with pytest.raises(ExtractionError):
        extract_vendor_proposal(client, "some proposal text", filename_hint="broken.pdf")


def test_markdown_fenced_json_is_parsed():
    fenced = f"```json\n{VALID_JSON}\n```"
    client = _FakeClient([fenced])
    proposal = extract_vendor_proposal(client, "text", filename_hint="vendor_a.pdf")
    assert proposal.vendor_name == "Vendor A"


def test_validation_repair_recovers_from_bad_types():
    # First response has an invalid type (a sentence instead of a number) for total_cost,
    # but our validators coerce it to None. That still validates -- so instead we simulate a
    # genuinely malformed JSON that requires a second corrected attempt.
    bad_json = '{"vendor_name": "Vendor A", "total_cost": 800000,'  # truncated / invalid JSON
    client = _FakeClient([bad_json, VALID_JSON])
    proposal = extract_vendor_proposal(client, "text", filename_hint="vendor_a.pdf")
    assert proposal.vendor_name == "Vendor A"
    assert len(client.calls) == 2  # confirms a repair round-trip happened


def test_missing_vendor_name_falls_back_to_filename():
    data = json.loads(VALID_JSON)
    data["vendor_name"] = None
    client = _FakeClient([json.dumps(data)])
    proposal = extract_vendor_proposal(client, "text", filename_hint="acme_corp_proposal.pdf")
    assert proposal.vendor_name == "Acme Corp Proposal"
