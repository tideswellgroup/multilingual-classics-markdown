#!/usr/bin/env python3
"""
convert-bharati.py: build the markdown for Subramania Bharati's தேசிய கீதங்கள்
(National Songs) from the ta.wikisource collection index.

This reuses the tested index walk, template stripping and heading logic of
scripts/convert-wikisource-collection.py, and adds the cleaning the Tamil
poetry sub-pages need and that the generic walker leaves behind:

  - <Poem> ... </Poem>   the generic walker only strips lowercase <poem>;
                         the Tamil pages also use the capitalised tag, so the
                         opening tag survives as debris. Stripped here.
  - leading ":" / "::"   ta.wikisource indents refrain and verse lines with
                         wiki definition-list colons. In markdown a leading
                         colon is literal text, so these are stripped to the
                         bare verse line.
  - duplicate title      each sub-page opens its body with its own "N. title"
                         line, which then repeats under the "## N. title"
                         section heading. The leading repeat is dropped.

Everything else (fetch with 429 backoff, {{header}} stripping, italics/bold,
link flattening, template collapse) comes straight from the shared module so
output shape stays consistent with the rest of the corpus.

Usage:
  scripts/convert-bharati.py --index "<index page>" --title T --author A \
      --language ta --year Y --source-url URL --output books/ta/.../file.md \
      [--year-note ...] [--delay 6]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "wscollection", _HERE / "convert-wikisource-collection.py")
ws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ws)

LANG = "ta"


def clean_inline(text: str) -> str:
    """The shared convert_inline plus the Tamil-specific fixes."""
    text = ws.convert_inline(text)
    text = re.sub(r"(?i)</?poem[^>]*>", "", text)   # catch <Poem>, </Poem>
    text = re.sub(r"^:+\s*", "", text, flags=re.MULTILINE)  # wiki indent colons
    return text


def convert_one(page: str) -> str:
    wt = ws.fetch_wt(LANG, page)
    if not wt:
        return ""
    wt = ws.strip_top_metadata(wt)
    wt = clean_inline(wt)
    wt = ws.strip_simple_templates(wt)
    wt = ws.convert_headings(wt)
    return ws.normalise(wt)


def drop_leading_title(body: str, leaf: str) -> str:
    """Drop the sub-page's own title line when it repeats the section heading."""
    lines = body.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip().rstrip(".") == leaf.strip().rstrip("."):
        del lines[i]
    return "\n".join(lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert Bharati's National Songs from ta.wikisource.")
    ap.add_argument("--index", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--year", required=True)
    ap.add_argument("--year-note")
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--delay", type=float, default=6.0)
    args = ap.parse_args()

    pages = ws.index_sub_pages(LANG, args.index)
    chunks: list[str] = []
    for sp in pages:
        body = convert_one(sp)
        if not body:
            sys.stderr.write(f"[skip] empty: {sp}\n")
            time.sleep(args.delay)
            continue
        leaf = ws.page_leaf(sp)
        body = drop_leading_title(body, leaf)
        chunks.append(f"## {leaf}\n\n{body}")
        time.sleep(args.delay)

    md_body = re.sub(r"\n{3,}", "\n\n", "\n\n".join(chunks)).strip() + "\n"

    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
    }
    if args.year_note:
        meta["year_note"] = args.year_note
    meta.update({
        "source": f"Wikisource ({LANG})",
        "source_url": args.source_url,
        "license": "Public domain in the United States",
    })
    out = ws.make_frontmatter(meta) + md_body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    sys.stderr.write(f"[ok] wrote {dest} ({len(out.encode('utf-8'))} bytes, {len(pages)} sub-pages)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
