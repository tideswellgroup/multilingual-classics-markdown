#!/usr/bin/env python3
"""
convert-rtl-sources.py: fetchers and HTML-to-markdown converters for the
RTL / Indic cluster of the multilingual-classics-markdown corpus.

Sources covered:
  - Project Ben-Yehuda (benyehuda.org) -- Hebrew literature; reader HTML at
    /read/<id> contains the prose body inside <div id="actualtext"> with
    <h2> chapter headings and <p> paragraphs. Footnotes hang off the end of
    the same div as <ol class="footnotes">.
  - Ganjoor.net -- Classical Persian poetry. Has a JSON API at
    /api/ganjoor/poem/<id> returning {title, plainText, ...}. We can also
    walk /api/ganjoor/cat/<id> to enumerate poems in a section.
  - ar.wikisource.org -- Arabic Wikisource. Uses the generic convert-wikisource
    helper already in scripts/, but we add a small wrapper that concatenates
    several sub-pages (e.g. tales from One Thousand and One Nights).

Usage examples:
  ./convert-rtl-sources.py benyehuda --id 29532 --title 'מסביב לנקודה' \
      --author 'יוסף חיים ברנר' --language he --year 1904 \
      --output /path/to/output.md

  ./convert-rtl-sources.py ganjoor --cat 24 --title 'رباعیات' \
      --author 'عمر خیام' --language fa --year 1100 \
      --output /path/to/output.md \
      --source-url 'https://ganjoor.net/khayyam/robaee'

  ./convert-rtl-sources.py wikisource-multi --lang ar \
      --pages 'الف ليلة وليلة/الليلة الأولى,الف ليلة وليلة/الليلة الثانية' \
      --title 'ألف ليلة وليلة' --author 'مجهول' --language ar --year 1835 \
      --output /path/to/output.md \
      --source-url 'https://ar.wikisource.org/wiki/الف_ليلة_وليلة'

The wikisource-multi mode reuses the conversion functions from
scripts/convert-wikisource.py by importing them; if that path is not
available it falls back to a self-contained reimplementation (kept here so
the helper works standalone for testing).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path

UA = "multilingual-classics-markdown/1.0 (https://github.com/tideswellgroup/multilingual-classics-markdown)"


def fetch(url: str, *, timeout: int = 60) -> bytes:
    """GET with retry on 429 and on transient network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last_err = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                wait = 10 * (attempt + 1)
                sys.stderr.write(f"[fetch] 429 from {url}, sleeping {wait}s\n")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < 5:
                wait = 3 * (attempt + 1)
                sys.stderr.write(f"[fetch] transient error {e} from {url}, sleeping {wait}s\n")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("retry budget exhausted: " + url + " -- " + str(last_err))


# ---------------------------------------------------------------------------
# benyehuda (Project Ben-Yehuda) HTML reader -> markdown
# ---------------------------------------------------------------------------

class BenYehudaExtractor(HTMLParser):
    """Pull prose paragraphs and chapter headings out of the #actualtext div.

    We accept the page-wrapped HTML (https://benyehuda.org/read/<id>) and
    walk the DOM with a tiny state machine. We ignore footnote popovers
    (<a class="footnote">), inline numeric refs, and the trailing <ol
    class="footnotes"> block which the reader appends after the prose.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_actualtext = 0  # depth counter once we see id="actualtext"
        self.in_footnotes_ol = 0
        self.collected: list[tuple[str, str]] = []  # (kind, text)
        self.current_kind: str | None = None
        self.current_buf: list[str] = []
        self.heading_depth = 0
        self.suppress_depth = 0  # inside footnote markers / inline refs

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.in_actualtext:
            if tag == "div" and a.get("id") == "actualtext":
                self.in_actualtext = 1
            return
        # We are inside actualtext. Track div nesting for the close logic.
        if tag == "div":
            self.in_actualtext += 1
            return
        if tag == "ol" and "footnotes" in (a.get("class") or ""):
            self.in_footnotes_ol += 1
            return
        if self.in_footnotes_ol:
            return
        # Inline footnote reference link (sup-style numeric)
        cls = a.get("class") or ""
        if tag == "a" and ("footnote" in cls or "fn-anchor" in cls or "ch_anch" in cls):
            self.suppress_depth += 1
            return
        # Heading
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.current_kind = f"h{tag[1]}"
            self.current_buf = []
            return
        if tag == "p":
            self.flush()
            self.current_kind = "p"
            self.current_buf = []
            return
        if tag == "br":
            if self.current_kind:
                self.current_buf.append("\n")
            return
        if tag in ("em", "i"):
            if self.current_kind:
                self.current_buf.append("*")
            return
        if tag in ("strong", "b"):
            if self.current_kind:
                self.current_buf.append("**")
            return
        if tag == "sup":
            self.suppress_depth += 1

    def handle_endtag(self, tag):
        if not self.in_actualtext:
            return
        if tag == "div":
            self.in_actualtext -= 1
            if self.in_actualtext == 0:
                self.flush()
            return
        if tag == "ol" and self.in_footnotes_ol:
            self.in_footnotes_ol -= 1
            return
        if self.in_footnotes_ol:
            return
        if tag == "a" and self.suppress_depth:
            self.suppress_depth -= 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            return
        if tag == "p":
            self.flush()
            return
        if tag in ("em", "i"):
            if self.current_kind:
                self.current_buf.append("*")
            return
        if tag in ("strong", "b"):
            if self.current_kind:
                self.current_buf.append("**")
            return
        if tag == "sup" and self.suppress_depth:
            self.suppress_depth -= 1

    def handle_data(self, data):
        if not self.in_actualtext or self.in_footnotes_ol:
            return
        if self.suppress_depth:
            return
        if self.current_kind:
            self.current_buf.append(data)

    def flush(self):
        if self.current_kind and self.current_buf:
            text = "".join(self.current_buf)
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r" *\n *", "\n", text)
            text = text.strip()
            if text:
                self.collected.append((self.current_kind, text))
        self.current_kind = None
        self.current_buf = []


def benyehuda_to_markdown(html_doc: str) -> str:
    p = BenYehudaExtractor()
    p.feed(html_doc)
    p.close()
    lines: list[str] = []
    for kind, text in p.collected:
        # Strip permalink icons (🔗) that the reader injects next to headings
        text = text.replace("\U0001f517", "").strip()
        if not text:
            continue
        if kind.startswith("h"):
            level = int(kind[1:])
            # Promote h2 (chapter) to h1 so chapters are top-level. h3 -> h2.
            level = max(1, level - 1)
            lines.append("\n" + ("#" * level) + " " + text + "\n")
        else:
            text = re.sub(r"\s+", " ", text).strip()
            text = re.sub(r"\s*\[\d+\]", "", text)
            lines.append(text + "\n")
    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def cmd_benyehuda(args):
    url = f"https://benyehuda.org/read/{args.id}"
    raw = fetch(url).decode("utf-8")
    md_body = benyehuda_to_markdown(raw)
    fm = make_frontmatter({
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Project Ben-Yehuda",
        "source_url": url,
        "license": "Public domain in the United States",
    })
    out = fm + md_body
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"wrote {args.output} ({len(out):,} bytes)")


# ---------------------------------------------------------------------------
# Ganjoor (Persian classical poetry) JSON API -> markdown
# ---------------------------------------------------------------------------

def ganjoor_get(path: str):
    """GET https://api.ganjoor.net/api/ganjoor<path> as JSON."""
    url = f"https://api.ganjoor.net/api/ganjoor{path}"
    raw = fetch(url)
    return json.loads(raw.decode("utf-8"))


def cmd_ganjoor(args):
    """Pull every poem under a Ganjoor category and emit markdown.

    --cat is the category id (e.g. Khayyam Rubaiyat = 24). The category
    listing returns metadata + child poems; for each poem we hit the poem
    endpoint to get verses with proper line breaks.
    """
    cat_id = args.cat
    cat = ganjoor_get(f"/cat/{cat_id}?poems=true&mainSections=true")
    # API returns poems either at top level or nested under cat.poems depending
    # on the endpoint variant; handle both.
    poems = cat.get("poems") or cat.get("cat", {}).get("poems") or []
    if not poems:
        print(f"[ganjoor] no poems in cat {cat_id}", file=sys.stderr)
        return

    lines: list[str] = []
    cat_node = cat.get("cat", {}) if isinstance(cat.get("cat"), dict) else {}
    cat_title = cat_node.get("title") or args.title
    lines.append(f"# {cat_title}\n")

    count = 0
    limit = args.limit if args.limit > 0 else None
    for stub in poems:
        if limit is not None and count >= limit:
            break
        pid = stub["id"]
        poem = ganjoor_get(f"/poem/{pid}")
        title = poem.get("title") or f"شعر {pid}"
        verses = poem.get("verses") or []
        if not verses:
            continue
        lines.append(f"\n## {title}\n")
        # Ganjoor verses have positions: 0=right hemistich (مصرع اول),
        # 1=left hemistich (مصرع دوم), -1=centered. We pair 0+1 into
        # two-line couplets with a blank line between couplets.
        buf: list[str] = []
        prev_pos = None
        for v in verses:
            text = (v.get("text") or "").strip()
            if not text:
                continue
            pos = v.get("vOrder", 0)
            position = v.get("versePosition", 0)
            if position == 0:
                # right hemistich -- start a new line, may pair with next
                if buf and prev_pos == 1:
                    buf.append("")
                buf.append(text)
            elif position == 1:
                buf.append(text)
                buf.append("")  # blank line after couplet
            else:
                if buf and buf[-1] != "":
                    buf.append("")
                buf.append(text)
                buf.append("")
            prev_pos = position
        # trim trailing blanks
        while buf and buf[-1] == "":
            buf.pop()
        lines.append("\n".join(buf) + "\n")
        count += 1
        time.sleep(0.2)  # be polite to the API

    md_body = "\n".join(lines)
    md_body = re.sub(r"\n{3,}", "\n\n", md_body).strip() + "\n"

    fm = make_frontmatter({
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Ganjoor.net",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    })
    out = fm + md_body
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"wrote {args.output} ({len(out):,} bytes, {count} poems)")


# ---------------------------------------------------------------------------
# wikisource-multi: concatenate several Wikisource pages into one file
# ---------------------------------------------------------------------------
# We replicate the minimum we need from scripts/convert-wikisource.py so this
# helper stands alone for testing. The user can swap the import line in
# when integrating.

def _ws_fetch_wikitext(lang: str, page: str) -> str:
    base = f"https://{lang}.wikisource.org/w/api.php"
    params = {"action": "parse", "page": page, "prop": "wikitext",
              "format": "json", "formatversion": "2"}
    raw = fetch(base + "?" + urllib.parse.urlencode(params))
    data = json.loads(raw.decode("utf-8"))
    if "parse" not in data:
        raise RuntimeError(f"no parse for {lang}:{page}: {data}")
    return data["parse"]["wikitext"]


def _ws_strip_top(text: str) -> str:
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


def _ws_strip_bottom(text: str) -> str:
    for marker in [
        "== Примечания ==", "== Notes ==", "==Notes==", "== Footnotes ==",
        "== הערות שוליים ==", "== المراجع ==", "==المراجع==",
    ]:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    text = re.sub(r"\[\[(Категория|Category|Catégorie|Categoria|Kategorie|分类|تصنيف|קטגוריה|श्रेणी):[^\]]+\]\]", "", text)
    text = re.sub(r"\n\[\[[a-z][a-z-]*:[^\]]+\]\]", "", text)
    return text.rstrip()


def _ws_inline(text: str) -> str:
    text = re.sub(r"<center[^>]*>\s*(.*?)\s*</center>",
                  lambda m: f"\n\n# {m.group(1)}\n\n" if m.group(1).strip() else "",
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


def _ws_templates(text: str) -> str:
    def repl(m: re.Match) -> str:
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


def _ws_headings(text: str) -> str:
    text = re.sub(r"^======\s*(.+?)\s*======\s*$", r"###### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^=====\s*(.+?)\s*=====\s*$", r"##### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^====\s*(.+?)\s*====\s*$", r"#### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^===\s*(.+?)\s*===\s*$", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^==\s*(.+?)\s*==\s*$", r"## \1", text, flags=re.MULTILINE)
    return text


def _ws_normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def ws_convert_page(lang: str, page: str) -> str:
    wt = _ws_fetch_wikitext(lang, page)
    wt = _ws_strip_top(wt)
    wt = _ws_strip_bottom(wt)
    wt = _ws_inline(wt)
    wt = _ws_templates(wt)
    wt = _ws_headings(wt)
    return _ws_normalise(wt)


class WikisourceHTMLExtractor(HTMLParser):
    """Pull prose paragraphs and headings out of a Wikisource parse-text
    response. Targets <div class="prp-pages-output"> (ProofreadPage) and
    falls back to <div class="mw-parser-output">. Skips header/footer
    boilerplate, page-number markers, footnotes, and noprint blocks.
    """

    SKIP_CLASSES = {
        "ws-noexport", "noprint", "pagenum", "ws-pagenum",
        "mw-references-wrap", "references", "reflist",
        "headertemplate", "gen_header_backlink", "gen_header_forelink",
        "ws-page-container",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_body = 0          # depth inside prp-pages-output / mw-parser-output
        self.skip_depth = 0       # inside a class we want to drop
        self.in_ref = 0           # inside ref / footnote
        self.current_kind: str | None = None
        self.current_buf: list[str] = []
        self.collected: list[tuple[str, str]] = []

    def _is_skip(self, attrs):
        cls = (attrs.get("class") or "").split()
        for c in cls:
            if c in self.SKIP_CLASSES:
                return True
        if attrs.get("id") in ("headerContainer", "ws-data", "footerContainer"):
            return True
        if attrs.get("role") == "note":
            return True
        return False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.in_body:
            cls = (a.get("class") or "").split()
            if "prp-pages-output" in cls or "mw-parser-output" in cls:
                self.in_body = 1
            return
        # Inside body. Skip-region check.
        if self.skip_depth:
            if tag in ("div", "span", "table", "tr", "td", "p", "a", "sup", "section"):
                self.skip_depth += 1
            return
        if self._is_skip(a):
            self.skip_depth = 1
            return
        if tag in ("script", "style"):
            self.skip_depth = 1
            return
        if tag == "div":
            self.in_body += 1
            return
        if tag == "sup":
            cls = (a.get("class") or "")
            if "reference" in cls or "noprint" in cls:
                self.in_ref += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            self.current_kind = f"h{tag[1]}"
            self.current_buf = []
            return
        if tag == "p":
            self.flush()
            self.current_kind = "p"
            self.current_buf = []
            return
        if tag == "br":
            if self.current_kind:
                self.current_buf.append("\n")
            return
        if tag in ("em", "i"):
            if self.current_kind:
                self.current_buf.append("*")
            return
        if tag in ("strong", "b"):
            if self.current_kind:
                self.current_buf.append("**")
            return

    def handle_endtag(self, tag):
        if not self.in_body:
            return
        if self.skip_depth:
            if tag in ("div", "span", "table", "tr", "td", "p", "a", "sup", "section", "script", "style"):
                self.skip_depth -= 1
            return
        if tag == "div":
            self.in_body -= 1
            if self.in_body == 0:
                self.flush()
            return
        if tag == "sup" and self.in_ref:
            self.in_ref -= 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush()
            return
        if tag == "p":
            self.flush()
            return
        if tag in ("em", "i"):
            if self.current_kind:
                self.current_buf.append("*")
            return
        if tag in ("strong", "b"):
            if self.current_kind:
                self.current_buf.append("**")
            return

    def handle_data(self, data):
        if not self.in_body or self.skip_depth or self.in_ref:
            return
        if self.current_kind:
            self.current_buf.append(data)

    def flush(self):
        if self.current_kind and self.current_buf:
            text = "".join(self.current_buf)
            text = text.replace("​", "")  # zero-width space (page markers)
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r" *\n *", "\n", text)
            text = text.strip()
            if text:
                self.collected.append((self.current_kind, text))
        self.current_kind = None
        self.current_buf = []


def ws_fetch_html(lang: str, page: str) -> str:
    base = f"https://{lang}.wikisource.org/w/api.php"
    params = {"action": "parse", "page": page, "prop": "text",
              "format": "json", "formatversion": "2"}
    raw = fetch(base + "?" + urllib.parse.urlencode(params))
    data = json.loads(raw.decode("utf-8"))
    if "parse" not in data:
        raise RuntimeError(f"no parse for {lang}:{page}: {data}")
    return data["parse"]["text"]


def ws_html_to_markdown(html_doc: str, *, heading_offset: int = 0) -> str:
    p = WikisourceHTMLExtractor()
    p.feed(html_doc)
    p.close()
    lines: list[str] = []
    for kind, text in p.collected:
        if kind.startswith("h"):
            level = max(1, int(kind[1:]) - 1 + heading_offset)
            lines.append("\n" + ("#" * min(level, 6)) + " " + text + "\n")
        else:
            lines.append(text + "\n")
    body = "\n".join(lines)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def cmd_wikisource_html(args):
    pages = [p.strip() for p in args.pages.split(",") if p.strip()]
    chunks: list[str] = []
    for page in pages:
        html_doc = ws_fetch_html(args.lang, page)
        md = ws_html_to_markdown(html_doc)
        if len(pages) > 1:
            leaf = page.split("/")[-1].replace("_", " ")
            chunks.append(f"# {leaf}\n\n{md}")
        else:
            chunks.append(md)
        time.sleep(0.5)
    body = "\n\n".join(chunks)
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    fm = make_frontmatter({
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    })
    out = fm + body
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"wrote {args.output} ({len(out):,} bytes, {len(pages)} pages)")


def cmd_wikisource_multi(args):
    pages = [p.strip() for p in args.pages.split(",") if p.strip()]
    chunks: list[str] = []
    for page in pages:
        body = ws_convert_page(args.lang, page)
        # heading from page title -- promote to top-level chapter
        # split off any leading shared prefix like "X/Y" -> use Y
        leaf = page.split("/")[-1].replace("_", " ")
        chunks.append(f"# {leaf}\n\n{body}")
        time.sleep(0.5)
    body = "\n\n".join(chunks)
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    fm = make_frontmatter({
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    })
    out = fm + body
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(out, encoding="utf-8")
    print(f"wrote {args.output} ({len(out):,} bytes, {len(pages)} pages)")


# ---------------------------------------------------------------------------
# Frontmatter helper (same shape as scripts/convert-wikisource.py)
# ---------------------------------------------------------------------------

def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    by = sub.add_parser("benyehuda", help="Project Ben-Yehuda")
    by.add_argument("--id", required=True, help="numeric work id (the /read/N id)")
    by.add_argument("--title", required=True)
    by.add_argument("--author", required=True)
    by.add_argument("--language", required=True)
    by.add_argument("--year", required=True)
    by.add_argument("--output", required=True)
    by.set_defaults(func=cmd_benyehuda)

    gj = sub.add_parser("ganjoor", help="Ganjoor.net Persian poetry")
    gj.add_argument("--cat", type=int, required=True, help="category id (e.g. 24 for Khayyam Rubaiyat)")
    gj.add_argument("--limit", type=int, default=0, help="max poems (0 = all)")
    gj.add_argument("--title", required=True)
    gj.add_argument("--author", required=True)
    gj.add_argument("--language", required=True)
    gj.add_argument("--year", required=True)
    gj.add_argument("--source-url", required=True)
    gj.add_argument("--output", required=True)
    gj.set_defaults(func=cmd_ganjoor)

    wh = sub.add_parser("wikisource-html", help="Wikisource via rendered HTML (handles ProofreadPage)")
    wh.add_argument("--lang", required=True)
    wh.add_argument("--pages", required=True, help="comma-separated page titles")
    wh.add_argument("--title", required=True)
    wh.add_argument("--author", required=True)
    wh.add_argument("--language", required=True)
    wh.add_argument("--year", required=True)
    wh.add_argument("--source-url", required=True)
    wh.add_argument("--output", required=True)
    wh.set_defaults(func=cmd_wikisource_html)

    wm = sub.add_parser("wikisource-multi", help="concatenate Wikisource pages")
    wm.add_argument("--lang", required=True)
    wm.add_argument("--pages", required=True, help="comma-separated page titles")
    wm.add_argument("--title", required=True)
    wm.add_argument("--author", required=True)
    wm.add_argument("--language", required=True)
    wm.add_argument("--year", required=True)
    wm.add_argument("--source-url", required=True)
    wm.add_argument("--output", required=True)
    wm.set_defaults(func=cmd_wikisource_multi)

    args = p.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
