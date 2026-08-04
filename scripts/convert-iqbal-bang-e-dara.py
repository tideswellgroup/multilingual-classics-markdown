#!/usr/bin/env python3
"""
Build a markdown file of Iqbal's Bang-e-Dara (1924) by pulling poems
from ur.wikisource. The Iqbal author page (Musannif:Muhammad_Iqbal)
groups poems by collection; we lift the Bang-e-Dara group and walk
each poem page, converting wikitext to markdown.

This is a one-off, not a general helper: ur.wikisource has no per-book
index page for Bang-e-Dara, so we section-slice the author page HTML
between the 'Bang-e-Dara (1924)' and 'Bal-e-Jibril (1935)' headings to
get the right poem set.
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
AUTHOR_PAGE = "مصنف:محمد اقبال"
BOOK_START = "بانگ درا"
BOOK_END = "بال جبریل"
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


def get_poem_titles() -> list[str]:
    url = f"https://{LANG}.wikisource.org/wiki/" + urllib.parse.quote(AUTHOR_PAGE.replace(" ", "_"))
    h = fetch(url).decode("utf-8")
    # Locate the actual section header (h4) rather than a TOC link.
    # The author page repeats the section title in its table of contents
    # near the top; a naive `find` lands on the TOC, which is a few hundred
    # characters wide and contains no poem links. We scan h-tags directly.
    sec_starts = []
    for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", h, re.DOTALL):
        plain = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        sec_starts.append((m.start(), plain))
    start = end = -1
    for pos, plain in sec_starts:
        if BOOK_START in plain and start < 0:
            start = pos
        elif start >= 0 and BOOK_END in plain and end < 0:
            end = pos
            break
    if start < 0 or end < 0:
        raise SystemExit("could not slice Bang-e-Dara section on the author page")
    section = h[start:end]
    pat = re.compile(r'href="(/wiki/[^"#]+)"[^>]*?title="([^"]+)"')
    titles: list[str] = []
    seen: set[str] = set()
    for m in pat.finditer(section):
        href = m.group(1)
        title_attr = m.group(2)
        # skip non-content namespaces and the section anchor
        if title_attr.startswith(("فائل:", "خاص:", "مصنف:")) or "ویکی" in title_attr:
            continue
        leaf = urllib.parse.unquote(href[len("/wiki/"):]).replace("_", " ")
        if leaf in seen:
            continue
        seen.add(leaf)
        titles.append(leaf)
    return titles


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
    if "parse" not in data:
        return ""
    return data["parse"]["wikitext"]


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
        # keep the longest non-empty arg that looks like prose
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


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


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

    titles = get_poem_titles()
    sys.stderr.write(f"[iqbal] {len(titles)} poems queued from Bang-e-Dara\n")

    chunks: list[str] = []
    n_ok = 0
    for t in titles:
        wt = fetch_wt(t)
        if not wt:
            time.sleep(args.delay)
            continue
        body = strip_header(wt)
        body = convert_inline(body)
        body = strip_templates(body)
        body = normalise(body)
        if not body:
            time.sleep(args.delay)
            continue
        chunks.append(f"## {t}\n\n{body}")
        n_ok += 1
        time.sleep(args.delay)

    md = "\n\n".join(chunks)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"

    fm = make_frontmatter({
        "title": "بانگ درا",
        "author": "محمد اقبال",
        "language": "ur",
        "year": 1924,
        "source": "Wikisource (ur)",
        "source_url": "https://ur.wikisource.org/wiki/" + urllib.parse.quote(AUTHOR_PAGE.replace(" ", "_")),
        "license": "Public domain in the United States",
    })
    out = fm + md
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    sys.stderr.write(f"wrote {dest} ({len(out):,} bytes, {n_ok}/{len(titles)} poems)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
