from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Set, Tuple

import pdfplumber


RAW_ROOT = Path(__file__).parent / "corpus" / "raw"
PROCESSED_ROOT = Path(__file__).parent / "corpus" / "processed"
SUBSET_CHOICES = {"user", "internal", "all"}
MIN_PAGE_WORDS = 40
RUNNING_LINE_THRESHOLD = 0.4


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _iter_pdf_paths(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.pdf") if path.is_file())


def _detect_running_lines(pages: List[str], threshold: float = RUNNING_LINE_THRESHOLD) -> Set[str]:
    """Find lines appearing in the first/last 2 lines of >= threshold fraction of pages."""
    counter: Counter = Counter()
    for text in pages:
        lines = text.strip().splitlines()
        for line in lines[:2] + lines[-2:]:
            stripped = line.strip()
            if stripped:
                counter[stripped] += 1
    min_count = max(2, int(len(pages) * threshold))
    return {line for line, count in counter.items() if count >= min_count}


def _strip_running_lines(text: str, running_lines: Set[str]) -> str:
    return "\n".join(
        line for line in text.splitlines() if line.strip() not in running_lines
    )


def _read_pdf_text(path: Path) -> str:
    raw_pages: List[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            raw_pages.append(page.extract_text() or "")

    non_empty = [p for p in raw_pages if p.strip()]
    running_lines = _detect_running_lines(non_empty)

    pages: List[str] = []
    for text in raw_pages:
        if not text.strip():
            continue
        text = _strip_running_lines(text, running_lines)
        if len(text.split()) >= MIN_PAGE_WORDS:
            pages.append(text)

    return "\n\n".join(pages)


def _convert_pdf(path: Path, raw_root: Path, processed_root: Path, force: bool = False) -> Tuple[bool, Path]:
    relative = path.relative_to(raw_root)
    output_path = processed_root / relative.with_suffix(".txt")
    if output_path.exists() and not force:
        return False, output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = _read_pdf_text(path)
    cleaned = _collapse_whitespace(text)
    output_path.write_text(cleaned, encoding="utf-8")
    return True, output_path


def _targets_for_subset(subset: str) -> List[Tuple[Path, Path]]:
    subset = subset.lower()
    if subset not in SUBSET_CHOICES:
        raise ValueError(f"Invalid subset '{subset}'. Choose from {sorted(SUBSET_CHOICES)}.")

    targets: List[Tuple[Path, Path]] = []
    if subset in {"user", "all"}:
        targets.append((RAW_ROOT / "user", PROCESSED_ROOT / "user"))
    if subset in {"internal", "all"}:
        targets.append((RAW_ROOT / "internal", PROCESSED_ROOT / "internal"))
    return targets


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PDF files to .txt for the RAG corpus.")
    parser.add_argument(
        "--subset",
        choices=sorted(SUBSET_CHOICES),
        default="all",
        help="Subset of PDFs to convert.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-process PDFs even if .txt output already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    targets = _targets_for_subset(args.subset)

    pdfs_found = 0
    converted = 0
    skipped = 0
    failed = 0

    for raw_root, processed_root in targets:
        for pdf_path in _iter_pdf_paths(raw_root):
            pdfs_found += 1
            try:
                did_convert, _ = _convert_pdf(pdf_path, raw_root, processed_root, force=args.force)
                if did_convert:
                    converted += 1
                else:
                    skipped += 1
            except Exception as exc:
                failed += 1
                print(f"Failed to convert {pdf_path}: {exc}")

    print("PDF preprocessing summary")
    print(f"- PDFs found: {pdfs_found}")
    print(f"- converted: {converted}")
    print(f"- skipped: {skipped}")
    print(f"- failed: {failed}")


if __name__ == "__main__":
    main()
