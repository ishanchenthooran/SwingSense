"""Pattern-based detection of table-of-contents / index style text.

The 40-word page-length filter in preprocess_pdfs.py does not catch TOC or
back-of-book index pages: they're often long enough in word count, but their
lines are dominated by numeric page-leaders ("Rule 6 - Playing a Hole 59"),
dotted leaders ("Intro .......... 6"), or bare page numbers rather than prose.
This module classifies a block of text as TOC-like by the fraction of its
lines that match those shapes, so it can be dropped at both the page level
(preprocess_pdfs.py) and the paragraph-block level (ingest.py), independent
of raw word count.
"""

from __future__ import annotations

import re

TOC_LINE_RATIO_THRESHOLD = 0.5
MIN_LINES_TO_CLASSIFY = 2

_BARE_PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
_PIPE_TOC_RE = re.compile(r"^\d{1,4}\s*\|\s*.*$|^\|\s*.+$|^.+?\s*\|\s*\d{1,4}$")
_DOTTED_LEADER_RE = re.compile(r"^.{2,}?\.{3,}\s*\d{1,4}$")
_RULE_INDEX_PREFIX_RE = re.compile(
    r"^(?:Rule\s+\d+(?:\.\d+)*\b|[IVXLC]+\.\s|\d+(?:\.\d+)+\b)",
    re.IGNORECASE,
)
_TRAILING_NUM_RE = re.compile(r"\d{1,4}$")
_SPACED_LEADER_RE = re.compile(r"^.{3,}?\s\d{1,4}$")


def _is_toc_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _BARE_PAGE_NUM_RE.match(stripped):
        return True
    if _PIPE_TOC_RE.match(stripped):
        return True
    if _DOTTED_LEADER_RE.match(stripped):
        return True
    if _RULE_INDEX_PREFIX_RE.match(stripped) and _TRAILING_NUM_RE.search(stripped):
        return True
    if _SPACED_LEADER_RE.match(stripped):
        return True
    return False


def is_toc_like(
    text: str,
    threshold: float = TOC_LINE_RATIO_THRESHOLD,
    min_lines: int = MIN_LINES_TO_CLASSIFY,
) -> bool:
    """True if >= threshold fraction of text's non-empty lines look like TOC/index entries."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < min_lines:
        return False
    toc_count = sum(1 for line in lines if _is_toc_line(line))
    return (toc_count / len(lines)) >= threshold
