# RAG Architecture

This documents the actual pipeline as implemented under `swingsense-backend/app/rag/`,
current as of the `project-exploration` branch.

## Pipeline

```
PDFs (app/rag/corpus/raw/user/*.pdf)
  |  preprocess_pdfs.py
  v
.txt files (app/rag/corpus/processed/user/*.txt)
  |  ingest.py
  v
chunks.json + faiss.index (app/rag/index/)
  |  retrieve.py
  v
top-k RetrievedChunk list
  |  prompt.py (for /questions and /plans) or resources.py's own summarizer
  v
gpt-4o-mini response
```

Run offline via:
```
python -m app.rag.preprocess_pdfs [--subset user|internal|all] [--force]
python -m app.rag.ingest --validate --k 5
python -m app.rag.retrieve "your question" --k 5
python -m scripts.validate_retrieval          # or: pytest scripts/test_validate_retrieval.py
```
Ingestion never runs at import time or on FastAPI startup — it's CLI-only, per CLAUDE.md §3/§6.

## Preprocessing (`preprocess_pdfs.py`)

- Extracts text per page via `pdfplumber`.
- Detects and strips running headers/footers (lines repeated across ≥40% of pages).
- Drops pages under 40 words, and pages that look like a table of contents or index
  (`toc_filter.is_toc_like`: ≥50% of a block's non-empty lines match page-leader/dotted-leader/
  bare-page-number patterns).
- Inserts a `[[PAGE N]]` marker before each surviving page's text, later parsed back out by
  `ingest.py` to tag each chunk with its starting page number.
- Output: one `.txt` file per source PDF under `corpus/processed/<subset>/`.

## Ingestion (`ingest.py`)

- Loads every `.md`/`.txt` file under `app/rag/corpus/` (both `user` and `internal` subsets,
  if present — there's currently no `internal` corpus).
- **Title inference** (`_infer_title`): derived from the filename, not from in-corpus text.
  Corpus files are named `<Title-Words>_<Author>.txt` (e.g. `Golf-Hacks_AdamYoung.txt` →
  `"Golf Hacks (Adam Young)"`). This was changed from "first heading-like line in the text"
  because that often picked a generic section header ("Introduction") or disclaimer boilerplate
  instead of a stable, meaningful title. A leading markdown `# Heading` still wins for `.md` files.
- **Chunking** (`_chunk_text`): splits on blank-line paragraph boundaries first
  (`DEFAULT_CHUNK_SIZE = 1200` chars), re-applies the TOC filter at the block level as a second
  pass, then falls back to sentence-aware splitting for any block that's still too long, and a
  hard character split (with 100-char overlap) only for a single oversized sentence.
- Embeds all chunk texts with `text-embedding-3-small` in batches of 96.
- L2-normalizes every document vector (`faiss.normalize_L2`), then builds a `faiss.IndexFlatIP`
  index — inner product over normalized vectors is equivalent to cosine similarity.
- Saves `chunks.json` (chunk metadata, one entry per `Chunk`: id/text/source/title/url/tags/page)
  and `faiss.index` side by side in `app/rag/index/`.
- `--validate` re-loads what was just saved and asserts `index.ntotal == len(chunks)` and
  `index.d == embedding_dim` before running one sample query.

## Retrieval (`retrieve.py`)

- `retrieve(query, k)` returns `[]` immediately for an empty/whitespace query — no embedding
  call, no network access, no index load.
- **Short-query handling**: a bare query missing the word "golf" (e.g. "fix my slice") is embedded
  twice — once as-is, once prefixed with `"golf "` — and the two embeddings are averaged before
  normalization. This exists because `text-embedding-3-small` scores short/colloquial queries
  systematically lower against these ~1000-char corpus chunks (a bare `"How do I fix a slice?"`
  scored 0.36 vs 0.60 for the same question with "golf" in it). Prefixing alone overcorrected for
  at least one query ("unplayable lie": score went from 0.39 to 0.56, but the top-1 match flipped
  from the correct Golf-Rules chunk to an unrelated glossary chunk in a different book);
  averaging the raw and prefixed embeddings recovers most of the score boost without flipping a
  correct match to a wrong one.
- The query vector is L2-normalized before `index.search()`, matching the document vectors'
  normalization so the index's inner product is a true cosine similarity.

## Prompting (`prompt.py`)

- Used by `/questions` and (with its own copy of the same pattern) `/plans`.
- Each retrieved chunk is labeled `Source: <title>` in the context block passed to the model.
- System prompt instructs the model to answer only from the provided context, explicitly say so
  when context is insufficient, cite sources inline in prose (`"According to <title>..."`) rather
  than as a separate references section, and keep responses to 3-6 bullets / one drill max.

## Retrieval quality gate (`scripts/validate_retrieval.py`)

- Fires 24 fixed real golf questions (15 full-sentence, 9 short/colloquial) through the live index
  and checks: top-1 cosine ≥ 0.5, no TOC-like content in the top-5, and — for the short queries —
  that the top-1 result's source is one of a pre-approved set for that query (catches a
  high-scoring but *wrong-document* match that a score-only gate would miss).
- Runnable standalone (`python -m scripts.validate_retrieval`) or via pytest
  (`pytest scripts/test_validate_retrieval.py`); each question is its own parametrized test case.
- One known, tracked gap: `"unplayable lie"` scores 0.49 (just under the gate) but from the
  *correct* source — marked `xfail(strict=True)` rather than hidden, so a future regression or
  fix is visible.

## Current corpus (as of this branch)

7 PDFs under `corpus/raw/user/`, all rules/instruction books, producing 808 chunks:

| Source | Chunks |
|---|---|
| Golf-Rules_USGA.txt | 440 |
| Intro-Golf_PGA.txt | 112 |
| Golf-Over50_PeterCroker.txt | 85 |
| Golf-Hacks_AdamYoung.txt | 70 |
| Golf-Drills_GolfAcademy.txt | 41 |
| AtoB-Golf-Drills_PeterCroker.txt | 38 |
| ShortGame-Drills_AdamYoung.txt | 22 |

Coverage is uneven — rules content dominates. Some issues (e.g. "slice") only match thin,
glossary-style, PDF-column-garbled text at moderate confidence (~0.5-0.6 after the short-query
fix above); `/resources` now has a 0.5 confidence floor to avoid presenting those as solid matches
(see `docs/project_status.md`).

## Corpus policy (per CLAUDE.md §4)

Only `processed/user/` is indexed and served to the product-facing endpoints. There is currently
no `internal/` corpus in this repo; if one is added, it must never be mixed into the product index
without an explicit instruction to do so.
