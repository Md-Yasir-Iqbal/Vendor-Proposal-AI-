# Evaluation harnesses

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

## LLM extraction evaluation

1. Place the PDFs you want to evaluate in `evaluation/proposals/`.
2. Open `evaluation/ground_truth.json`. Add one object per PDF and replace every `TODO` with your hand-checked value. Use JSON `null` only when the proposal genuinely does not specify that field.
3. Run the real extraction pipeline:

```powershell
.\.venv\Scripts\python.exe evaluation\run_extraction_eval.py
```

The evaluator calls the project's existing PyMuPDF parser and `extract_vendor_proposal` function. It requires `GROQ_API_KEY` and `GROQ_MODEL` in `.env`; it does not use mock data or change analysis/scoring logic.

It writes:

- `evaluation/results.csv` — one row per proposal and evaluated field, with expected value, extracted value, correctness, and error type.
- `evaluation/summary.md` — model name, date, extraction limit, skipped entries, per-field and overall accuracy, and every recorded error.

Entries containing `TODO` are skipped. If no fully labelled proposal is available, the summary explicitly reports that accuracy was not calculated.
