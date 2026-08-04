#!/usr/bin/env python3
"""
Build a markdown file of Mirza Ghalib's Divan (Urdu ghazals,
qasaid, mathnavi) from ur.wikisource by walking the multi-level
'Divan e Ghalib' index.

ur.wikisource organises the Divan as:
  دیوان غالب
    └── دیوان غالب/غزلیات
        └── دیوان غالب/غزلیات/ردیف <letter>
            └── دیوان غالب/غزلیات/ردیف <letter>/ردیف <letter> غزل N تا N+14

This script walks the radif index pages, finds the chunked leaf pages,
fetches each, strips the wikitext templates, and emits one markdown
file with the radif as H2 sections and each batch of ghazals inline.

The Mathnaviyat and Qasaid sections are simpler (one or two leaf pages
each) and are included with H2 section markers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"
LANG = "ur"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                time.sleep(10 * (attempt + 1))
                continue
            raise


def fetch_wt(page: str) -> str:
    url = f"https://{LANG}.wikisource.org/w/api.php?" + urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "wikitext",
        "format": "json", "formatversion": "2",
    })
    try:
        raw = fetch(url)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"[skip] {page}: {e}\n")
        return ""
    data = json.loads(raw.decode("utf-8"))
    return data.get("parse", {}).get("wikitext", "")


def find_links(wt: str, prefix: str) -> list[str]:
    """Find [[prefix/...]] links inside wikitext. Dedupe in order."""
    seen: set[str] = set()
    out: list[str] = []
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", wt):
        link = m.group(1).strip()
        if not link.startswith(prefix + "/"):
            continue
        if link in seen:
            continue
        seen.add(link)
        out.append(link)
    return out


def strip_header(text: str) -> str:
    if text.lstrip().startswith("{{"):
        depth = 0
        i = 0
        while i < len(text):
            if text[i:i + 2] == "{{":
                depth += 1
                i += 2
            elif text[i:i + 2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    text = text[i:]
                    break
            else:
                i += 1
    return re.sub(r"__[A-Z]+__", "", text).lstrip()


def convert_inline(text: str) -> str:
    text = re.sub(r"'''([^']+?)'''", r"**\1**", text)
    text = re.sub(r"''([^']+?)''", r"*\1*", text)
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    text = re.sub(r"<poem[^>]*>", "", text)
    text = re.sub(r"</poem>", "", text)
    text = re.sub(r"<center[^>]*>\s*(.*?)\s*</center>",
                  lambda m: m.group(1).strip() + "\n",
                  text, flags=re.DOTALL)
    text = re.sub(r"<div[^>]*>", "", text)
    text = re.sub(r"</div>", "", text)
    text = re.sub(r"<br\s*/?>", "  \n", text)
    text = text.replace("&nbsp;", " ").replace("&mdash;", "—").replace("&ndash;", "–").replace("&amp;", "&")
    return text


def strip_templates(text: str) -> str:
    def repl(m):
        body = m.group(1)
        if "|" not in body:
            return ""
        parts = body.split("|")[1:]
        cands = [p.strip() for p in parts if p.strip()]
        cands.sort(key=lambda s: (s.count(" ") + sum(1 for c in s if ord(c) > 127), len(s)), reverse=True)
        for c in cands:
            if len(c) > 8 and (" " in c or any(ord(ch) > 127 for ch in c)):
                return c
        return ""
    pat = re.compile(r"\{\{([^{}]+?)\}\}", flags=re.DOTALL)
    prev = None
    while text != prev:
        prev = text
        text = pat.sub(repl, text)
    return text


def convert_headings(text: str) -> str:
    text = re.sub(r"^======\s*(.+?)\s*======\s*$", r"###### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^=====\s*(.+?)\s*=====\s*$", r"##### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^====\s*(.+?)\s*====\s*$", r"#### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^===\s*(.+?)\s*===\s*$", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^==\s*(.+?)\s*==\s*$", r"## \1", text, flags=re.MULTILINE)
    return text


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def page_to_md(page: str, delay: float = 0.3) -> str:
    wt = fetch_wt(page)
    if not wt:
        time.sleep(delay)
        return ""
    body = strip_header(wt)
    body = convert_inline(body)
    body = strip_templates(body)
    body = convert_headings(body)
    body = normalise(body)
    time.sleep(delay)
    return body


def leaf(page: str) -> str:
    return page.split("/")[-1]


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
    p.add_argument("--output", required=True)
    p.add_argument("--delay", type=float, default=0.25)
    args = p.parse_args()

    root = "دیوان غالب"
    sections = [
        ("غزلیات", "Ghazaliyat"),
        ("قصائد", "Qasaid"),
        ("مثنویاں", "Mathnaviyat"),
    ]

    chunks: list[str] = [f"# {root}\n"]

    for sec_name, _ in sections:
        sec_page = f"{root}/{sec_name}"
        sec_wt = fetch_wt(sec_page)
        time.sleep(args.delay)
        sub_links = find_links(sec_wt, sec_page)
        if not sub_links:
            sys.stderr.write(f"[ghalib] {sec_page}: no sub-links found, fetching directly\n")
            body = page_to_md(sec_page, args.delay)
            if body:
                chunks.append(f"## {sec_name}\n\n{body}")
            continue
        sys.stderr.write(f"[ghalib] {sec_page}: {len(sub_links)} sub-pages\n")
        chunks.append(f"## {sec_name}\n")
        for sl in sub_links:
            # If this is a radif index, walk one more level.
            sl_wt = fetch_wt(sl)
            time.sleep(args.delay)
            leaves = find_links(sl_wt, sl)
            if leaves:
                # Radif index: emit the radif as H3 then each leaf as H4
                chunks.append(f"### {leaf(sl)}\n")
                for lf in leaves:
                    body = page_to_md(lf, args.delay)
                    if not body:
                        continue
                    chunks.append(f"#### {leaf(lf)}\n\n{body}")
            else:
                # Direct content page
                body = strip_header(sl_wt)
                body = convert_inline(body)
                body = strip_templates(body)
                body = convert_headings(body)
                body = normalise(body)
                if body:
                    chunks.append(f"### {leaf(sl)}\n\n{body}")

    md = "\n\n".join(chunks)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"

    fm = make_frontmatter({
        "title": "دیوان غالب",
        "author": "مرزا اسد اللہ خان غالب",
        "language": "ur",
        "year": 1869,
        "source": "Wikisource (ur)",
        "source_url": f"https://{LANG}.wikisource.org/wiki/" + urllib.parse.quote(root.replace(" ", "_")),
        "license": "Public domain in the United States",
    })
    out = fm + md
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    sys.stderr.write(f"wrote {dest} ({len(out):,} bytes)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
