#!/usr/bin/env python3
"""
convert-whitman-1855.py: build the en-US Whitman book from the FIRST edition of
Leaves of Grass (1855) on English Wikisource.

The 1855 first edition is the twelve untitled poems (the first six run under the
shared title "Leaves of Grass"); it is a different text from every later,
retitled and revised edition. Wikisource transcribes it page by page and gives
one subpage per poem, keyed by first line. This script fetches the rendered
text of each of the twelve poem subpages, lifts the verse out of the ppoem
markup, and writes one markdown file, heading each poem by its 1855 first line.

The 1855 wording, punctuation and Whitman's long dotted ellipses are kept as
printed. The prose Preface and later editions are not vendored.
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
WORK = "Leaves of Grass (1855)"

# The twelve poems in first-edition order, keyed by first line (their subpage
# titles), with the title later editions gave them, for the heading.
POEMS = [
    ("I celebrate myself", "Song of Myself"),
    ("Come closer to me", "A Song for Occupations"),
    ("To think of time", "To Think of Time"),
    ("I wander all night in my vision", "The Sleepers"),
    ("The bodies of men and women engirth me", "I Sing the Body Electric"),
    ("Sauntering the pavement or riding the country byroad here", "Faces"),
    ("A young man came to me", "Song of the Answerer"),
    ("Suddenly out of its stale and drowsy lair", "Europe"),
    ("Clear the way there Jonathan!", "A Boston Ballad"),
    ("There was a child went forth every day", "There Was a Child Went Forth"),
    ("Who learns my lesson complete?", "Who Learns My Lesson Complete"),
    ("Great are the myths", "Great Are the Myths"),
]

CSSISH = re.compile(r"mw-parser-output|[{}]|text-transform|font-size|dropinitial")


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


def clean_poem(html: str) -> list[str]:
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<figure[^>]*>.*?</figure>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<img\b[^>]*/?>", "", html, flags=re.IGNORECASE)
    # page-number chrome (running-header spans) before other structure
    html = re.sub(r'<span class="pagenum[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    html = re.sub(r'<span[^>]*class="[^"]*ws-pagenum[^"]*"[^>]*>.*?</span>', "", html, flags=re.DOTALL)
    html = strip_balanced_div(html, "noexport")
    # each verse stanza is its own <div class="ws-poem-stanza">; turn the stanza
    # boundary into a blank line so stanza gaps survive the tag strip
    html = re.sub(r'<div class="ws-poem-stanza"[^>]*>', "\n\n", html)
    html = re.sub(r"<br\s*/?>", "\n", html)
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
        if s.upper() in {"LEAVES OF GRASS", "LEAVES OF GRASS."}:  # running title
            continue
        if re.fullmatch(r"\W*\d+\W*", s):  # bare page number
            continue
        lines.append(s)  # hard break added at assembly
        prev_blank = False
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--delay", type=float, default=6.0)
    p.add_argument("--output", default="books/en-US/Walt Whitman/Leaves of Grass (1855).md")
    p.add_argument("--dry-run", action="store_true", help="fetch first & last poem only, report counts")
    args = p.parse_args()

    todo = [POEMS[0], POEMS[-1]] if args.dry_run else POEMS
    parts = []
    for i, (incipit, later) in enumerate(todo):
        lines = clean_poem(fetch_rendered(f"{WORK}/{incipit}"))
        nstanza = 1 + sum(1 for l in lines if l == "")
        print(f"{incipit!r}: {sum(1 for l in lines if l)} lines, {nstanza} stanzas (later titled {later})")
        block = "\n".join((l + "  ") if l else "" for l in lines)
        parts.append(f"## {incipit}\n\n" + block)
        if i + 1 < len(todo):
            time.sleep(args.delay)

    if args.dry_run:
        return 0

    fm = (
        "---\n"
        "title: Leaves of Grass\n"
        "author: Walt Whitman\n"
        "language: en-US\n"
        "year: 1855\n"
        "source: Wikisource (en)\n"
        f'source_url: "https://en.wikisource.org/wiki/{urllib.parse.quote(WORK.replace(chr(32), chr(95)))}"\n'
        "license: Public domain in the United States\n"
        'year_note: "The 1855 first edition, self-published by Whitman in Brooklyn. This is the twelve-poem original, distinct from the retitled and heavily revised later editions through 1892."\n'
        'selection_note: "The complete twelve poems of the 1855 first edition, in first-edition order, each headed by its opening line (the poems were untitled in 1855; the later editorial titles are Song of Myself, A Song for Occupations, To Think of Time, The Sleepers, I Sing the Body Electric, Faces, Song of the Answerer, Europe, A Boston Ballad, There Was a Child Went Forth, Who Learns My Lesson Complete, and Great Are the Myths). The prose Preface is omitted."\n'
        'source_note: "Verbatim 1855 text as transcribed on English Wikisource from the first-edition page scans. Whitman\'s 1855 wording, capitalization, and his long dotted ellipses stand as printed; nothing is revised toward a later edition. Running page headers and page numbers are removed and a first-line heading is supplied per poem."\n'
        "---\n"
    )
    body = "\n\n".join(parts) + "\n"
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + body, encoding="utf-8")
    print(f"wrote {out} ({len(fm+body):,} bytes, {len(POEMS)} poems)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
