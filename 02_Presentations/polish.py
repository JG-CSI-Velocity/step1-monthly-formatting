"""Deck polish driver -- post-hoc PPTX compliance pass.

Reads a deck, scores each slide, writes a Markdown report. With --apply,
also writes a polished PPTX with safe force-applied fixes (fonts,
near-palette colors). Never rewrites headlines or annotations.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="polish",
        description="Post-hoc PPTX polish pass (SLIDE_MAPPING.md compliance).",
    )
    p.add_argument("deck", nargs="?", type=Path, help="Path to input .pptx")
    p.add_argument("--batch", type=Path, help="Process every .pptx in this folder")
    p.add_argument(
        "--apply", action="store_true",
        help="Write polished PPTX (default is dry-run: report only)"
    )
    p.add_argument(
        "--report-only", action="store_true",
        help="Skip force-apply fixes; emit report only (implied by dry-run)"
    )
    p.add_argument("--out", type=Path, default=None, help="Output directory")
    p.add_argument(
        "--strict", action="store_true",
        help="Exit non-zero if any slide scores <2 on any axis"
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.batch is None and args.deck is None:
        logger.error("Provide a deck path or --batch <dir>")
        return 2
    logger.info(f"polish.py invoked (apply={args.apply}, strict={args.strict})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
