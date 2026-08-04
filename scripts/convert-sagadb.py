#!/usr/bin/env python3
"""
convert-sagadb.py: fetch a sagadb.org plain-text saga and
convert to vendor-ready markdown for the multilingual-classics-markdown corpus.

sagadb.org plain-text files use '<N>. kafli' (Icelandic) as chapter markers.
We promote those to H1 headings and prepend YAML frontmatter consistent with
the rest of the corpus.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def promote_chapter_markers(body: str) -> str:
    """Promote '<N>. kafli' lines to H1 headings."""
    return re.sub(
        r"^(\d+)\.\s*kafli\s*$",
        lambda m: f"# {m.group(1)}. kafli",
        body,
        flags=re.MULTILINE,
    )


def strip_leading_title_block(body: str, title: str) -> str:
    """Drop the leading title heading the .txt file repeats on its first line."""
    lines = body.splitlines()
    out = []
    seen_body = False
    for line in lines:
        if not seen_body:
            if line.strip() == "" or line.strip() == title:
                continue
            seen_body = True
        out.append(line)
    return "\n".join(out)


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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True, help="sagadb.org plain-text file URL")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True, help="Author/attribution (e.g. 'Anonymous')")
    p.add_argument("--year", required=True, help="Original composition year (approximate ok)")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    raw = fetch_text(args.url)
    body = strip_leading_title_block(raw, args.title)
    body = promote_chapter_markers(body)
    body = normalise_whitespace(body)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": "is",
        "year": args.year,
        "source": "sagadb.org",
        "source_url": args.url,
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
