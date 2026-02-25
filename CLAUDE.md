# CLAUDE.md — SwingSense

This file defines how Claude should collaborate on the SwingSense codebase. Claude must follow these rules before proposing designs, code, or structural changes.

Failure to follow these rules is considered incorrect behavior.

---

# 1. Project Overview

SwingSense is a full-stack application that provides golf swing guidance and explanations using a Retrieval-Augmented Generation (RAG) backend.

It is built as:

- Backend: FastAPI (Python 3.12)
- RAG: OpenAI embeddings + FAISS (cosine similarity via L2 normalization + IndexFlatIP)
- DB: PostgreSQL (Supabase)
- Auth: Supabase JWT
- Frontend: Next.js + Tailwind
- Dev environment: WSL Ubuntu + local venv

SwingSense is a **product-facing assistant**, not an infrastructure control plane.

It must:
- Provide grounded golf-related responses
- Avoid hallucination
- Cite retrieved context
- Remain deterministic and explainable

---

# 2. Core Goals (Priority Order)

Claude must optimize for:

1. Grounded, correct responses over creativity  
2. Deterministic and reproducible ingestion  
3. Clean separation of data acquisition and indexing  
4. Simplicity and readability over abstraction  
5. Demo-ready, interview-defensible architecture  

If a change increases complexity without improving grounding, reliability, or clarity, it should be rejected.

---

# 3. RAG Architecture (High-Level)

SwingSense follows a standard RAG flow:

PDFs / docs (local corpus)
↓
preprocess_pdfs.py
↓
.txt files (processed corpus)
↓
ingest.py (chunk + embed + normalize + FAISS index)
↓
retrieve.py (vector search)
↓
prompt.py (construct context-bounded prompt)
↓
LLM response


## Key Design Decisions

- Embeddings model: `text-embedding-3-small`
- Similarity metric: cosine similarity
- FAISS index type: `IndexFlatIP`
- All document vectors must be L2-normalized
- Query vectors must be L2-normalized before search
- Ingestion is CLI-only and never runs at import time
- Retrieval must be testable without FastAPI

---

# 4. Corpus Policy (Very Important)

The corpus defines what the assistant is allowed to know.

## Folder Structure
app/rag/corpus/
raw/
user/
internal/
processed/
user/
internal/


### User Corpus

Contains golf-related knowledge:

- Rules of golf  
- Swing mechanics  
- Common faults and drills  
- Glossaries and FAQs  

Only `processed/user/` should be indexed for product answers.

### Internal Corpus (Optional)

Contains engineering documentation:

- RAG architecture notes  
- API contracts  
- Project overview  

This must not be mixed into the user-facing index unless explicitly requested.

Claude must never propose mixing internal engineering docs into the product-facing assistant without explicit instruction.

---

# 5. Engineering Principles

Claude must:

- Prefer explicit code over clever abstractions  
- Avoid side effects at import time  
- Keep ingestion deterministic and offline  
- Separate preprocessing from indexing  
- Avoid network calls during ingestion (except embeddings)  
- Fail loudly on missing API keys or corpus  

All secrets must use environment variables.  
No secrets may be committed to the repository.

---

# 6. Hard Constraints (Non-Negotiable)

Claude must never:

- Fetch internet content during ingestion  
- Hardcode API keys  
- Trigger indexing on FastAPI startup  
- Introduce background threads or async jobs into ingestion  
- Modify routers unless explicitly asked  
- Break compatibility with `numpy < 2` (FAISS constraint)  
- Introduce new dependencies without justification  

All batch processes must be runnable via:
python -m app.rag.<module>


---

# 7. Retrieval Safety Policy

SwingSense must:

- Only answer using retrieved context  
- Explicitly acknowledge when context is insufficient  
- Avoid hallucinating rule numbers or technical claims  
- Prefer citation-style answers  

Claude must ensure:

- Query embeddings are normalized  
- Index dimensionality matches embedding dim  
- Index count equals metadata count  
- Retrieval handles empty queries safely  

---

# 8. Repository Workflow

This is a solo project.

Branching is optional but encouraged for non-trivial changes.

Branch naming convention:
feat/<description>
fix/<description>
docs/<description>
rag/<description>


Direct commits to `main` are allowed.

---

# 9. Documentation Policy

SwingSense uses living documentation.

Claude must:

- Update documentation when architecture changes  
- Keep RAG behavior documented  
- Keep ingestion behavior documented  
- Avoid duplicating large docs inside CLAUDE.md  

Core docs (if present):

- docs/rag_architecture.md  
- docs/project_status.md  
- docs/changelog.md  

Claude should suggest documentation updates when modifying ingestion, retrieval, or corpus structure.

---

# 10. Frequently Used Commands

## Environment
source .venv/bin/activate

## Preprocess PDFs
python -m app.rag.preprocess_pdfs

## Ingest Corpus
python -m app.rag.ingest --validate --k 5

## Test Retrieval
python -m app.rag.retrieve "How do I fix a slice?" --k 5

## Run Backend
uvicorn app.main:app --reload

---

# 11. Design Philosophy

SwingSense is:

- A product-facing, grounded assistant  
- Not an open-domain chatbot  
- Not a search engine  
- Not a golf encyclopedia  

It must remain:

- Controlled  
- Explainable  
- Deterministic  
- Demo-ready  

Claude should prioritize correctness and architecture clarity over feature expansion.
