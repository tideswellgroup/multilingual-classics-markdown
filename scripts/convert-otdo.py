#!/usr/bin/env python3
"""
convert-otdo.py: build the bo book, the Old Tibetan Chronicle (Bibliotheque
nationale de France, Pelliot tibetain 1287), from Old Tibetan Documents
Online (OTDO, ILCAA, Tokyo University of Foreign Studies).

OTDO publishes each manuscript twice: a transliteration in extended Wylie,
which is its critical master, and a Tibetan-script rendering labelled beta.
The book is taken from the Tibetan-script page and checked line by line
against the master:

1. Each of the 536 manuscript lines is parsed from the page. Where OTDO
   offers a normalised reading in a tooltip (བགྱིསྣ་ with བགྱིས་ན་), the
   manuscript reading is kept and the normalisation dropped.
2. Every line's syllable count is compared with the Wylie master, after
   setting aside the master's struck-through syllables (scribal deletions,
   which the Tibetan page correctly omits). The converter refuses to write
   if any line disagrees beyond the six listed in CORRECTIONS, where the
   beta rendering drops a doubt mark inside a syllable or splits one; those
   six are corrected to the master. Where the master's doubt mark covers
   part of a syllable ([g?]I), the Tibetan carries it on the whole syllable
   ([གྀ?]), since a vowel sign cannot stand outside the bracket.
3. Lines are joined into running text: a line ending in a tsheg continues
   the syllable chain directly, any other line end becomes a space. The
   manuscript's own section heads (༄༅, fifteen of them) start paragraphs;
   the scroll has no other divisions and none are added.
4. OTDO's editorial sigla stay as published: [---] for a lacuna, [X?] for
   an uncertain reading, [A(/B)] for an alternative. So do the few
   syllables the beta rendering leaves in Wylie (the name rhya, and [-ng]).

Politeness: two page requests (the Tibetan rendering and the master), kept
in --cache; User-Agent with a contact address.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0 (contact@tideswellgroup.com)"
TIBETAN_URL = "https://otdo.aa-ken.jp/tibetan/archives?p=Pt_1287"
WYLIE_URL = "https://otdo.aa-ken.jp/archives?p=Pt_1287"
LINES = 536

# (line, beta rendering, corrected to the Wylie master)
CORRECTIONS = [
    (65, "དགྲ་ལ་ད་པའ་", "དགྲ་ལ་དཔའ་"),            # dgra la dpa'
    (255, "གྀ རྗེས", "[གྀ?] རྗེས"),               # [g?]I rjes
    (269, "ཀྱྀས ནྀ", "[ཀྱྀས?] ནྀ"),               # [kyI?]s nI
    (518, "ལྕེ་ཕབ་ནས", "ལྕེ་ཕབ་[ནས?]"),           # lce phab na[s?]
    (522, "འགྲེང་བ་ཡང", "འགྲེང་བ་[ཡང]"),          # 'greng ba ya[ng]
    (523, "མྱང་དང [---]", "མྱང་[དང?] [---]"),     # myang da[ng?] [---]
]


def fetch(url: str, cache: Path | None, name: str) -> str:
    path = cache / name if cache else None
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8")
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    time.sleep(1.5)
    return text


def parse_lines(page: str) -> dict[int, str]:
    start = page.index('id="hoge"')
    body = page[start:page.index("</div>", start)]
    found = re.findall(
        r'<span class="text-xs text-gray-400">\((\d+)\) </span>(.*?)<br id="br\d+" class="no">',
        body, re.DOTALL,
    )
    lines = {}
    for n, raw in found:
        raw = re.sub(r'<span class="tooltip-content">.*?</span></span>', "", raw, flags=re.DOTALL)
        raw = re.sub(r'<span class="line-through">.*?</span>', "", raw, flags=re.DOTALL)
        lines[int(n)] = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
    if sorted(lines) != list(range(1, LINES + 1)):
        raise SystemExit(f"expected lines 1..{LINES}, found {len(lines)}")
    return lines


def tibetan_syllables(s: str) -> int:
    s = re.sub(r"\[[^\]]*\]", " X ", s)
    return len([x for x in re.split(r"[་།༎༔༄༅\s]+", s) if x])


def wylie_syllables(s: str) -> int:
    s = re.sub(r"\[[^\]]*\]", " X ", s)
    return len([x for x in re.split(r"[\s/:$]+", s) if x])


def build(tib: dict[int, str], wylie: dict[int, str]) -> str:
    tib = dict(tib)
    for n, wrong, right in CORRECTIONS:
        if tib[n].count(wrong) != 1:
            raise SystemExit(f"line {n}: correction target {wrong!r} not found exactly once")
        tib[n] = tib[n].replace(wrong, right)
    # The corrected lines were each compared with the master by eye; the
    # count cannot judge them, because a doubt mark inside a syllable splits
    # it in the Wylie count and not in the Tibetan.
    corrected = {n for n, _, _ in CORRECTIONS}
    disagree = [
        n for n in tib
        if n not in corrected and tibetan_syllables(tib[n]) != wylie_syllables(wylie[n])
    ]
    if disagree:
        raise SystemExit(f"lines disagreeing with the Wylie master: {disagree}")

    text = ""
    for n in range(1, LINES + 1):
        line = re.sub(r"\s+", " ", tib[n])
        if text and not text.endswith("་"):
            text += " "
        text += line
    paragraphs = [p.strip() for p in re.split(r"(?=༄༅)", text) if p.strip()]
    return "\n\n".join(paragraphs) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frontmatter", required=True, help="file holding the YAML block, fences included: a .yml, or the existing book itself")
    p.add_argument("--output", required=True)
    p.add_argument("--cache", default=None, metavar="DIR")
    args = p.parse_args()
    cache = Path(args.cache) if args.cache else None

    tib_page = fetch(TIBETAN_URL, cache, "otdo-pt1287.html")
    wylie_page = fetch(WYLIE_URL, cache, "otdo-pt1287-wylie.html")
    body = build(parse_lines(tib_page), parse_lines(wylie_page))
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)  # a .yml, or an existing book
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    digest = hashlib.sha256(tib_page.encode("utf-8")).hexdigest()
    print(
        f"wrote {dest}: {body.count(chr(10) + chr(10)) + 1} paragraphs; "
        f"Tibetan page sha256 {digest}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
