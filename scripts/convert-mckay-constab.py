#!/usr/bin/env python3
"""
convert-mckay-constab.py: build the en-JM corpus book from Claude McKay's
Constab Ballads (1912) on English Wikisource, one of the first books of poetry
in Jamaican Patois.

Wikisource transcribes the book from the page scans and gives one subpage per
poem (plus a Glossary), so this fetches each poem's rendered text in the book's
printed order, lifts the verse out of the ppoem markup, and writes one markdown
file with a heading per poem.

The creole-inflected dialect spelling is deliberate literary form and is kept
verbatim; nothing is normalized to standard English.
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
WORK = "Constab Ballads"

# Poems in printed order, then the Glossary, as titled on their subpages.
ITEMS = [
    "De Route March", "Flat-Foot Drill", "Bennie's Departure", "Consolation",
    "Fire Practice", "Second-Class Constable Alston", "Last Words of the Dying Recruit",
    "Bound fe Duty", "Bumming", "De Dog-Driver's Frien'", "To Inspector W. E. Clark",
    "Papine Corner", "Disillusioned", "Cotch Donkey", "Me Whoppin' Big-Tree Boy",
    "A Recruit on the Corpy", "Pay-Day", "The Apple Woman's Complaint",
    "Knutsford Park Races", "The Heart of a Constab", "Fe Me Sal",
    "The Bobby to the Sneering Lady", "The Malingerer", "A Labourer's Life Give Me",
    "Free!", "Comrades Four", "To W. G. G.", "Sukee River", "Glossary",
]

CSSISH = re.compile(r"mw-parser-output|[{}]|text-transform|font-size|dropinitial")


CACHE = Path(__file__).resolve().parent.parent / ".mckay-cache"


def fetch_rendered(page: str, retries: int = 5) -> tuple[str, bool]:
    """Return (rendered_html, from_cache). Rendered pages are cached to disk so
    the parse logic can be re-run without re-crawling Wikisource."""
    CACHE.mkdir(exist_ok=True)
    cache_file = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", page) + ".html")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8"), True
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
            html = data["parse"]["text"]
            cache_file.write_text(html, encoding="utf-8")
            return html, False
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt + 1 < retries:
                time.sleep(30 * (attempt + 1))
                continue
            raise


def strip_balanced_div(html: str, needle: str) -> str:
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


def clean(html: str, title: str) -> list[str]:
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<figure[^>]*>.*?</figure>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<img\b[^>]*/?>", "", html, flags=re.IGNORECASE)
    html = re.sub(r'<span class="pagenum[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    html = re.sub(r'<span[^>]*class="[^"]*ws-pagenum[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    # footnote reference superscripts and the footnote list at the foot of a page
    html = re.sub(r'<sup[^>]*class="[^"]*reference[^"]*"[^>]*>.*?</sup>', "", html, flags=re.DOTALL)
    html = strip_balanced_div(html, "noexport")
    html = strip_balanced_div(html, "references")
    # Stanza gaps: this book renders each poem as a <p> of lines joined by
    # <br />, with stanzas separated by a double <br /> and by <p> boundaries.
    # Each <br /> is followed by a literal newline in the source, so consume
    # that newline (otherwise every single line break becomes a blank line).
    # A line break is then one \n; a stanza break is \n\n.
    html = re.sub(r"</p\s*>", "\n\n", html)
    html = re.sub(r"<br\s*/?>\n?", "\n", html)
    html = re.sub(r"<[^>]+>", "", html)
    html = H.unescape(html)
    html = "".join(ch for ch in html if unicodedata.category(ch) != "Cf")
    lines = []
    prev_blank = True
    for raw in html.split("\n"):
        s = raw.strip()
        if not s:
            if not prev_blank:
                lines.append("")
                prev_blank = True
            continue
        if CSSISH.search(s):
            continue
        if re.fullmatch(r"\W*\d+\W*", s):  # bare page number
            continue
        if s.startswith("↑"):  # footnote backlink line (Jekyll's glosses)
            continue
        lines.append(s)
        prev_blank = False
    while lines and lines[0] == "":
        lines.pop(0)
    # the rendered subpage repeats the poem title as its first line; drop it so
    # it isn't duplicated under the heading we add
    while lines and lines[0].strip().lower() == title.strip().lower():
        lines.pop(0)
    while lines and (lines[0] == "" or lines[-1] == ""):
        lines.pop(0) if lines[0] == "" else lines.pop()
    return lines


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--delay", type=float, default=6.0)
    p.add_argument("--output", default="books/en-JM/Claude McKay/Constab Ballads.md")
    p.add_argument("--dry-run", nargs="*", help="fetch only the named items and print them")
    args = p.parse_args()

    todo = args.dry_run if args.dry_run else ITEMS
    parts = []
    for i, title in enumerate(todo):
        html, cached = fetch_rendered(f"{WORK}/{title}")
        lines = clean(html, title)
        nstanza = 1 + sum(1 for l in lines if l == "")
        print(f"  {title}: {sum(1 for l in lines if l)} lines, {nstanza} stanzas{' (cached)' if cached else ''}")
        block = "\n".join((l + "  ") if l else "" for l in lines)
        if args.dry_run:
            print(block)
            print("----")
        parts.append(f"## {title}\n\n" + block)
        if i + 1 < len(todo) and not cached:
            time.sleep(args.delay)
    if args.dry_run:
        return 0

    fm = (
        "---\n"
        "title: Constab Ballads\n"
        "author: Claude McKay\n"
        "language: en-JM\n"
        "year: 1912\n"
        "source: Wikisource (en)\n"
        f'source_url: "https://en.wikisource.org/wiki/{urllib.parse.quote(WORK.replace(chr(32), chr(95)))}"\n'
        "license: Public domain in the United States\n"
        'selection_note: "Complete: all twenty-eight ballads in the book\'s printed order, with McKay\'s Glossary of Jamaican words retained as a closing section, each poem a heading. McKay\'s companion 1912 volume Songs of Jamaica is not included: it is not transcribed on Wikisource and is absent from Project Gutenberg, so no clean dialect-faithful text was available."\n'
        'source_note: "Verbatim Jamaican Patois orthography as transcribed on English Wikisource from the 1912 page scans. The creole-inflected spellings (fe, fe me, whoppin\', cotch, frien\') are deliberate literary form and are kept exactly as printed; nothing is normalized to standard English. Running page numbers are removed and a title heading is supplied per poem."\n'
        "---\n"
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + "\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(ITEMS)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
