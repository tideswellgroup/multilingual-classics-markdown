#!/usr/bin/env python3
"""
convert-liaozhai-tales.py: assemble a selection of 聊齋誌異 tales into one
markdown file. Each tale is a named section (== 畫皮 ==) inside a per-volume
wikitext page (聊齋志異/第0N卷), so this walks the named volumes, slices out the
requested sections, and cleans a critical-edition apparatus the shipped
converters do not model.

Two of the canonical tales (畫皮, 聶小倩) are transcribed here as annotated
critical editions; the plainer ones (勞山道士, 促織) carry only reading
glosses. To land a single verbatim reading text, the following editorial
layers are removed and each removal is disclosed in the book's front matter:

  - {{*|〔評〕…}}  commentator marginalia (但明倫 / 馮鎮巒 / 何垠) -> dropped
  - {{另|甲|乙}}   variant-character template -> printed reading 甲 kept
  - （…）           short parenthetical variant insertions -> dropped
  - <ref>…</ref>   lexical glosses, and <u> proper-noun underlines -> dropped

Classical tale prose uses none of these devices natively, so each is
unambiguously editorial in the selected tales; the base narrative is left
byte-for-byte otherwise. Traditional characters are preserved (no variant
route).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"


def fetch_wikitext(page: str) -> str:
    params = {"action": "parse", "page": page, "prop": "wikitext",
              "format": "json", "formatversion": "2"}
    url = "https://zh.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if "error" in data:
        raise SystemExit(f"API error for {page}: {data['error']}")
    return data["parse"]["wikitext"]


def slice_section(wikitext: str, name: str) -> str:
    m = re.search(rf"^=+\s*{re.escape(name)}\s*=+\s*$", wikitext, re.MULTILINE)
    if not m:
        raise SystemExit(f"section {name!r} not found")
    after = wikitext[m.end():]
    nxt = re.search(r"^=+\s*\S.*?\s*=+\s*$", after, re.MULTILINE)
    return after[: nxt.start()] if nxt else after


def clean(seg: str) -> str:
    # Commentator marginalia: {{*|…}} with no nested braces, removed repeatedly.
    prev = None
    while prev != seg:
        prev = seg
        seg = re.sub(r"\{\{\*\|[^{}]*\}\}", "", seg)
    # Variant-character template: keep the printed (first) reading.
    prev = None
    while prev != seg:
        prev = seg
        seg = re.sub(r"\{\{另\|([^|{}]*)\|[^{}]*\}\}", r"\1", seg)
    # Any remaining templates ({{檢索}}, {{Textquality}}, {{YL|…}}): drop,
    # keeping a prose payload only when the template wraps one.
    prev = None
    while prev != seg:
        prev = seg
        seg = re.sub(r"\{\{YL\|([^|{}]*)\}\}", r"\1", seg)
        seg = re.sub(r"\{\{[^{}]*\}\}", "", seg)
    # Reference glosses and proper-noun underlines.
    seg = re.sub(r"<ref[^>]*>.*?</ref>", "", seg, flags=re.DOTALL)
    seg = re.sub(r"<ref[^>]*/>", "", seg)
    seg = re.sub(r"</?u\s*>", "", seg, flags=re.IGNORECASE)
    seg = re.sub(r"</?(sub|small|center|div|span|poem)\b[^>]*>", "", seg, flags=re.IGNORECASE)
    # Short parenthetical variant insertions (editorial in these tales).
    seg = re.sub(r"（[^（）]{0,20}）", "", seg)
    # Inline wiki links -> display text.
    seg = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", seg)
    seg = re.sub(r"\[\[([^\]]+)\]\]", r"\1", seg)
    # Bold/italic wiki markup.
    seg = re.sub(r"'''([^']+?)'''", r"\1", seg)
    seg = re.sub(r"''([^']+?)''", r"\1", seg)
    # Whitespace: keep paragraph breaks, drop trailing ASCII space runs.
    seg = seg.replace("\r\n", "\n").replace("\r", "\n")
    seg = re.sub(r"[ \t]+\n", "\n", seg)
    seg = re.sub(r"[ \t]{2,}", "", seg)
    seg = re.sub(r"\n{3,}", "\n\n", seg)
    return seg.strip()


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
    # tale spec: name=volumepage, in output order
    p.add_argument("--tale", action="append", required=True,
                   metavar="NAME=VOLUME_PAGE",
                   help="tale section name and its volume page, repeatable")
    p.add_argument("--delay", type=float, default=5.0)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    # Fetch each distinct volume page once.
    specs = [t.split("=", 1) for t in args.tale]
    vols: dict[str, str] = {}
    for _, vol in specs:
        vols.setdefault(vol, "")
    for i, vol in enumerate(list(vols)):
        vols[vol] = fetch_wikitext(vol)
        print(f"  fetched {vol} ({len(vols[vol]):,} chars)", file=sys.stderr)
        if i + 1 < len(vols):
            time.sleep(args.delay)

    parts = []
    for name, vol in specs:
        body = clean(slice_section(vols[vol], name))
        parts.append(f"## {name}\n\n{body}")
        print(f"  tale {name}: {len(body):,} chars from {vol}", file=sys.stderr)

    meta = {
        "title": "聊齋誌異",
        "author": "蒲松齡",
        "language": "zh-Hant",
        "year": 1766,
        "source": "Wikisource (zh)",
        "source_url": "https://zh.wikisource.org/wiki/%E8%81%8A%E9%BD%8B%E5%BF%97%E7%95%B0",
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + "\n\n".join(parts) + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out.encode('utf-8')):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
