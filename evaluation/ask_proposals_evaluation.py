"""Dependency-free metrics for manually verified Ask the Proposals evaluations.

Usage: python evaluation/ask_proposals_evaluation.py evaluation/ground_truth.json
The script reports only metrics derived from labelled records; it never
generates expected answers or fabricated percentages.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def precision_recall_f1(expected: set[str], actual: set[str]) -> dict[str, float]:
    tp = len(expected & actual)
    precision = tp / len(actual) if actual else 0.0
    recall = tp / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def reciprocal_rank(expected: set[str], retrieved: list[str]) -> float:
    for index, value in enumerate(retrieved, start=1):
        if value in expected:
            return 1 / index
    return 0.0


def evaluate(records: list[dict]) -> dict:
    """Evaluate labelled tool choices, citations, and retrieval IDs."""
    tool_scores, evidence_scores, reciprocal_ranks = [], [], []
    for record in records:
        if "expected_tools" in record and "actual_tools" in record:
            tool_scores.append(precision_recall_f1(set(record["expected_tools"]), set(record["actual_tools"])))
        if "expected_evidence_ids" in record and "actual_evidence_ids" in record:
            expected = set(record["expected_evidence_ids"])
            evidence_scores.append(precision_recall_f1(expected, set(record["actual_evidence_ids"])))
            reciprocal_ranks.append(reciprocal_rank(expected, record["actual_evidence_ids"]))
    def average(items, key):
        return sum(item[key] for item in items) / len(items) if items else None
    return {
        "labelled_queries": len(records),
        "tool_selection": {key: average(tool_scores, key) for key in ("precision", "recall", "f1")},
        "retrieval_evidence": {key: average(evidence_scores, key) for key in ("precision", "recall", "f1")},
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else None,
        "note": "Null metrics mean the input records did not contain the corresponding manually verified labels.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: python evaluation/ask_proposals_evaluation.py evaluation/ground_truth.json")
        if len(sys.argv) == 2:
            raise SystemExit(0)
        raise SystemExit("Usage: python evaluation/ask_proposals_evaluation.py evaluation/ground_truth.json")
    records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(evaluate(records), indent=2))
