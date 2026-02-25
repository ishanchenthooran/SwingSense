from __future__ import annotations

from typing import List, Sequence, Tuple

import faiss
import numpy as np

from app.rag.retrieve import embed_query
from app.rag.schemas import Chunk
from app.rag.store import load_index_and_metadata


DEFAULT_QUERIES = [
    "What is SwingSense and how does it use FAISS cosine similarity?",
    "How do I build and validate the RAG index?",
    "Where is the training plan or progress tracked?",
]


def _format_result(score: float, chunk: Chunk) -> str:
    title = chunk.title or "Untitled"
    preview = chunk.text.replace("\n", " ")[:120]
    return f"- score={score:.4f} | chunk_id={chunk.id} | title={title} | text={preview}"


def _run_query(index: faiss.Index, chunks: Sequence[Chunk], query: str, k: int = 3) -> List[str]:
    query_vector = embed_query(query).astype("float32").reshape(1, -1)
    faiss.normalize_L2(query_vector)
    scores, indices = index.search(query_vector, k)
    results: List[Tuple[float, Chunk]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        if idx < 0 or idx >= len(chunks):
            continue
        results.append((float(score), chunks[idx]))
    return [_format_result(score, chunk) for score, chunk in results]


def main() -> None:
    try:
        index, chunks = load_index_and_metadata()
    except FileNotFoundError:
        print("Missing index artifacts. Run `python -m app.rag.ingest --validate` first.")
        return

    for query in DEFAULT_QUERIES:
        print(f"\nQuery: {query}")
        for line in _run_query(index, chunks, query, k=3):
            print(line)


if __name__ == "__main__":
    main()
