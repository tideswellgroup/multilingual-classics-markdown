#!/usr/bin/env python3
"""
convert-crowther-reocr.py: rebuild yo Crowther Vocabulary from re-OCR.

Two-engine re-OCR (REOCR.md) of Crowther's A Vocabulary of the Yoruba
Language (1852). The value here is diacritic recovery: the old Internet
Archive OCR destroyed the subdot vowels (ọ ẹ ṣ) and tone marks that the
Yoruba orthography depends on; the Vision pass with the Yoruba model
reads them. This is a dictionary, so the assembly is entry-based rather
than the shared prose reflow: each entry opens with an all-caps headword
and runs, with continuation lines, to the next headword. The base engine
is chosen by noise (pick_base).

Stdlib only; reads the cached engine outputs (scans/, see REOCR.md).

Usage:
  python3 scripts/convert-crowther-reocr.py [--out books/yo] [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import clean_lines, make_is_body, agreement, stats_sentence, pick_base

SCANS = 'scans/vocabularyofyoru00crow'
LATIN = re.compile(r'[A-Za-zÀ-ÿḀ-ỿ]')
# a dictionary entry opens with an all-caps Yoruba headword: a single token
# (no internal space, which excludes the title-page phrases and the all-caps
# proverbs of the specimens section) of sub-dot-capable capitals, at least
# two letters, followed by an etymology paren, a part-of-speech, or a comma
CAPS = "A-ZṢẸỌÀ-Þ"
HEADWORD = re.compile(rf'^[{CAPS}][{CAPS}\'()-]*[{CAPS}][,.(]')
PAGE_NUM = re.compile(r'^\W*\d{1,4}\W*$')
# single-word page-guide header (e.g. "ADA") on its own line: skip
GUIDE = re.compile(rf'^[{CAPS}]{{2,6}}$')

FRONTMATTER = '''---
title: A Vocabulary of the Yoruba Language
title_translit: A Vocabulary of the Yoruba Language
author: Samuel Adjai Crowther
language: yo
year: 1852
source: Internet Archive
source_url: "https://archive.org/details/vocabularyofyoru00crow"
license: Public domain in the United States
text_quality: noisy
language_note: "A Yoruba-English dictionary; the headwords are Yoruba, the definitions English. A reference work, included as a yo locale-filler."
source_note: "Machine OCR, re-run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md) with the Yoruba model, base engine chosen by measured noise, replacing an earlier Internet Archive OCR that had destroyed the sub-dot vowels (ọ ẹ ṣ) and tone marks. The re-OCR recovers most of them, which is the point of the rebuild; the reading is still machine OCR. Each entry opens with its all-caps headword; page numbers, page-guide headers, and line-end hyphenation are dropped. {STATS} The flagged lines are where a Yoruba reader should look first."
---
'''


def load(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def is_entry_page(txt):
    # a real A-Z dictionary page is dense with headwords; front-matter and
    # title pages have only a few scattered all-caps lines
    lines = clean_lines(txt)
    if not lines:
        return False
    return sum(1 for l in lines if HEADWORD.match(l)) >= 6


def assemble(tess, vision):
    pages = sorted(set(tess) & set(vision))
    base, cross, base_name = pick_base(tess, vision, LATIN)
    body_pages = [p for p in pages if is_entry_page(base[p])]
    body = {p: base[p] for p in body_pages}
    stats, _ = agreement(body, {p: cross[p] for p in body_pages}, make_is_body())

    entries, cur, carry = [], [], ''
    for p in body_pages:
        for l in base[p].splitlines():
            s = re.sub(r'[ \t]+', ' ', l).strip()
            if not s or PAGE_NUM.match(s) or GUIDE.match(s):
                continue
            if carry:
                s = carry + s
                carry = ''
            if s.endswith('-'):
                carry = s[:-1]
                continue
            if HEADWORD.match(s):
                if cur:
                    entries.append(' '.join(cur))
                cur = [s]
            elif cur:
                cur.append(s)
    if cur:
        entries.append(' '.join(cur))

    # bold the headword (up to its first comma / paren / part-of-speech)
    blocks = []
    for e in entries:
        m = re.match(rf'^([{CAPS}][{CAPS} \'()-]*[{CAPS}])', e)
        if m:
            blocks.append(f'**{m.group(1)}**' + e[m.end():])
        else:
            blocks.append(e)
    stats['base_engine'] = base_name
    stats['entries'] = len(blocks)
    return blocks, stats_sentence(stats), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default=SCANS)
    ap.add_argument('--out', default='books/yo')
    ap.add_argument('--stats-only', action='store_true')
    args = ap.parse_args()
    tess, vision = load(Path(args.scans) / 'tess'), load(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out = Path(args.out) / 'Samuel Adjai Crowther' / 'Vocabulary of the Yoruba Language.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'crowther: {len(body)} chars, {raw["entries"]} entries -> {out}')


if __name__ == '__main__':
    main()
