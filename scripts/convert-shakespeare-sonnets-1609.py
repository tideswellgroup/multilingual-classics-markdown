#!/usr/bin/env python3
"""
convert-shakespeare-sonnets-1609.py: build the en-GB corpus book from the
original-spelling 1609 Quarto of Shake-speares Sonnets on English Wikisource.

The Quarto is transcribed page-by-page in the Page: namespace and assembled
into one subpage per sonnet (.../Sonnet 1 .. /Sonnet 154), each subpage
transcluding the right page sections so a sonnet that runs across a page break
is delivered whole. This script fetches the rendered text of every sonnet
subpage, lifts the verse lines out of the ppoem markup (dropping the ornamental
sonnet number, the drop-cap and small-cap styling, the fleuron and the running
chrome), and writes one markdown file with a heading per sonnet.

Original 1609 orthography is preserved verbatim: u/v and i/j swaps (neuer,
liuery, ioy), the long-s already normalised by the transcription, -ie and -esse
endings, and the Quarto's own spelling and punctuation. Nothing is modernized.
"""

from __future__ import annotations

import argparse
import html as H
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"
BASE = "https://en.wikisource.org/w/api.php"
WORK = "Shake-speares Sonnets, Never before Imprinted"


def fetch_rendered(page: str, retries: int = 5) -> str:
    q = urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "text",
        "format": "json", "formatversion": "2",
        "disableeditsection": "1", "disabletoc": "1",
    })
    req = urllib.request.Request(f"{BASE}?{q}", headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            if "error" in data:
                raise SystemExit(f"API error on {page}: {data['error']}")
            return data["parse"]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt + 1 < retries:
                time.sleep(30 * (attempt + 1))
                continue
            raise


def strip_balanced_div(html: str, needle: str) -> str:
    """Remove <div ...needle...>...</div> blocks, balancing nested divs."""
    open_re = re.compile(r"<div\b([^>]*)>", re.IGNORECASE)
    close_re = re.compile(r"</div\s*>", re.IGNORECASE)
    out, i, n = [], 0, len(html)
    while i < n:
        m = open_re.search(html, i)
        if not m:
            out.append(html[i:])
            break
        if needle not in m.group(1):
            out.append(html[i:m.end()])
            i = m.end()
            continue
        depth, j = 1, m.end()
        while j < n and depth:
            no, nc = open_re.search(html, j), close_re.search(html, j)
            if not nc:
                break
            if no and no.start() < nc.start():
                depth += 1
                j = no.end()
            else:
                depth -= 1
                j = nc.end()
        out.append(html[i:m.start()])
        i = j
    return "".join(out)


CSSISH = re.compile(r"mw-parser-output|[{}]|text-transform|font-size|dropinitial")


def clean_sonnet(html: str) -> list[str]:
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<figure[^>]*>.*?</figure>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<img\b[^>]*/?>", "", html, flags=re.IGNORECASE)
    html = strip_balanced_div(html, "noexport")     # running header + footer chrome
    html = re.sub(r"<br\s*/?>", "\n", html)
    html = re.sub(r"<[^>]+>", "", html)              # drop all remaining tags
    html = H.unescape(html)
    # drop every Unicode format character (zero-width spaces, joiners, BOM,
    # directional marks) that the ppoem rendering scatters around the text
    html = "".join(ch for ch in html if unicodedata.category(ch) != "Cf")
    lines = []
    for raw in html.split("\n"):
        s = raw.strip()
        if not s:
            continue
        if re.fullmatch(r"\W*\d+\W*", s):            # ornamental sonnet number (may carry an invisible prefix)
            continue
        if CSSISH.search(s):                         # leaked style fragments
            continue
        if re.fullmatch(r"Shake-speares,?|SONNETS\.|Shake-speares SONNETS\.|FINIS\.", s):
            continue                                 # collection title / terminal rubric
        lines.append(s)
    return lines


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--first", type=int, default=1)
    p.add_argument("--last", type=int, default=154)
    p.add_argument("--delay", type=float, default=4.0)
    p.add_argument("--output", default="books/en-GB/William Shakespeare/Shake-speares Sonnets.md")
    p.add_argument("--dry-run", type=int, nargs="*", help="print given sonnet numbers and exit")
    args = p.parse_args()

    if args.dry_run:
        for n in args.dry_run:
            page = f"{WORK}/Sonnet {n}"
            lines = clean_sonnet(fetch_rendered(page))
            print(f"--- Sonnet {n}: {len(lines)} lines ---")
            for ln in lines:
                print(ln)
            time.sleep(args.delay)
        return 0

    fm = (
        "---\n"
        "title: Shake-speares Sonnets\n"
        "author: William Shakespeare\n"
        "language: en-GB\n"
        "year: 1609\n"
        "source: Wikisource (en)\n"
        f'source_url: "https://en.wikisource.org/wiki/{urllib.parse.quote(WORK.replace(chr(32), chr(95)))}"\n'
        "license: Public domain in the United States\n"
        'selection_note: "The complete sequence of 154 sonnets from the 1609 first edition (Quarto), in order. The prefatory dedication epistle and the poem A Lover\'s Complaint that follows the sonnets in the Quarto are omitted; each sonnet is a heading."\n'
        'source_note: "Verbatim original-spelling text of the 1609 Quarto (the John Wright imprint) as transcribed on English Wikisource from the page-scan edition. Orthography stands as printed: u/v and i/j are unmodernized (neuer, liuery, ioy, vse), as are the -ie and -esse endings and the Quarto punctuation. The ornamental sonnet numbers, drop-capital styling and the fleuron are dropped; a plain Sonnet N heading is supplied for each."\n'
        "---\n"
    )
    parts = []
    for n in range(args.first, args.last + 1):
        lines = clean_sonnet(fetch_rendered(f"{WORK}/Sonnet {n}"))
        if not (10 <= len(lines) <= 16):
            raise SystemExit(f"Sonnet {n}: unexpected line count {len(lines)}; aborting")
        parts.append(f"## Sonnet {n}\n\n" + "\n".join(lines))
        if n < args.last:
            time.sleep(args.delay)
    body = "\n\n".join(parts) + "\n"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + body, encoding="utf-8")
    print(f"wrote {out} ({len(fm+body):,} bytes, {args.last - args.first + 1} sonnets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
