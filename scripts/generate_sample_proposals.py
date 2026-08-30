"""
Generates three synthetic vendor proposal PDFs used as sample data for
demoing and testing the application. All content is fictional.

Run:  python scripts/generate_sample_proposals.py
"""
from __future__ import annotations

import os

import pymupdf as fitz

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_proposals")
os.makedirs(OUT_DIR, exist_ok=True)

PAGE_WIDTH, PAGE_HEIGHT = 595, 842  # A4-ish
MARGIN = 56


def render_pdf(filename: str, sections: list[tuple[str, str]]) -> None:
    """sections: list of (heading, body_text). Each heading starts a new
    visual block; the layout engine flows text and adds new pages as needed."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = MARGIN

    def new_page():
        nonlocal page, y
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        y = MARGIN

    for heading, body in sections:
        # Heading
        if y > PAGE_HEIGHT - MARGIN - 60:
            new_page()
        page.insert_text((MARGIN, y), heading, fontsize=13, fontname="helv", color=(0.05, 0.05, 0.2))
        y += 22

        # Body: manual wrap at ~95 chars, respecting existing newlines/bullets.
        for raw_line in body.split("\n"):
            raw_line = raw_line.rstrip()
            if raw_line == "":
                y += 10
                continue
            wrapped = _wrap(raw_line, 92)
            for line in wrapped:
                if y > PAGE_HEIGHT - MARGIN:
                    new_page()
                page.insert_text((MARGIN, y), line, fontsize=10.2, fontname="helv", color=(0.15, 0.15, 0.15))
                y += 15
        y += 14

    out_path = os.path.join(OUT_DIR, filename)
    doc.save(out_path)
    doc.close()
    print(f"Wrote {out_path}")


def _wrap(text: str, width: int) -> list[str]:
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        candidate = (current + " " + w).strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


# ---------------------------------------------------------------------------
# Vendor A — strong all-round proposal (should score highest)
# ---------------------------------------------------------------------------
vendor_a_sections = [
    ("Proposal for Customer Support Platform Implementation", "Prepared by: NimbusDesk Technologies Pvt. Ltd.\nDate: March 2026\nContact: sales@nimbusdesk.example"),
    ("1. Executive Summary",
     "NimbusDesk Technologies is pleased to submit this proposal for the implementation of a "
     "cloud-based Customer Support Platform. Our solution combines ticketing, live chat, and "
     "a customer knowledge base into a single unified system, with a proven track record across "
     "120+ mid-market deployments."),
    ("2. Commercial Terms",
     "Total Implementation Cost: INR 8,00,000 (Rupees Eight Lakh only), inclusive of setup, "
     "configuration, data migration, and training.\n"
     "Recurring Cost: INR 45,000 per month for platform licensing and hosting, billed monthly "
     "in advance.\n"
     "Payment Terms: 40% advance on signing, 40% on go-live, 20% after 30 days of stable operation.\n"
     "Pricing Conditions: Pricing is fixed for the first 24 months from go-live and will not "
     "change without 90 days written notice."),
    ("3. Implementation Timeline",
     "Total implementation time: 6 weeks from contract signing to go-live, structured as:\n"
     "- Week 1-2: Requirements workshop and environment setup\n"
     "- Week 3-4: Configuration, data migration, and integration development\n"
     "- Week 5: User acceptance testing\n"
     "- Week 6: Go-live and hypercare support"),
    ("4. Support & SLA",
     "Support Duration: 18 months of included post-launch support from go-live date.\n"
     "SLA: 99.5% uptime guarantee, with a committed 4-hour response time for critical (P1) "
     "issues and 1 business day for standard requests, backed by financial service credits "
     "for missed SLA targets.\n"
     "Warranty: 12-month warranty on all custom-developed integrations."),
    ("5. Features & Technical Capabilities",
     "Features:\n"
     "- Omnichannel ticketing (email, chat, social)\n"
     "- Customer self-service knowledge base\n"
     "- Built-in analytics and reporting dashboards\n"
     "- Role-based access control\n"
     "Technical Capabilities:\n"
     "- REST API integration is fully supported, with a published API reference and sandbox access\n"
     "- Single Sign-On (SAML 2.0 and OAuth 2.0)\n"
     "- Data encryption at rest (AES-256) and in transit (TLS 1.2+)"),
    ("6. Compliance & Security",
     "NimbusDesk Technologies holds a valid ISO 27001:2022 certification (Certificate No. "
     "ND-ISO-2025-114), renewed annually and available on request.\n"
     "We are fully GDPR compliant for all customer data processed on behalf of EU-based end users, "
     "with data processing agreements available on request.\n"
     "Security Information: All customer data is hosted in ISO 27001 certified data centers "
     "with daily encrypted backups and role-based data access controls."),
    ("7. Contract Terms & Exclusions",
     "Contract Terms: Initial contract term of 24 months, with automatic renewal for successive "
     "12-month periods unless either party provides 60 days written notice of non-renewal.\n"
     "Exclusions:\n"
     "- Custom mobile application development is not included in this proposal\n"
     "- Third-party SMS gateway costs are billed separately at actual usage\n"
     "Other Clauses:\n"
     "- Source code for custom integrations will be shared under an escrow arrangement"),
]

# ---------------------------------------------------------------------------
# Vendor B — budget-friendly but fails on timeline/support (should score lower)
# ---------------------------------------------------------------------------
vendor_b_sections = [
    ("Proposal: Customer Support Platform", "Submitted by: QuickServe Solutions\nMarch 2026"),
    ("Overview",
     "QuickServe Solutions offers an affordable customer support solution suitable for growing "
     "businesses. This document outlines our commercial and technical offer."),
    ("Pricing",
     "Total Cost: Rs. 6,50,000 for the full project.\n"
     "Recurring Cost: Rs. 30,000 per month.\n"
     "Note: Additional charges may apply for extra user seats beyond the initial 20 agents, and "
     "pricing is subject to change annually based on our standard rate card.\n"
     "Payment Terms: 50% upfront, 50% on delivery."),
    ("Timeline",
     "Our estimated implementation timeline is 12 weeks, depending on the complexity of your "
     "existing systems and data volume. Delays due to client-side dependencies are common and "
     "may extend this further."),
    ("Support",
     "We provide 3 months of complimentary support after go-live. Extended support plans are "
     "available at an additional cost of Rs. 15,000/month.\n"
     "Our team makes a best effort to respond to support tickets within 2 business days; however, "
     "we do not currently offer a formal SLA with guaranteed response times."),
    ("Features",
     "- Basic ticketing system\n"
     "- Email support channel\n"
     "- Simple reporting dashboard\n"
     "Our platform does not currently support direct REST API integration with external systems; "
     "this is on our product roadmap for a future release."),
    ("Compliance",
     "QuickServe Solutions is currently in the process of applying for ISO 27001 certification, "
     "which we expect to receive within the next 12-18 months. We have not yet completed a "
     "formal GDPR compliance assessment."),
    ("Terms & Conditions",
     "This agreement automatically renews annually unless cancelled in writing 30 days prior to "
     "the renewal date. All payments made under this agreement are non-refundable.\n"
     "Exclusions: Data migration from legacy systems, custom report development, and after-hours "
     "support are not included and will be quoted separately upon request."),
]

# ---------------------------------------------------------------------------
# Vendor C — strong technical fit, but missing several key disclosures
# ---------------------------------------------------------------------------
vendor_c_sections = [
    ("Vendor Proposal — Support Platform Modernization", "Prepared by: Orbitel Systems\nProposal Reference: ORB-2026-0417"),
    ("Introduction",
     "Orbitel Systems specializes in enterprise-grade customer engagement platforms for regulated "
     "industries. We are excited to propose our platform for your customer support modernization "
     "initiative."),
    ("Commercial Proposal",
     "The total cost for this engagement will be finalized after a scoping workshop; a preliminary "
     "estimate is in the range of Rs. 9,00,000 to Rs. 11,00,000 depending on the final feature set "
     "selected during discovery.\n"
     "A recurring platform fee of Rs. 60,000 per month applies once the platform goes live."),
    ("Delivery Approach",
     "Implementation Timeline: 7 weeks from kickoff to production go-live, assuming timely client "
     "sign-off at each milestone gate."),
    ("Support Commitments",
     "Post-launch support is included for 12 months from go-live.\n"
     "SLA: We commit to a Service Level Agreement with 99.9% uptime and priority-based response "
     "times, detailed further in Schedule C of the Master Services Agreement (to be shared during "
     "contracting)."),
    ("Platform Capabilities",
     "Features:\n"
     "- AI-assisted ticket routing and triage\n"
     "- Live chat with co-browsing\n"
     "- Advanced analytics suite with custom dashboards\n"
     "Technical Capabilities:\n"
     "- Full REST and GraphQL API integration supported, with dedicated integration engineering support\n"
     "- Webhooks for real-time event notifications\n"
     "- Multi-region deployment options for data residency"),
    ("Security & Compliance",
     "Orbitel Systems maintains SOC 2 Type II attestation. Additional compliance documentation, "
     "including our current ISO 27001 and GDPR compliance status, will be provided during the "
     "contracting phase upon request from your security team."),
    ("Commercial Conditions",
     "Contract Terms: 36-month initial term. Early termination prior to month 12 will incur an "
     "early termination fee equal to 50% of the remaining contract value.\n"
     "Exclusions: Custom AI model training beyond the standard routing model is out of scope for "
     "this proposal and will be quoted separately."),
]


def main() -> None:
    render_pdf("vendor_a_nimbusdesk.pdf", vendor_a_sections)
    render_pdf("vendor_b_quickserve.pdf", vendor_b_sections)
    render_pdf("vendor_c_orbitel.pdf", vendor_c_sections)


if __name__ == "__main__":
    main()
