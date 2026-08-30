"""Page 6 — Full detail view for a single vendor."""
from __future__ import annotations

import streamlit as st

from app.ui.styles import severity_class, status_badge
from app.utils.helpers import NOT_SPECIFIED, format_currency, truncate_text
from app.utils.state import get_requirements, get_vendor_results


def _display(value, formatter=None):
    if value is None or value == [] or value == "":
        return NOT_SPECIFIED
    return formatter(value) if formatter else value


def render() -> None:
    st.markdown("# Vendor Details")

    results = get_vendor_results()
    requirements = get_requirements()
    if not results:
        st.info("No vendors analyzed yet.")
        return

    vendor_names = sorted(results.keys())
    selected = st.selectbox("Select a vendor", vendor_names)
    result = results[selected]
    p = result.proposal
    currency = requirements.currency_symbol if requirements else "\u20b9"

    if result.extraction_failed:
        st.error(f"This vendor's document could not be processed: {result.extraction_error}")
        return

    st.markdown(f"### {selected}")
    st.markdown(f"**Overall Score:** {result.score.total_score} / 100")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Total Cost**")
        st.write(_display(p.total_cost, lambda v: format_currency(v, currency)))
        st.markdown("**Recurring Cost**")
        freq = f" / {p.recurring_cost_frequency}" if p.recurring_cost_frequency else ""
        st.write(_display(p.recurring_cost, lambda v: format_currency(v, currency) + freq))
    with col2:
        st.markdown("**Implementation Timeline**")
        st.write(_display(p.implementation_timeline_weeks, lambda v: f"{v:g} weeks") if p.implementation_timeline_weeks else (p.implementation_timeline_raw or NOT_SPECIFIED))
        st.markdown("**Support Duration**")
        st.write(_display(p.support_duration_months, lambda v: f"{v:g} months"))
    with col3:
        st.markdown("**SLA**")
        st.write(_display(p.sla, lambda v: truncate_text(v, 160)))
        st.markdown("**Warranty**")
        st.write(_display(p.warranty))

    st.markdown("#### Features & Technical Capabilities")
    fc1, fc2 = st.columns(2)
    with fc1:
        st.markdown("**Features**")
        st.write("\n".join(f"- {f}" for f in p.features) if p.features else NOT_SPECIFIED)
    with fc2:
        st.markdown("**Technical Capabilities**")
        st.write("\n".join(f"- {f}" for f in p.technical_capabilities) if p.technical_capabilities else NOT_SPECIFIED)

    st.markdown("#### Compliance & Security")
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown("**Certifications**")
    cc1.write(", ".join(p.certifications) if p.certifications else NOT_SPECIFIED)
    cc2.markdown("**ISO 27001**")
    cc2.write({True: "Yes", False: "No", None: NOT_SPECIFIED}[p.iso27001_certified])
    cc3.markdown("**GDPR Compliant**")
    cc3.write({True: "Yes", False: "No", None: NOT_SPECIFIED}[p.gdpr_compliant])
    st.markdown("**Security Information**")
    st.write(_display(p.security_information, lambda v: truncate_text(v, 300)))

    st.markdown("#### Contract & Commercial Terms")
    st.markdown("**Payment Terms**")
    st.write(_display(p.payment_terms))
    st.markdown("**Pricing Conditions**")
    st.write(_display(p.pricing_conditions))
    st.markdown("**Contract Terms**")
    st.write(_display(p.contract_terms, lambda v: truncate_text(v, 300)))
    st.markdown("**Exclusions**")
    st.write("\n".join(f"- {e}" for e in p.exclusions) if p.exclusions else NOT_SPECIFIED)

    st.markdown("#### Requirement Results")
    for r in result.requirement_results:
        cols = st.columns([2.5, 1, 2, 3])
        cols[0].markdown(f"**{r.label}**")
        cols[1].markdown(status_badge(r.status.value), unsafe_allow_html=True)
        cols[2].markdown(f"Required: {r.requirement_value}  \nVendor: {r.vendor_value}")
        cols[3].caption(r.explanation)

    st.markdown("#### Score Breakdown")
    st.dataframe(result.score.as_rows(), width="stretch", hide_index=True)

    st.markdown("#### Risks & Missing Information")
    if not result.risks:
        st.caption("No risks flagged for this vendor.")
    for risk in result.risks:
        css = severity_class(risk.severity.value)
        source_tag = "AI-identified" if risk.source == "ai_identified" else "Rule-based"
        st.markdown(
            f"""<div class="risk-card {css}">
                <b>{risk.category}</b> · <span style="font-size:0.78rem;color:#6b7280;">{risk.severity.value} · {source_tag}</span><br/>
                {risk.description}
            </div>""",
            unsafe_allow_html=True,
        )
        if risk.evidence:
            st.caption(f'Evidence (page {risk.evidence.page_number or "?"}): "{risk.evidence.source_text[:200]}"')

    if result.missing_information:
        st.markdown("**Missing Information**")
        for m in result.missing_information:
            st.markdown(f"- {m}")
