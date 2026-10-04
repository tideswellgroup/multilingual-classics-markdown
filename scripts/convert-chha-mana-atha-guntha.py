#!/usr/bin/env python3
"""
convert-chha-mana-atha-guntha.py: build the or book Chha Mana Atha Guntha
(Fakir Mohan Senapati) from its or.wikisource transcription.

The source is the Srujanika and NIT Rourkela digital edition (Index
`Chha mana atha guntha.pdf`, CC0), transcribed page by page and validated.
That edition names no base printing, and its pages 1 to 3 carry a modern
introduction; the introduction lives on the main page and is not shipped.
The 29 chapters are sub-pages, walked in the main page's order through
convert-bn-proofread.py (shared strip pipeline, cache, polite fetch).

Book-specific work:

1. Headings. Each chapter opens with its printed number line
   (`ପ୍ରଥମ ପରିଚ୍ଛେଦ`) and a title line ending in a colon
   (`**ରାମଚନ୍ଦ୍ର ମଙ୍ଗରାଜ :**`); they become an H2 and an H3, the colon and
   bold dropped. The closing ଉପସଂହାର has a single head line.
2. The conjunct ṇḍa is encoded throughout as ଣ୍ତ (ṇ + virama + ta), 385
   times, against 19 correct ଣ୍ଡ: the ṇḍa glyph of the legacy font the
   edition was set in was mapped to the wrong subjoined letter when it was
   converted to Unicode. ṇ + ta is not an Odia cluster; ṇṭa is encoded
   correctly (ଣ୍ଟ) 62 times, so the fault is confined to ṇḍa, and every
   affected word that could be read is a ṇḍa word (ମୁଣ୍ଡ, ଖଣ୍ଡ, ପଣ୍ଡିତ,
   ଇଣ୍ଡିଆ). All are repaired to ଣ୍ଡ and counted.
3. One page opens a <poem> it never closes, so the tag shows as text; it
   is dropped and the lines it was meant to keep apart become hard breaks.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("walker", SCRIPT_DIR / "convert-bn-proofread.py")
walker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(walker)

LANG = "or"
TOP = "ଛମାଣ ଆଠଗୁଣ୍ଠ"
TITLE = "ଛମାଣ ଆଠଗୁଣ୍ଠ"
NUMBER_LINE = re.compile(r"\**\s*([^\s*]+\s+ପରି(?:ଚ୍ଛ|ଛ)େଦ)\s*\**")  # ପରିଛେଦ once, as printed


def headings(body: str, last: bool) -> str:
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    first = lines.pop(0).strip()
    if last:
        if first.strip("* ") != "ଉପସଂହାର":
            raise SystemExit(f"closing unit: unexpected head {first!r}")
        return "## ଉପସଂହାର\n\n" + "\n".join(lines).lstrip("\n")
    m = NUMBER_LINE.fullmatch(first)
    if not m:
        raise SystemExit(f"unexpected chapter number line {first!r}")
    while lines and not lines[0].strip():
        lines.pop(0)
    t = lines.pop(0).strip().replace("*", "").strip().rstrip(" :'")  # one title keeps a stray quote from its bold markup
    return f"## {m.group(1)}\n\n### {t}\n\n" + "\n".join(lines).lstrip("\n")


def unclosed_poem(text: str) -> str:
    """One page opens a <poem> it never closes, so the wiki prints the tag as
    text. Its purpose was line structure (the judge's date and signature
    under the verdict): drop the tag and keep each line of that paragraph,
    and the one above the tag, as a hard break."""
    def fix(m: re.Match) -> str:
        lines = [m.group(1)] + m.group(2).split("\n")
        return "  \n".join(l.rstrip() for l in lines)
    text, n = re.subn(r"(?m)^([^\n]+)\n<poem>\n((?:[^\n]+\n?)+?)(?=\n\n|\Z)", fix, text)
    if "<poem>" in text:
        raise SystemExit("an unclosed <poem> survived")
    return text


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frontmatter", required=True, help="file holding the YAML block, fences included: a .yml, or the existing book itself")
    p.add_argument("--output", required=True)
    p.add_argument("--cache", default=None, metavar="DIR")
    p.add_argument("--delay", type=float, default=1.5)
    args = p.parse_args()
    if args.cache:
        walker.CACHE_DIR = Path(args.cache)

    order = walker.resolve_order(LANG, TOP, "flat", skip_redirects=True)
    if len(order) != 29:
        raise SystemExit(f"expected 29 chapters, found {len(order)}")
    sections = []
    for i, title in enumerate(order):
        if i and not walker.is_cached(LANG, title):
            time.sleep(args.delay)
        body = walker.convert_body(walker.fetch_rendered(LANG, title), br_hard=True)
        sections.append(headings(body, last=(i == len(order) - 1)).strip() + "\n")

    body = f"# {TITLE}\n\n" + "\n".join(sections)
    body = unclosed_poem(body)
    n = body.count("ଣ୍ତ")
    body = body.replace("ଣ୍ତ", "ଣ୍ଡ")
    body = body.replace("\ufeff", "")
    body = re.sub(r"\n{3,}", "\n\n", body)
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)  # a .yml, or an existing book
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    print(f"wrote {dest}: {len(order)} chapters, {n} ଣ୍ତ repaired to ଣ୍ଡ", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
