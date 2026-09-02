#!/usr/bin/env python3
"""Count whitespace-delimited words in a Lab 1 Playground paste.

Exit 0 if the count is at most 120, else 1. This does not create or replace an
Azure run; paste the real Playground output into a local text file first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LIMIT = 120


def count_words(text: str) -> int:
    return len(text.split())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="count_lab1_words")
    parser.add_argument("path", type=Path, help="UTF-8 file containing the model output only")
    args = parser.parse_args(argv)
    text = args.path.read_text(encoding="utf-8").strip()
    n = count_words(text)
    print(n)
    if n > LIMIT:
        print(f"error: {n} words exceeds the Lab 1 limit of {LIMIT}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
