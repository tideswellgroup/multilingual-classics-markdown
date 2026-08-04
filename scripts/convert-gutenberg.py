#!/usr/bin/env python3
"""
convert-gutenberg.py: fetch a Project Gutenberg plain-text edition and convert
to vendor-ready markdown for the multilingual-classics-markdown corpus.

Strips Gutenberg header / footer boilerplate, optionally trims to a sub-range
(for collection editions where we want one story), prepends a YAML frontmatter
block with attribution and license posture, and writes the result.

Not a general-purpose Gutenberg converter. Tuned for the v1 corpus picks where
plain-text quality is high and chapter markup can be left implicit.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
import urllib.request
from pathlib import Path

GUT_START = re.compile(r"^\s*\*+\s*START OF (THE|THIS) PROJECT GUTENBERG.*\*+\s*$", re.IGNORECASE | re.MULTILINE)
GUT_END = re.compile(r"^\s*\*+\s*END OF (THE|THIS) PROJECT GUTENBERG.*\*+\s*$", re.IGNORECASE | re.MULTILINE)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    return raw.decode("utf-8")


def strip_gutenberg_boilerplate(text: str) -> str:
    start = GUT_START.search(text)
    end = GUT_END.search(text)
    if not start or not end:
        raise ValueError("Gutenberg START/END markers not found")
    body = text[start.end() : end.start()]
    body = strip_producer_credit(body)
    return body.strip()


def strip_producer_credit(body: str) -> str:
    """Remove the 'Produced by ...' transcriber credit block that PG inserts
    after the START marker. It's typically 1-4 lines beginning with 'Produced
    by' and ending before the first run of blank lines preceding the title."""
    pattern = re.compile(r"\A\s*Produced by [^\n]*(?:\n[^\n]+)*?\n\s*\n", flags=re.IGNORECASE)
    return pattern.sub("", body, count=1)


def strip_leading_whitespace(body: str) -> str:
    """PG plain text centres title-page lines with leading spaces. Markdown
    treats 4+ leading spaces as a code block, which mis-renders centred
    headings as code. Strip leading whitespace from every line so title-page
    blocks render as plain prose. Body prose is already flush-left so this is
    a no-op for the bulk of the document."""
    return "\n".join(line.lstrip() for line in body.splitlines())


def promote_chapter_markers(body: str, pattern: str | None) -> str:
    """Promote lines matching the chapter pattern to H1 markdown headings.
    Default pattern matches bare Roman numerals with optional trailing period.
    Pass --chapter-pattern '' to disable; pass a custom pattern for non-Roman
    chapter conventions (e.g. 'Tratado [a-z]+' for Lazarillo)."""
    if pattern is None:
        pattern = r"[IVXLCDM]+\.?"
    if not pattern:
        return body
    rx = re.compile(rf"^({pattern})\s*$", flags=re.MULTILINE | re.IGNORECASE)
    return rx.sub(lambda m: f"# {m.group(1).rstrip('.')}", body)


def trim_range(body: str, start_marker: str | None, end_marker: str | None) -> str:
    if start_marker:
        m = re.search(re.escape(start_marker), body)
        if not m:
            raise ValueError(f"start_marker not found: {start_marker!r}")
        body = body[m.start() :]
    if end_marker:
        m = re.search(re.escape(end_marker), body)
        if not m:
            raise ValueError(f"end_marker not found: {end_marker!r}")
        body = body[: m.start()]
    return body.strip()


def normalise_whitespace(body: str) -> str:
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = re.sub(r"[ \t]+\n", "\n", body)
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


def convert(args) -> None:
    text = fetch_text(args.url)
    body = strip_gutenberg_boilerplate(text)
    if args.start_marker or args.end_marker:
        body = trim_range(body, args.start_marker, args.end_marker)
    body = strip_leading_whitespace(body)
    body = promote_chapter_markers(body, args.chapter_pattern)
    body = normalise_whitespace(body)
    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Project Gutenberg",
        "source_url": args.url,
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines)")


def main() -> int:
    p = argparse.ArgumentParser(description=textwrap.dedent(__doc__))
    p.add_argument("--url", required=True, help="Project Gutenberg plain-text URL")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 tag (e.g. de, fr, es, ru)")
    p.add_argument("--year", required=True, help="Original publication year")
    p.add_argument("--output", required=True, help="Output markdown path")
    p.add_argument("--start-marker", help="Body-text substring to trim to (for collections)")
    p.add_argument("--end-marker", help="Body-text substring to trim before")
    p.add_argument(
        "--chapter-pattern",
        default=None,
        help="Regex matching chapter markers to promote to H1 headings. "
        "Default: bare Roman numerals with optional period. "
        "Pass empty string to disable. Custom example: 'Tratado [a-záéíóú]+'",
    )
    args = p.parse_args()
    convert(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
