# Vendorlens

### AI-assisted, evidence-grounded vendor proposal evaluation for procurement teams.

Vendorlens turns messy vendor proposal PDFs into a structured, auditable comparison workspace. It extracts proposal facts, validates them, evaluates every vendor against the same requirements, surfaces risks, and connects recommendations back to the original source text.

**Upload proposals → Define requirements → Compare vendors → Inspect risks → Trace evidence → Make a decision**

> The LLM helps understand documents and explain results. Deterministic Python logic selects the recommended vendor. Final procurement decisions always remain with people.

## Demo

> Run the application locally to explore the full workflow. No screenshots are currently included in this repository.

The repository includes three synthetic PDFs in [`data/sample_proposals/`](data/sample_proposals/) for a quick judge-ready demo.

## The Problem

Vendor proposals hide critical details in different formats and sections: pricing, implementation timelines, support commitments, SLAs, certifications, technical capabilities, exclusions, and contract language. Manual comparison is slow, inconsistent, and makes it easy to overlook a missing commitment or a risky condition.

## The Solution

Vendorlens creates a repeatable decision trail:

1. Define project requirements and scoring weights.
2. Upload one proposal PDF per vendor.
3. Parse, clean, and chunk the source documents by page and section.
4. Extract structured facts with an LLM and validate them with Pydantic.
5. Deterministically match requirements, detect risks, calculate scores, and rank vendors.
6. Retrieve relevant source excerpts from the proposal corpus.
7. Generate an explainable recommendation from the computed results and retrieved evidence.

The LLM does **not** choose the winning vendor.

## Why Vendorlens is Different

Uploading a PDF to a general-purpose LLM can produce a plausible answer, but it blends document interpretation, business rules, and recommendation into one opaque step.

Vendorlens separates those responsibilities:

| Stage | Responsibility |
|---|---|
| Document understanding | Parse proposal text and use the LLM for structured extraction. |
| Validation | Validate extracted data with Pydantic models. |
| Decision logic | Apply deterministic requirement matching, risk rules, scoring, ranking, and vendor selection. |
| Evidence | Retrieve page- and section-aware source excerpts from Chroma. |
| Explanation | Use the LLM only to explain the already-computed outcome. |

**Don’t ask an LLM to make the decision. Use AI to understand the documents, deterministic logic to evaluate them, and retrieval to show the evidence.**

## What You Get

- A ranked vendor landscape and transparent overall scores
- `PASS`, `FAIL`, `NOT SPECIFIED`, and `REQUIRES REVIEW` requirement outcomes
- Score breakdowns across technical fit, budget, delivery, support/SLA, and risk
- A side-by-side vendor comparison matrix
- Extracted vendor profiles covering cost, timeline, support, capabilities, compliance, and contract information
- A risk register with severity and available source evidence
- An evidence browser with vendor, document, page, section, and source text
- An evidence-backed recommendation brief
- Authenticated, user-scoped saved analysis history

## How It Works

### Evidence and retrieval

Every proposal is parsed, cleaned, and divided into chunks tagged with its vendor, document name, page number, and nearest detected section. Those chunks are embedded and stored in a project-specific Chroma collection.

When a recommendation is generated, Vendorlens retrieves topic-relevant chunks for the recommended vendor—such as pricing, timeline, support, certifications, and contract terms. The resulting evidence snippets include the vendor, document, page, section, and source text so users can trace a finding back to the proposal rather than trust an unexplained model output. If retrieval produces no evidence, the UI states that instead of fabricating a citation.

### Recommendation flow

Vendor selection is determined in Python from the evaluated results. Groq is used only to write a plain-language recommendation narrative; if the LLM is unavailable, the app produces a deterministic fallback explanation.

## AI vs Deterministic Logic

| Capability | Implementation | Role |
|---|---|---|
| Structured extraction | Groq LLM | Reads unstructured proposal text into structured fields. |
| Validation | Pydantic | Rejects or normalizes malformed extracted data. |
| Ambiguity detection | Groq-assisted risk analysis | Flags ambiguous language with a verified source quote. |
| Requirement matching | Python | Computes requirement status from validated fields. |
| Scoring and ranking | Python | Computes weighted scores and ordering. |
| Vendor selection | Python | Selects the recommended vendor from the ranked evaluated results. |
| Rule-based risks | Python | Flags defined commercial, compliance, support, and information risks. |
| Evidence retrieval | Chroma | Finds relevant proposal chunks with metadata. |
| Recommendation narrative | Groq or Python fallback | Explains the computed outcome; does not decide it. |

## Architecture

```text
Vendor Proposal PDFs
        │
        ▼
PDF Parsing → Cleaning + Page/Section Chunking
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  │
LLM Extraction       Embeddings → Chroma      │
        ▼                                     │
Pydantic Validation                          │
        │                                     │
Requirements ──► Deterministic Matching ─► Risk Detection
                                            │
                                            ▼
                                 Deterministic Scoring + Ranking
                                            │
                                            ▼
                                      Evidence Retrieval
                                            │
                                            ▼
                           AI Recommendation Narrative / Fallback
                                            │
                                            ▼
                              Streamlit UI + SQLite History
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit with custom CSS |
| Language | Python |
| LLM | Groq API |
| PDF processing | PyMuPDF |
| Validation | Pydantic v2 |
| Retrieval | Chroma with its embedding function and a hash fallback |
| Persistence | SQLite for accounts and saved analysis snapshots |
| Authentication | PBKDF2-HMAC password hashing and Streamlit session state |
| Testing | pytest + pytest-mock |

## Demo Workflow

From the project root, start the app:

```bash
streamlit run app.py
```

Then:

1. Sign up or sign in.
2. Open **Create Analysis** and enter `Customer Support Platform` as the project name.
3. Set maximum budget to `1000000`, timeline to `8` weeks, and support to `12` months.
4. Mark API integration, SLA, ISO 27001, and GDPR as required.
5. Upload all PDFs from [`data/sample_proposals/`](data/sample_proposals/).
6. Review **Analysis Dashboard**, **Vendor Comparison**, **Vendor Details**, **Risk Analysis**, and **Evidence**.
7. On **Recommendation**, select **Generate / Refresh Recommendation**.
8. Confirm saved snapshots appear in **Analysis History** for the signed-in account.

The supplied NimbusDesk sample is designed as the strongest all-round proposal for this configuration; the exact output depends on successful extraction.

## Project Structure

```text
vendor-proposal-ai/
├── app.py                         # Streamlit entry point and navigation
├── app/
│   ├── ai/                        # Groq client, extraction, risk analysis, recommendation
│   ├── auth/                      # Signup, login, session, welcome email
│   ├── business_logic/            # Deterministic matching, scoring, risks, selection
│   ├── document_processing/       # PDF parsing, cleaning, chunking
│   ├── persistence/               # SQLite users and history snapshots
│   ├── retrieval/                 # Chroma store, embeddings, evidence retrieval
│   ├── schemas/                   # Pydantic contracts
│   ├── ui/                        # Streamlit pages and design system
│   └── utils/                     # Configuration and session-state helpers
├── data/sample_proposals/         # Synthetic demo PDFs
├── scripts/generate_sample_proposals.py
├── tests/
├── .env.example
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.11 or newer
- A Groq API key and supported model name for LLM extraction and AI-written narratives (the deterministic parts run without one)

### Install

```bash
git clone <your-repository-url>
cd vendor-proposal-ai
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### Configure

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
# cp .env.example .env
```

Add your Groq settings to `.env`:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=your_supported_groq_model
```

Do not commit `.env`, API keys, passwords, SQLite databases, or Chroma data.

### Run

Run this from the **project root**, where `app.py` is located:

```bash
streamlit run app.py
```

## Testing

```bash
pytest -v
```

The current suite contains **51 tests** covering PDF parsing, chunking, schemas, extraction and repair, matching, scoring, risk rules, retrieval, authentication, and SQLite persistence. Live Groq calls are mocked in tests; retrieval tests use the hash embedding fallback and an in-memory Chroma client.

## Requirement Matching & Scoring

| Status | Meaning |
|---|---|
| `PASS` | The extracted vendor value satisfies the configured requirement. |
| `FAIL` | The extracted vendor value does not satisfy it. |
| `NOT SPECIFIED` | The proposal does not provide the information. |
| `REQUIRES REVIEW` | The value is present but ambiguous or needs human confirmation. |

The score is a weighted combination of five transparent 0–100 sub-scores: technical fit, budget, delivery timeline, support/SLA, and risk. The configured weights are normalized to 100%. See [`app/business_logic/`](app/business_logic/) for the decision rules.

## Known Limitations

- Scanned or image-only PDFs are detected but are not OCR-processed.
- Long documents are truncated for the single structured-extraction call according to `MAX_EXTRACTION_CHARS`; evidence retrieval remains chunk-based.
- The primary embedding model may need an initial download. If unavailable, the app uses a lower-quality hash-based fallback so retrieval still works.
- SQLite and local Chroma persistence suit a hackathon/demo deployment, not a production multi-instance environment.
- Vendorlens is decision support only; users should verify figures and contract terms against the original documents.

## Roadmap

- OCR for scanned proposals
- Exportable PDF/Word decision briefs
- Multiple documents per vendor
- Richer custom requirement types
- Managed database and vector-store integrations for production deployments

---

Built for faster, more transparent procurement decisions.
