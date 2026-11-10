# Ask the Proposals evaluation

This folder provides a reproducible, dependency-free metric calculator. It deliberately contains no invented benchmark results.

Create `ground_truth.json` as a JSON array after manually reviewing realistic proposal questions. Each record can contain:

```json
{
  "question": "Which vendor has the lowest comparable three-year cost?",
  "expected_tools": ["calculate_total_cost", "search_evidence"],
  "actual_tools": ["calculate_total_cost", "search_evidence"],
  "expected_evidence_ids": ["vendor_a.pdf:p2"],
  "actual_evidence_ids": ["vendor_a.pdf:p2", "vendor_b.pdf:p3"],
  "faithful": true,
  "answer_relevant": true,
  "unsupported_claim": false
}
```

Run:

```powershell
.\.venv\Scripts\python.exe evaluation\ask_proposals_evaluation.py evaluation\ground_truth.json
```

The script calculates tool-selection precision/recall/F1, evidence precision/recall/F1, and MRR from labels. Faithfulness, answer relevance, unsupported-answer rate, extraction accuracy, requirement-matching confusion matrices, and financial-calculation agreement need a manually verified dataset before they can be reported honestly.
