# Vendorlens — Presentation, Viva, and Interview Guide

Use this document to explain Vendorlens clearly during a college presentation, project viva, or technical interview.

## 1. One-minute project introduction

> Vendorlens is an AI-assisted procurement decision-support application. A user uploads vendor proposal PDFs and defines requirements such as budget, implementation time, support period, API support, SLA, ISO 27001, and GDPR compliance. The system extracts structured vendor data from the PDFs, validates it, evaluates every vendor against the same requirements, detects risks, calculates transparent scores, retrieves source evidence, and recommends the strongest vendor. The important design decision is that the LLM does not choose the winner: deterministic Python code performs matching, scoring, ranking, and final selection. This makes the result explainable and auditable.

## 2. Problem statement

Procurement teams receive proposals in different PDF formats. Important details—pricing, timeline, support, compliance, and exclusions—are scattered through long documents. Comparing them manually is slow and inconsistent.

Vendorlens solves this by converting unstructured proposals into a repeatable, evidence-backed comparison workflow.

## 3. End-to-end pipeline

```text
Vendor proposal PDFs
        |
        v
PyMuPDF text extraction
        |
        v
Text cleaning + page/section-aware chunking
        |
        +--------------------------+
        |                          |
        v                          v
Groq structured extraction     Chroma vector storage
        |                          |
        v                          |
Pydantic validation             |
        |                          |
        +------------+-------------+
                     v
Deterministic matching, risk rules, scoring, ranking
                     |
                     v
Recommendation evidence retrieval (RAG)
                     |
                     v
Groq narrative or Python fallback explanation
                     |
                     v
Streamlit dashboard + SQLite saved history
```

## 4. Technology used and why

| Technology | Used for | Why it is used |
|---|---|---|
| Python | Main application and decision logic | Strong ecosystem for AI, PDF processing, data validation, and business rules. |
| Streamlit | Web UI | Quickly builds interactive upload, dashboard, comparison, review, and history pages in Python. |
| PyMuPDF | PDF text extraction | Reads PDF text page by page and detects likely scanned/image-only documents. |
| Groq API | AI document understanding | Extracts structured facts, identifies ambiguous risks, and writes recommendation narratives. |
| Pydantic v2 | Validation | Validates the fields returned by the LLM before business logic uses them. |
| ChromaDB | Vector store / RAG | Stores embedded PDF chunks and retrieves relevant source evidence for recommendations. |
| Chroma Default Embedding Function | Embeddings | Uses the local ONNX MiniLM embedding model when available. |
| Hash embedding fallback | Retrieval resilience | Keeps retrieval working locally if the embedding model cannot load; semantic quality is lower. |
| SQLite | Persistence | Saves account data and per-user analysis snapshots for a simple demo deployment. |
| PBKDF2-HMAC-SHA256 | Password security | Stores salted password hashes instead of plain-text passwords. |
| Gmail SMTP + STARTTLS | Welcome email | Sends an optional account-created notification through Gmail using an App Password. |
| pytest | Testing | Tests parsing, validation, extraction repair, matching, scoring, retrieval, authentication, persistence, and review evidence. |

## 5. Which AI model is used, and for what?

### Groq LLM

The application uses the **Groq API**. The actual hosted LLM is selected through the `GROQ_MODEL` environment variable, not hard-coded into Python. The example configuration in `.env.example` is:

```env
GROQ_MODEL=llama-3.3-70b-versatile
```

Use this precise statement in a presentation:

> “The project uses a Groq-hosted language model configured through `GROQ_MODEL`—for example, Llama 3.3 70B Versatile. I use it for structured proposal extraction, ambiguity-focused risk analysis, and recommendation writing. I do not use it for scoring, ranking, or selecting the winning vendor.”

Your deployed environment may use a different value. Before presenting, check only the `GROQ_MODEL` line in your private `.env`; **never show or read out the API key**.

### Embedding model for RAG

This is separate from the Groq LLM.

- Primary embedding path: ChromaDB `DefaultEmbeddingFunction`, which uses an ONNX MiniLM model (`all-MiniLM-L6-v2`).
- Fallback: a local deterministic hash-based embedding when the primary embedding model is unavailable.

Use this statement:

> “Groq understands the proposal text; Chroma embeddings support semantic retrieval of source evidence. They are separate parts of the architecture.”

## 6. What Groq does vs. what Python does

| Task | Groq LLM | Deterministic Python |
|---|:---:|:---:|
| Read unstructured proposal wording | Yes | No |
| Extract structured vendor facts | Yes | No |
| Validate extracted structure | No | Yes, through Pydantic |
| Match requirements | No | Yes |
| Detect predefined risks | Optional for ambiguity | Yes, for rule-based risks |
| Calculate score | No | Yes |
| Rank vendors | No | Yes |
| Select recommended vendor | No | Yes |
| Write a human-readable explanation | Yes, when available | Python fallback available |

This separation is the strongest technical point of the project. It reduces the risk of an LLM making an opaque procurement decision.

## 7. RAG explained simply

**RAG** means Retrieval-Augmented Generation.

Instead of asking the LLM to answer only from its general knowledge, Vendorlens retrieves relevant excerpts from the uploaded vendor PDFs and attaches them as evidence.

In this project:

1. PDF text is split into chunks while preserving vendor, file name, page number, section, and source text.
2. Chunks are embedded and stored in ChromaDB.
3. During recommendation generation, the system searches Chroma for topics such as price, timeline, support, compliance, and exclusions.
4. The application displays the retrieved evidence beside the recommendation.

Important accuracy note: the **Recommendation** page uses semantic Chroma queries. The **Evidence Library** filters the stored in-session chunks directly, and **Human Review** ranks available chunks to show useful source context.

## 8. Human-in-the-loop review explained

LLMs can misread or miss a value in a PDF. Vendorlens therefore includes a Human Review workspace.

The reviewer can inspect and correct:

- Total and recurring cost
- Implementation timeline
- Support duration and SLA
- API support
- ISO 27001 and GDPR status
- Certifications and exclusions

When the reviewer applies corrections, the system preserves the original extraction and re-runs the same deterministic matching, risk detection, scoring, ranking, and recommendation-state reset. This demonstrates responsible AI: the AI assists humans instead of replacing them.

## 9. Authentication and persistence

Explain it like this:

> “The app supports signup and login using email and password. Passwords are salted and hashed with PBKDF2-HMAC-SHA256; the plain password is never stored. SQLite stores users and user-scoped analysis snapshots. Streamlit session state stores the active logged-in session. Gmail SMTP sends an optional welcome email using a Google App Password and STARTTLS.”

Be honest about the scope:

- This is suitable for a portfolio/demo deployment.
- SQLite, local Chroma, and Gmail SMTP are not the intended final architecture for a high-scale production application.
- PostgreSQL, managed vector storage, transactional email, role-based access, and secret management are future production improvements.

## 10. Suggested live demo flow (five minutes)

1. Start on the login screen and sign in.
2. Open **Create Analysis** and define requirements: budget, timeline, support, API, SLA, ISO 27001, and GDPR.
3. Open **Upload Proposals** and upload the included sample PDFs.
4. Explain that PDFs are parsed, chunked, embedded, extracted with Groq, validated with Pydantic, then evaluated in Python.
5. Open **Analysis Dashboard** to show scores, rankings, requirement outcomes, and risks.
6. Open **Vendor Comparison** to show the side-by-side PASS/FAIL matrix.
7. Open **Human Review**, show the extracted value and source evidence, then explain that a correction triggers recalculation.
8. Open **Evidence** and **Recommendation** to show traceability from decision back to the PDF.
9. Open **Analysis History** to show that the signed-in user’s snapshot is saved.

## 11. Code excerpts worth explaining

These short extracts are simplified representations of the actual code. Open the listed source files during a viva if the examiner wants the complete implementation.

### A. Deterministic vendor selection

File: `app/business_logic/recommendation.py`

```python
ranked_all = sorted(results, key=lambda result: result.score.total_score, reverse=True)
eligible = [
    result for result in ranked_all
    if not result.has_mandatory_failure and not result.extraction_failed
]

if eligible:
    return eligible[0].vendor_name, False, ranked_all

# If every vendor fails a mandatory requirement, return the best available
# option but mark the choice as forced so the UI can warn the reviewer.
usable = [result for result in ranked_all if not result.extraction_failed]
if usable:
    return usable[0].vendor_name, True, ranked_all

return None, True, ranked_all
```

How to explain it:

> “This proves the LLM does not pick the winner. The code sorts vendors by the Python-computed score, first prefers vendors without mandatory failures, and clearly marks a forced best-available choice.”

### B. The core proposal-processing pipeline

File: `app/pipeline.py`

```python
parsed = parse_pdf(file_bytes, filename)
chunks = chunk_document(parsed, vendor=vendor_name_guess, document_name=filename)
store.add_chunks(chunks)
proposal = extract_vendor_proposal(client, parsed.full_text, filename_hint=filename)
result = analyze_vendor(vendor_name, proposal, source_documents, requirements, all_chunks, client)
```

How to explain it:

> “The pipeline first creates auditable source chunks, then uses Groq to extract structured fields. Only after Pydantic-backed extraction does the application run deterministic analysis.”

### C. Password hashing

File: `app/auth/auth.py`

```python
salt = secrets.token_bytes(16)
digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
```

How to explain it:

> “Passwords are salted and hashed before storage. The application stores the salt and hash, never the password itself.”

### D. Embedding fallback

File: `app/retrieval/embeddings.py`

```python
try:
    self._backend = embedding_functions.DefaultEmbeddingFunction()
    self._backend(["smoke test"])
    self._mode = "minilm"
except Exception:
    self._mode = "hash"
```

How to explain it:

> “The preferred semantic embedding model is used when available. If it cannot load, the system still works locally with a deterministic hash embedding, while acknowledging lower retrieval quality.”

### E. Human review recalculation

File: `app/ui/review.py`

```python
revised_proposal = result.proposal.model_copy(update=update, deep=True)
recalculated = analyze_vendor(
    vendor_name=vendor,
    proposal=revised_proposal,
    source_documents=result.source_documents,
    requirements=requirements,
    all_chunks=get_all_chunks(),
    client=get_groq_client(),
)
```

How to explain it:

> “After a reviewer correction, I do not manually alter the score. I create a revised proposal and call the same analysis function, so matching, risks, scoring, and ranking remain consistent.”

## 12. The five files to show a supervisor

Open these files in this order if someone asks to see the main code:

1. **`app.py`** — application entry point, authentication gate, sidebar navigation, and page wiring.
2. **`app/pipeline.py`** — the complete PDF → chunking → extraction → validation → evaluation workflow.
3. **`app/business_logic/recommendation.py`** — deterministic final-vendor selection; this is the best file to prove the LLM does not choose the winner.
4. **`app/retrieval/chroma_store.py`** — Chroma vector storage and semantic evidence query implementation.
5. **`app/ui/review.py`** — the human-in-the-loop correction workflow and recalculation after approval.

If the supervisor specifically asks about the Groq model/API call, open **`app/ai/groq_client.py`** next. If they ask about password security or SQLite history, open **`app/auth/auth.py`** and **`app/persistence/database.py`**.

## 13. Likely viva and interview questions

### Why did you use an LLM instead of regular expressions for extraction?

Proposal PDFs use inconsistent language and layouts. An LLM can interpret phrases such as “go-live within six weeks,” “annual subscription,” or “supports REST APIs.” Pydantic validates the result afterward, and deterministic rules make the final decision.

### Why not let the LLM select the vendor directly?

LLM output can vary and may be difficult to audit. Procurement decisions need repeatable rules. Python performs the actual matching, weighting, scoring, mandatory-failure checks, and ranking.

### What is RAG doing here?

RAG retrieves relevant content from the uploaded PDFs, so a recommendation can be tied to proposal evidence such as a price clause or compliance statement instead of relying on model memory.

### Is ChromaDB the LLM?

No. ChromaDB is a vector database. It stores numerical embeddings of PDF chunks and retrieves similar chunks. Groq provides the language model.

### What happens if Groq is unavailable?

New structured extraction cannot complete because it needs Groq. If evaluated vendor results already exist, the application can still create a deterministic, template-based recommendation explanation instead of an AI-written one.

### How do you prevent incorrect LLM output from affecting the decision?

The output is validated with Pydantic, then requirement matching and scoring are done by deterministic Python code. Human Review also lets a reviewer correct extracted values and trigger a full recalculation.

### How are passwords protected?

Passwords are salted and hashed using PBKDF2-HMAC-SHA256 with 310,000 iterations. The code compares hashes securely and never stores the plain password.

### Why SQLite instead of PostgreSQL?

SQLite makes a portfolio/demo project easy to run with no separate database server. For production or multiple concurrent app instances, I would migrate to PostgreSQL and add proper migrations, backups, role management, and connection pooling.

### Why Gmail SMTP instead of an email service?

It is convenient for development. In production I would use a verified transactional provider such as Amazon SES, SendGrid, or Postmark, plus SPF, DKIM, and DMARC configuration to improve delivery.

### What are the project limitations?

The project does not have OCR for scanned PDFs, uses demo-oriented SQLite/local Chroma/Gmail infrastructure, and requires human verification for final procurement decisions.

### What would you build next?

OCR, PostgreSQL, Docker, a managed vector database, transactional email, role-based access control, audit reports, and exportable decision briefs.

## 14. Presentation closing statement

> Vendorlens is not just a PDF chatbot. It is a human-in-the-loop procurement decision-support system. AI handles the difficult task of understanding inconsistent documents, while deterministic Python rules, source evidence, and reviewer approval keep the decision transparent, repeatable, and defensible.
