"""Page 2 — Create / edit the requirements and scoring configuration."""
from __future__ import annotations

import streamlit as st

from app.business_logic.requirements import RequirementsConfigError, build_requirements_config
from app.ui.styles import page_header
from app.utils.state import get_requirements, set_requirements


def render() -> None:
    page_header("Set the rules for a fair comparison.", "Define the business, financial, technical, and compliance requirements every proposal will be evaluated against.", "ANALYSIS SETUP")
    st.markdown(
        '<div class="app-subtitle">Define the business, financial, technical, and compliance '
        "requirements this project will evaluate vendors against.</div>",
        unsafe_allow_html=True,
    )

    existing = get_requirements()

    with st.form("requirements_form", clear_on_submit=False):
        st.markdown("#### Project")
        project_name = st.text_input(
            "Project name", value=existing.project_name if existing else "", placeholder="e.g. Customer Support Platform"
        )

        st.markdown("#### Financial & Delivery Requirements")
        col1, col2, col3 = st.columns(3)
        with col1:
            max_budget = st.number_input(
                "Maximum budget (₹)", min_value=0.0, step=10000.0,
                value=float(existing.max_budget) if existing and existing.max_budget else 0.0,
                help="Leave at 0 to skip a budget requirement.",
            )
        with col2:
            max_timeline_weeks = st.number_input(
                "Maximum implementation time (weeks)", min_value=0.0, step=1.0,
                value=float(existing.max_timeline_weeks) if existing and existing.max_timeline_weeks else 0.0,
            )
        with col3:
            min_support_months = st.number_input(
                "Minimum support period (months)", min_value=0.0, step=1.0,
                value=float(existing.min_support_months) if existing and existing.min_support_months else 0.0,
            )

        st.markdown("#### Technical & Compliance Requirements")
        col4, col5, col6, col7 = st.columns(4)
        with col4:
            api_required = st.checkbox("API Integration Required", value=existing.api_integration_required if existing else True)
        with col5:
            sla_required = st.checkbox("SLA Required", value=existing.sla_required if existing else True)
        with col6:
            iso_required = st.checkbox("ISO 27001 Required", value=existing.iso27001_required if existing else False)
        with col7:
            gdpr_required = st.checkbox("GDPR Required", value=existing.gdpr_required if existing else False)

        st.markdown("#### Scoring Weights (%)")
        st.caption("Weights are automatically normalized to total 100%.")
        w = existing.scoring_weights if existing else None
        wc1, wc2, wc3, wc4, wc5 = st.columns(5)
        with wc1:
            weight_technical = st.number_input("Technical Fit", 0.0, 100.0, float(w.technical_fit) if w else 30.0, step=5.0)
        with wc2:
            weight_budget = st.number_input("Budget", 0.0, 100.0, float(w.budget) if w else 25.0, step=5.0)
        with wc3:
            weight_delivery = st.number_input("Delivery Timeline", 0.0, 100.0, float(w.delivery_timeline) if w else 20.0, step=5.0)
        with wc4:
            weight_support = st.number_input("Support & SLA", 0.0, 100.0, float(w.support_sla) if w else 15.0, step=5.0)
        with wc5:
            weight_risk = st.number_input("Risk", 0.0, 100.0, float(w.risk) if w else 10.0, step=5.0)

        submitted = st.form_submit_button("Save Requirements", type="primary")

    if submitted:
        if not project_name.strip():
            st.error("Project name is required.")
            return
        try:
            config = build_requirements_config(
                project_name=project_name,
                max_budget=max_budget or None,
                max_timeline_weeks=max_timeline_weeks or None,
                min_support_months=min_support_months or None,
                api_integration_required=api_required,
                sla_required=sla_required,
                iso27001_required=iso_required,
                gdpr_required=gdpr_required,
                weight_technical=weight_technical,
                weight_budget=weight_budget,
                weight_delivery=weight_delivery,
                weight_support=weight_support,
                weight_risk=weight_risk,
            )
        except RequirementsConfigError as exc:
            st.error(str(exc))
            return

        set_requirements(config)
        st.success("Requirements saved. You can now upload vendor proposals.")
        st.session_state["_nav_target"] = "Upload Proposals"
        st.rerun()
