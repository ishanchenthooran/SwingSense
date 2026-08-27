from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import faiss
import numpy as np
from openai import OpenAI

from app.core.config import settings
from app.rag.schemas import Chunk
from app.rag.store import DEFAULT_INDEX_DIR, DEFAULT_TOP_K, load_index_and_metadata, save_index
from app.rag.toc_filter import is_toc_like


EMBED_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 100  # only used in hard-split fallback for oversized sentences
CORPUS_DIR = Path(__file__).parent / "corpus"
_PAGE_MARKER_RE = re.compile(r"^\[\[PAGE (\d+)\]\]\s*\n?")


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
        if not stripped or _PAGE_MARKER_RE.match(stripped):
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
        return stripped[:80]
    return path.stem


def _chunk_text(
    text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Tuple[str, Optional[int]]]:
    """Split text on page boundaries (\n\n), then fall back to sentence-aware splitting
    for blocks that exceed chunk_size. overlap is only used when a single sentence itself
    exceeds chunk_size and must be hard-split.

    Each returned segment is paired with the page number of the block it came from
    (parsed from the "[[PAGE N]]" markers preprocess_pdfs.py inserts). A block that
    itself gets split into multiple chunks has all of its pieces tagged with that
    block's starting page — approximate, not precise, for blocks that straddle pages."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

    current_page: Optional[int] = None
    blocks: List[Tuple[str, Optional[int]]] = []
    for block in raw_blocks:
        match = _PAGE_MARKER_RE.match(block)
        if match:
            current_page = int(match.group(1))
            block = _PAGE_MARKER_RE.sub("", block, count=1).strip()
        if not block or is_toc_like(block):
            continue
        blocks.append((block, current_page))

    chunks: List[Tuple[str, Optional[int]]] = []
    for block, page in blocks:
        if len(block) <= chunk_size:
            chunks.append((block, page))
            continue

        # Sentence-aware split for long blocks
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", block)
        current = ""
        for sentence in sentences:
            if not current:
                current = sentence
            elif len(current) + 1 + len(sentence) <= chunk_size:
                current = current + " " + sentence
            else:
                chunks.append((current, page))
                if len(sentence) > chunk_size:
                    # Hard-split oversized single sentence with overlap
                    start = 0
                    while start < len(sentence):
                        chunks.append((sentence[start : start + chunk_size], page))
                        start += chunk_size - overlap
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append((current, page))

    return [(c, p) for c, p in chunks if c.strip()]


def _build_chunks(documents: Sequence[Document]) -> List[Chunk]:
    chunks: List[Chunk] = []
    chunk_id = 0
    for doc in documents:
        for segment, page in _chunk_text(doc.text):
            chunks.append(
                Chunk(
                    id=str(chunk_id),
                    text=segment,
                    source=doc.path.relative_to(CORPUS_DIR).as_posix(),
                    title=doc.title,
                    page=page,
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
        page = chunk.page if chunk.page is not None else "n/a"
        print(f"- score={score:.4f} | chunk_id={chunk.id} | title={title} | page={page} | text={preview}")


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


def ingest(validate: bool = False, k: int = DEFAULT_TOP_K) -> None:
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
        default=DEFAULT_TOP_K,
        help="Number of results to print for validation sample query.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    ingest(validate=args.validate, k=args.k)


if __name__ == "__main__":
    main()
