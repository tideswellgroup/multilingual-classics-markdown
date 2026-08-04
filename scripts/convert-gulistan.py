#!/usr/bin/env python3
"""convert-gulistan.py: rebuild books/fa/سعدی شیرازی/گلستان.md from source with
its verse restored.

Why a dedicated converter: the fa.wikisource Gulistan (Foroughi edition) lives
on subpages that transclude the proofread Page: namespace via
`<pages index="KoliyatSaadiForoughi.pdf" .../>`. The shared convert-wikisource.py
fetches `prop=wikitext`, which for these pages returns only the transclusion
directive, so an earlier conversion that leaned on rendered text dropped every
embedded beyt (the famous بنی آدم اعضای یکدیگرند, the Fereydun-arch quatrain,
etc. were absent). This wrapper instead fetches the RENDERED html
(`action=parse&prop=text`), where verse survives as
`<span class="poem">…<span class="beyt">HEMISTICH</span>…` inside a table, and
emits markdown following the corpus convention: prose paragraphs blank-line
separated, verse hemistichs hard-broken (two trailing spaces) within a poem
block, blank lines separating verse from prose.

Frontmatter is carried over verbatim from the existing file (title, author,
language, year, source, source_url, license). Fetches are spaced by a polite
delay.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

LANG = "fa"
# The file's selection structure: preface + the eight babs (no editor
# introduction, variant apparatus, or name index).
SECTIONS = [
    "کلیات سعدی/گلستان/دیباچه",
    "کلیات سعدی/گلستان/باب اول",
    "کلیات سعدی/گلستان/باب دوم",
    "کلیات سعدی/گلستان/باب سوم",
    "کلیات سعدی/گلستان/باب چهارم",
    "کلیات سعدی/گلستان/باب پنجم",
    "کلیات سعدی/گلستان/باب ششم",
    "کلیات سعدی/گلستان/باب هفتم",
    "کلیات سعدی/گلستان/باب هشتم",
]

OUT_PATH = Path("books/fa/سعدی شیرازی/گلستان.md")
FETCH_DELAY_S = 12.0

SKIP_CLASS = {
    "ws-noexport", "reference", "references", "pagenum", "mw-editsection",
    "noprint", "reflist", "mw-references", "mw-cite-backlink",
}
SKIP_ID = {"headerContainer"}
VOID = {"br", "hr", "img", "meta", "link", "input", "area", "base", "col",
        "embed", "source", "track", "wbr", "param"}


CACHE_DIR = Path(__file__).resolve().parent / ".gulistan-html-cache"


def fetch_html(page: str) -> str:
    CACHE_DIR.mkdir(exist_ok=True)
    cache = CACHE_DIR / (urllib.parse.quote(page, safe="") + ".html")
    if cache.exists():
        sys.stderr.write("  (cached)\n")
        return cache.read_text(encoding="utf-8")
    base = f"https://{LANG}.wikisource.org/w/api.php"
    params = {
        "action": "parse", "page": page, "prop": "text",
        "format": "json", "formatversion": "2", "disablelimitreport": "1",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "multilingual-classics-markdown/1.0 (corpus verse-restoration)"})
    backoff = 30.0
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 4:
                sys.stderr.write(f"  {e.code}; backing off {backoff:.0f}s\n")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    if "error" in data:
        raise RuntimeError(f"API error for {page}: {data['error']}")
    text = data["parse"]["text"]
    cache.write_text(text, encoding="utf-8")
    return text


class GulistanParser(HTMLParser):
    """Walk the rendered page, emitting an ordered list of
    ('heading'|'prose'|'verse', payload) blocks. Verse payload is a list of
    hemistich strings; heading/prose payloads are strings. Navigation, page
    markers, and the footnote apparatus (which itself contains verse) are
    dropped by class/id."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.blocks: list[tuple[str, object]] = []

    def _has(self, key: str) -> bool:
        return any(f.get(key) for f in self.stack)

    def _inner(self, key: str):
        for f in reversed(self.stack):
            if f.get(key):
                return f
        return None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = set((d.get("class", "") or "").split())
        _id = d.get("id", "") or ""
        f = {"tag": tag}
        if self._has("skip"):
            f["skip"] = True
        elif tag == "style" or _id in SKIP_ID or (cls & SKIP_CLASS):
            f["skip"] = True
        elif tag == "span" and "poem" in cls:
            f["poem"] = True
            f["lines"] = []
        elif self._has("poem"):
            if tag == "span" and "beyt" in cls:
                f["beyt"] = True
                f["buf"] = []
        elif tag == "div" and "tiInherit" in cls:
            f["heading"] = True
            f["buf"] = []
        elif tag == "p" and not self._has("heading"):
            f["p"] = True
            f["buf"] = []
        if tag in VOID:
            if tag == "br" and not self._has("skip"):
                tgt = self._inner("p") or self._inner("heading")
                if tgt is not None:
                    tgt["buf"].append("\n")
            return
        self.stack.append(f)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                idx = i
                break
        if idx is None:
            return
        popped = self.stack[idx:]
        del self.stack[idx:]
        for f in reversed(popped):
            if f.get("skip"):
                continue
            if f.get("beyt"):
                t = re.sub(r"\s+", " ", html.unescape("".join(f["buf"]))).strip()
                poem = self._inner("poem")
                if t and poem is not None:
                    poem["lines"].append(t)
            elif f.get("poem"):
                if f["lines"]:
                    self.blocks.append(("verse", f["lines"]))
            elif f.get("heading"):
                t = re.sub(r"\s+", " ", html.unescape("".join(f["buf"]))).strip()
                if t:
                    self.blocks.append(("heading", t))
            elif f.get("p"):
                t = html.unescape("".join(f["buf"]))
                t = re.sub(r"[ \t]+", " ", t)
                t = re.sub(r"\s*\n\s*", " ", t).strip()
                if t:
                    self.blocks.append(("prose", t))

    def handle_data(self, data):
        if self._has("skip"):
            return
        b = self._inner("beyt")
        if b is not None:
            b["buf"].append(data)
            return
        if self._has("poem"):
            return
        h = self._inner("heading")
        if h is not None:
            h["buf"].append(data)
            return
        p = self._inner("p")
        if p is not None:
            p["buf"].append(data)


def render_section(blocks: list[tuple[str, object]], title: str) -> list[str]:
    # The section title (e.g. دیباچه, باب اول) is the H1. The babs repeat their
    # bare title as the first body heading, so drop a body heading equal to the
    # title; every other body heading (subtitle, حکایت markers, the بسم‌الله
    # invocation) becomes an H2.
    out: list[str] = [f"# {title}"]
    for kind, payload in blocks:
        if kind == "heading":
            if payload.strip() == title:
                continue
            out.append(f"## {payload}")
        elif kind == "prose":
            out.append(re.sub(r"\s+", " ", payload).strip())
        elif kind == "verse":
            lines = payload
            vb = [ln + "  " if i < len(lines) - 1 else ln
                  for i, ln in enumerate(lines)]
            out.append("\n".join(vb))
    return out


def read_frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5]
    raise RuntimeError("existing file has no frontmatter to preserve")


def main() -> int:
    fm = read_frontmatter(OUT_PATH)
    all_blocks: list[str] = []
    for i, page in enumerate(SECTIONS):
        if i:
            time.sleep(FETCH_DELAY_S)
        sys.stderr.write(f"fetching {page} ...\n")
        html_text = fetch_html(page)
        p = GulistanParser()
        p.feed(html_text)
        title = page.rsplit("/", 1)[-1]
        rendered = render_section(p.blocks, title)
        nverse = sum(1 for k, _ in p.blocks if k == "verse")
        sys.stderr.write(f"  blocks: {len(p.blocks)}  verse: {nverse}\n")
        all_blocks.extend(rendered)
    body = "\n\n".join(all_blocks).strip() + "\n"
    OUT_PATH.write_text(fm + body, encoding="utf-8")
    sys.stderr.write(f"wrote {OUT_PATH}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
