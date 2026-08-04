#!/usr/bin/env python3
"""
convert-internet-archive.py: convert OCR plain text from Internet Archive
djvu.txt downloads into vendor-ready markdown for the i18n-books corpus
. Language-agnostic; pass --language as a BCP-47 tag.

The script strips Google/IA scan boilerplate via configurable start markers
but otherwise passes the OCR through. OCR quality varies wildly across
items; the output is suitable for stress-testing markdown rendering, not
necessarily for human reading.

Originally tuned for Yoruba (Crowther 1852, Dennett 1916) but generalised
when es-MX Tomóchic and other IA-sourced items joined the corpus.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8")


def skip_to_body(text: str, marker_candidates: list[str]) -> str:
    """Locate the first occurrence of any marker; return text from there.
    Used to skip past the Google boilerplate and front matter."""
    earliest = len(text)
    chosen = None
    for marker in marker_candidates:
        i = text.find(marker)
        if i != -1 and i < earliest:
            earliest = i
            chosen = marker
    if chosen is None:
        return text
    return text[earliest:]


def normalise_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build(args) -> None:
    raw = fetch_text(args.url)
    body = skip_to_body(raw, args.start_markers.split("||")) if args.start_markers else raw
    body = normalise_whitespace(body)
    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Internet Archive",
        "source_url": args.detail_url,
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True, help="IA djvu.txt download URL")
    p.add_argument("--detail-url", required=True, help="IA /details/ page URL for citation")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 language tag (e.g. yo, es-MX, sw)")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    p.add_argument(
        "--start-markers",
        default="",
        help="Pipe-separated body-start markers (||); skip OCR before the earliest match",
    )
    args = p.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
