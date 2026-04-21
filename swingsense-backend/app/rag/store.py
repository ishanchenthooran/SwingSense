from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import faiss

from app.rag.schemas import Chunk


DEFAULT_INDEX_DIR = Path(__file__).parent / "index"


def _ensure_dir(index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)


def save_index(index: faiss.Index, chunks: List[Chunk], index_dir: Path = DEFAULT_INDEX_DIR) -> None:
    """
    Saves FAISS index + chunk metadata side-by-side.
    - app/rag/index/faiss.index
    - app/rag/index/chunks.json
    """
    _ensure_dir(index_dir)

    faiss_path = index_dir / "faiss.index"
    chunks_path = index_dir / "chunks.json"

    faiss.write_index(index, str(faiss_path))

    chunks_payload = [chunk.__dict__ for chunk in chunks]
    chunks_path.write_text(json.dumps(chunks_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(index_dir: Path = DEFAULT_INDEX_DIR) -> Tuple[faiss.Index, List[Chunk]]:
    """
    Loads FAISS index + chunk metadata.
    Raises FileNotFoundError if artifacts aren't built yet.
    """
    faiss_path = index_dir / "faiss.index"
    chunks_path = index_dir / "chunks.json"

    if not faiss_path.exists():
        raise FileNotFoundError(f"Missing FAISS index at {faiss_path}. Run ingestion first.")
    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing chunks metadata at {chunks_path}. Run ingestion first.")

    index = faiss.read_index(str(faiss_path))

    raw = json.loads(chunks_path.read_text(encoding="utf-8"))
    chunks = [Chunk(**item) for item in raw]

    return index, chunks


def load_index_and_metadata(index_dir: Path = DEFAULT_INDEX_DIR) -> Tuple[faiss.Index, List[Chunk]]:
    """
    Backwards-compatible alias for loading FAISS index + chunk metadata.
    """
    return load_index(index_dir=index_dir)
