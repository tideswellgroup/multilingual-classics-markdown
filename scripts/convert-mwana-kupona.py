#!/usr/bin/env python3
"""
convert-mwana-kupona.py: extract the Swahili stanzas of
Utendi wa Mwana Kupona from the africanpoems.net page and convert to
vendor-ready markdown for the multilingual-classics-markdown corpus.

africanpoems.net renders each numbered stanza as a single <p> with the
stanza number on its own line followed by the four-line verse. We pull
the consecutive paragraph block beginning with stanza 1 (Negema wangu
binti) and ending with stanza 102 (Nahimidi nkisalia).
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def extract_stanzas(html: str) -> list[str]:
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
    stanzas = []
    started = False
    for p in paragraphs:
        text = re.sub(r"<[^>]+>", "", p).strip()
        text = (text
                .replace("&nbsp;", " ")
                .replace("&#8211;", "–")
                .replace("&#8217;", "'")
                .replace("&#8216;", "'")
                .replace("&amp;", "&"))
        if not started:
            if "Negema wangu" in text:
                started = True
            else:
                continue
        if not started:
            continue
        m = re.match(r"^(\d+)\s*\n(.+)$", text, re.DOTALL)
        if not m:
            break
        stanzas.append((int(m.group(1)), m.group(2).strip()))
        if int(m.group(1)) >= 102:
            break
    return stanzas


def format_body(stanzas: list[tuple[int, str]]) -> str:
    out = []
    for num, body in stanzas:
        out.append(f"**{num}**")
        out.append("")
        out.append(body)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


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
    p.add_argument("--url", default="https://africanpoems.net/epic/the-book-of-mwana-kupona/")
    p.add_argument("--output", required=True)
    args = p.parse_args()

    html = fetch_html(args.url)
    stanzas = extract_stanzas(html)
    if len(stanzas) < 100:
        print(f"warning: only {len(stanzas)} stanzas extracted (expected 102)", file=sys.stderr)
    body = format_body(stanzas)

    meta = {
        "title": "Utendi wa Mwana Kupona",
        "author": "Mwana Kupona binti Msham",
        "language": "sw",
        "year": 1858,
        "source": "africanpoems.net (text from Allen, Tendi, 1971)",
        "source_url": args.url,
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(stanzas)} stanzas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
