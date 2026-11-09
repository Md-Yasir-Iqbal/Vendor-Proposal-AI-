# Vendorlens

### AI-powered, evidence-grounded vendor proposal analysis for procurement teams

Vendorlens is a full-stack Python application that turns vendor proposal PDFs into a structured, auditable procurement workspace. It extracts commercial and technical facts, evaluates each vendor against configurable requirements, highlights risks, retrieves supporting source evidence, and produces a transparent recommendation.

The project is designed around a simple principle: **AI interprets unstructured documents; deterministic Python logic makes the decision.**

> **Live demo:** <https://vendorlens-algox.streamlit.app/>
> **Demo video:** _Add video URL here_  
> **Screenshots:** _Add dashboard, comparison, review, and evidence screenshots below_

## Demo gallery

> Replace these placeholders with repository-hosted images or image URLs before sharing the project.

| Login and workspace | Analysis dashboard |
|---|---|
| _Add screenshot_ | _Add screenshot_ |

| Vendor comparison | Human review and evidence |
|---|---|
| _Add screenshot_ | _Add screenshot_ |

## Key capabilities

- Upload and analyze multiple vendor proposal PDFs
- Extract vendor data such as one-time cost, recurring cost, implementation timeline, support period, SLA, API availability, certifications, compliance, and exclusions
- Define project requirements and weighted evaluation criteria
- Classify requirements as `PASS`, `FAIL`, `NOT SPECIFIED`, or `REQUIRES REVIEW`
- Calculate transparent scores, rankings, mandatory-failure checks, and risk summaries in Python
- Compare vendors in a side-by-side requirement matrix
- Browse source evidence with document, page, and section metadata
- Generate an evidence-backed recommendation narrative
- Review and correct AI-extracted fields before re-running the deterministic evaluation
- Create accounts, log in securely, receive welcome emails, and save analysis history per user

## Product workflow

```text
Create analysis requirements
          |
          v
Upload proposal PDFs
          |
          v
Parse, clean, and chunk document text by page/section
          |
          +------------------------+
          |                        |
          v                        v
Groq structured extraction     Embed chunks in Chroma
          |                        |
          v                        |
Pydantic validation             |
          |                        |
          +----------+-------------+
                     v
      Deterministic requirement matching
                     |
                     v
     Risk detection, scoring, and ranking
                     |
                     v
     Retrieve source evidence through RAG
                     |
                     v
  Human review/correction and recommendation
                     |
                     v
      Streamlit dashboard + SQLite history
```

## Architecture and decision model

Vendorlens deliberately separates document understanding from procurement decision-making.

| Responsibility | Technology / implementation | Purpose |
|---|---|---|
| PDF extraction | PyMuPDF | Reads text and page-level information from uploaded PDFs. |
| Text preparation | Python cleaner and chunker | Cleans text and creates page/section-aware chunks. |
| Structured extraction | Groq API | Converts proposal text into structured vendor fields. |
| Schema validation | Pydantic v2 | Validates and normalizes AI-extracted fields. |
| Requirement evaluation | Deterministic Python | Produces PASS/FAIL/NOT SPECIFIED/REQUIRES REVIEW outcomes. |
| Risk detection | Python rules + Groq-assisted ambiguity review | Flags commercial, technical, compliance, and wording risks. |
| Scoring and ranking | Deterministic Python | Computes weighted scores and selects the best-ranked eligible vendor. |
| RAG / evidence | Chroma vector store | Retrieves relevant, metadata-rich proposal excerpts. |
| Recommendation narrative | Groq with Python fallback | Explains the already-computed result; it does not choose the winner. |

The LLM never owns the final vendor selection. Recommendation eligibility, weighted scoring, ranking, and mandatory requirement failures are calculated by the Python business-logic layer.

## Key engineering decisions

### 1. AI extracts; Python evaluates

A vendor recommendation is too important to leave to a probabilistic model. Groq is used for document interpretation, structured extraction, ambiguity analysis, and natural-language explanations. Deterministic Python functions perform requirement matching, mandatory-failure checks, scoring, ranking, and final vendor selection.

### 2. Evidence is a first-class output

Rather than presenting unsupported AI conclusions, the application stores page- and section-aware PDF chunks in Chroma. Retrieval attaches source context to recommendation, risk, and review workflows.

### 3. Human approval can correct extraction errors

Reviewers can correct extracted values while retaining the original extraction. Applying a correction reuses the same evaluation pipeline, preserving consistency and auditability.

### 4. Graceful degradation for a demo environment

The application isolates per-document processing failures, uses a deterministic recommendation fallback when Groq is unavailable after vendor results exist, and supports a hash-embedding fallback when the primary embedding model cannot load. New structured proposal extraction still requires a working Groq configuration.

## RAG and evidence retrieval

Each uploaded proposal is split into coherent chunks tagged with:

- Vendor name
- Source document name
- PDF page number
- Detected section
- Original text excerpt

Chunks are embedded and stored in a project-specific Chroma collection. The Recommendation workflow performs semantic Chroma queries across topics such as pricing, implementation, support, SLA, certifications, GDPR, ISO 27001, and contract exclusions. The Evidence Library provides direct filtering of the stored session chunks, while Human Review and AI-assisted risk analysis use the uploaded vendor chunks to retain source context.

This makes the analysis explainable: users can trace a result back to source text instead of accepting an unsupported AI answer. Chroma uses its default embedding function when available and has a hash-based fallback for local/demo resilience.

## Human-in-the-loop review

The **Human Review** workspace makes the system safer and more credible for procurement use. A reviewer can inspect the extracted data next to the available source evidence, correct fields, and apply the correction.

Reviewable fields include:

- Total and recurring cost
- Implementation timeline and support duration
- SLA and API support
- ISO 27001 and GDPR status
- Certifications and exclusions

After approval, the application reuses the same existing deterministic matching, risk, scoring, ranking, and recommendation logic. The original AI extraction is preserved for auditability.

## User interface

The frontend is built entirely with **Streamlit** and a custom CSS design system. It provides a responsive, light-mode procurement workspace with pages for:

- Home
- Create Analysis
- Upload Proposals
- Analysis Dashboard
- Vendor Comparison
- Vendor Details
- Human Review
- Risk Analysis
- Evidence Library
- Recommendation
- Analysis History
- Account management

The analytical pages dynamically use live session and stored analysis data; they do not rely on hard-coded vendor analysis results. The login screen includes a decorative static preview solely for visual presentation.

## Authentication, database, and email

Vendorlens includes lightweight application authentication suitable for a demo or portfolio deployment.

- Email and password signup/sign-in
- Email format and password validation
- Passwords are salted and hashed using `PBKDF2-HMAC-SHA256` with 310,000 iterations
- Secure hash comparison through `hmac.compare_digest`
- SQLite persistence for user accounts and per-user analysis snapshots
- Streamlit session state for the active authenticated session
- Gmail SMTP welcome email support using a Google App Password and STARTTLS

SQLite is intentionally used for simple local/demo persistence. A production deployment should migrate accounts and history to a managed database, use a transactional email provider, and protect persistent vector data appropriately.

## Technology stack

| Area | Technology |
|---|---|
| Language | Python |
| Web UI | Streamlit + custom CSS |
| LLM provider | Groq API |
| Default/example model | Configurable through `GROQ_MODEL`; example: `llama-3.3-70b-versatile` |
| PDF processing | PyMuPDF |
| Data validation | Pydantic v2 |
| Vector retrieval / RAG | ChromaDB |
| Authentication | PBKDF2-HMAC, Streamlit session state |
| Relational persistence | SQLite |
| Email | Gmail SMTP with STARTTLS |
| Configuration | python-dotenv |
| Testing | pytest and pytest-mock |

## Configuration reference

Copy `.env.example` to `.env` and supply only the settings needed for your environment.

| Variable | Required | Description |
|---|---:|---|
| `GROQ_API_KEY` | Yes for AI analysis | API key used for extraction, ambiguity analysis, and AI narratives. |
| `GROQ_MODEL` | Yes for AI analysis | A Groq-supported model, for example `llama-3.3-70b-versatile`. |
| `GROQ_TIMEOUT_SECONDS` | No | Groq request timeout; defaults to `45`. |
| `GROQ_MAX_RETRIES` | No | Retry count for transient Groq failures; defaults to `2`. |
| `MAX_EXTRACTION_CHARS` | No | Maximum proposal text included in structured extraction. |
| `CHUNK_MAX_CHARS` | No | Maximum size of a retrieval chunk. |
| `CHUNK_OVERLAP_CHARS` | No | Text overlap between adjacent chunks. |
| `CHROMA_PERSIST_DIR` | No | Local directory for Chroma persistence. |
| `CHROMA_COLLECTION_NAME` | No | Base collection name for proposal evidence. |
| `RETRIEVAL_TOP_K` | No | Reserved retrieval-limit setting; the current recommendation helper uses its own topic-query limits. |
| `SQLITE_DB_PATH` | No | SQLite location for accounts and saved analysis snapshots. |
| `SMTP_HOST` / `SMTP_PORT` | No | Gmail SMTP host and port; use `smtp.gmail.com` and `587`. |
| `SMTP_USERNAME` | No | Gmail address used to send welcome emails. |
| `SMTP_PASSWORD` | No | Google App Password, never the normal Gmail password. |
| `SMTP_FROM_EMAIL` | No | Sender email address for welcome emails. |
| `APP_ENV` / `LOG_LEVEL` | No | Environment label reserved for deployment context and the active application logging level. |

## Project structure

```text
vendor-proposal-ai/
├── app.py                       # Streamlit entry point and navigation
├── app/
│   ├── ai/                      # Groq client, extraction, risk analysis, recommendation
│   ├── auth/                    # Authentication, session state, Gmail SMTP email
│   ├── business_logic/          # Matching, scoring, risk rules, vendor selection
│   ├── document_processing/     # PDF parsing, cleaning, and chunking
│   ├── persistence/             # SQLite users and analysis-history snapshots
│   ├── retrieval/               # Chroma store, embeddings, RAG retrieval
│   ├── schemas/                 # Pydantic data models
│   ├── ui/                      # Streamlit pages and shared styling
│   └── utils/                   # Configuration and application state helpers
├── data/sample_proposals/       # Synthetic vendor proposals for demonstration
├── tests/                       # Automated tests
├── .env.example                 # Safe configuration template
├── requirements.txt
└── Readme1.md
```

## Installation

### Prerequisites

- Python 3.11 or later
- A Groq API key and a supported Groq model name
- Optional: a Gmail account with two-step verification and a Google App Password for welcome emails

### Setup

```powershell
git clone <your-repository-url>
cd vendor-proposal-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `.env` without committing it to Git:

```env
# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# SQLite
SQLITE_DB_PATH=data/vendor_proposal_ai.sqlite3

# Optional Gmail SMTP welcome email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_gmail_address
SMTP_PASSWORD=your_16_character_google_app_password
SMTP_FROM_EMAIL=your_gmail_address
```

Never place API keys, Gmail App Passwords, SQLite database files, or Chroma data in source control.

## Run the application

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then create an account, define your evaluation requirements, upload the supplied sample PDFs or your own text-based proposal PDFs, and review the dashboard, evidence, human-review, and recommendation views.

## Five-minute demo walkthrough

1. Start the application and create an account.
2. Open **Create Analysis** and define budget, timeline, support, technical, and compliance requirements.
3. Go to **Upload Proposals** and upload the synthetic PDFs in `data/sample_proposals/`.
4. Inspect the **Analysis Dashboard** and **Vendor Comparison** pages for rankings and requirement outcomes.
5. Open **Human Review** to compare extracted values with source evidence and apply a correction if needed.
6. Use **Risk Analysis** and **Evidence** to inspect the supporting proposal excerpts.
7. Open **Recommendation** to generate an explanation of the already-computed ranking.
8. Confirm the analysis appears under **Analysis History** for the signed-in user.

## Testing

Run the automated test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests cover document parsing and chunking, Pydantic validation, extraction repair, requirement matching, scoring, risk rules, retrieval, authentication, SQLite persistence, and review evidence handling. External Groq calls are mocked during tests.

## Current limitations

- Image-only/scanned PDFs are detected, but OCR is **not currently implemented**.
- Extraction length is capped by `MAX_EXTRACTION_CHARS`; retrieval remains chunk-based.
- SQLite and local Chroma persistence are appropriate for a portfolio, demo, or hackathon deployment, not a multi-instance production system.
- Gmail SMTP is suitable for development notifications; production email should use a dedicated transactional provider with a verified sending domain.
- Vendorlens is decision support software. Final procurement decisions must be verified by a human reviewer against the original proposal and contract documents.

## Engineering trade-offs

| Decision | Benefit | Trade-off |
|---|---|---|
| Deterministic scoring and selection | Transparent, testable procurement decisions | Rules must be expanded as requirement types grow. |
| Groq for extraction and explanations | Fast interpretation of varied proposal formats | Requires an API key and structured-output validation. |
| Local SQLite and Chroma | Simple demo setup with minimal infrastructure | Not suitable for horizontally scaled production deployments. |
| Gmail SMTP | Easy development email delivery | Deliverability is weaker than a verified transactional email provider. |
| No OCR | Smaller, focused codebase | Image-only/scanned PDFs cannot be fully analyzed. |

## Future roadmap — not implemented yet

- Add OCR support for scanned and image-only proposals
- Exportable PDF or Word decision briefs
- More custom requirement types and scoring rules
- Support for multiple documents per vendor
- Verified transactional email provider and domain authentication
- Docker containerization for reproducible local and deployment environments
- PostgreSQL (or another managed SQL database) and a managed vector store for production deployments
- Role-based access controls and reviewer audit reporting

## Security notes

- Passwords are never stored or displayed in plain text.
- User passwords use a unique random salt and PBKDF2-HMAC-SHA256 hashing.
- Secrets are read from environment variables and must not be committed to Git.
- Analysis history is scoped to the authenticated user email in SQLite.
- Gmail integration requires a Google App Password, not a primary account password.
- This repository is a portfolio/demo system; production use requires secure hosting, database access controls, secret management, backups, monitoring, and a verified email-sending domain.

---

Built to make vendor evaluation faster, more consistent, and easier to defend.

## Contact and license

> **Author:** MD YASIR IQBAL 
> **GitHub:** https://github.com/Md-Yasir-Iqbal/Vendor-Proposal-AI-  
> **LinkedIn:** www.linkedin.com/in/mdyasiriqbal  
> **License:** _Choose and add a license, for example MIT_
