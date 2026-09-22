# Changelog

Human-readable history, grouped by theme, most recent first within each group. Seeded from
`git log --oneline` on 2026-09-22. **Going forward, append new entries here rather than
regenerating this file from git log** — group theme is the useful signal, and the git log's
exact commit ordering isn't.

## RAG pipeline

- Add retrieval safety test coverage per CLAUDE.md §7 (index/metadata parity, embedding
  dimension, normalized query vectors, empty-query handling — none previously tested).
- Add a 0.5 confidence floor to `/resources` instead of always returning 3 matches regardless
  of score.
- Fix short-query retrieval sensitivity: bare queries (e.g. "fix my slice") scored far lower
  than full-sentence ones purely from embedding-model behavior; fixed via blending the raw and
  a "golf"-prefixed embedding rather than a naive text prefix (which overcorrected and flipped
  at least one query to the wrong source document).
- Ground `/plans/generate` in the corpus: retrieves matching content before generating a
  training plan, cites sources inline, fails loudly (503) on retrieval failure instead of
  silently falling back to ungrounded generation.
- Ground `/resources` in the corpus instead of asking the LLM to invent external article/video
  URLs — a real hallucination risk. Returns retrieved corpus excerpts with source/page citation
  instead.
- Fix citation-title inference (`_infer_title`): derive from filename instead of the first
  heading-like line in the text, which often picked a generic section header or disclaimer
  boilerplate.
- RAG cleanups: inline source attribution in prompts, page-number tracking through the
  pipeline, corpus-relative source paths (not absolute machine paths), single shared
  `DEFAULT_TOP_K`.
- Fix TOC/index-page leakage into retrieval results via a pattern-based classifier
  (`toc_filter.py`), applied at both the page level (preprocessing) and paragraph-block level
  (ingestion); added the first retrieval quality validation gate.
- Wire the RAG pipeline into the FastAPI app (`/questions`) and fix assorted path/dependency
  bugs from the initial pdfplumber + paragraph-chunking implementation.
- (Superseded) An earlier RAG revamp attempt failed validation (0.36 vs 0.5 target, TOC leakage
  in top-5) before the TOC filter and validation gate above were added.

## Auth

- Add Supabase JWKS-based JWT verification (`RS256`/`ES256` only, algorithm never taken from
  the token header, to avoid algorithm-confusion attacks).

## DB schema

- Fix `training_plans`/`swing_feedback` schema drift; apply `user_profiles` and `round_logs`
  migrations.
- Add pytest suite for `/me` and `/progress` endpoints.
- Wire `/me` and `/progress` to real DB-backed CRUD (previously stubbed).
- Add `round_logs` table/migration, `user_profiles` table/migration, `UserProfile` model.

## Frontend

- Fix `ProtectedRoute` to respect auth loading state (was showing a flash of unauthenticated
  content before the auth check resolved).
- Add loading states to the plans and logs pages; redesign the logs page as Q&A pairs with
  sources shown.
- Refactor to a shared Supabase client; fix API base URLs after a router-prefix fix.
- Initial frontend structure (Next.js + Tailwind + Supabase auth).

## Documentation

- Added `docs/rag_architecture.md`, `docs/project_status.md`, this changelog (per CLAUDE.md §9
  — none of the three existed before).

## Earlier history

The repo predates the current FastAPI/RAG architecture — early commits include a Flask-based
API with its own pytest suite, several rounds of README updates, and general housekeeping
(`.gitignore` fixes, removing an accidentally-committed backup file). Collapsed here since
none of it reflects the current architecture; see `git log` directly if that era matters.
