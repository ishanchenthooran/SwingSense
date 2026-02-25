"""
RAG module public API.

Flow: ingest corpus -> build FAISS index -> retrieve relevant chunks.
Offline usage:
- Build index: `python -m app.rag.ingest --validate`
- Query index: `python -m app.rag.retrieve "your question"`
"""

from app.rag.schemas import Chunk, RetrievedChunk

try:
    from app.rag.retrieve import retrieve
except ImportError:  # pragma: no cover - keep package importable without deps
    retrieve = None  # type: ignore[assignment]

__all__ = ["Chunk", "RetrievedChunk", "retrieve"]
