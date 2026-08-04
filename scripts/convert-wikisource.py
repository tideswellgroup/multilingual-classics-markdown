#!/usr/bin/env python3
"""
convert-wikisource.py: fetch a Wikisource page (any language) and convert
the wikitext body to vendor-ready markdown for the multilingual-classics-markdown corpus.

Strips metadata templates, footnote refs, categories, interlanguage links.
Converts the wiki idioms we actually encounter in literary texts: chapter
markers, italics/bold, internal links, simple templates wrapping content.

Not a general-purpose wikitext parser. Tuned for the v1 corpus picks; passes
through anything it doesn't recognise and accepts a small amount of residual
template syntax in the output if the alternative is silently swallowing prose.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_wikitext(lang: str, page: str) -> str:
    base = f"https://{lang}.wikisource.org/w/api.php"
    params = {
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["parse"]["wikitext"]


def _is_metadata_template(body: str) -> bool:
    """A top-of-page template is metadata (strippable) when none of its
    unnamed args look like prose. Headers carry named params only; banners
    carry bare flags; verse/content templates carry unnamed prose args and
    must stop the stripping loop."""
    body = re.sub(r"\{\{[^{}]*\}\}", "", body)  # nested template spans are not args
    parts = [p.strip() for p in body.split("|")[1:]]
    for p in parts:
        if not p or re.match(r"^[^=\s]+\s*=", p):
            continue
        if re.fullmatch(r"[\d๐-๙\s.,:;()\-]+", p):
            continue  # bare numbers (incl. Thai digits): banner flags, not prose
        if re.search(r"\.(pdf|djvu|png|jpe?g|svg|tiff?)\s*$", p, re.IGNORECASE):
            continue  # scan-index filenames in maintenance banners
        if re.search(r"[^\x00-\x7F]", p) or (len(p) > 12 and " " in p):
            return False
    return True


def strip_top_metadata(text: str) -> str:
    """Strip top-of-page metadata templates (e.g. {{Отексте|...}} on ru,
    {{Header|...}} on en) and magic words like __NOTOC__. Pages often stack
    several (maintenance banner, then header), so strip repeatedly, but only
    while the leading template is metadata-shaped; a content-bearing template
    (e.g. th verse templates directly after the header) stops the loop."""
    while True:
        lt = text.lstrip()
        if not lt.startswith("{{"):
            text = lt
            break
        depth = 0
        i = 0
        end = None
        while i < len(lt):
            if lt[i : i + 2] == "{{":
                depth += 1
                i += 2
            elif lt[i : i + 2] == "}}":
                depth -= 1
                i += 2
                if depth == 0:
                    end = i
                    break
            else:
                i += 1
        if end is None:
            text = lt
            break
        if _is_metadata_template(lt[2 : end - 2]):
            text = lt[end:]
        else:
            text = lt
            break
    text = re.sub(r"__[A-Z]+__", "", text)
    return text.lstrip()


def strip_bottom_metadata(text: str) -> str:
    """Strip footnotes section, categories, and interlanguage links from the
    bottom of the page."""
    for marker in ["== Примечания ==", "== Notes ==", "==Notes==", "== Footnotes =="]:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx]
            break
    text = re.sub(r"\[\[(Категория|Category|Catégorie|Categoria|Kategorie|分类|หมวดหมู่|Thể loại|קטגוריה|تصنيف|رده|زمرہ|श्रेणी|분류|Κατηγορία|Categori|Luokka|Flokkur|Kategoria|Kategorio):[^\]]+\]\]", "", text)
    text = re.sub(r"^(หมวดหมู่|Thể loại|קטגוריה|تصنيف|رده|زمرہ|श्रेणी|분류|Κατηγορία|Categori|Luokka|Flokkur|Kategoria|Kategorio|Category):.+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n\[\[[a-z][a-z-]*:[^\]|]+\]\]", "", text)
    return text.rstrip()


def convert_chapter_markers(text: str) -> str:
    """<center>...</center> blocks become H1 headings; empty centres collapse."""
    text = re.sub(
        r"<center[^>]*>\s*(.*?)\s*</center>",
        lambda m: f"\n\n# {m.group(1)}\n\n" if m.group(1).strip() else "",
        text,
        flags=re.DOTALL,
    )
    return text


def convert_div_blocks(text: str) -> str:
    """Unwrap <div>...</div> blocks, keeping inner content as its own
    paragraph. ar.wikisource uses div-wrapped verse interludes inside prose
    (hemistichs separated by &nbsp; runs, normalised by the inline pass that
    runs after this). Nested divs unwrap iteratively."""
    pattern = re.compile(r"<div[^>]*>\s*(.*?)\s*</div>", re.DOTALL)
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(lambda m: "\n\n" + m.group(1).strip() + "\n\n", text)
    return text


def convert_inline_markup(text: str) -> str:
    text = re.sub(r"'''([^']+?)'''", r"**\1**", text)
    text = re.sub(r"''([^']+?)''", r"*\1*", text)
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    text = re.sub(r"<poem[^>]*>", "", text)
    text = re.sub(r"</poem>", "", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&mdash;", "—")
    text = text.replace("&ndash;", "–")
    text = text.replace("&amp;", "&")
    return text


def convert_wikitables(text: str) -> str:
    """Flatten MediaWiki table markup ({| ... |}) into plain verse lines.

    Two-column verse tables (e.g. Thai klon on th.wikisource) put one verse
    line per row, hemistichs in separate cells; rows may carry lone
    stanza-mark cells (fongman ๏ opening a stanza, angkhankhu ๚ and khomut ๛
    closing a section, often right-aligned via cell attributes). Cells join
    with a single space so the caesura survives and lone-mark cells stay on
    their verse line. Cell attributes (`|align="right"|๛`) are stripped;
    captions keep their text. Each row becomes its own paragraph."""
    attr_prefix = re.compile(r'^\s*(?:[\w-]+\s*=\s*(?:"[^"|]*"|\'[^\'|]*\'|[^\s|]+)\s*)+\|')

    def clean_cell(cell: str) -> str:
        return attr_prefix.sub("", cell).strip()

    out: list[str] = []
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("{|"):
            in_table = True
            continue
        if in_table and s.startswith("|}"):
            in_table = False
            continue
        if in_table or s.startswith("|"):
            if s.startswith("|-") or s.startswith("!"):
                continue
            if s.startswith("|+"):
                caption = clean_cell(s[2:])
                if caption:
                    out.append(caption)
                    out.append("")
                continue
            if s.startswith("|"):
                cells = [clean_cell(c) for c in s.lstrip("|").split("||")]
                cells = [c for c in cells if c]
                if cells:
                    out.append(" ".join(cells))
                    out.append("")
            continue
        out.append(line)
    return "\n".join(out)


def convert_simple_templates(text: str) -> str:
    """Best-effort: where a template wraps prose content, extract the prose.
    {{template|arg|prose|prose2|}} -> keep every pipe-separated arg that looks
    like prose (length > 12 with a space or non-ASCII), in original order,
    joined by a single space. Verse templates (e.g. th กาพย์กลอน with one
    hemistich per arg) thus keep both hemistichs with the caesura preserved.
    Args that are purely Thai section marks (fongman ๏, angkhankhu ๚, khomut
    ๛, paiyannoi ฯ) are kept too. Named parameters (name=value) and other
    non-prose args are dropped; templates yielding nothing collapse to empty."""
    # No-pipe templates that render a specific glyph rather than wrapping
    # prose. ar.wikisource {{ص}} renders the honorific ligature U+FDFA.
    GLYPH_TEMPLATES = {
        "ص": "ﷺ",
        "صلى الله عليه وسلم": "ﷺ",
    }

    def replace_template(m: re.Match) -> str:
        body = m.group(1)
        if "|" not in body:
            return GLYPH_TEMPLATES.get(body.strip(), "")
        keep = []
        for part in body.split("|")[1:]:
            c = part.strip()
            if not c:
                continue
            if re.match(r"^[^=\s]+\s*=", c):
                continue
            if re.search(r"[^\x00-\x7F]", c) or (len(c) > 12 and " " in c):
                keep.append(c)
        return " ".join(keep)

    pattern = re.compile(r"\{\{([^{}]+?)\}\}", flags=re.DOTALL)
    prev = None
    while text != prev:
        prev = text
        text = pattern.sub(replace_template, text)
    return text


def convert_headings(text: str) -> str:
    text = re.sub(r"^======\s*(.+?)\s*======\s*$", r"###### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^=====\s*(.+?)\s*=====\s*$", r"##### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^====\s*(.+?)\s*====\s*$", r"#### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^===\s*(.+?)\s*===\s*$", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^==\s*(.+?)\s*==\s*$", r"## \1", text, flags=re.MULTILINE)
    return text


def normalise_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing whitespace EXCEPT an exact two-space CommonMark hard
    # break, which the corpus uses for verse lines within a stanza.
    text = re.sub(r"(?<=\S)  \n", "\x00\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    # Collapse runs of plain ASCII spaces; NBSP runs (verse caesuras) survive
    # untouched since markdown renderers collapse plain runs anyway.
    text = re.sub(r"  +", " ", text)
    text = text.replace("\x00\n", "  \n")
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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lang", required=True, help="Wikisource subdomain (ru, fr, vi, etc.)")
    p.add_argument("--page", required=True, help="Wikisource page title (URL-decoded)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 language tag for the content")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    wt = fetch_wikitext(args.lang, args.page)
    wt = strip_top_metadata(wt)
    wt = strip_bottom_metadata(wt)
    wt = convert_chapter_markers(wt)
    wt = convert_div_blocks(wt)
    wt = convert_inline_markup(wt)
    wt = convert_wikitables(wt)
    wt = convert_simple_templates(wt)
    wt = convert_headings(wt)
    wt = normalise_whitespace(wt)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": f"https://{args.lang}.wikisource.org/wiki/{urllib.parse.quote(args.page.replace(' ', '_'))}",
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + wt
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out.encode(chr(39)+chr(117)+chr(116)+chr(102)+chr(45)+chr(56)+chr(39))):,} bytes, {len(out):,} chars, {len(wt.splitlines()):,} body lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
