from __future__ import annotations

from evaluation.run_extraction_eval import compare_field, normalise_text


def test_vendor_name_comparison_is_case_and_whitespace_insensitive():
    assert normalise_text("  Nexora   Solutions ") == normalise_text("nexora solutions")
    assert compare_field("vendor_name", "Nexora Solutions", "  nexora  solutions ") == (True, "")


def test_numeric_comparison_uses_small_tolerance_and_separates_missing_errors():
    assert compare_field("total_cost", 1500000, 1500000.005) == (True, "")
    assert compare_field("total_cost", 1500000, None) == (False, "missing_when_present")
    assert compare_field("total_cost", None, 1500000) == (False, "wrong_value")


def test_boolean_and_not_specified_comparisons_are_exact():
    assert compare_field("api_integration_supported", True, True) == (True, "")
    assert compare_field("api_integration_supported", True, False) == (False, "wrong_value")
    assert compare_field("sla", None, None) == (True, "")
    assert compare_field("sla", None, "99.9% uptime") == (False, "wrong_value")
    assert compare_field("sla", "not specified", None) == (True, "")
