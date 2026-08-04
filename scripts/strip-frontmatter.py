#!/usr/bin/env python3
"""
strip-frontmatter.py: mirror the corpus with frontmatter removed.

Most real-world markdown carries no frontmatter, so applications testing
against this corpus often need the bare-text path as well. Rather than the
repo shipping a duplicate (drift-prone) content set, this script generates
one: it mirrors the input tree into the output directory with each file's
YAML frontmatter block removed and the body byte-identical, including any
leading blank line the body had after the closing fence.

Usage:
  scripts/strip-frontmatter.py                          # books/ -> books-no-frontmatter/
  scripts/strip-frontmatter.py --output /tmp/bare       # custom output dir
  scripts/strip-frontmatter.py books/ja --output /tmp/j # subtree only

Files without a leading frontmatter fence are copied unchanged. Exits 0 on
success, 1 if any file could not be processed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def strip(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    body = text[end + len("\n---\n"):]
    return body.lstrip("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="books", help="directory to mirror (default: books)")
    parser.add_argument("--output", default="books-no-frontmatter", help="output directory (default: books-no-frontmatter)")
    args = parser.parse_args()

    src = Path(args.source)
    out = Path(args.output)
    if not src.is_dir():
        print(f"error: {src} is not a directory", file=sys.stderr)
        return 1

    count, failures = 0, 0
    for p in sorted(src.rglob("*.md")):
        rel = p.relative_to(src)
        dest = out / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(strip(p.read_text(encoding="utf-8")), encoding="utf-8")
            count += 1
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"FAIL {p}: {e}", file=sys.stderr)
            failures += 1
    print(f"wrote {count} file(s) to {out}" + (f", {failures} failure(s)" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
