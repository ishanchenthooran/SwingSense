from __future__ import annotations

import argparse
import os
from typing import List

import faiss
import numpy as np
from openai import OpenAI

from app.core.config import settings
from app.rag.schemas import Chunk, RetrievedChunk
from app.rag.store import load_index_and_metadata


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


def retrieve(query: str, k: int = 5) -> List[RetrievedChunk]:
    if not query.strip():
        return []

    try:
        index, chunks = load_index_and_metadata()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Missing index artifacts. Run `python -m app.rag.ingest` first."
        ) from exc

    query_vector = embed_query(query).reshape(1, -1)
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
    url = chunk.url or "n/a"
    tags = ", ".join(chunk.tags) if chunk.tags else "n/a"
    return (
        f"- score={result.score:.4f} | chunk_id={chunk.id} | title={title} | "
        f"source={source} | url={url} | tags={tags} | text={preview}"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrieve chunks from FAISS index.")
    parser.add_argument("query", type=str, help="Query text to retrieve against.")
    parser.add_argument("--k", type=int, default=5, help="Number of results to return.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = retrieve(args.query, k=args.k)
    print(f"Top {min(args.k, len(results))} results")
    for result in results:
        print(_format_result(result))


if __name__ == "__main__":
    main()
