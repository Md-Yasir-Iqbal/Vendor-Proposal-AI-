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
- Ask uploaded proposals natural-language questions through a persistent, analysis-specific, read-only tool-using research agent with citations
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
 Human review/correction, recommendation, or Ask the Proposals agent
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
| Proposal research agent | Groq tool planner + read-only Python tools + SQLite | Selects evidence, cost, requirement, risk, and comparison tools; preserves analysis-specific cited conversations. |
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

Chunks are embedded and stored in a project-specific Chroma collection. The Recommendation workflow performs semantic Chroma queries across topics such as pricing, implementation, support, SLA, certifications, GDPR, ISO 27001, and contract exclusions. The Evidence Library provides direct filtering of the stored session chunks, while Human Review and AI-assisted risk analysis use the uploaded vendor chunks to retain source context. The **Ask the Proposals** agent can select read-only evidence, cost, requirement, risk, and comparison tools for a user question, then returns retrieved source excerpts as citations.

This makes the analysis explainable: users can trace a result back to source text instead of accepting an unsupported AI answer. Chroma uses its default embedding function when available and has a hash-based fallback for local/demo resilience.

## Ask the Proposals: read-only procurement agent

**Ask the Proposals** is a bounded, tool-using assistant available from the header-level **AI** control. It is not a generic chatbot and cannot modify uploaded documents, extracted facts, requirements, scores, rankings, risks, recommendations, or user data.

For every question, the Groq model receives the question, a small window of recent conversation context, and the names of the available vendors. It chooses the smallest relevant set of the following Python tools. Python executes only those read-only tools, then sends the real results back to Groq to write a cited response.

| Tool | Source of truth | Responsibility |
|---|---|---|
| `search_evidence` | Chroma and uploaded proposal chunks | Retrieves relevant source excerpts with vendor, filename, page, and section metadata. |
| `calculate_total_cost` | Validated `VendorProposal` values | Computes annual recurring cost and three-year TCO deterministically when both the required values and recurrence frequency are known. |
| `check_requirements` | Existing deterministic matching results | Reads `PASS`, `FAIL`, `NOT SPECIFIED`, and `REQUIRES REVIEW` outcomes. |
| `analyze_vendor_risks` | Existing evaluated risk results | Reads risk categories, severities, and known missing information. |
| `compare_vendors` | Existing deterministic scores and ranking | Compares current score totals and mandatory-failure state. |

### Financial-comparison safeguards

Financial arithmetic is performed by Python, never by the LLM. The three-year calculation is only produced when the quoted one-time cost, recurring cost, and recurrence frequency are available:

```text
Three-year TCO = quoted one-time cost + (annual recurring cost × 3)
```

Monthly recurring cost is annualized by multiplying by 12. If the recurrence frequency, initial cost, or recurring cost is unavailable, the assistant reports that a comparable three-year total cannot be calculated. It does not invent taxes, additional charges, maintenance costs, contractual penalties, termination fees, or other unquantified amounts; those limitations are surfaced in the tool output.

### Conversation persistence and evidence

Each procurement analysis has one simple persistent assistant conversation. Messages are stored in SQLite and are isolated by both the authenticated user email and the analysis/project ID, so switching analyses does not mix conversations. A response stores its own citation metadata and concise tool-execution record. Users can clear the current analysis conversation after confirmation; clearing it does not affect any other analysis.

Each assistant response includes:

- A source-grounded answer, normally at least two complete sentences when supporting evidence is available
- Expandable cited proposal evidence showing vendor, original filename, page, section, and exact excerpt
- Expandable **Agent Execution Details** showing tool names, concise actual execution outcomes, and whether the answer used Groq or the deterministic fallback

If Groq, retrieval, or planning is unavailable, the feature returns a conservative deterministic fallback and explicitly avoids unsupported conclusions. Conversation context helps resolve follow-up terms such as “it” or “that vendor,” but fresh evidence retrieval remains the source of truth for factual claims.

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
- Ask the Proposals
- Recommendation
- Analysis History
- Account management

The analytical pages dynamically use live session and stored analysis data; they do not rely on hard-coded vendor analysis results. The login screen uses the same Vendorlens visual identity while remaining separate from procurement analysis functionality.

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
| `SQLITE_DB_PATH` | No | SQLite location for accounts, saved analysis snapshots, and analysis-specific assistant conversations. |
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

The current suite contains **65 tests** covering document parsing and chunking, Pydantic validation, extraction repair, requirement matching, scoring, risk rules, retrieval, authentication, SQLite persistence, review evidence handling, agent tool/citation handling, deterministic three-year cost calculation, analysis-specific conversation persistence, and extraction-evaluation comparison rules. External Groq calls are replaced by local test doubles during tests.

## Extraction evaluation

The repository includes a reproducible evaluation harness in [`evaluation/`](evaluation/) for measuring real structured-extraction accuracy against hand-verified labels. It does not contain sample accuracy figures or guessed ground truth.

1. Copy the proposal PDFs selected for evaluation into `evaluation/proposals/`.
2. Fill one entry per PDF in `evaluation/ground_truth.json`. Replace each `TODO` with the value verified from the original proposal. Use JSON `null` only when the proposal genuinely does not specify a field.
3. Ensure `GROQ_API_KEY` and `GROQ_MODEL` are configured in `.env`, then run:

```powershell
.\.venv\Scripts\python.exe evaluation\run_extraction_eval.py
```

The script calls the existing PyMuPDF parser and `extract_vendor_proposal` function, so it evaluates the same LLM extraction path used by the application. It writes `evaluation/results.csv` with per-proposal/per-field expected and extracted values, correctness, and error type, plus `evaluation/summary.md` with model name, UTC date, extraction limit, skipped entries, per-field accuracy, overall accuracy, and all observed errors. Entries containing `TODO` are skipped, and no accuracy is reported until at least one complete, hand-labelled proposal is evaluated.

### Latest measured extraction run

The current `evaluation/summary.md` records one completed, hand-labelled evaluation run over five synthetic vendor proposal PDFs (50 field comparisons). It used `GROQ_MODEL=openai/gpt-oss-120b` with `MAX_EXTRACTION_CHARS=16000` and produced **45 correct comparisons out of 50 (90.00% overall accuracy)**. This number describes this specific dataset, field definition, model configuration, and run; it is not a general guarantee of production accuracy.

| Field | Correct / total | Accuracy |
|---|---:|---:|
| Vendor name | 5 / 5 | 100.00% |
| Total cost | 5 / 5 | 100.00% |
| Recurring cost | 2 / 5 | 40.00% |
| Recurring-cost frequency | 5 / 5 | 100.00% |
| Implementation timeline | 4 / 5 | 80.00% |
| Support duration | 5 / 5 | 100.00% |
| SLA | 4 / 5 | 80.00% |
| API support | 5 / 5 | 100.00% |
| ISO 27001 | 5 / 5 | 100.00% |
| GDPR | 5 / 5 | 100.00% |

The observed errors are retained in `evaluation/results.csv` and include recurring-cost interpretation, one conditional implementation timeline, and one SLA response that included an extra verified incident-response detail. These are useful evidence for the Human Review workflow: a schema-valid extraction still requires a reviewer to confirm commercial interpretation and contract wording.
 
## Design challenges and engineering resolutions

Building a procurement tool on top of a probabilistic language model creates risks that cannot be solved by prompting alone. Vendorlens separates interpretation from decision logic and documents the engineering choices used to make its results more inspectable. The automated suite covers many of the underlying rules, schemas, parsing paths, retrieval behaviour, authentication operations, and persistence flows.

### 1. An all-in-one LLM answer is opaque

Asking a general-purpose model to read proposals and name the best vendor would blend document interpretation, business rules, scoring, and recommendation into one answer that is difficult to inspect or reproduce. Vendorlens restricts Groq to structured extraction, AI-assisted ambiguity/risk analysis, and recommendation wording. Requirement matching, rule-based risks, weighted scoring, ranking, and vendor selection are deterministic Python functions. Given the same validated inputs and configured requirements, these functions produce the same result and can be unit-tested independently.

### 2. LLM output is not guaranteed to be well formed

An LLM may return malformed JSON, missing keys, or values of the wrong type. Passing that output directly into scoring could turn one bad field into a misleading ranking. Vendorlens places Pydantic v2 validation between extraction and evaluation. The extraction flow parses the model response, validates it against the `VendorProposal` schema, and attempts a constrained repair for recoverable JSON or validation issues. Persistent extraction failures are isolated to the affected document rather than silently used in scoring.

### 3. Unsupported claims and fabricated citations

An explanation can sound convincing while referring to information that is absent from the proposal. Vendorlens treats evidence as a separate first-class output: proposal chunks retain vendor, document, page, and section metadata before being stored in Chroma. The Recommendation page displays retrieved evidence snippets with that metadata, and it explicitly states when no snippet was retrieved. AI-assisted risk findings are retained only when their quoted evidence can be verified against the uploaded source text; unsupported findings are discarded.

### 4. Extraction errors must be correctable

Schema-valid output can still be wrong, such as when a model chooses the wrong price from a table or misses a qualification. The Human Review workspace lets a reviewer compare extracted facts with available source evidence, edit supported fields, and apply corrections. The original extracted proposal remains available in application state, while approved values are re-evaluated through the same deterministic matching, risk, scoring, ranking, and recommendation pipeline. This avoids maintaining a separate manual-analysis path.

### 5. The embedding model may be unavailable

Chroma's default local MiniLM embedding model may need an initial model download. In a restricted or offline environment, that dependency could otherwise disable retrieval. Vendorlens uses a deterministic hash-based embedding fallback when MiniLM cannot initialize or fails at runtime. Retrieval remains functional, with the explicit trade-off that semantic matching of paraphrased content is weaker. Retrieval tests intentionally force this fallback with an in-memory Chroma client, so they run offline without downloading a model.

### 6. Partial failure must not stop the analysis

In a multi-vendor comparison, one unreadable PDF or failed extraction should not discard the work completed for the remaining vendors. Processing failures are stored as document-specific status and error information, while other uploaded proposals continue through the pipeline. After valid vendor results exist, an unavailable Groq service also does not block a final explanation: the system produces a deterministic Python fallback recommendation while preserving the vendor selected by the existing deterministic ranking.

### 7. Long and scanned documents require different handling

Long proposals can exceed the practical size of one structured-extraction request. Vendorlens caps that request with `MAX_EXTRACTION_CHARS`, retaining text from the beginning and end of the document while omitting the middle when necessary. The full parsed text is still chunked for retrieval, but a fact missed by structured extraction is not automatically promoted into a structured field. Image-only PDFs are detected because the parser finds little or no embedded text. They are shown with a warning when limited text exists, or marked as failed when no text can be extracted; OCR is intentionally listed as future work.

### 8. User credentials and secrets must be protected

Passwords are never stored or displayed in plain text. Vendorlens stores a unique salt and PBKDF2-HMAC-SHA256 password hash using 310,000 iterations, then uses `hmac.compare_digest` during verification. Analysis history is retrieved only with the signed-in user's email, and API, SMTP, and database configuration values are loaded from environment variables. The repository `.gitignore` excludes local `.env` files while retaining `.env.example` as a safe configuration template.

### 9. Testing should not depend on live services

Live LLM calls make tests slower, chargeable, and non-deterministic. The test suite uses local test doubles for the extraction client rather than making real Groq requests, and retrieval tests use an in-memory Chroma collection with forced hash embeddings. The 56 current tests cover PDF parsing, chunking, Pydantic schemas, extraction and repair, matching, scoring, rule-based risks, retrieval, authentication, SQLite persistence, review-evidence handling, and the assistant's read-only tools and conversation persistence. They run without a Groq API key or network access.

### 10. Email syntax validation is not email ownership verification

The signup form validates that an email has a valid structural format and validates password strength before an account is created. It does not currently prove that the user owns that mailbox through a verification link or one-time code. Gmail SMTP sends a welcome notification after account creation, but this should not be treated as an account-verification or password-recovery system. A production implementation would add verified-email flows, rate limiting, reset tokens, and a dedicated transactional email provider.

## Current limitations

Vendorlens is deliberately presented as a decision-support application, not as an autonomous procurement system. The following limitations define its current scope and should be considered when interpreting results.

### 1. Decision support, not decision making

Vendorlens ranks vendors using the configured requirements, extracted proposal facts, deterministic matching rules, and risk signals. It does not replace procurement, legal, financial, security, or compliance approval. A reviewer must verify material figures, contractual terms, exclusions, and source evidence against the original proposal and contract documents before making a final decision.

### 2. No OCR for scanned proposals

The PDF parser extracts embedded text only. It detects image-only or likely scanned PDFs and reports a warning, but it does not run optical character recognition (OCR). These documents may produce limited text and therefore cannot be fully extracted, matched, or evaluated until OCR support is added.

### 3. Dependence on LLM extraction

New structured proposal extraction requires a working Groq API configuration, including a valid API key and supported model. Pydantic validation, deterministic downstream rules, source evidence, and the Human Review page reduce risk, but they cannot guarantee that every plausible LLM-extracted value is correct. AI-assisted analysis of ambiguous risks is also skipped when Groq is unavailable. Once valid vendor results already exist, recommendation writing falls back to a deterministic Python summary without changing the selected vendor.

### 4. Truncation of long documents

Structured extraction is limited by `MAX_EXTRACTION_CHARS` to keep a single LLM call predictable. For documents above this limit, the extractor includes a portion from the beginning and a portion from the end, while omitting the middle. A fact contained only in an omitted middle section can therefore be missed during structured extraction. Full text is still chunked for evidence retrieval, but retrieval does not automatically turn a missed fact into a structured field.

### 5. Embedding quality and availability

Chroma's local `all-MiniLM-L6-v2` default embedding model may need to download on first use. If it cannot initialize or later fails, Vendorlens falls back to deterministic hash-based embeddings so storage and retrieval remain available. The fallback is less semantic, so it is weaker at retrieving paraphrased or conceptually similar evidence than the MiniLM model.

### 6. One proposal document per vendor

The upload workflow is designed for one proposal PDF per vendor. Multiple PDFs can be uploaded for comparison across vendors, but a multi-document vendor package (for example, proposal, pricing appendix, security response, and contract addendum) is not combined into one vendor analysis yet. Supporting that use case requires document-to-vendor grouping and consolidated extraction logic.

### 7. Limited requirement types

The application evaluates the defined commercial, delivery, support, API, SLA, ISO 27001, and GDPR requirement types using explicit Python rules and weighted scoring. It does not yet provide an end-user rule builder for arbitrary procurement requirements, complex legal clauses, regional regulatory frameworks, or custom scoring formulas. These can be added by extending the schemas and deterministic business rules.

### 8. Local persistence and lightweight access control

SQLite and local Chroma persistence are appropriate for a portfolio, classroom, demonstration, or hackathon deployment. They are not designed for multi-instance production hosting, high concurrency, centralized backups, enterprise secret management, or operational monitoring. Authentication supports individual accounts, but there are no role-based permissions, organization workspaces, or formal persistent reviewer-audit reports.

### 9. Email delivery

Gmail SMTP with STARTTLS is practical for development account notifications, but delivery can be inconsistent and messages may be classified as spam. A production deployment should use a dedicated transactional email provider with a verified sending domain and SPF, DKIM, and DMARC configuration.

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
