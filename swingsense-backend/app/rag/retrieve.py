from __future__ import annotations

import argparse
import os
from typing import List

import faiss
import numpy as np
from openai import OpenAI

from app.core.config import settings
from app.rag.schemas import Chunk, RetrievedChunk
from app.rag.store import DEFAULT_TOP_K, load_index


EMBED_MODEL = "text-embedding-3-small"


def _require_openai_api_key() -> str:
    api_key = (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")).strip()
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY. Set it before running retrieval.")
    return api_key


def embed_query(text: str) -> np.ndarray:
    if not text.strip():
        raise ValueError("Query text must be non-empty for embedding.")
    api_key = _require_openai_api_key()
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=EMBED_MODEL, input=[text])
    vector = np.array(response.data[0].embedding, dtype="float32")
    if vector.ndim != 1:
        raise ValueError("Query embedding is not 1D as expected.")
    return vector


def _embed_query_for_retrieval(query: str) -> np.ndarray:
    """Embed a query for retrieval, boosting bare/short queries that lack
    golf context.

    Short queries like "How do I fix a slice?" score ~0.2 cosine lower than
    the same question with "golf" in it, purely from embedding-model
    behavior against paragraph-sized corpus chunks. Simply replacing the
    query text with "golf " + query fixes that score gap but can overcorrect:
    for "unplayable lie", it raises the top-1 score from 0.39 to 0.56 but
    *changes which document wins*, from the correct Golf-Rules chunk to an
    unrelated glossary chunk in a different book. Averaging the raw query's
    embedding with the "golf "-prefixed one keeps the correct source in that
    case (0.49, still Golf-Rules) while still recovering most of the score
    boost for queries where the raw embedding was already pointing at the
    right chunk (e.g. "fix my slice" still lands correctly at 0.58, up from
    ~0.36 with no boost at all).
    """
    if "golf" in query.lower():
        return embed_query(query)
    raw = embed_query(query)
    boosted = embed_query(f"golf {query}")
    return (raw + boosted) / 2.0


def retrieve(query: str, k: int = DEFAULT_TOP_K) -> List[RetrievedChunk]:
    if not query.strip():
        return []

    try:
        index, chunks = load_index()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Missing index artifacts. Run `python -m app.rag.ingest` first."
        ) from exc

    query_vector = _embed_query_for_retrieval(query).reshape(1, -1)
    faiss.normalize_L2(query_vector)

    scores, indices = index.search(query_vector, k)
    results: List[RetrievedChunk] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        if idx < 0 or idx >= len(chunks):
            continue
        chunk = chunks[idx]
        results.append(RetrievedChunk(chunk=chunk, score=float(score)))
    return results


def _format_result(result: RetrievedChunk) -> str:
    chunk: Chunk = result.chunk
    title = chunk.title or "Untitled"
    preview = chunk.text.replace("\n", " ")[:160]
    source = chunk.source or "unknown"
    page = chunk.page if chunk.page is not None else "n/a"
    url = chunk.url or "n/a"
    tags = ", ".join(chunk.tags) if chunk.tags else "n/a"
    return (
        f"- score={result.score:.4f} | chunk_id={chunk.id} | title={title} | "
        f"source={source} | page={page} | url={url} | tags={tags} | text={preview}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrieve chunks from FAISS index.")
    parser.add_argument("query", type=str, help="Query text to retrieve against.")
    parser.add_argument("--k", type=int, default=DEFAULT_TOP_K, help="Number of results to return.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = retrieve(args.query, k=args.k)
    print(f"Top {min(args.k, len(results))} results")
    for result in results:
        print(_format_result(result))


if __name__ == "__main__":
    main()
