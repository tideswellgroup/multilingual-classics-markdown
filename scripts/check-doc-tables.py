#!/usr/bin/env python3
"""
check-doc-tables.py: catch Markdown tables that split when rendered.

A table nested in a list item must indent every row to the item's content
column. When a later row is added at column zero, GitHub ends the table at
the last indented row and prints the rest as a run of pipe-separated text.
Nothing looks wrong in the source or in a plain diff, which is how the
README's transmission-base table came to render four of its eight books as
prose.

The rule checked: within a run of consecutive table rows (lines whose first
non-space character is a pipe), every row has the same indentation. Fenced
code blocks are skipped. The books are not checked; lint-corpus.py covers
them, and this gate covers the repository's own documents.

Usage:
  python3 scripts/check-doc-tables.py            # verify, exit 1 on a split table
  python3 scripts/check-doc-tables.py --quiet    # print nothing on success

Exit codes: 0 clean, 1 split table found, 2 could not list the documents.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLE_ROW = re.compile(r"^( *)\|")
FENCE = re.compile(r"^ *(```|~~~)")


def tracked_docs() -> list[Path]:
    """Every tracked Markdown file outside books/."""
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md", ":!books/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [REPO_ROOT / name for name in out.split("\0") if name]


def split_rows(text: str) -> list[tuple[int, int, int]]:
    """Return (line, indent, previous_indent) for each row that breaks its table."""
    problems = []
    in_fence = False
    prev_indent: int | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            prev_indent = None
            continue
        match = None if in_fence else TABLE_ROW.match(line)
        if match is None:
            prev_indent = None
            continue
        indent = len(match.group(1))
        if prev_indent is not None and indent != prev_indent:
            problems.append((number, indent, prev_indent))
        prev_indent = indent
    return problems


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv

    try:
        docs = tracked_docs()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"check-doc-tables: could not list tracked documents: {exc}", file=sys.stderr)
        return 2

    found = 0
    for path in docs:
        for line, indent, prev in split_rows(path.read_text(encoding="utf-8")):
            found += 1
            print(
                f"  {path.relative_to(REPO_ROOT)}:{line}: table row indented {indent}, "
                f"the row above {prev}; GitHub will end the table here",
                file=sys.stderr,
            )

    if found:
        print(f"check-doc-tables: {found} split table row(s)", file=sys.stderr)
        return 1

    if not quiet:
        print(f"check-doc-tables: tables consistent in {len(docs)} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
