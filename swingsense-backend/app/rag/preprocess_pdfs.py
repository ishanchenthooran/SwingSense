from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from pypdf import PdfReader


RAW_ROOT = Path(__file__).parent / "corpus" / "raw"
PROCESSED_ROOT = Path(__file__).parent / "corpus" / "processed"
SUBSET_CHOICES = {"user", "internal", "all"}


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _iter_pdf_paths(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.pdf") if path.is_file())


def _read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _convert_pdf(path: Path, raw_root: Path, processed_root: Path) -> Tuple[bool, Path]:
    relative = path.relative_to(raw_root)
    output_path = processed_root / relative.with_suffix(".txt")
    if output_path.exists():
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
                did_convert, _ = _convert_pdf(pdf_path, raw_root, processed_root)
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
