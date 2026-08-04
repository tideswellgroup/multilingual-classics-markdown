#!/usr/bin/env python3
"""
convert-wikisource-proofread-div.py: variant of convert-wikisource-html.py for
ProofreadPage transclusions whose entire body is wrapped in a centering
`role="presentation"` table (the {{CentrujStart2}}/{{JustowanieStart2}} idiom
common on pl.wikisource).

convert-wikisource-html.py strips every <table> as chrome. On these pages that
table wraps the whole poem/prose, so the shared route yields only the footnote
apparatus. This script first isolates the inner content of the single
`<div class="prp-pages-output">...</div>` block (the proofread body), then hands
it to the exact same cleaning pipeline as convert-wikisource-html.py. Because
the isolated body contains no tables of its own (verified per source), the
table strip in that pipeline is a harmless no-op and the verse survives.

Use for pl.wikisource proofread pages where convert-wikisource-html.py returns
an almost-empty body. Inspect first: if the rendered HTML has one
prp-pages-output div and no content tables inside it, this is the right tool.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import urllib.parse
from pathlib import Path

# Load the sibling hyphenated module so the cleaning pipeline stays single-source.
_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "convert_wikisource_html", _HERE / "convert-wikisource-html.py"
)
_wh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wh)


def extract_proofread_body(html: str) -> str:
    """Return the inner HTML of the first <div class="prp-pages-output"> block,
    balancing nested <div> so we stop at the matching close tag."""
    idx = html.find('class="prp-pages-output"')
    if idx == -1:
        raise SystemExit("no prp-pages-output block found; wrong tool for this page")
    open_tag = re.compile(r"<div\b[^>]*>")
    m = None
    for cand in open_tag.finditer(html, 0, idx + 1):
        m = cand
    if m is None or m.end() <= idx:
        # opening tag of this div starts at or before idx; find the div that owns idx
        start = html.rfind("<div", 0, idx)
        m = open_tag.match(html, start)
    close_tag = re.compile(r"</div>")
    depth = 1
    j = m.end()
    n = len(html)
    while j < n and depth > 0:
        no = open_tag.search(html, j)
        nc = close_tag.search(html, j)
        if not nc:
            break
        if no and no.start() < nc.start():
            depth += 1
            j = no.end()
        else:
            depth -= 1
            j = nc.end()
    return html[m.end(): j - len("</div>")]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lang", required=True)
    p.add_argument("--page", required=True)
    p.add_argument("--variant", default=None)
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True)
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    html = _wh.fetch_html(args.lang, args.page, variant=args.variant)
    html = extract_proofread_body(html)
    # Drop display:none spans. On pl.wikisource these are page-anchor markers and
    # the hidden half of {{Korekta}} correction pairs (the printed typo, hidden
    # in favour of the visible corrected reading). Keeping them would emit both
    # readings as one doubled word. We reproduce the reading the page displays.
    html = re.sub(
        r'<span[^>]*style="[^"]*display:none[^"]*"[^>]*>.*?</span>',
        "",
        html,
        flags=re.DOTALL,
    )
    html = _wh.strip_chrome(html)
    html = _wh.convert_headings(html)
    html = _wh.convert_blocks(html)
    html = _wh.convert_inline(html)
    html = _wh.strip_residual_tags(html)
    body = _wh.normalise(html)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": f"Wikisource ({args.lang})",
        "source_url": f"https://{args.lang}.wikisource.org/wiki/"
        + urllib.parse.quote(args.page.replace(" ", "_")),
        "license": "Public domain in the United States",
    }
    out = _wh.make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
