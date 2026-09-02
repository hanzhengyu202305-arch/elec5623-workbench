#!/usr/bin/env python3
"""Locally check headings against the 12-section order in the captured brief."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXPECTED_SECTIONS = [
    (1, "Cover and group information"),
    (2, "Executive summary"),
    (3, "Introduction and background"),
    (4, "Problem statement and motivation"),
    (5, "Stakeholders and requirements engineering"),
    (6, "Proposed product and innovation"),
    (7, "Proposed methodology and system design"),
    (8, "Business and product analysis"),
    (9, "Evaluation plan"),
    (10, "Risks, ethics and responsible AI"),
    (11, "Semester plan and team responsibilities"),
    (12, "References"),
]

NUMBERED_H2 = re.compile(r"^## ([1-9][0-9]*)\. (.+?)\s*$", re.MULTILINE)


def numbered_sections(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    return [(int(number), title) for number, title in NUMBERED_H2.findall(text)]


def check(path: Path) -> None:
    actual = numbered_sections(path)
    if actual != EXPECTED_SECTIONS:
        raise ValueError(
            "Proposal numbered H2 sections do not match the captured brief order:\n"
            f"expected={EXPECTED_SECTIONS}\nactual={actual}"
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    default = Path(__file__).resolve().parents[1] / "PROPOSAL_DRAFT.md"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=default)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        check(args.path)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        f"PASS: {args.path} headings locally match the captured brief's "
        "numbered sections 1..12"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
