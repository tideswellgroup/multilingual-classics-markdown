#!/usr/bin/env python3
"""
convert-jangnama.py: build the pa book Jangnama (Shah Muhammad) from the
pa.wikisource page transcriptions of the Lahore 1904 Gurmukhi printing
(Index `ਜੰਗਨਾਮਾ - ਸ਼ਾਹ ਮੁਹੰਮਦ.pdf`, all text pages validated).

The mainspace page `ਜੰਗਨਾਮਾ ਸ਼ਾਹ ਮੁਹੰਮਦ` is a different, unsourced modern
text, so the book is assembled from the Page namespace of the 1904 scan:
pages 5 to 28 carry the poem (printed pages 1 to 24); page 3 is the title
page, which supplies the edition and is not shipped.

The 1904 printing runs the verse on as prose, as Gurmukhi qissa printings
of the period do: each line of a four-line stanza ends in a double danda
(॥), and each stanza closes with its number between dandas (॥੧॥). The line
structure is rebuilt from those marks, one verse line per line with a hard
break, stanzas separated by blank lines, every mark kept as printed. The
converter refuses to write unless the stanza numbers run unbroken from 1
and every stanza comes out at four lines; any stanza that does not is
reported by number.

Seven transcription slips (stanza numbers, a danda, a word) were found by
reading three pages against the scan, and are corrected to the print; the
CORRECTIONS table lists each one.

Wiki links the transcribers added (to Wikipedia articles on the people
named) are reduced to their printed text; running heads and rules are page
furniture and are dropped.

Politeness: the 24 pages come in two batched API requests, with the
User-Agent and Retry-After handling of convert-bn-proofread.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("walker", SCRIPT_DIR / "convert-bn-proofread.py")
walker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(walker)

LANG = "pa"
PAGE = "ਪੰਨਾ:ਜੰਗਨਾਮਾ - ਸ਼ਾਹ ਮੁਹੰਮਦ.pdf/{}"
TEXT_PAGES = range(5, 29)
TITLE = "ਜੰਗਨਾਮਾ"
PA_DIGITS = "੦੧੨੩੪੫੬੭੮੯"


def pa_int(s: str) -> int:
    return int("".join(str(PA_DIGITS.index(c)) for c in s))


def fetch_pages(cache: Path | None, delay: float) -> dict[int, str]:
    if cache and cache.exists():
        raw = json.loads(cache.read_text(encoding="utf-8"))
        return {int(k): v for k, v in raw.items()}
    pages: dict[int, str] = {}
    numbers = list(TEXT_PAGES)
    for k in range(0, len(numbers), 12):
        chunk = numbers[k:k + 12]
        data = walker.api_get(LANG, {
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "titles": "|".join(PAGE.format(n) for n in chunk),
        })
        for p in data["query"]["pages"]:
            n = int(p["title"].rsplit("/", 1)[1])
            pages[n] = p["revisions"][0]["slots"]["main"]["content"]
        time.sleep(delay)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    return pages


def clean(wikitext: str) -> str:
    t = re.sub(r"<noinclude>.*?</noinclude>", "", wikitext, flags=re.DOTALL)
    t = re.sub(r"\{\{(?:dhr|rule|nop)[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\{\{center\|([^{}]*)\}\}", r"\1", t)
    if "{{" in t or "[[" in t or "<" in t:
        raise SystemExit(f"unhandled markup: {t[:200]!r}")
    return t.strip()


# A line ends at a danda group; a stanza ends at a group carrying its number
# (॥੧॥, and once ॥੫। and ।॥੪੯॥ as printed). A number may run straight on
# into the next word.
LINE = re.compile(r"(.+?(?:।?॥\s*([੦-੯]+)\s*[॥।]|॥(?!\s*[੦-੯])|।।|।(?![॥।])))", re.DOTALL)

# Transcription slips, each read against the page image of the 1904 scan
# (Commons, the Index's PDF) and corrected to it: (page, transcribed, printed).
# Found in a sampled collation of pages 21, 22 and 24; see QUALITY.md.
CORRECTIONS = [
    (21, "ਪੱਲੇ॥੭੩॥ ਓੜਕ", "ਪੱਲੇ॥ ਓੜਕ"),            # a stanza number the print does not have
    (21, "ਹੱਲੇ॥੧੩॥", "ਹੱਲੇ॥੭੩॥"),                 # ੭੩ printed, ੧੩ transcribed
    (21, "ਫੰਡ ਮੀਆਂ॥੭੪॥ ਕਿਨੇ", "ਫੰਡ ਮੀਆਂ॥ ਕਿਨੇ"),  # a stanza number the print does not have
    (22, "ਪੋਤਰੇ ਜੀ ਸ਼ਾਹ", "ਪੋਤਰੇ ਜੀ॥ ਸ਼ਾਹ"),       # the printed danda dropped
    (22, "ਵਹੀਰ ਮੀਆਂ॥੨੮॥", "ਵਹੀਰ ਮੀਆਂ॥੭੮॥"),     # ੭੮ printed, ੨੮ transcribed
    (24, "ਕਾਇਮ ਜੰਗ ਹੋਏ", "ਕਾਇਮ ਜੰਗ ਨੂੰ ਹੋਏ"),     # a printed word dropped
    (24, "ਦੂਰ ਮੀਆਂ॥੯॥", "ਦੂਰ ਮੀਆਂ॥੮੯॥"),         # ੮੯ printed, ੯ transcribed
]


SIGNATURE = re.compile(r"ਸ਼ਾਹ\s?ਮੁ\s?ਹੰਮਦ")


def build(pages: dict[int, str]) -> tuple[str, list[str]]:
    pages = dict(pages)
    for n, wrong, right in CORRECTIONS:
        if pages[n].count(wrong) != 1:
            raise SystemExit(f"page {n}: correction target {wrong!r} not found exactly once")
        pages[n] = pages[n].replace(wrong, right)
    first = clean(pages[TEXT_PAGES[0]]).split("\n")
    head = [l.strip() for l in first if l.strip()][:2]
    if head[0] != "ੴ ਸਤਿਗੁਰ ਪ੍ਰਸਾਦਿ॥" or not head[1].startswith("ਅਬ ਕਿੱਸਾ"):
        raise SystemExit(f"unexpected opening lines: {head}")
    body_first = "\n".join(l for l in first if l.strip() and l.strip() not in head)
    text = " ".join([body_first] + [clean(pages[n]) for n in TEXT_PAGES[1:]])
    text = re.sub(r"\s+", " ", text).strip()

    stanzas: list[list[str]] = []
    current: list[str] = []
    problems: list[str] = []
    expected = 1
    pos = 0
    for m in LINE.finditer(text):
        pos = m.end()
        current.append(m.group(1).strip())
        if m.group(2):
            n = pa_int(m.group(2))
            if n != expected:
                problems.append(f"stanza numbered {n} where {expected} was expected")
            if len(current) != 4:
                problems.append(f"stanza {n} has {len(current)} lines")
            elif not SIGNATURE.search(current[3]):
                # The poet names himself in every closing line (usually at its
                # head, four times within it), an independent check on the split.
                problems.append(f"stanza {n}: closing line lacks the signature")
            stanzas.append(current)
            current = []
            expected = n + 1
    if current or text[pos:].strip():
        problems.append(f"text after the last numbered stanza: {' '.join(current)[:60]!r}")

    out = [f"# {TITLE}", "", "  \n".join(head), ""]
    for s in stanzas:
        out.append("  \n".join(s))
        out.append("")
    return "\n".join(out), problems + [f"{len(stanzas)} stanzas"]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frontmatter", required=True, help="file holding the YAML block, fences included: a .yml, or the existing book itself")
    p.add_argument("--output", required=True)
    p.add_argument("--cache", default=None, metavar="FILE", help="JSON file to keep the page texts in")
    p.add_argument("--delay", type=float, default=1.5)
    args = p.parse_args()

    pages = fetch_pages(Path(args.cache) if args.cache else None, args.delay)
    body, report = build(pages)
    problems = report[:-1]
    print("\n".join(report), file=sys.stderr)
    if problems:
        raise SystemExit("refusing to write: the stanza structure did not rebuild cleanly")
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)  # a .yml, or an existing book
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    print(f"wrote {dest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
