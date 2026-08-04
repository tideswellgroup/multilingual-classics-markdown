#!/usr/bin/env python3
"""
convert-burns-kilmarnock.py: build the sco (Scots) corpus book, a selection of
the poems that made up Burns's 1786 Kilmarnock edition (Poems, Chiefly in the
Scottish Dialect), taken from the Project Gutenberg collected text (etext 1279,
Poems and Songs of Robert Burns), which preserves Burns's Scots orthography
verbatim.

The collected etext annotates the poems with editorial footnotes set inline as
"[Footnote N: ... ]" blocks and "^N" reference markers, and prints a combined
glossary after all the poems. This script pulls out the selected poems by title,
using the fact that a real poem title is a flush-left line preceded by two blank
lines (epigraph labels and chorus headings inside a poem are not), strips the
editorial footnote apparatus and the reference markers, and sets the verse
flush-left. Burns's Scots spelling is left exactly as printed.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

URL = "https://www.gutenberg.org/cache/epub/1279/pg1279.txt"
UA = "multilingual-classics-markdown/1.0"

# Selected Kilmarnock (1786) poems, in the edition's order, matched by a
# distinctive substring of the collected-edition title line.
SELECTION = [
    "Death And Dying Words Of Poor Mailie",
    "Man Was Made To Mourn",
    "The Holy Fair",
    "Halloween",
    "To A Mouse, On Turning Her Up",
    "The Cotter",
    "Address To The Deil",
    "The Twa Dogs",
    "The Vision",
    "To A Louse, On Seeing One",
    "To A Mountain Daisy",
]


def fetch() -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def body_lines(text: str) -> list[str]:
    s = re.search(r"\*\*\* START OF.*?\*\*\*", text, re.S)
    e = re.search(r"\*\*\* END OF", text)
    body = text[s.end(): e.start()]
    return body.replace("\r\n", "\n").split("\n")


def boundaries(lines: list[str]) -> list[int]:
    """Indices of real poem-title lines: flush-left, non-blank, preceded by two
    blank lines."""
    out = []
    for i in range(2, len(lines)):
        l = lines[i]
        if l and not l[0].isspace() and lines[i - 1] == "" and lines[i - 2] == "":
            out.append(i)
    return out


def clean_block(block: list[str]) -> tuple[str, str]:
    """Return (title, body) for one poem block. Strips ^N markers, drops
    [Footnote ...] apparatus, flush-lefts the verse, collapses blank runs."""
    title = re.sub(r"\^\d+", "", block[0]).strip()
    out = []
    skipping_footnote = False
    for line in block[1:]:
        if skipping_footnote:
            if "]" in line:
                skipping_footnote = False
            continue
        if re.match(r"\s*\[Footnote\b", line):
            if "]" not in line:
                skipping_footnote = True
            continue
        line = re.sub(r"\^\d+", "", line)
        out.append(line.strip())
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip("\n")
    return title, text


def main() -> int:
    lines = body_lines(fetch())
    bounds = boundaries(lines)
    bset = bounds  # sorted ascending

    def next_boundary(i: int) -> int:
        for b in bset:
            if b > i:
                return b
        return len(lines)

    poems = []
    for needle in SELECTION:
        idx = None
        for i in bset:
            if needle.lower() in lines[i].lower():
                idx = i
                break
        if idx is None:
            raise SystemExit(f"not found: {needle}")
        block = lines[idx:next_boundary(idx)]
        title, text = clean_block(block)
        poems.append((title, text))
        print(f"  {title[:60]}: {len(text.splitlines())} lines")

    fm = (
        "---\n"
        "title: Poems, Chiefly in the Scottish Dialect\n"
        "author: Robert Burns\n"
        "language: sco\n"
        "year: 1786\n"
        "source: Project Gutenberg\n"
        f'source_url: "{URL}"\n'
        "license: Public domain in the United States\n"
        'year_note: "The Kilmarnock edition, Burns\'s first book, was printed by John Wilson at Kilmarnock in 1786."\n'
        'selection_note: "A selection of eleven poems from the 1786 Kilmarnock edition, in the edition\'s order: The Death and Dying Words of Poor Mailie, Man Was Made to Mourn, The Holy Fair, Halloween, To a Mouse, The Cotter\'s Saturday Night, Address to the Deil, The Twa Dogs, The Vision, To a Louse, and To a Mountain Daisy. The remaining Kilmarnock poems, and the many later poems and songs, are omitted."\n'
        'source_note: "Verbatim Scots orthography, taken from the Project Gutenberg collected edition (etext 1279, Poems and Songs of Robert Burns), which preserves Burns\'s spelling and apostrophes exactly (sleekit, cow\'rin, tim\'rous, gie, a\'). The collected edition\'s inline editorial footnotes and their reference markers are removed and the verse is set flush-left; no spelling is normalized."\n'
        "---\n"
    )
    parts = [f"## {t}\n\n{b}" for t, b in poems]
    out = Path("books/sco/Robert Burns/Poems, Chiefly in the Scottish Dialect.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + "\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(poems)} poems)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
