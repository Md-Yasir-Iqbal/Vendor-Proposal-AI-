# Vendorlens

An AI-assisted, evidence-grounded system that helps procurement teams compare multiple
vendor proposals against a shared set of requirements — turning unstructured PDF proposals
into a transparent, explainable, side-by-side evaluation.

> **Positioning:** This is an **AI-assisted decision-support tool**, not a trained ML
> prediction model, not an autonomous procurement decision-maker, and not a legal
> compliance system. Every score is computed deterministically in Python. The LLM (via
> Groq) is used only for reading unstructured text, extracting structured fields, spotting
> ambiguous language, and writing plain-language explanations. **Final procurement
> decisions remain with the human user.**

---

## Problem Statement

Organizations evaluating multiple vendor proposals for the same project face proposals that
differ wildly in format, structure, and terminology — pricing, SLAs, certifications, contract
terms, exclusions, and technical capabilities are scattered throughout dense PDFs. Manually
reading and comparing these documents is slow and error-prone, and it's easy to miss:

- Requirement mismatches (budget overruns, missed deadlines, missing certifications)
- Hidden or additional costs and price-escalation clauses
- Unfavorable or ambiguous contract/SLA language
- Missing information that the proposal simply never addresses

## Solution

This system provides a structured, repeatable workflow:

1. Define requirements (budget, timeline, support, compliance) and scoring weights.
2. Upload vendor proposal PDFs.
3. The system extracts text, cleans it, and chunks it with page/section metadata.
4. An LLM (Groq) extracts structured vendor data into a validated schema — never inventing
   values it can't find.
5. Python deterministically matches each vendor against your requirements, detects risks,
   and computes a transparent weighted score.
6. Proposal chunks are embedded and stored in a vector database (Chroma) so every risk and
   recommendation can be traced back to real source text.
7. An LLM writes a plain-language recommendation explanation — grounded in the
   already-computed scores, requirement results, and retrieved evidence, never deciding the
   winner itself.
8. Everything is presented in a clean, professional Streamlit dashboard.

## Key Features

- **Configurable requirements** — budget, timeline, support period, API/SLA/ISO 27001/GDPR
  flags, custom requirements, and adjustable scoring weights (auto-normalized to 100%).
- **Robust PDF processing** — PyMuPDF-based extraction with page-aware, section-aware,
  contextual chunking; graceful handling of corrupt, empty, or scanned/image-only PDFs.
- **Structured LLM extraction** — a strict JSON schema, Pydantic validation, and automatic
  one-shot repair if the model returns malformed JSON or invalid types.
- **Deterministic matching, scoring, and ranking** — every PASS/FAIL/NOT SPECIFIED/REQUIRES
  REVIEW decision and every point of the vendor score is computed in plain Python, not by
  the LLM.
- **Two-layer risk detection** — fast deterministic rule checks (missing certifications,
  vague SLA language, price-escalation keywords, exclusions, etc.) plus an optional
  AI-assisted layer that flags ambiguous proposal language, grounded in a verified quote from
  the source text.
- **RAG-based evidence retrieval** — proposal chunks are embedded and stored in Chroma so
  every risk/recommendation can cite a vendor, document, page number, and section.
- **Resilient by design** — if the Groq API is unavailable, misconfigured, or rate-limited,
  the app still parses documents, runs deterministic matching/scoring, and produces a
  template-based fallback recommendation rather than crashing.
- **Professional Streamlit dashboard** — 7 pages covering the entire workflow from project
  setup to final, evidence-backed recommendation.

## Architecture

```
                    Multiple Vendor PDFs
                             |
                             v
                   PDF Text Extraction (PyMuPDF)
                             |
                             v
                    Text Cleaning
                             |
                             v
                Contextual Document Chunking (page + section aware)
                             |
                ------------------------------
                |                            |
                v                            v
      Structured LLM Extraction        Embeddings (Chroma)
      (Groq, JSON, validated)                |
                |                            v
                v                       Chroma Vector Store
      Pydantic Validation                    |
                |                            |
                ------------------------------
                             |
                             v
                  Requirement Matching (Python, deterministic)
                             |
                             v
               Risk Detection (rule-based + AI-assisted, grounded)
                             |
                             v
                    Vendor Scoring (Python, weighted, deterministic)
                             |
                             v
                    Vendor Ranking
                             |
                             v
                   Evidence Retrieval (RAG, per-vendor topics)
                             |
                             v
                 AI-Assisted Recommendation Explanation
                 (vendor selection is deterministic; only the
                  narrative is AI-generated, with a safe fallback)
                             |
                             v
                   Streamlit Dashboard (7 pages)
```

## Running the application

Run the Streamlit application from the project root:

```bash
streamlit run app.py
```

### AI Workflow

The LLM (Groq) is used for exactly four things, each isolated behind its own module:

| Task | Module | LLM decides? |
|---|---|---|
| Structured field extraction from proposal text | `app/ai/extractor.py` | Extracts facts only; never invents values |
| Ambiguous/vague language detection | `app/ai/risk_analyzer.py` | Flags risks; every quote is verified against the source text or discarded |
| Recommendation narrative | `app/ai/recommender.py` | Writes the explanation only — **the recommended vendor is chosen by Python**, not the LLM |
| — | `app/business_logic/*` | All matching, scoring, and ranking is 100% deterministic Python |

If `GROQ_API_KEY`/`GROQ_MODEL` are not configured, or a Groq call fails, the app degrades
gracefully: PDF parsing, chunking, retrieval, deterministic matching, risk rules, and scoring
all continue to work, and the recommendation page falls back to a template-based summary
built entirely from the computed data.

## Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM inference | Groq API (OpenAI-compatible chat completions, JSON mode) |
| PDF processing | PyMuPDF |
| Validation | Pydantic v2 |
| Vector retrieval | Chroma (persistent, local) |
| Embeddings | Chroma's bundled ONNX MiniLM (`DefaultEmbeddingFunction`), with an offline hash-based fallback |
| Testing | pytest, pytest-mock |
| Language | Python 3.11+ |

No relational database, no Docker, no separate backend server — this is intentionally a
single Streamlit process backed by session state and a local Chroma store, sized for a
36-hour hackathon build while remaining clean enough for a capstone portfolio.

## Project Structure

```
vendor-proposal-ai/
│
├── app.py                          # Streamlit entry point / navigation
├── app/
│   ├── pipeline.py                 # Orchestrates parse -> chunk -> extract -> analyze
│   ├── ui/
│   │   ├── home.py                 # Page 1 — Home / Dashboard
│   │   ├── create_analysis.py      # Page 2 — Create Analysis
│   │   ├── upload.py               # Page 3 — Upload Proposals
│   │   ├── dashboard.py            # Page 4 — Analysis Dashboard
│   │   ├── comparison.py           # Page 5 — Vendor Comparison
│   │   ├── vendor_details.py       # Page 6 — Vendor Details
│   │   ├── recommendation.py       # Page 7 — Evidence / Recommendation
│   │   └── styles.py               # Shared CSS + small render helpers
│   ├── ai/
│   │   ├── groq_client.py          # Isolated Groq wrapper + error hierarchy
│   │   ├── prompts.py              # All prompt templates
│   │   ├── extractor.py            # Structured extraction + repair logic
│   │   ├── risk_analyzer.py        # AI-assisted, evidence-grounded risk detection
│   │   └── recommender.py          # Recommendation narrative + deterministic fallback
│   ├── document_processing/
│   │   ├── pdf_parser.py           # PyMuPDF extraction + error handling
│   │   ├── cleaner.py              # Whitespace/hyphenation/header cleanup
│   │   └── chunker.py              # Page- and section-aware contextual chunking
│   ├── retrieval/
│   │   ├── embeddings.py           # MiniLM embeddings with hash-based offline fallback
│   │   ├── chroma_store.py         # Chroma wrapper (insert / query / metadata)
│   │   └── retriever.py            # Topic-based evidence retrieval helpers
│   ├── business_logic/
│   │   ├── requirements.py         # Build/validate RequirementsConfig
│   │   ├── matching.py             # Deterministic PASS/FAIL/NOT SPECIFIED/REQUIRES REVIEW
│   │   ├── scoring.py              # Deterministic weighted scoring + ranking
│   │   ├── risk_rules.py           # Deterministic rule-based risk detection
│   │   └── recommendation.py       # Deterministic recommended-vendor selection
│   ├── schemas/
│   │   ├── vendor.py                # VendorProposal, VendorDocumentMeta
│   │   ├── requirements.py          # RequirementsConfig, ScoringWeights
│   │   ├── analysis.py              # RequirementResult, RiskItem, ScoreBreakdown, etc.
│   │   └── evidence.py              # DocumentChunk, EvidenceSnippet
│   └── utils/
│       ├── config.py                 # Environment-variable settings
│       ├── logging.py                # Logging setup
│       ├── helpers.py                # Formatting / misc helpers
│       └── state.py                  # Centralized Streamlit session-state management
│
├── scripts/
│   └── generate_sample_proposals.py  # Generates the 3 synthetic sample PDFs
├── data/
│   ├── sample_proposals/             # Synthetic Vendor A/B/C proposal PDFs
│   └── chroma/                       # Local persistent Chroma store (created at runtime)
├── tests/                            # 49 tests across 8 files (see below)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 or newer
- A free [Groq API key](https://console.groq.com) (optional but recommended — the app runs
  without one, with reduced functionality; see "Known Limitations")

## Installation

```bash
# 1. Clone / unzip the project, then from the project root:
python -m venv .venv

# 2. Activate the virtual environment
# macOS / Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Environment Setup

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=your_supported_model
```

### Groq API Setup

1. Create a free account at [console.groq.com](https://console.groq.com).
2. Generate an API key and paste it into `GROQ_API_KEY` in `.env`.
3. Set `GROQ_MODEL` to any current Groq-hosted instruction/chat model available to your
   account (for example, a current Llama 3.x instruct model served by Groq). Check
   [Groq's model list](https://console.groq.com/docs/models) for what's currently supported —
   this project deliberately reads the model name from the environment instead of
   hard-coding one, since Groq's supported models change over time.

### Embedding Setup

No separate setup is required. On first use, the retrieval layer tries to load Chroma's
bundled `DefaultEmbeddingFunction` (a small ONNX MiniLM model), which downloads its weights
automatically the first time it runs (requires an internet connection once; cached locally
afterward). If that model can't be loaded (e.g., a fully offline environment), the app
automatically falls back to a lightweight, dependency-free hashing-based embedding so
retrieval keeps working end-to-end, with a logged notice that semantic search quality is
reduced in that mode.

## Running the Application

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## Running Tests

```bash
pytest tests/ -v
```

All 49 tests run fully offline:

- **No test calls the live Groq API** — `app/ai/groq_client.GroqClient` is subclassed/mocked
  in `tests/test_extractor.py` with canned responses.
- **No test downloads an embedding model** — retrieval tests (`tests/test_retrieval.py`) force
  the dependency-free hash-based embedding fallback via `EmbeddingProvider(force_hash_fallback=True)`
  and use Chroma's in-memory `EphemeralClient`.

| File | Covers |
|---|---|
| `test_pdf_parser.py` | Valid PDF, corrupted PDF, zero-byte file, scanned/image-only PDF |
| `test_chunker.py` | Max chunk size, page alignment, section-heading tagging, empty pages |
| `test_schemas.py` | Valid extraction data, missing fields, malformed numeric fields, weight normalization |
| `test_extractor.py` | Valid extraction, malformed JSON, markdown-fenced JSON, repair round-trip, vendor-name fallback |
| `test_matching.py` | PASS / FAIL / NOT SPECIFIED / REQUIRES REVIEW for every requirement type |
| `test_scoring.py` | Weighted score bounds, ranking order, weight sensitivity, missing-data penalties |
| `test_risk_rules.py` | Missing info, recurring cost, unfavorable pricing/contract language, certification gaps |
| `test_retrieval.py` | Insertion, count, query relevance, vendor filtering, metadata preservation, empty store |

## Sample Workflow (Demo Script)

Three synthetic sample proposals are included in `data/sample_proposals/` (regenerate any
time with `python scripts/generate_sample_proposals.py`):

- **Vendor A (NimbusDesk)** — strong all-round proposal: within budget, fast timeline, long
  support period, clear SLA, both certifications confirmed. Expected to score highest and
  pass every mandatory requirement.
- **Vendor B (QuickServe)** — cheaper, but fails the timeline and support requirements, has
  no confirmed API integration, and uses vague/unfavorable pricing and contract language.
  Expected to fail multiple mandatory requirements.
- **Vendor C (Orbitel)** — strong technical fit, but leaves total cost as a range (not a firm
  number) and defers ISO 27001/GDPR confirmation, resulting in "Not Specified" results and a
  middle-of-the-pack score.

**To demo end-to-end:**

1. Run `streamlit run app.py`.
2. Go to **Create Analysis** and set: Project = "Customer Support Platform", Max Budget =
   1000000, Max Timeline = 8 weeks, Min Support = 12 months, and check API Integration, SLA,
   ISO 27001, and GDPR as required. Save.
3. Go to **Upload Proposals** and upload all three PDFs from `data/sample_proposals/`.
4. Watch the per-file processing status (parsed, chunked, extracted).
5. Open **Analysis Dashboard** to see the ranking and requirement summary.
6. Open **Vendor Comparison** for the side-by-side PASS/FAIL matrix and score breakdown.
7. Open **Vendor Details** to inspect any vendor's full extracted data, risks, and score
   components.
8. Open **Recommendation**, click **Generate / Refresh Recommendation**, and review the
   evidence-backed explanation (Vendor A should be recommended).

## How Requirement Matching Works

Every requirement produces exactly one of four statuses, decided by plain Python
comparisons against the validated, extracted vendor data — never by the LLM:

- **PASS** — e.g. `vendor_cost <= max_budget`
- **FAIL** — e.g. `vendor_timeline > max_timeline_weeks`
- **NOT SPECIFIED** — the field was never found in the proposal (never guessed or inferred)
- **REQUIRES REVIEW** — e.g. an SLA is present but contains hedging language like "best
  effort" or "no guarantee"

See `app/business_logic/matching.py`.

## How Vendor Scoring Works

Each vendor gets five 0–100 sub-scores, each computed with plain arithmetic:

| Sub-score | How it's computed |
|---|---|
| Technical Fit | Average of API-integration/compliance requirement outcomes (PASS=100, REQUIRES REVIEW=60, NOT SPECIFIED=30, FAIL=0) |
| Budget | 90–100 if comfortably under budget, sliding down to 0 the further over budget the cost is; 30 if unspecified |
| Delivery Timeline | Same shape as Budget, applied to implementation weeks |
| Support & SLA | Blend of support-duration-vs-minimum ratio and the SLA requirement outcome |
| Risk | `100 - sum(risk severity penalties)`, floored at 0 (Info = -3, Requires Review = -8, Potential Risk = -15) |

The **total score** is the weighted sum of these five sub-scores, using the
user-configured (auto-normalized-to-100%) weights:

```
total = (technical_fit * w_tech + budget * w_budget + delivery * w_delivery
         + support * w_support + risk * w_risk) / 100
```

This is a transparent, rule-based decision-support score — explicitly **not** a prediction,
probability, or machine-learning output. See `app/business_logic/scoring.py`.

## How Risk Detection Works

Two independent layers, both surfaced together in the UI with a clear source tag:

1. **Rule-based** (`app/business_logic/risk_rules.py`) — deterministic Python checks:
   missing pricing, recurring costs, price-escalation/unfavorable-term keyword scans,
   timelines/support periods that miss requirements, missing certifications, and ambiguous
   SLA wording.
2. **AI-assisted** (`app/ai/risk_analyzer.py`) — the LLM reviews a vendor's proposal excerpts
   for ambiguous or vague language beyond fixed keyword lists. Every AI-identified risk must
   include a short quote that is checked against the actual source text; if the quote can't
   be verified in the source, the risk is silently dropped rather than trusted.

Severities are always one of `Info`, `Requires Review`, or `Potential Risk` — the system
never makes legal claims or calls anything illegal.

## How RAG / Evidence Retrieval Works

1. Every uploaded PDF is parsed, cleaned, and split into page- and section-aware chunks
   (`app/document_processing/chunker.py`).
2. Chunks are embedded and stored in a per-project Chroma collection, tagged with vendor,
   document, page number, and section (`app/retrieval/chroma_store.py`).
3. When building a recommendation, the system queries Chroma for the recommended vendor
   across a fixed set of topics (pricing, recurring costs, timeline, support/SLA,
   certifications, contract terms) and attaches the top matches as `EvidenceSnippet` objects
   with vendor, document, page number, and source text (`app/retrieval/retriever.py`).
4. Evidence is never fabricated: if nothing relevant is retrieved, the UI says so rather than
   inventing a citation.

## Known Limitations

- **No OCR.** Scanned/image-only PDFs are detected and flagged, but their text is not
  extracted. This is called out explicitly in the UI and in document processing warnings.
- **Very large documents are truncated for extraction.** To keep a single LLM extraction call
  fast and affordable, only the first ~65% and last ~35% of a very long document (configurable
  via `MAX_EXTRACTION_CHARS`) are sent to the model for structured extraction. Full-document
  coverage for evidence/citations is still provided separately through chunk-based retrieval,
  independent of this truncation.
- **Vendor-name detection before LLM extraction is heuristic.** A lightweight regex-based
  guess is shown immediately during upload; the LLM-extracted name (once available) is treated
  as authoritative.
- **Custom requirements use keyword presence, not deep semantic matching.** A custom
  requirement is marked "Requires Review" (not an automatic PASS) if its name is found in the
  vendor's free-text fields, since presence of a keyword doesn't confirm it's actually met.
- **No persistent multi-user database.** State lives in the Streamlit session (by design, per
  the hackathon scope) plus the local Chroma store; closing the browser tab clears the
  in-session analysis (re-upload to rebuild it, or wire in file-based project export as a
  future improvement).
- **Embeddings quality depends on internet access.** The primary embedding model downloads
  ~90MB of ONNX weights on first use. In fully offline environments, the app automatically
  falls back to a lower-quality hashing-based embedding rather than failing.
- **This is decision support, not a legal or compliance authority.** Risk descriptions
  deliberately avoid legal conclusions ("illegal", "invalid") and instead flag items as
  needing human review.

## Future Improvements

- OCR support for scanned proposals (e.g., via a dedicated OCR pass before chunking).
- Persistent, file-based project save/load so an analysis can be reopened across sessions
  without re-uploading PDFs.
- Multi-document-per-vendor support (e.g., a proposal plus a separate pricing sheet).
- Configurable custom requirement types beyond keyword presence (e.g., numeric custom
  requirements with their own comparison operators).
- Export the comparison/recommendation to a shareable PDF or Word report.
- Side-by-side diffing of contract clauses across vendors.

---

**Disclaimer:** This tool provides AI-assisted analysis to support human decision-making in
procurement. It does not replace legal, financial, or compliance review. Always verify
extracted figures and contract terms against the original vendor documents before making a
final decision.
