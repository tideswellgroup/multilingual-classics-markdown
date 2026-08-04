#!/usr/bin/env python3
"""
check-verse-breaks.py: detector for soft-wrapped verse.

Flags files containing runs of consecutive short lines separated by bare
single newlines with no CommonMark hard break (trailing two spaces). In
markdown, such lines MERGE into prose when rendered; verse converted this
way displays as a prose wall. The corpus convention (see FRONTMATTER.md
§Verse) is a two-space hard break on every verse line within a stanza and
blank lines between stanzas.

A flag is a LEAD, not a verdict: hard-wrapped prose (source text wrapped at
a column width) legitimately merges and should be left alone, so every flag
needs a human judgment about whether the line structure is semantic. The
line-break repair campaign (2026-07-17) found both real verse walls and
correct hard-wrapped prose among flagged files in roughly equal measure.

Usage:
  scripts/check-verse-breaks.py                # scan books/
  scripts/check-verse-breaks.py books/xx/      # scan a subtree or file
  scripts/check-verse-breaks.py --max-line 50  # tune the short-line bound

Exits 0 when nothing is flagged, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def scan(path: Path, max_line: int, min_run: int, min_runs: int):
    body = path.read_text(encoding="utf-8")
    if body.startswith("---\n") and "\n---\n" in body[4:]:
        body = body.split("\n---\n", 1)[1]
    run = 0
    max_run = 0
    runs = 0
    for raw in body.split("\n"):
        line = raw.rstrip("\n")
        s = line.strip()
        is_verse_suspect = (
            s
            and not s.startswith("#")
            and len(s) < max_line
            and not line.endswith("  ")
            and not line.endswith("\\")
        )
        if is_verse_suspect:
            run += 1
            max_run = max(max_run, run)
        else:
            if run >= min_run:
                runs += 1
            run = 0
    if run >= min_run:
        runs += 1
    return runs, max_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["books"], help="files or directories (default: books/)")
    parser.add_argument("--max-line", type=int, default=65, help="short-line bound in characters (default: 65)")
    parser.add_argument("--min-run", type=int, default=4, help="consecutive suspect lines forming a run (default: 4)")
    parser.add_argument("--min-runs", type=int, default=3, help="runs required to flag a file (default: 3)")
    args = parser.parse_args()

    targets = []
    for raw in args.paths:
        p = Path(raw)
        targets.extend(sorted(p.rglob("*.md")) if p.is_dir() else [p])

    flagged = 0
    for p in targets:
        runs, max_run = scan(p, args.max_line, args.min_run, args.min_runs)
        if runs >= args.min_runs:
            flagged += 1
            print(f"SUSPECT runs={runs:4} maxrun={max_run:4}  {p}")
    print(f"done: {flagged} suspect of {len(targets)} scanned (flags are leads, not verdicts)")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
