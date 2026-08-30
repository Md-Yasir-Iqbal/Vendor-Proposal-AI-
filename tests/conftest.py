import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from app.schemas.requirements import RequirementsConfig


@pytest.fixture
def sample_requirements() -> RequirementsConfig:
    return RequirementsConfig(
        project_name="Customer Support Platform",
        max_budget=1_000_000,
        max_timeline_weeks=8,
        min_support_months=12,
        api_integration_required=True,
        sla_required=True,
        iso27001_required=True,
        gdpr_required=True,
    )
