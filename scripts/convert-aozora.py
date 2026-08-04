#!/usr/bin/env python3
"""
convert-aozora.py: fetch an Aozora Bunko HTML file and convert to
vendor-ready markdown for the multilingual-classics-markdown corpus.

Aozora HTML idioms handled:
- Shift-JIS encoding (declared in HTTP body)
- <ruby><rb>kanji</rb><rp>(</rp><rt>furigana</rt><rp>)</rp></ruby> -> keep kanji only
- <br /> line breaks: every <br /> ends a line; runs of empty lines collapse;
  paragraphs are separated by the ideographic space U+3000 at line start
- [#editorial note] markers in full-width brackets -> stripped
- <img class="gaiji" alt="...">: keep the alt text fragment that explains the
  out-of-JIS character; not pretty but lossless-ish
- <div class="chitsuki_2"> ... </div>: right-aligned, typically a date; render
  as own paragraph
- <div class="jisage_*"> indented blocks: keep prose, drop the indent

Not a general HTML parser. Tuned for the Aozora work pages the v1 corpus
uses; passes through anything unrecognised.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    # Aozora work HTML is Shift_JIS; declared in the prolog. Try sjis then fallback.
    for enc in ("shift_jis", "cp932", "utf-8"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("shift_jis", errors="replace")


def extract_main(html: str) -> str:
    m = re.search(r'<div class="main_text">(.*?)</div>\s*(?:<div class="bibliographical_information">|</body>)',
                  html, re.DOTALL)
    if not m:
        # fallback: just grab from main_text to end-of-body
        m = re.search(r'<div class="main_text">(.*?)</body>', html, re.DOTALL)
    if not m:
        raise SystemExit("could not locate <div class=\"main_text\">")
    return m.group(1)


def strip_ruby(text: str) -> str:
    """Keep <rb>kanji</rb>, drop <rp>...</rp> and <rt>furigana</rt>."""
    # Form 1: <ruby><rb>X</rb><rp>(</rp><rt>Y</rt><rp>)</rp></ruby>
    text = re.sub(
        r"<ruby>\s*<rb>(.*?)</rb>\s*<rp>.*?</rp>\s*<rt>.*?</rt>\s*<rp>.*?</rp>\s*</ruby>",
        r"\1",
        text,
        flags=re.DOTALL,
    )
    # Form 2: <ruby>X<rt>Y</rt></ruby>  (no <rb>, no <rp>)
    text = re.sub(
        r"<ruby>(.*?)<rt>.*?</rt>\s*</ruby>",
        r"\1",
        text,
        flags=re.DOTALL,
    )
    # Form 3: any remaining <rb>/<rt>/<rp> tags get dropped or extracted defensively
    text = re.sub(r"<rb>", "", text)
    text = re.sub(r"</rb>", "", text)
    text = re.sub(r"<rt>.*?</rt>", "", text, flags=re.DOTALL)
    text = re.sub(r"<rp>.*?</rp>", "", text, flags=re.DOTALL)
    text = re.sub(r"</?ruby>", "", text)
    return text


def strip_editorial(text: str) -> str:
    # ［＃...］ full-width-bracket editorial notes
    text = re.sub(r"［＃[^］]*］", "", text)
    # ※［＃...］ gaiji descriptors
    text = re.sub(r"※［＃[^］]*］", "", text)
    return text


def convert_gaiji_img(text: str) -> str:
    """gaiji <img> tags carry an alt= that describes the missing character.
    Replace the whole tag with a tagged placeholder so the text stays parseable.
    Falls back to dropping if no alt."""
    def repl(m: re.Match) -> str:
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        if alt:
            return alt.group(1)
        return ""
    text = re.sub(r'<img[^>]*class="gaiji"[^>]*/?>', repl, text)
    text = re.sub(r'<img[^>]*gaiji="gaiji"[^>]*/?>', repl, text)
    return text


def convert_divs(text: str) -> str:
    # chitsuki_2: right-aligned, usually a date or attribution. Promote to own paragraph.
    text = re.sub(
        r'<div class="chitsuki_2"[^>]*>(.*?)</div>',
        lambda m: f"\n\n{m.group(1).strip()}\n\n",
        text,
        flags=re.DOTALL,
    )
    # jisage_N: indented block, prose. Keep contents, drop wrapper.
    text = re.sub(
        r'<div class="jisage_[^"]*"[^>]*>(.*?)</div>',
        lambda m: m.group(1),
        text,
        flags=re.DOTALL,
    )
    # Generic remaining <div>...</div>: keep contents
    text = re.sub(r'</?div[^>]*>', '', text)
    return text


def convert_headings(text: str) -> str:
    """Aozora headings: h3/h4 inside main_text usually mark section breaks."""
    for level in (1, 2, 3, 4):
        text = re.sub(
            rf'<h{level}[^>]*>(.*?)</h{level}>',
            lambda m, lv=level: f"\n\n{'#' * lv} {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
            text,
            flags=re.DOTALL,
        )
    # Aozora also marks heads with classes like midashi
    text = re.sub(
        r'<span class="(?:o-)?midashi[^"]*">(.*?)</span>',
        lambda m: f"\n\n# {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
        text,
        flags=re.DOTALL,
    )
    return text


def linebreaks_to_paragraphs(text: str) -> str:
    # <br /> -> newline. Successive newlines collapse later.
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Strip any remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    # Aozora paragraphs typically open with U+3000 (ideographic space). Treat
    # those as paragraph starts and normalise: keep one blank line between
    # paragraphs, drop the leading 3000 spaces (markdown reflow handles it).
    lines = [ln.rstrip() for ln in text.split("\n")]
    out: list[str] = []
    para_buf: list[str] = []
    def flush():
        if para_buf:
            joined = "".join(para_buf).strip()
            if joined:
                out.append(joined)
            para_buf.clear()
    for ln in lines:
        if not ln.strip():
            flush()
            continue
        # Heading lines start with '#'
        if ln.lstrip().startswith("#"):
            flush()
            out.append(ln.strip())
            continue
        # New paragraph if line starts with ideographic space
        if ln.startswith("　"):
            flush()
            para_buf.append(ln.lstrip("　").strip())
        else:
            para_buf.append(ln.strip())
    flush()
    return "\n\n".join(out)


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
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
    p.add_argument("--url", required=True, help="Aozora work HTML URL (https://www.aozora.gr.jp/cards/.../files/N_M.html)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", default="ja")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    html = fetch(args.url)
    body = extract_main(html)
    body = strip_ruby(body)
    body = strip_editorial(body)
    body = convert_gaiji_img(body)
    body = convert_divs(body)
    body = convert_headings(body)
    body = linebreaks_to_paragraphs(body)
    body = normalise(body)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Aozora Bunko",
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
