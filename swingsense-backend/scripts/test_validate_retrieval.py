"""CI-facing pytest wrapper around the retrieval quality gate.

Each fixed question is its own test case so a regression shows exactly which
query dropped below the score bar or started surfacing TOC-like content,
rather than one opaque pass/fail for the whole set.
"""

from __future__ import annotations

import pytest

from scripts.validate_retrieval import QUESTIONS, evaluate_query, min_score_for


@pytest.mark.parametrize("question", QUESTIONS)
def test_retrieval_quality(question: str) -> None:
    check = evaluate_query(question)

    floor = min_score_for(question)
    assert check.top1_score >= floor, (
        f"Top-1 score {check.top1_score:.4f} below {floor} for query: {question!r}"
    )
    assert check.source_ok, f"Unexpected top-1 source {check.top1_source!r} for query: {question!r}"
    assert not check.toc_chunk_ids, (
        f"TOC-like chunk(s) {check.toc_chunk_ids} leaked into top-5 for query: {question!r}"
    )
