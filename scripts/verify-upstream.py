#!/usr/bin/env python3
"""
verify-upstream.py: fidelity audit of vendored books against their live
upstream sources.

For every book whose frontmatter `source_url` points at a Wikisource page,
fetch the current wikitext and compare occurrence counts of drop-prone
literary marks (Thai section marks, danda, Arabic punctuation and the
honorific ligature, guillemets, ellipses). A book is flagged when the
vendored body carries FEWER of a mark than the source: the signature of a
conversion step silently swallowing content.

This gate found real losses before the v1 release: dropped Thai fongman
stanza marks (table-cell flattening), and all 48 verse interludes of Alf
Laylah wa-Laylah (unhandled div blocks). It also produces false positives
by design: marks inside stripped editorial apparatus (notes sections, ref
footnotes, header templates) count in the source but are correctly absent
from the vendored body. EVERY flag therefore needs root-causing before
action; the reliable follow-up is regenerating the book with the matching
convert-*.py script and diffing against the vendored file.

Usage:
  scripts/verify-upstream.py                 # audit every Wikisource book
  scripts/verify-upstream.py books/th/       # audit a subtree
  scripts/verify-upstream.py --delay 10      # be extra polite to the API
  scripts/verify-upstream.py --marks "๏๚๛"   # custom mark set

Exits 0 when nothing is flagged, 1 when at least one book shows drops,
2 when any source could not be fetched. Non-Wikisource sources (Gutenberg,
Internet Archive, Aozora, ...) are skipped; extending the fetch layer to
more upstreams is welcome.
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
from pathlib import Path

# Drop-prone marks seen across the corpus's scripts: Thai section marks and
# abbreviation signs, Devanagari danda, Urdu full stop, Arabic punctuation
# and the honorific ligature (U+FDFA, travels as a template on ar.wikisource),
# guillemets, low quotes, ellipsis, and CJK punctuation (ideographic comma
# and full stop, corner and title brackets, full-width punctuation), without
# which the comparison is vacuous for zh/ja/ko books.
DEFAULT_MARKS = "๏๚๛ฯๆ।॥۔؟،؛ﷺ«»„…、。，「」『』《》！？；："

USER_AGENT = "multilingual-classics-markdown/1.0 (verify-upstream)"

WIKISOURCE_URL = re.compile(
    r'source_url:\s*"?(https://(?:([a-z-]+)\.)?wikisource\.org/wiki/([^"\s]+))"?'
)


def find_wikisource_books(paths: list[Path]) -> list[tuple[Path, str, str]]:
    books = []
    for root in paths:
        candidates = sorted(root.rglob("*.md")) if root.is_dir() else [root]
        for p in candidates:
            text = p.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                continue
            fm = text.split("\n---\n", 1)[0]
            m = WIKISOURCE_URL.search(fm)
            if m:
                # group 2 is None for the multilingual wikisource.org (no
                # language subdomain): fetch_source maps that to the bare host
                books.append((p, m.group(2) or '', urllib.parse.unquote(m.group(3))))
    return books


def fetch_source(lang: str, page: str, rendered: bool, retries: int = 3) -> str | None:
    """Fetch the page's raw wikitext, or with rendered=True its rendered text
    (HTML stripped to plain text). Rendered mode is REQUIRED for books built
    by multi-page walks or ProofreadPage transclusion: their top page's raw
    wikitext is only an index, so a wikitext comparison passes vacuously.
    Rendered text includes transclusions and template output (the ar {{ص}}
    honorific, th verse-table content) at the cost of extra apparatus noise
    from header and license boxes."""
    prop = "text" if rendered else "wikitext"
    host = f"{lang}.wikisource.org" if lang else "wikisource.org"
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "parse",
            "page": page.replace("_", " "),
            "prop": prop,
            "format": "json",
            "formatversion": "2",
        }
    )
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                content = json.loads(r.read().decode("utf-8"))["parse"][prop]
            if rendered:
                content = re.sub(r"<[^>]+>", " ", content)
                content = html.unescape(content)
            return content
        except Exception as e:  # noqa: BLE001 - report and retry/skip
            if "429" in str(e) and attempt + 1 < retries:
                time.sleep(30 * (attempt + 1))
                continue
            print(f"FETCH FAIL {lang}:{page}: {e}", file=sys.stderr)
            return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["books"], help="files or directories (default: books/)")
    parser.add_argument("--marks", default=DEFAULT_MARKS, help="characters to count (default: curated drop-prone set)")
    parser.add_argument("--delay", type=float, default=6.0, help="seconds between API requests (default: 6)")
    parser.add_argument("--rendered", action="store_true", help="compare against rendered page text (transclusions and template output included); use for books built by multi-page walks")
    args = parser.parse_args()

    books = find_wikisource_books([Path(p) for p in args.paths])
    print(f"auditing {len(books)} Wikisource-sourced book(s), {args.delay:.0f}s spacing")

    flagged = 0
    fetch_failures = 0
    for i, (path, lang, page) in enumerate(books):
        wikitext = fetch_source(lang, page, args.rendered)
        if wikitext is None:
            fetch_failures += 1
            continue
        body = path.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        drops = []
        for ch in dict.fromkeys(args.marks):
            src, vend = wikitext.count(ch), body.count(ch)
            if vend < src:
                drops.append(f"{ch} source x{src} vendored x{vend}")
        if drops:
            flagged += 1
            print(f"DROPS {path}: " + "; ".join(drops))
        else:
            print(f"ok    {path}")
        if i + 1 < len(books):
            time.sleep(args.delay)

    print(f"done: {flagged} flagged, {fetch_failures} fetch failure(s), {len(books)} audited")
    if fetch_failures:
        return 2
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
