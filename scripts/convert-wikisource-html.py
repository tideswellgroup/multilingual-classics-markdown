#!/usr/bin/env python3
"""
convert-wikisource-html.py: fetch a Wikisource page via the MediaWiki action=parse
prop=text endpoint (HTML render, not wikitext) and convert to vendor-ready
markdown.

Use when the wikitext is a thin shell around <pages index="..."> proofread
transclusions (common for zh, ja, ko) so the wikitext route gives you nothing
useful. The rendered HTML inlines the page-by-page text.

For zh.wikisource specifically, the API will deliver simplified-character HTML
when the request goes through with the appropriate variant query
(`uselang=zh-cn` or `variant=zh-cn`). We pass both.

Strips:
- header/footer navigation tables
- prp page-number spans (Page:... markers)
- noprint, sister-project boxes
- citation/category links
Preserves:
- <h2>/<h3> chapter markers as # / ##
- <p> paragraphs
- <dl><dd> blocks (treats as paragraph)
- Inline emphasis from <i>/<em>/<b>/<strong>
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fetch_html(lang: str, page: str, variant: str | None = None) -> str:
    params = {
        "action": "parse",
        "page": page,
        "prop": "text",
        "format": "json",
        "formatversion": "2",
        "disableeditsection": "1",
        "disabletoc": "1",
    }
    if variant:
        params["uselang"] = variant
        params["variant"] = variant
    url = f"https://{lang}.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "multilingual-classics-markdown/1.0",
        "Accept-Language": variant or lang,
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        import json
        data = json.loads(r.read().decode("utf-8"))
    if "error" in data:
        raise SystemExit(f"API error: {data['error']}")
    return data["parse"]["text"]


def _strip_balanced(html: str, tag: str, attr_predicate=None) -> str:
    """Strip all <tag ...>...</tag> blocks balancing nesting. If attr_predicate
    is given, only strip blocks where attr_predicate(attrs_string) is truthy."""
    open_re = re.compile(rf'<{tag}\b([^>]*)>', re.IGNORECASE)
    close_re = re.compile(rf'</{tag}\s*>', re.IGNORECASE)
    out_parts: list[str] = []
    i = 0
    n = len(html)
    while i < n:
        m = open_re.search(html, i)
        if not m:
            out_parts.append(html[i:])
            break
        # Decide whether to strip this block based on attr predicate
        attrs = m.group(1)
        strip_this = (attr_predicate is None) or attr_predicate(attrs)
        if not strip_this:
            # Skip past this open tag, keep it intact, and continue
            out_parts.append(html[i:m.end()])
            i = m.end()
            continue
        # Walk forward balancing opens/closes from m.end()
        depth = 1
        j = m.end()
        while j < n and depth > 0:
            no = open_re.search(html, j)
            nc = close_re.search(html, j)
            if not nc:
                break
            if no and no.start() < nc.start():
                depth += 1
                j = no.end()
            else:
                depth -= 1
                j = nc.end()
        # Append everything before this block
        out_parts.append(html[i:m.start()])
        i = j
    return "".join(out_parts)


def strip_chrome(html: str) -> str:
    # Remove pagenum span chrome FIRST (these are leaf spans, no nesting concern)
    html = re.sub(r'<span class="pagenum ws-pagenum"[^>]*>.*?</span>\s*</span>\s*</span>', '', html, flags=re.DOTALL)
    html = re.sub(r'<span class="pagenum ws-pagenum"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    html = re.sub(r'<span[^>]*class="pagenum-inner[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    html = re.sub(r'<span[^>]*class="[^"]*ws-noexport[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    # Hidden spans: correction templates (e.g. pl {{Korekta}}) render the
    # printed typo in a display:none span next to the visible corrected
    # reading; keeping both concatenates them into one doubled word. Drop
    # anything the page itself hides. (Found during the pl conversion.)
    html = re.sub(r'<span[^>]*style="[^"]*display:\s*none[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)

    # Remove sister-project list
    html = re.sub(r'<ul id="plainSister"[^>]*>.*?</ul>', "", html, flags=re.DOTALL)
    # Reference footnotes / cite_ref
    html = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', "", html, flags=re.DOTALL)
    # Strip <table>...</table> blocks (balanced)
    html = _strip_balanced(html, "table")
    # Strip license / header containers (balanced)
    html = _strip_balanced(html, "div", lambda a: 'id="headerContainer"' in a)
    html = _strip_balanced(html, "div", lambda a: 'class="licenseContainer' in a)
    html = _strip_balanced(html, "div", lambda a: 'class="licensetpl"' in a)
    html = _strip_balanced(html, "div", lambda a: 'class="mw-references-wrap"' in a or 'class="references"' in a)
    # Strip mw-heading wrapper divs but keep the <hN> inside
    html = re.sub(r'<div class="mw-heading[^"]*">(.*?)</div>', r"\1", html, flags=re.DOTALL)
    # Drop HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Drop <style>...</style> and <script>...</script>
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Self-closing link tags
    html = re.sub(r'<link\b[^>]*/?>', '', html, flags=re.IGNORECASE)
    return html


def convert_headings(html: str) -> str:
    for level in (1, 2, 3, 4, 5, 6):
        html = re.sub(
            rf'<h{level}[^>]*>(.*?)</h{level}>',
            lambda m, lv=level: f"\n\n{'#' * lv} {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
            html,
            flags=re.DOTALL,
        )
    return html


def convert_inline(html: str) -> str:
    html = re.sub(r'<(i|em)\b[^>]*>(.*?)</\1>', r"*\2*", html, flags=re.DOTALL)
    html = re.sub(r'<(b|strong)\b[^>]*>(.*?)</\1>', r"**\2**", html, flags=re.DOTALL)
    # Underline -> drop emphasis marker, keep text (markdown has no underline)
    html = re.sub(r'<u\b[^>]*>(.*?)</u>', r"\1", html, flags=re.DOTALL)
    # span carrying underline style; drop wrapper, keep text
    html = re.sub(r'<span[^>]*style="[^"]*underline[^"]*"[^>]*>(.*?)</span>', r"\1", html, flags=re.DOTALL)
    # All remaining <a>/<span>/<small>: drop tag, keep content
    html = re.sub(r'<a\b[^>]*>(.*?)</a>', r"\1", html, flags=re.DOTALL)
    html = re.sub(r'<small\b[^>]*>(.*?)</small>', r"\1", html, flags=re.DOTALL)
    html = re.sub(r'<span[^>]*>(.*?)</span>', r"\1", html, flags=re.DOTALL)
    return html


def convert_blocks(html: str) -> str:
    # <p>...</p> -> own paragraph
    html = re.sub(r'<p[^>]*>\s*(.*?)\s*</p>', lambda m: f"\n\n{m.group(1).strip()}\n\n", html, flags=re.DOTALL)
    # <dl><dd>...</dd></dl> -> paragraph (used for preface/blockquote-ish)
    html = re.sub(r'<dl[^>]*>(.*?)</dl>', lambda m: m.group(1), html, flags=re.DOTALL)
    html = re.sub(r'<dd[^>]*>\s*(.*?)\s*</dd>', lambda m: f"\n\n{m.group(1).strip()}\n\n", html, flags=re.DOTALL)
    html = re.sub(r'<dt[^>]*>\s*(.*?)\s*</dt>', lambda m: f"\n\n**{m.group(1).strip()}**\n\n", html, flags=re.DOTALL)
    # <br> -> line break (then collapse later)
    html = re.sub(r'<br\s*/?>', '\n', html)
    # Remove residual block wrappers
    html = re.sub(r'</?div[^>]*>', '', html)
    return html


def strip_residual_tags(html: str) -> str:
    # Drop anything we didn't recognise
    html = re.sub(r'<[^>]+>', '', html)
    # HTML entities
    repls = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#8203;": "",
        "&#160;": " ",
    }
    for k, v in repls.items():
        html = html.replace(k, v)
    # Generic numeric entities
    html = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), html)
    return html


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    # Collapse empty paragraphs
    text = re.sub(r"(\n\n)\s*(\n\n)+", "\n\n", text)
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
    p.add_argument("--lang", required=True, help="Wikisource subdomain (zh, ja, ko, ...)")
    p.add_argument("--page", required=True)
    p.add_argument("--variant", default=None, help="Script variant (e.g. zh-cn for simplified)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 language tag for content")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    html = fetch_html(args.lang, args.page, variant=args.variant)
    html = strip_chrome(html)
    html = convert_headings(html)
    html = convert_blocks(html)
    html = convert_inline(html)
    html = strip_residual_tags(html)
    body = normalise(html)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": f"https://{args.lang}.wikisource.org/wiki/{urllib.parse.quote(args.page.replace(' ', '_'))}",
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
