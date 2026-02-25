from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import faiss
import numpy as np
from openai import OpenAI

from app.core.config import settings
from app.rag.schemas import Chunk
from app.rag.store import DEFAULT_INDEX_DIR, load_index_and_metadata, save_index


EMBED_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_K = 3
CORPUS_DIR = Path("app/rag/corpus")


@dataclass(frozen=True)
class Document:
    path: Path
    title: str
    text: str


def _require_openai_api_key() -> str:
    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in settings. Set it before running ingestion.")
    return api_key


def _load_corpus(corpus_dir: Path) -> List[Document]:
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    documents: List[Document] = []
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue

        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        title = _infer_title(path, text)
        documents.append(Document(path=path, title=title, text=text))

    if not documents:
        raise ValueError(f"No .md or .txt files found in {corpus_dir}")

    return documents


def _infer_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
        return stripped[:80]
    return path.stem


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def _build_chunks(documents: Sequence[Document]) -> List[Chunk]:
    chunks: List[Chunk] = []
    chunk_id = 0
    for doc in documents:
        for segment in _chunk_text(doc.text, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP):
            chunks.append(
                Chunk(
                    id=str(chunk_id),
                    text=segment,
                    source=str(doc.path),
                    title=doc.title,
                )
            )
            chunk_id += 1
    return chunks


def _embed_texts(client: OpenAI, texts: Sequence[str], model: str) -> np.ndarray:
    vectors: List[List[float]] = []
    batch_size = 96
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(model=model, input=batch)
        batch_vectors = [item.embedding for item in response.data]
        vectors.extend(batch_vectors)
    array = np.array(vectors, dtype="float32")
    if array.ndim != 2:
        raise ValueError("Embedding output is not 2D as expected.")
    return array


def _normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    if vectors.dtype != np.float32:
        vectors = vectors.astype("float32")
    faiss.normalize_L2(vectors)
    return vectors


def _build_index(vectors: np.ndarray) -> faiss.Index:
    dimension = vectors.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)
    return index


def _print_summary(
    documents_count: int,
    chunks_count: int,
    embedding_dim: int,
    index_total: int,
    metadata_total: int,
) -> None:
    print("Ingestion validation summary")
    print(f"- docs count: {documents_count}")
    print(f"- chunks count: {chunks_count}")
    print(f"- embedding dim: {embedding_dim}")
    print(f"- index.ntotal: {index_total}")
    print(f"- metadata chunk count: {metadata_total}")


def _print_results(results: Sequence[Tuple[float, Chunk]], k: int) -> None:
    print(f"Sample retrieval results (top {k})")
    for score, chunk in results:
        preview = chunk.text.replace("\n", " ")[:120]
        title = chunk.title or "Untitled"
        print(f"- score={score:.4f} | chunk_id={chunk.id} | title={title} | text={preview}")


def _run_validation(
    client: OpenAI,
    index_dir: Path,
    embedding_dim: int,
    query: str,
    k: int,
    documents_count: int,
    chunks_count: int,
) -> None:
    index, chunks_loaded = load_index_and_metadata(index_dir=index_dir)

    if index.ntotal != len(chunks_loaded):
        raise AssertionError(
            f"Index total {index.ntotal} does not match metadata count {len(chunks_loaded)}."
        )
    if index.d != embedding_dim:
        raise AssertionError(
            f"Index dimension {index.d} does not match embedding dimension {embedding_dim}."
        )

    response = client.embeddings.create(model=EMBED_MODEL, input=[query])
    query_vector = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(query_vector)
    print("Normalized query vector before cosine similarity search.")

    scores, indices = index.search(query_vector, k)
    results: List[Tuple[float, Chunk]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(chunks_loaded):
            continue
        results.append((float(score), chunks_loaded[idx]))

    _print_summary(
        documents_count=documents_count,
        chunks_count=chunks_count,
        embedding_dim=embedding_dim,
        index_total=index.ntotal,
        metadata_total=len(chunks_loaded),
    )
    _print_results(results, k=k)


def ingest(validate: bool = False, k: int = DEFAULT_K) -> None:
    api_key = _require_openai_api_key()
    client = OpenAI(api_key=api_key)

    documents = _load_corpus(CORPUS_DIR)
    chunks = _build_chunks(documents)
    if not chunks:
        raise ValueError("No chunks created from corpus.")

    texts = [chunk.text for chunk in chunks]
    vectors = _embed_texts(client, texts, EMBED_MODEL)
    print("Normalizing document embeddings for cosine similarity.")
    vectors = _normalize_vectors(vectors)

    index = _build_index(vectors)
    save_index(index, chunks, index_dir=DEFAULT_INDEX_DIR)
    print(f"Saved FAISS index and metadata to {DEFAULT_INDEX_DIR}.")

    if validate:
        _run_validation(
            client=client,
            index_dir=DEFAULT_INDEX_DIR,
            embedding_dim=vectors.shape[1],
            query="What is SwingSense and how does it use FAISS cosine similarity?",
            k=k,
            documents_count=len(documents),
            chunks_count=len(chunks),
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest RAG corpus into FAISS index.")
    parser.add_argument(
        "--validate",
        action="store_true",
        default=False,
        help="Run post-ingestion validation checks.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=DEFAULT_K,
        help="Number of results to print for validation sample query.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    ingest(validate=args.validate, k=args.k)


if __name__ == "__main__":
    main()
