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
from typing import List

from app.rag.retrieve import retrieve
from app.rag.store import DEFAULT_TOP_K
from app.rag.toc_filter import is_toc_like

MIN_TOP1_SCORE = 0.5
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


@dataclass(frozen=True)
class QueryCheck:
    query: str
    top1_score: float
    toc_chunk_ids: List[str]

    @property
    def passed(self) -> bool:
        return self.top1_score >= MIN_TOP1_SCORE and not self.toc_chunk_ids


def evaluate_query(query: str, k: int = K) -> QueryCheck:
    results = retrieve(query, k=k)
    if not results:
        return QueryCheck(query=query, top1_score=0.0, toc_chunk_ids=[])

    top1_score = results[0].score
    toc_chunk_ids = [r.chunk.id for r in results if is_toc_like(r.chunk.text)]
    return QueryCheck(query=query, top1_score=top1_score, toc_chunk_ids=toc_chunk_ids)


def _print_report(checks: List[QueryCheck]) -> None:
    print(f"Retrieval validation ({len(checks)} queries, k={K}, min top-1 score={MIN_TOP1_SCORE})")
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"- [{status}] top1={check.top1_score:.4f} | toc_chunks={check.toc_chunk_ids} | {check.query}")


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
