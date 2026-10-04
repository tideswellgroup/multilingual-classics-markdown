#!/usr/bin/env python3
"""
convert-koti-chennaya.py: build the kn book Koti Chennaya (Panje Mangesha
Rao, Mangalore 1924) from its kn.wikisource transcription.

The main page `ಕೋಟಿ ಚೆನ್ನಯ` transcludes the 1924 scan
(Index `ಕೋಟಿ ಚೆನ್ನಯ-ಪಂಜೆ ಮಂಗೇಶರಾವ್.pdf`) in three ranges: the title page,
the author's preface (ಮುನ್ನುಡಿ), and the text. The rendered HTML is taken
through the walker in convert-bn-proofread.py, whose strip pipeline is shared,
and five book-specific repairs follow:

1. Printer's signature marks (`1*`, `3`, `3*`) sit at page feet inside
   {{right}} and are removed: they are binding furniture, not text.
2. The title page and the repeated book title at the head of part 1 are
   dropped; the book title is the H1.
3. The three part heads are promoted to H2. The transcription letter-spaces
   two of them (`೨ ನೆ ಯ ಭಾ ಗ .`) as the print does; the heading carries the
   unspaced form `೨ನೆಯ ಭಾಗ`, the form the transcription gives part 1.
4. Printed line ends survive inside some paragraphs. Where a line end splits
   a word, a renderer shows a space inside it. A split is joined only when
   the joined form occurs elsewhere in the book as a single word and the
   spaced form never does (ಕೋಟಿ ಚೆನ್ನಯ is written both ways, so it stays
   as printed); every other
   line end is left as it is, because most are real word boundaries and
   telling the rest apart needs a reader of Kannada. Joins are reported.
5. The digit ೦ typed for the anusvara ಂ (ಚೆ೦ದುಗಿಡಿ) is repaired wherever it
   touches a letter and no other digit, and counted.

Politeness: a single action=parse request, through the walker's api_get
(User-Agent with contact address, Retry-After honoured).
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("walker", SCRIPT_DIR / "convert-bn-proofread.py")
walker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(walker)

PAGE = "ಕೋಟಿ ಚೆನ್ನಯ"
TITLE = "ಕೋಟಿ ಚೆನ್ನಯ"
KN = r"[\u0C80-\u0CFF]"

PART_HEAD = re.compile(r"^\**\s*([೧-೯])\s*ನೆ\s*ಯ\s*ಭಾ\s*ಗ\s*\.?\s*\**$")


def strip_signatures(html: str) -> str:
    return re.sub(
        r'<div class="wst-right">\s*<p>\s*[0-9*]+\s*</p>\s*</div>', "", html
    )


def join_attested_splits(text: str) -> tuple[str, list[str]]:
    words = collections.Counter(re.findall(KN + "+", text))
    joined: list[str] = []

    def fix(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        if words[a + b] > 0 and not re.search(
            r"(?<!\S)" + re.escape(a) + r"[^\S\n]+" + re.escape(b), text
        ):
            joined.append(a + b)
            return a + b
        return m.group(0)

    text = re.sub(r"(" + KN + r"+)[^\S\n]*\n(?!\n)[^\S\n]*(" + KN + r"+)", fix, text)
    return text, joined


def build(html: str) -> tuple[str, list[str]]:
    body = walker.convert_body(strip_signatures(html))
    lines = body.split("\n")

    # Drop everything before the preface heading: the title page.
    start = next(i for i, l in enumerate(lines) if l.strip() == "## ಮುನ್ನುಡಿ")
    lines = lines[start:]

    out: list[str] = []
    for line in lines:
        s = line.strip()
        if s == "ಕೋಟಿ-ಚೆನ್ನಯ.":
            continue  # book title repeated at the head of part 1
        m = PART_HEAD.match(s)
        if m:
            out.append(f"## {m.group(1)}ನೆಯ ಭಾಗ")
            continue
        out.append(line)
    text = "\n".join(out)
    # Headings stand in their own paragraph.
    text = re.sub(r"\n*(## [^\n]+)\n*", r"\n\n\1\n\n", text).strip("\n")
    text, joined = join_attested_splits(text)
    # The digit ೦ typed for the anusvara ಂ it resembles (ಚೆ೦ದುಗಿಡಿ), wherever
    # it touches a letter and no other digit; numerals (೧೯೦೪ರಲ್ಲಿ) are untouched.
    text, slips = walker.repair_digit_slips(text, ["೦=ಂ"])
    print(f"digit slips repaired: {slips}", file=sys.stderr)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return f"# {TITLE}\n\n{text}\n", joined


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frontmatter", required=True, help="file holding the YAML block, fences included: a .yml, or the existing book itself")
    p.add_argument("--output", required=True)
    p.add_argument("--cache", default=None, metavar="DIR", help="keep the fetched page here and reuse it")
    args = p.parse_args()
    if args.cache:
        walker.CACHE_DIR = Path(args.cache)

    html = walker.fetch_rendered("kn", PAGE)
    body, joined = build(html)
    parts = re.findall(r"(?m)^## (.+)$", body)
    if parts != ["ಮುನ್ನುಡಿ", "೧ನೆಯ ಭಾಗ", "೨ನೆಯ ಭಾಗ", "೩ನೆಯ ಭಾಗ"]:
        raise SystemExit(f"unexpected heading sequence: {parts}")
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)  # a .yml, or an existing book
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    print(f"wrote {dest}; joined {len(joined)} attested line-end split(s): {joined}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
