"""Run real Vendorlens extraction against manually verified ground truth.

Comparison rules:
* Numeric fields use their schema-normalised units and match within 0.01.
* Booleans match exactly.
* Vendor names match case-insensitively after whitespace normalisation.
* Text fields (including SLA/frequency) match case-insensitively after
  whitespace normalisation.
* A null expected value means "not specified" and only matches null output.
* A non-null expected value with null output is ``missing_when_present``;
  every other mismatch is ``wrong_value``.

No extraction, scoring, ranking, or recommendation logic is reimplemented:
this script calls the project's existing PDF parser, Groq client, and
``extract_vendor_proposal`` function.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow ``python evaluation/run_extraction_eval.py`` from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.extractor import ExtractionError, extract_vendor_proposal
from app.ai.groq_client import GroqClient, GroqClientError
from app.document_processing.pdf_parser import PDFProcessingError, parse_pdf
from app.utils.config import get_settings

FIELDS = (
    "vendor_name",
    "total_cost",
    "recurring_cost",
    "recurring_cost_frequency",
    "implementation_timeline_weeks",
    "support_duration_months",
    "sla",
    "api_integration_supported",
    "iso27001_certified",
    "gdpr_compliant",
)
NUMERIC_FIELDS = {"total_cost", "recurring_cost", "implementation_timeline_weeks", "support_duration_months"}
BOOLEAN_FIELDS = {"api_integration_supported", "iso27001_certified", "gdpr_compliant"}
NUMERIC_TOLERANCE = 0.01


def _is_todo(value: Any) -> bool:
    return isinstance(value, str) and value.strip().upper() == "TODO"


def _is_not_specified(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip().casefold() in {"", "not specified", "n/a", "na", "null"})


def normalise_text(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def compare_field(field: str, expected: Any, extracted: Any) -> tuple[bool, str]:
    """Return correctness and a reportable error category without API calls."""
    expected_missing = _is_not_specified(expected)
    extracted_missing = _is_not_specified(extracted)
    if expected_missing and extracted_missing:
        return True, ""
    if not expected_missing and extracted_missing:
        return False, "missing_when_present"
    if expected_missing and not extracted_missing:
        return False, "wrong_value"
    if field in NUMERIC_FIELDS:
        try:
            return (abs(float(expected) - float(extracted)) <= NUMERIC_TOLERANCE,
                    "" if abs(float(expected) - float(extracted)) <= NUMERIC_TOLERANCE else "wrong_value")
        except (TypeError, ValueError):
            return False, "wrong_value"
    if field in BOOLEAN_FIELDS:
        return (expected is extracted, "" if expected is extracted else "wrong_value")
    return (normalise_text(expected) == normalise_text(extracted), "" if normalise_text(expected) == normalise_text(extracted) else "wrong_value")


def _entry_is_complete(entry: dict[str, Any]) -> bool:
    return bool(entry.get("filename")) and not any(_is_todo(entry.get(field)) for field in ("filename", *FIELDS))


def _serialise(value: Any) -> str:
    return "not specified" if value is None else str(value)


def evaluate_entries(entries: list[dict[str, Any]], proposals_dir: Path, client: GroqClient | None) -> tuple[list[dict[str, str]], list[str], int]:
    """Extract every completely labelled proposal and return CSV-ready rows."""
    rows: list[dict[str, str]] = []
    skipped: list[str] = []
    evaluated = 0
    for entry in entries:
        filename = str(entry.get("filename", ""))
        if not _entry_is_complete(entry):
            skipped.append(filename or "<missing filename>")
            continue
        path = proposals_dir / filename
        if not path.is_file():
            skipped.append(f"{filename} (file not found)")
            continue
        if client is None:  # Guarded by main; retained for direct function callers.
            raise RuntimeError("A Groq client is required when at least one labelled proposal is evaluated.")
        try:
            parsed = parse_pdf(path.read_bytes(), filename)
            proposal = extract_vendor_proposal(client, parsed.full_text, filename_hint=filename)
        except (PDFProcessingError, ExtractionError, GroqClientError) as exc:
            for field in FIELDS:
                rows.append({"proposal": filename, "field": field, "expected": _serialise(entry.get(field)), "extracted": "", "correct": "no", "error_type": f"extraction_error: {exc}"})
            evaluated += 1
            continue
        evaluated += 1
        for field in FIELDS:
            expected = entry.get(field)
            extracted = getattr(proposal, field)
            correct, error_type = compare_field(field, expected, extracted)
            rows.append({"proposal": filename, "field": field, "expected": _serialise(expected), "extracted": _serialise(extracted), "correct": "yes" if correct else "no", "error_type": error_type})
    return rows, skipped, evaluated


def write_results(rows: list[dict[str, str]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["proposal", "field", "expected", "extracted", "correct", "error_type"])
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: list[dict[str, str]], skipped: list[str], evaluated: int, settings) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Vendorlens extraction evaluation summary", "",
        f"- Generated at (UTC): `{now}`",
        f"- GROQ_MODEL: `{settings.groq_model}`",
        f"- MAX_EXTRACTION_CHARS: `{settings.max_extraction_chars}`",
        f"- Labelled proposals evaluated: **{evaluated}**",
        f"- Entries skipped (missing `TODO` labels or PDF): **{len(skipped)}**",
    ]
    if skipped:
        lines.extend(["", "## Skipped entries", *[f"- `{item}`" for item in skipped]])
    if evaluated < 1:
        lines.extend(["", "## Accuracy", "No accuracy is reported because fewer than one completely labelled proposal was evaluated."])
        return "\n".join(lines) + "\n"

    lines.extend(["", "## Accuracy by field", "", "| Field | Correct / total | Accuracy |", "|---|---:|---:|"])
    all_correct = sum(row["correct"] == "yes" for row in rows)
    for field in FIELDS:
        field_rows = [row for row in rows if row["field"] == field]
        correct = sum(row["correct"] == "yes" for row in field_rows)
        total = len(field_rows)
        lines.append(f"| {field} | {correct} / {total} | {(100 * correct / total):.2f}% |")
    lines.extend(["", f"**Overall accuracy:** {all_correct} / {len(rows)} ({(100 * all_correct / len(rows)):.2f}%)", "", "## Errors"])
    errors = [row for row in rows if row["correct"] != "yes"]
    if not errors:
        lines.append("No extraction errors recorded for the evaluated ground-truth entries.")
    else:
        for row in errors:
            lines.append(f"- `{row['proposal']}` / `{row['field']}` — {row['error_type']}; expected: `{row['expected']}`; extracted: `{row['extracted']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate real Vendorlens extraction against hand-checked labels.")
    parser.add_argument("--ground-truth", type=Path, default=Path("evaluation/ground_truth.json"))
    parser.add_argument("--proposals-dir", type=Path, default=Path("evaluation/proposals"))
    parser.add_argument("--results", type=Path, default=Path("evaluation/results.csv"))
    parser.add_argument("--summary", type=Path, default=Path("evaluation/summary.md"))
    args = parser.parse_args()
    try:
        entries = json.loads(args.ground_truth.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Ground-truth file was not found: {args.ground_truth}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Ground-truth JSON is invalid: {exc}")
    if not isinstance(entries, list):
        raise SystemExit("Ground truth must be a JSON array with one object per proposal PDF.")
    settings = get_settings()
    has_complete_entry = any(_entry_is_complete(entry) for entry in entries)
    if has_complete_entry and not settings.is_groq_configured():
        raise SystemExit("GROQ_API_KEY and GROQ_MODEL are required for extraction evaluation. Add them to .env and try again.")
    rows, skipped, evaluated = evaluate_entries(
        entries, args.proposals_dir, GroqClient(settings) if has_complete_entry else None
    )
    write_results(rows, args.results)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(build_summary(rows, skipped, evaluated, settings), encoding="utf-8")
    print(f"Wrote {args.results} and {args.summary}. Evaluated {evaluated} labelled proposal(s); skipped {len(skipped)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
