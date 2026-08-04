#!/usr/bin/env python3
"""
Vendor helper for Internet Archive djvu OCR plain-text sources.

Tuned for the Mariano Azuela "Los de abajo" 1916 Tampico edition
(archive.org/details/azuela-mariano-los-de-abajo). The djvu text is high
quality but carries a few artifacts: bare page-number lines, occasional
OCR confusion between I/l/| in chapter markers, and trailing pre-text
front matter.

Reads a local djvu plain-text file, trims to a body range, normalises
whitespace and page-number lines, promotes chapter markers to H1
headings, and writes a vendor-ready markdown file with YAML frontmatter
matching the existing i18n-books corpus shape.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def trim_range(body: str, start_marker: str | None, end_marker: str | None) -> str:
    if start_marker:
        m = re.search(re.escape(start_marker), body)
        if not m:
            raise SystemExit(f"start_marker not found: {start_marker!r}")
        body = body[m.start():]
    if end_marker:
        m = re.search(re.escape(end_marker), body)
        if not m:
            raise SystemExit(f"end_marker not found: {end_marker!r}")
        body = body[:m.start()]
    return body.strip()


def strip_page_numbers(body: str) -> str:
    """Drop standalone numeric lines that the djvu layer carries through
    from page footers. A line is treated as a page number if it has only
    digits (1-4) optionally surrounded by whitespace."""
    out = []
    for line in body.splitlines():
        if re.fullmatch(r"\s*\d{1,4}\s*", line):
            continue
        out.append(line)
    return "\n".join(out)


def promote_chapter_markers(body: str) -> str:
    """Promote chapter markers to H1. Handles Roman numerals as well as
    the OCR variants 'l' (lowercase L for I) and '|' (vertical bar for
    I). Also promotes PRIMERA / SEGUNDA / TERCERA PARTE."""
    body = re.sub(
        r"^(PRIMERA PARTE|SEGUNDA PARTE|TERCERA PARTE)\s*$",
        r"# \1",
        body,
        flags=re.MULTILINE,
    )
    # Roman numerals plus OCR variants
    body = re.sub(
        r"^([IVXLCDM]+|l|\|)\.?\s*$",
        lambda m: f"# {to_roman(m.group(1))}",
        body,
        flags=re.MULTILINE,
    )
    return body


def to_roman(s: str) -> str:
    if s in ("l", "|"):
        return "I"
    return s


def normalise_whitespace(body: str) -> str:
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing spaces on lines (OCR keeps them)
    body = re.sub(r"[ \t]+\n", "\n", body)
    # Collapse 3+ blank lines to single blank
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="Local djvu .txt path")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True)
    p.add_argument("--year", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--start-marker", help="Body substring to trim to")
    p.add_argument("--end-marker", help="Body substring to trim before")
    args = p.parse_args()

    body = Path(args.input).read_text(encoding="utf-8")
    if args.start_marker or args.end_marker:
        body = trim_range(body, args.start_marker, args.end_marker)
    body = strip_page_numbers(body)
    body = promote_chapter_markers(body)
    body = normalise_whitespace(body)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Internet Archive",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
