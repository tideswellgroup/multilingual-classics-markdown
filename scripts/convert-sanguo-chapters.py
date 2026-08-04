#!/usr/bin/env python3
"""
convert-sanguo-chapters.py: build a single markdown file from a contiguous
run of 三國演義 chapter pages on zh.wikisource, in the simplified-character
variant.

Each chapter lives at its own page (三國演義/第00N回) whose wikitext is a thin
{{Novel|...}} shell around ProofreadPage-style prose, so the rendered-HTML
route is the right one (same reasoning as convert-wikisource-html.py). Two
wrinkles that shipped converter does not cover, and why this helper exists:

  1. The chapter-title couplet renders only inside the {{Novel}} navigation
     table (class="ws-header"), which the chrome stripper removes. We lift the
     title out of that table first, then emit it as an H1 so each chapter stays
     a distinct unit.
  2. Several chapters are assembled into one file, so frontmatter is written
     once and the per-chapter converter frontmatter is discarded.

Simplified output comes from the same uselang/variant + Accept-Language route
convert-wikisource-html.py documents; verify with a 国-not-國 spot check.
"""

from __future__ import annotations

import argparse
import html as htmllib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"


def fetch_html(page: str, variant: str) -> str:
    params = {
        "action": "parse", "page": page, "prop": "text", "format": "json",
        "formatversion": "2", "disableeditsection": "1", "disabletoc": "1",
        "uselang": variant, "variant": variant,
    }
    url = "https://zh.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": variant})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if "error" in data:
        raise SystemExit(f"API error for {page}: {data['error']}")
    return data["parse"]["text"]


def extract_title(html: str) -> str:
    """Pull '第N回　<couplet>' out of the {{Novel}} nav table's centre cell."""
    for m in re.finditer(r'text-align:center"[^>]*>(.*?)</td>', html, re.DOTALL):
        cell = re.sub(r"<[^>]+>", "", m.group(1))
        cell = htmllib.unescape(cell).strip()
        if re.match(r"第[一-鿿]+回", cell):
            return re.sub(r"\s+", "　", cell)
    raise SystemExit("chapter title not found in nav table")


def strip_and_convert(html: str) -> str:
    # Drop the two ws-header nav tables (and any other tables) wholesale.
    html = re.sub(r"<table\b.*?</table>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Comments, style, script, self-closing links.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<link\b[^>]*/?>", "", html, flags=re.IGNORECASE)
    # Category / reference chrome.
    html = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", html, flags=re.DOTALL)
    # Intro-poem verse: nested <dl><dd> -> one paragraph per line.
    html = re.sub(r"</?dl[^>]*>", "", html)
    html = re.sub(r"<dd[^>]*>\s*(.*?)\s*</dd>", lambda m: f"\n\n{m.group(1).strip()}\n\n", html, flags=re.DOTALL)
    # Paragraphs.
    html = re.sub(r"<p[^>]*>\s*(.*?)\s*</p>", lambda m: f"\n\n{m.group(1).strip()}\n\n", html, flags=re.DOTALL)
    html = re.sub(r"<br\s*/?>", "\n", html)
    # Drop residual inline tags (links, spans, bold on year labels), keep text.
    html = re.sub(r"<[^>]+>", "", html)
    html = htmllib.unescape(html)
    # Whitespace normalise.
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    html = re.sub(r"[ \t]+\n", "\n", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    # Drop the rendered "back to top" footer link left as a bare paragraph.
    html = re.sub(r"^\s*返回页首\s*$", "", html, flags=re.MULTILINE)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


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
    p.add_argument("--first", type=int, required=True, help="first chapter number")
    p.add_argument("--last", type=int, required=True, help="last chapter number")
    p.add_argument("--variant", default="zh-cn")
    p.add_argument("--delay", type=float, default=5.0)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    bodies = []
    for n in range(args.first, args.last + 1):
        page = f"三國演義/第{n:03d}回"
        html = fetch_html(page, args.variant)
        title = extract_title(html)
        body = strip_and_convert(html)
        bodies.append(f"# {title}\n\n{body}")
        print(f"  chapter {n}: title={title!r} body={len(body):,} chars", file=sys.stderr)
        if n < args.last:
            time.sleep(args.delay)

    meta = {
        "title": "三国演义",
        "author": "罗贯中",
        "language": "zh-Hans",
        "year": 1522,
        "source": "Wikisource (zh)",
        "source_url": "https://zh.wikisource.org/wiki/%E4%B8%89%E5%9C%8B%E6%BC%94%E7%BE%A9",
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + "\n".join(bodies) + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
