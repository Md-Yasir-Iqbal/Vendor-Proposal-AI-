# Vendorlens extraction evaluation summary

- Generated at (UTC): `2026-11-11T21:24:55.015355+00:00`
- GROQ_MODEL: `openai/gpt-oss-120b`
- MAX_EXTRACTION_CHARS: `16000`
- Labelled proposals evaluated: **5**
- Entries skipped (missing `TODO` labels or PDF): **0**

## Accuracy by field

| Field | Correct / total | Accuracy |
|---|---:|---:|
| vendor_name | 5 / 5 | 100.00% |
| total_cost | 5 / 5 | 100.00% |
| recurring_cost | 2 / 5 | 40.00% |
| recurring_cost_frequency | 5 / 5 | 100.00% |
| implementation_timeline_weeks | 4 / 5 | 80.00% |
| support_duration_months | 5 / 5 | 100.00% |
| sla | 4 / 5 | 80.00% |
| api_integration_supported | 5 / 5 | 100.00% |
| iso27001_certified | 5 / 5 | 100.00% |
| gdpr_compliant | 5 / 5 | 100.00% |

**Overall accuracy:** 45 / 50 (90.00%)

## Errors
- `Vendor 1.pdf` / `recurring_cost` — wrong_value; expected: `not specified`; extracted: `580000.0`
- `Vendor 2.pdf` / `implementation_timeline_weeks` — missing_when_present; expected: `5`; extracted: `not specified`
- `Vendor 3.pdf` / `recurring_cost` — wrong_value; expected: `not specified`; extracted: `420000.0`
- `Vendor 4.pdf` / `recurring_cost` — wrong_value; expected: `120000`; extracted: `550000.0`
- `Vendor 4.pdf` / `sla` — wrong_value; expected: `99.9% guaranteed monthly availability.`; extracted: `99.9% guaranteed monthly availability; 30 minute critical incident response`
