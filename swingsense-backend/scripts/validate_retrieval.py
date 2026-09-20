"""RAG retrieval quality gate.

Runs a fixed set of real golf questions against the FAISS index and checks
two things per query:
  1. The top-1 result's cosine similarity score is >= MIN_TOP1_SCORE.
  2. None of the top-K results look like table-of-contents/index content
     (reuses the same classifier ingest.py/preprocess_pdfs.py use to drop
     TOC pages/blocks, as a regression check on the live index).

Run standalone:
    python -m scripts.validate_retrieval

Run via pytest (see scripts/test_validate_retrieval.py):
    pytest scripts/test_validate_retrieval.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

from app.rag.retrieve import retrieve
from app.rag.store import DEFAULT_TOP_K
from app.rag.toc_filter import is_toc_like

MIN_TOP1_SCORE = 0.5
# Short/colloquial queries ("How do I fix a slice?") embed with systematically
# lower cosine scores than full questions even when the right chunk is ranked
# first: text-embedding-3-small scores a bare query against ~1000-char chunks
# lower, and dropping the word "golf" costs another ~0.2 (0.36 without it vs
# 0.60 with "...in golf?"). Chunk size is not the cause. Rather than lower the
# gate for everything, short queries get a lower score floor PLUS a stricter
# check that top-1 comes from a source that should answer them, so the gate
# still fails on genuinely wrong retrievals. Real fix (needs a retrieve.py
# change, out of scope here): prefix bare queries with "golf" before embedding.
MIN_TOP1_SCORE_SHORT = 0.3
K = DEFAULT_TOP_K

QUESTIONS: List[str] = [
    "Why does my golf ball slice to the right?",
    "What is the correct golf grip?",
    "How should I set up my stance before swinging?",
    "What are the rules for a lost ball?",
    "How do I hit a bunker shot?",
    "What is a proper golf swing tempo?",
    "How do I chip the ball close to the hole?",
    "What causes a hook shot?",
    "How many penalty strokes for an unplayable lie?",
    "How do I improve my putting accuracy?",
    "What is the takeaway in the golf backswing?",
    "How do I practice my short game?",
    "What should my golf swing sequence look like at impact?",
    "What are the rules for taking relief from a penalty area?",
    "How can older golfers adjust their swing for less flexibility?",
]

# short/colloquial phrasing -> substring(s) one of which must appear in the
# top-1 chunk's source path.
SHORT_QUERIES: Dict[str, Tuple[str, ...]] = {
    "How do I fix a slice?": ("Golf-Hacks", "Over50", "Intro-Golf"),
    "fix my slice": ("Golf-Hacks", "Over50", "Intro-Golf"),
    "How do I stop hooking the ball?": ("Golf-Hacks", "Over50", "Intro-Golf"),
    "how to grip": ("Over50", "Intro-Golf", "Golf-Hacks"),
    "How do I get out of a bunker?": ("ShortGame", "Intro-Golf", "Golf-Hacks", "Golf-Rules"),
    "putting tips": ("Golf-Hacks", "ShortGame", "Intro-Golf", "Drills"),
    "What if I lose my ball?": ("Golf-Rules", "Intro-Golf"),
    "unplayable lie": ("Golf-Rules",),
    "how to chip": ("ShortGame", "Intro-Golf", "Golf-Hacks"),
}
QUESTIONS.extend(SHORT_QUERIES)


def min_score_for(query: str) -> float:
    return MIN_TOP1_SCORE_SHORT if query in SHORT_QUERIES else MIN_TOP1_SCORE


@dataclass(frozen=True)
class QueryCheck:
    query: str
    top1_score: float
    toc_chunk_ids: List[str]
    top1_source: str = ""

    @property
    def source_ok(self) -> bool:
        expected = SHORT_QUERIES.get(self.query)
        return expected is None or any(e in self.top1_source for e in expected)

    @property
    def passed(self) -> bool:
        return (
            self.top1_score >= min_score_for(self.query)
            and self.source_ok
            and not self.toc_chunk_ids
        )


def evaluate_query(query: str, k: int = K) -> QueryCheck:
    results = retrieve(query, k=k)
    if not results:
        return QueryCheck(query=query, top1_score=0.0, toc_chunk_ids=[])

    top1_score = results[0].score
    toc_chunk_ids = [r.chunk.id for r in results if is_toc_like(r.chunk.text)]
    return QueryCheck(
        query=query,
        top1_score=top1_score,
        toc_chunk_ids=toc_chunk_ids,
        top1_source=results[0].chunk.source or "",
    )


def _print_report(checks: List[QueryCheck]) -> None:
    print(f"Retrieval validation ({len(checks)} queries, k={K}, min top-1 score={MIN_TOP1_SCORE}, short queries {MIN_TOP1_SCORE_SHORT})")
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"- [{status}] top1={check.top1_score:.4f} | toc_chunks={check.toc_chunk_ids} | {check.query} -> {check.top1_source}")


def main() -> int:
    checks = [evaluate_query(query) for query in QUESTIONS]
    _print_report(checks)
    failed = [c for c in checks if not c.passed]
    if failed:
        print(f"\n{len(failed)}/{len(checks)} queries failed the retrieval quality gate.")
        return 1
    print(f"\nAll {len(checks)} queries passed the retrieval quality gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
