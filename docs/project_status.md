# Project Status

Point-in-time snapshot of `project-exploration`, written after the RAG-grounding and
hardening work in this branch. Treat this as a snapshot, not a living guarantee — re-verify
against the code for anything load-bearing.

## RAG grounding by endpoint

| Endpoint | Grounded? | Notes |
|---|---|---|
| `POST /questions/` | Yes | Retrieves via `retrieve()`, builds a context-bounded prompt via `prompt.py`, cites sources inline. Was already grounded before this branch. |
| `GET /resources/` | Yes | Rewritten this branch to retrieve top corpus matches (deduped one-per-source-page) instead of asking the LLM to invent external article/video URLs. `url` is always `null` now (no external link exists); response carries `source`/`page`/`citation`/`score` instead. A 0.5 confidence floor drops weak matches rather than presenting them as solid — see "Known limitations" below. |
| `POST /plans/generate` | Yes | Rewritten this branch to retrieve corpus content matching `weaknesses`+`goals` and inject it into the prompt as labeled `Source: <title>` passages; the model is instructed to cite sources inline and plainly label anything beyond the retrieved material as general guidance. Retrieval failure now returns `503` instead of silently falling back to fully ungrounded generation. |

## RAG pipeline quality

- Retrieval quality gate: `python -m scripts.validate_retrieval` / `pytest scripts/test_validate_retrieval.py` — 23 passing, 1 known `xfail` (see `docs/rag_architecture.md`).
- Citation titles are now stable and filename-derived (fixed this branch — previously some chunks cited generic section headers like "Introduction" or garbled PDF disclaimer text as their source title).
- Short/colloquial query scoring was a real gap (a bare "How do I fix a slice?" scored 0.36, well under the 0.5 gate) — fixed this branch via an embedding blend in `retrieve.py`. See `docs/rag_architecture.md` for why a naive fix wasn't safe.
- Automated retrieval safety tests (`tests/test_rag_retrieve.py`, new this branch) now cover the four things CLAUDE.md §7 calls out explicitly: query embeddings are normalized before search, index dimensionality matches the embedding model's, index count equals metadata count, and empty queries return `[]` without a network call.

## Known limitations (not blockers, but real)

- **Thin corpus coverage for some issues.** The corpus is rules-heavy (440 of 808 chunks are from the USGA rules book). Technique issues like "slice" only match glossary-style, PDF-column-garbled text at moderate confidence. The `/resources` confidence floor (0.5) means these now either return fewer results or a plain "limited coverage" note instead of a confidently-wrong answer, but the underlying content gap is unaddressed — more/better technique-drill sources would help.
- **`resources` DB table is unused.** `app/db/models.py` defines a `Resource` model (`__tablename__ = "resources"`), but `GET /resources/` doesn't read or write it — it's fully computed from live retrieval each request. Not necessarily wrong (nothing here needs persistence), but worth knowing if you're wondering why that table stays empty.
- **`unplayable lie` retrieval gap.** Tracked as an `xfail` in the test suite rather than hidden — see `docs/rag_architecture.md`.

## Backend, non-RAG

- **Auth**: Supabase JWT verified against a real JWKS endpoint (`app/core/auth.py`), restricted to `RS256`/`ES256` (never trusts an algorithm from the token header itself, to avoid algorithm-confusion attacks). `get_current_user` (required) guards `/resources`; `get_optional_user` (optional) guards `/plans`, `/questions`, `/me`, `/progress`.
- **DB schema** (`app/db/models.py`, via Alembic migrations): `swing_questions`, `swing_feedback`, `training_plans`, `progress_metrics`, `resources` (unused, see above), `user_profiles`, `round_logs`.
- **`/me` and `/progress`**: wired to real DB-backed CRUD with an existing pytest suite (`tests/test_me.py`, `tests/test_progress.py`) — predates this branch, not touched here.

## Known infra blocker

**The Supabase Postgres connection is currently unreachable** from this environment:
```
psycopg2.OperationalError: connection to server at "aws-1-ca-central-1.pooler.supabase.com"
FATAL: (ENOTFOUND) tenant/user postgres.ititjislmmraadpvupbj not found
```
Confirmed independently at least 3 times across this branch's work (from a sandboxed tool
environment, from a real terminal, and again during this session) — it's not a network
sandboxing artifact, it looks like the Supabase project is paused or its pooler credentials
were rotated. This blocks: all of `tests/test_me.py` and `tests/test_progress.py` (17 tests,
pre-existing, unrelated to this branch's changes), and live verification of `/plans/generate`'s
DB write path and `/questions`'/`/resources`' DB reads/writes. The RAG side of `/plans/generate`
(retrieval + LLM call) was confirmed working independently of this — only the `db.commit()` step
fails. **Action needed**: check the Supabase dashboard for project `ititjislmmraadpvupbj`
(unpause if paused; verify/rotate pooler credentials in `.env` if not).

## Frontend

Next.js pages present and non-stub: `login`, `logs`, `plans`, `resources` (200-360 lines each,
with loading states). `resources/page.tsx` was updated this branch (`url` is now optional; the
"View Resource" link falls back to showing the citation text when there's no external URL,
since the backend no longer fabricates one). Frontend build (`npm run build`) confirmed clean
after that change, all 8 pages statically generated. Not re-verified after every subsequent
backend change in this branch — worth a final build check before shipping.

## Documentation

This file, `docs/rag_architecture.md`, and `docs/changelog.md` didn't exist before this branch
(added per CLAUDE.md §9). `docs/changelog.md` should be appended to going forward rather than
regenerated from git log each time.
