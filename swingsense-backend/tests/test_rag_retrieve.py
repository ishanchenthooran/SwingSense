"""Retrieval safety checks required by CLAUDE.md §7:
- query embeddings are normalized
- index dimensionality matches embedding dim
- index count equals metadata count
- retrieval handles empty queries safely

These don't use the client/db_session fixtures from conftest.py since
app/rag/retrieve.py and app/rag/store.py have no DB dependency at all.

Patches go through `rag_retrieve`, fetched via sys.modules rather than
`import app.rag.retrieve as rag_retrieve` or a dotted-string monkeypatch
target. app/rag/__init__.py does `from app.rag.retrieve import retrieve`,
which rebinds the `app.rag` package's `retrieve` *attribute* to that
function — so any attribute-chain lookup (`app.rag.retrieve`, whether via
`import ... as`, a dotted monkeypatch string, or plain attribute access)
silently resolves to the function, not the submodule. sys.modules still
holds the real module under its fully-qualified name regardless.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

import app.rag.retrieve  # noqa: F401 - ensures it's imported/cached below
from app.core.config import settings
from app.rag.store import load_index

rag_retrieve = sys.modules["app.rag.retrieve"]

# Mirrors retrieve.py's own _require_openai_api_key() check — settings loads
# .env via pydantic-settings without touching os.environ, so a plain
# os.getenv() here would false-negative even with a real key configured.
_HAS_OPENAI_KEY = bool((settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")).strip())

EMBED_DIM = 1536  # text-embedding-3-small output size


class _ExplodingOpenAI:
    """Stand-in for openai.OpenAI that fails any use, so a test using it
    proves no network call was attempted."""

    def __init__(self, *args, **kwargs):
        raise AssertionError("OpenAI client should not be constructed for this input")


@pytest.mark.parametrize("query", ["", "   ", "\n\t"])
def test_empty_query_returns_empty_list_without_network_call(monkeypatch, query):
    monkeypatch.setattr(rag_retrieve, "OpenAI", _ExplodingOpenAI)
    assert rag_retrieve.retrieve(query) == []


def test_index_metadata_count_matches():
    index, chunks = load_index()
    assert index.ntotal == len(chunks)
    assert index.ntotal > 0


def test_index_dimension_matches_embedding_model():
    index, _ = load_index()
    assert index.d == EMBED_DIM


class _RecordingIndex:
    """Fake FAISS index that records whatever vector it's searched with."""

    def __init__(self):
        self.searched_with: np.ndarray | None = None

    def search(self, vec, k):
        self.searched_with = vec.copy()
        return np.array([[-1.0] * k], dtype="float32"), np.array([[-1] * k])


def test_query_vector_is_l2_normalized_before_search(monkeypatch):
    fake_index = _RecordingIndex()
    monkeypatch.setattr(rag_retrieve, "load_index", lambda: (fake_index, []))
    # A deliberately non-unit vector (norm=5) to prove retrieve() normalizes it.
    monkeypatch.setattr(
        rag_retrieve,
        "_embed_query_for_retrieval",
        lambda q: np.array([3.0, 4.0], dtype="float32"),
    )

    rag_retrieve.retrieve("golf test query")

    assert fake_index.searched_with is not None
    norm = float(np.linalg.norm(fake_index.searched_with))
    assert abs(norm - 1.0) < 1e-5


@pytest.mark.live
@pytest.mark.skipif(not _HAS_OPENAI_KEY, reason="requires a real OPENAI_API_KEY")
def test_live_retrieval_returns_normalized_scores():
    results = rag_retrieve.retrieve("How do I fix a slice?", k=5)
    assert len(results) > 0
    for r in results:
        assert isinstance(r.score, float)
        # cosine similarity of two L2-normalized vectors is bounded in [-1, 1]
        assert -1.0 - 1e-6 <= r.score <= 1.0 + 1e-6
        assert r.chunk.text
