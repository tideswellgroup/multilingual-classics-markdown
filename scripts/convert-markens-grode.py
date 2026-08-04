#!/usr/bin/env python3
"""
convert-markens-grode.py: assemble Knut Hamsun's Markens grøde (1917) from the
two Project Gutenberg volumes into one markdown file.

Gutenberg carries the novel as two ebooks, 43724 (Første del, nineteen
chapters) and 43725 (Anden del, twelve), both set from the Gyldendalske
Boghandel edition of 1917 whose title page the text itself reproduces. The
chapter counts are asserted, so a truncated download fails loudly rather than
producing a short book.

Removed as apparatus rather than text: Gutenberg's own header and footer, the
transcriber's bracketed note about character encoding, the title-page block,
and the "Trykkfeil" list of printer's errors each volume carries at the end.
That list records where the transcription departs from the print and where it
deliberately does not, so it is worth consulting at the ebook itself; the
source_note says so.

Source line wrapping is preserved, matching the other Gutenberg-derived prose
in this corpus.

Usage:
  scripts/convert-markens-grode.py --output books/no/...
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

USER_AGENT = "multilingual-classics-markdown/1.0"
PARTS = [
    ("Første del", 43724, 19),
    ("Anden del", 43725, 12),
]
ROMAN = re.compile(r"^\s*([IVXL]+)\.?\s*$")


def fetch(ebook_id: int) -> str:
    for url in (
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt",
    ):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                text = response.read().decode("utf-8")
            if len(text) > 20000:
                return text
        except Exception:
            continue
    raise RuntimeError(f"could not fetch Gutenberg {ebook_id}")


def body_of(text: str) -> list[str]:
    body = text.split("*** START", 1)[1].split("\n", 1)[1]
    body = body.split("*** END", 1)[0]
    lines = body.split("\n")

    # The transcriber's encoding note is a bracketed block at the top.
    start = 0
    for i, line in enumerate(lines[:40]):
        if line.rstrip().endswith("]"):
            start = i + 1
            break
    lines = lines[start:]

    # The printer's-error list closes each volume.
    for i, line in enumerate(lines):
        if line.strip() == "Trykkfeil:":
            lines = lines[:i]
            break
    while lines and (not lines[-1].strip() or set(lines[-1].strip()) <= {"*", " "}):
        lines.pop()

    # Everything before the first chapter numeral is the title page.
    for i, line in enumerate(lines):
        if ROMAN.match(line):
            return lines[i:]
    raise RuntimeError("no chapter numeral found")


def convert(lines: list[str], expected: int) -> tuple[str, int]:
    out: list[str] = []
    chapters = 0
    for line in lines:
        match = ROMAN.match(line)
        if match:
            chapters += 1
            out.append(f"## {match.group(1)}")
        else:
            out.append(line.rstrip())
    if chapters != expected:
        raise RuntimeError(f"expected {expected} chapters, found {chapters}")
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), chapters


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble Markens grøde from Gutenberg.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    sections = []
    total = 0
    for index, (label, ebook_id, expected) in enumerate(PARTS):
        if index:
            time.sleep(2)
        raw = fetch(ebook_id)
        text, chapters = convert(body_of(raw), expected)
        sections.append(f"# {label}\n\n{text}")
        total += chapters
        print(f"  {label}: Gutenberg {ebook_id}, {chapters} chapters, {len(text):,} chars")

    frontmatter = "\n".join([
        "---",
        "title: Markens grøde",
        "title_en: Growth of the Soil",
        "author: Knut Hamsun",
        "language: no",
        "year: 1917",
        "source: Project Gutenberg",
        'source_url: "https://www.gutenberg.org/ebooks/43724"',
        "license: Public domain in the United States",
        'year_note: "First published 1917 by Gyldendalske Boghandel, Kristiania and '
        "København, the edition whose title page both volumes reproduce (14. Tusinde). "
        'Hamsun was awarded the Nobel Prize in Literature for this novel in 1920."',
        'source_note: "Complete in two parts and thirty-one chapters, nineteen in Første '
        "del and twelve in Anden del, assembled from Gutenberg 43724 and 43725. The "
        "converter asserts those counts and refuses to write if either is short. Removed "
        "as apparatus: Gutenberg's header and footer, the transcriber's note on character "
        "encoding, and the title-page block. Each Gutenberg volume ends with a Trykkfeil "
        "list recording where the transcription corrects the print and where it leaves a "
        "reading unchanged; that list is apparatus rather than text and is not reproduced "
        "here, but it is worth consulting at the ebooks themselves. Source line wrapping is "
        "kept, as are the 181 non-breaking spaces the transcriber uses to bind short "
        "words such as 'i den' and 'Mening i'. They are invisible in a reader and "
        'will show up in tokenisation. No word of the text is changed."',
        "---",
    ])
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(frontmatter + "\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {total} chapters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
