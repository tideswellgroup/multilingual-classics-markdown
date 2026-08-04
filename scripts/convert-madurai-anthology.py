#!/usr/bin/env python3
"""
convert-madurai-anthology.py: fetch a Project Madurai UTF-8 etext of a Sangam
eṭṭuttokai anthology (HTML) and convert it to vendor-ready markdown for the
multilingual-classics-markdown corpus.

Tuned for the Kuṟuntokai etext (pm0110). These anthologies are laid out as a
run of independently numbered short poems, each shaped as:

  N. <tiṇai> - <speaker>      a numbered heading: poem number, landscape, and
                              the dramatic speaker (editorial apparatus that
                              the etext carries inline)
  <verse line>                the poem body, a handful of metrical lines
  ...
  -<poet name>.               the traditional colophon naming the composing
                              poet, on its own line prefixed with a hyphen

Each poem is emitted as a level-2 heading (the number, landscape and speaker)
followed by its verse lines joined with markdown hard line breaks so the line
structure is preserved, then the poet's name as an italic attribution line.

The invocatory god-praise verse some anthologies print before poem 1, and the
"... முற்றிற்று" completion colophon after the last poem, are apparatus and
are not emitted. A trailing poem heading with no verse body (a truncated stub
in the source) is skipped; pass --last to cap the run at the last complete
poem and record the coverage in a selection_note.

Not a general parser: it recognises the numbered-poem / hyphen-colophon idiom
of the eṭṭuttokai etexts.

Usage:
  scripts/convert-madurai-anthology.py --url <etext-url> --title T --author A \
      --language ta --year Y --output books/ta/.../file.md
"""

from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"

RE_POEM = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")   # "1. குறிஞ்சி - தோழி கூற்று"
RE_POET = re.compile(r"^-\s*(.+?)\s*$")           # "-திப்புத் தோளார்."


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def to_lines(raw: str) -> list[str]:
    """Flatten the HTML to plain, non-empty, whitespace-normalised lines."""
    body = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    body = htmllib.unescape(re.sub(r"<[^>]+>", "", body))
    out = []
    for line in body.splitlines():
        line = line.replace("\xa0", " ").strip()
        if line:
            out.append(re.sub(r"\s{2,}", " ", line))
    return out


def convert(url: str, title: str, author: str, language: str, year: str,
            source_url: str, last: int | None, year_note: str | None,
            selection_note: str | None, source_note: str | None) -> tuple[str, int]:
    lines = to_lines(fetch(url))

    md: list[str] = []
    count = 0
    num: str | None = None
    heading = ""
    verse: list[str] = []
    poet: str | None = None

    def flush() -> None:
        nonlocal count, num, heading, verse, poet
        # Emit only complete poems (a heading with at least one verse line)
        # that fall within the requested cap.
        if num is not None and verse and (last is None or int(num) <= last):
            count += 1
            md.append(f"## {num}. {heading}")
            md.append("")
            md.append("  \n".join(verse))
            if poet:
                md.append(f"\n*{poet}*")
            md.append("")
        num, heading, verse, poet = None, "", [], None

    for line in lines:
        if line.rstrip(".").endswith("முற்றிற்று"):
            break  # completion colophon: end of the work
        m = RE_POEM.match(line)
        if m:
            flush()
            num, heading = m.group(1), m.group(2)
            continue
        if num is None:
            continue  # front matter / invocation before the first numbered poem
        p = RE_POET.match(line)
        if p:
            poet = p.group(1)
            flush()  # the poet colophon closes the poem
            continue
        verse.append(line)
    flush()

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(md)).strip() + "\n"

    year_field = year if year.isdigit() else f'"{year}"'
    front = f"---\ntitle: {title}\nauthor: {author}\n"
    front += f"language: {language}\nyear: {year_field}\n"
    if year_note:
        front += f'year_note: "{year_note}"\n'
    front += f'source: Project Madurai\nsource_url: "{source_url}"\n'
    if selection_note:
        front += f'selection_note: "{selection_note}"\n'
    if source_note:
        front += f'source_note: "{source_note}"\n'
    front += "license: Public domain in the United States\n---\n\n"
    return front + text, count


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a Project Madurai Sangam anthology etext to corpus markdown.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--year", required=True)
    ap.add_argument("--last", type=int, help="cap at this poem number (drop a truncated tail)")
    ap.add_argument("--year-note")
    ap.add_argument("--selection-note")
    ap.add_argument("--source-note")
    ap.add_argument("--source-url")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    md, n = convert(
        args.url, args.title, args.author, args.language, args.year,
        args.source_url or args.url, args.last, args.year_note,
        args.selection_note, args.source_note,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    sys.stderr.write(f"[ok] wrote {out} ({n} poems, {len(md.encode('utf-8'))} bytes)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
