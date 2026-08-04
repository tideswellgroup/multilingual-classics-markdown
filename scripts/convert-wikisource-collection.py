#!/usr/bin/env python3
"""
Walk a Wikisource collection index page and concatenate all sub-pages
into one markdown file.

The Spanish, Portuguese, and Urdu Wikisource projects organise long
poetry collections and divans as an index page that links to one
sub-page per poem or section. This walker pulls the index, finds the
sub-page links, fetches each, strips wikitext templates, and emits a
single markdown file with each poem as a sub-section.

The wikitext-to-markdown logic here mirrors scripts/convert-wikisource.py
so output shape stays consistent with the rest of the corpus.
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


def fetch_wt(lang: str, page: str) -> str:
    url = f"https://{lang}.wikisource.org/w/api.php?" + urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "wikitext",
        "format": "json", "formatversion": "2",
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
            return data.get("parse", {}).get("wikitext", "")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    return ""


def index_sub_pages(lang: str, index_page: str) -> list[str]:
    """Pull the index page's HTML and find sub-page links under it.

    Sub-pages are wiki titles starting with '<index_page>/'. We dedupe
    while preserving order."""
    url = f"https://{lang}.wikisource.org/wiki/" + urllib.parse.quote(index_page.replace(" ", "_"))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    html_doc = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    prefix_q = urllib.parse.quote(index_page.replace(" ", "_")) + "/"
    pat = re.compile(r'href="(/wiki/' + re.escape(prefix_q) + r'[^"#]+)"', flags=re.IGNORECASE)
    seen = []
    seen_set = set()
    for m in pat.finditer(html_doc):
        href = m.group(1)
        title = urllib.parse.unquote(href[len("/wiki/"):]).replace("_", " ")
        if title in seen_set:
            continue
        seen_set.add(title)
        seen.append(title)
    return seen


def strip_top_metadata(text: str) -> str:
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
    text = re.sub(r"<center[^>]*>\s*(.*?)\s*</center>",
                  lambda m: f"\n\n## {m.group(1)}\n\n" if m.group(1).strip() else "",
                  text, flags=re.DOTALL)
    text = re.sub(r"'''([^']+?)'''", r"**\1**", text)
    text = re.sub(r"''([^']+?)''", r"*\1*", text)
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    text = re.sub(r"<poem[^>]*>", "", text)
    text = re.sub(r"</poem>", "", text)
    text = text.replace("&nbsp;", " ").replace("&mdash;", "—").replace("&ndash;", "–").replace("&amp;", "&")
    return text


def strip_simple_templates(text: str) -> str:
    """Collapse {{template|...}} forms. Pick the longest prose-shaped arg."""
    def repl(m):
        body = m.group(1)
        if "|" not in body:
            return ""
        parts = body.split("|")[1:]
        candidates = [p.strip() for p in parts if p.strip()]
        candidates.sort(key=lambda s: (s.count(" ") + sum(1 for c in s if ord(c) > 127), len(s)), reverse=True)
        for c in candidates:
            if len(c) > 12 and (" " in c or any(ord(ch) > 127 for ch in c)):
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


def page_leaf(full_title: str) -> str:
    return full_title.split("/")[-1]


def convert_one(lang: str, page: str) -> str:
    wt = fetch_wt(lang, page)
    if not wt:
        return ""
    wt = strip_top_metadata(wt)
    wt = convert_inline(wt)
    wt = strip_simple_templates(wt)
    wt = convert_headings(wt)
    wt = normalise(wt)
    return wt


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
    p.add_argument("--lang", required=True, help="Wikisource subdomain (es, ur, etc.)")
    p.add_argument("--index", required=True, help="Index page title (collection root)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 tag for output")
    p.add_argument("--year", required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--pages", help="Comma-separated explicit sub-page list (skip index walk)")
    p.add_argument("--include-index-body", action="store_true",
                   help="Include the converted text of the index page itself at top")
    p.add_argument("--max-pages", type=int, default=0,
                   help="Cap on sub-pages (0 = no cap)")
    p.add_argument("--delay", type=float, default=0.3,
                   help="Per-request delay in seconds (be polite)")
    args = p.parse_args()

    if args.pages:
        sub_pages = [s.strip() for s in args.pages.split(",") if s.strip()]
    else:
        sub_pages = index_sub_pages(args.lang, args.index)

    if args.max_pages and len(sub_pages) > args.max_pages:
        sub_pages = sub_pages[:args.max_pages]

    chunks: list[str] = []
    if args.include_index_body:
        body = convert_one(args.lang, args.index)
        if body:
            chunks.append(body)
    for sp in sub_pages:
        body = convert_one(args.lang, sp)
        if not body:
            time.sleep(args.delay)
            continue
        leaf = page_leaf(sp)
        chunks.append(f"## {leaf}\n\n{body}")
        time.sleep(args.delay)

    md_body = "\n\n".join(chunks)
    md_body = re.sub(r"\n{3,}", "\n\n", md_body).strip() + "\n"

    fm = make_frontmatter({
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    })
    out = fm + md_body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(sub_pages)} sub-pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
