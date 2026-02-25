from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Chunk:
    id: str
    text: str
    source: str = "unknown"
    title: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
