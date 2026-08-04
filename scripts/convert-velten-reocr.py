#!/usr/bin/env python3
"""
convert-velten-reocr.py: rebuild sw Velten from the re-OCR pipeline.

Velten's Safari za Wasuaheli (Berlin 1901) is a Swahili-text volume:
first-person travel narratives dictated by named Swahili speakers, its
German apparatus confined to the front matter (title, dedication,
Vorwort) and a closing table of contents. The corpus vendors the six
narratives. The Archive derive OCR'd them with a systematic u->n
substitution that corrupted nearly every word; this rebuild re-runs the
scan through the two-engine pipeline (REOCR.md) with the Swahili model.

Assembly: body runs from the first narrative heading through the last
page before the German table of contents; the six "Safari yangu ya ..."
lines become headings; page numbers, catchwords, and German-apparatus
lines are dropped; line-end hyphenation is rejoined. Agreement is
measured over Swahili body lines and written into the source_note.

Stdlib only; reads the cached engine outputs (scans/, see REOCR.md).

Usage:
  python3 scripts/convert-velten-reocr.py [--scans scans/safarizawasuahe00veltgoog]
                                          [--out books/sw] [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import clean_lines, make_is_body, agreement, stats_sentence

HEADING = re.compile(r'^\W*Safari yangu ya .+', re.I)
FIRST_HEADING = 'Safari yangu ya barra Afrika'
TOC_MARKER = re.compile(r'Safari yangu ya .*Slēmān|Inhalt|Yaliyomo', re.I)
PAGE_NUM = re.compile(r'^\W*\d{1,3}\W*$')
GERMAN = re.compile(r'\b(und|der|die|das|ist|von|Seite|Suaheli|Uebersetzung|'
                    r'Verlage|deutsche)\b')
CATCHWORD = re.compile(r'^[A-ZÀ-Þ]?[a-zà-ÿ]+[.,]?$')      # single word line (catchword)

FRONTMATTER = '''---
title: Safari za Wasuaheli
title_translit: Safari za Wasuaheli
author: Carl Velten (ed.)
language: sw
year: 1901
source: Internet Archive
source_url: "https://archive.org/details/safarizawasuahe00veltgoog"
license: Public domain in the United States
text_quality: noisy
year_note: "Reisen der Suaheli, collected and edited by Carl Velten, Berlin 1901: first-person travel narratives dictated by named Swahili speakers (Selemani bin Mwenye Chande and others). Six narratives are included."
selection_note: "The six travel narratives (Safari yangu ya barra Afrika; ya Nyassa; ya Ulaya toka Daressalama; ya Udoe hatta Uzigua; ya Afrika toka bahari ya suaheli hatta bahari ya pili; ya Russia na ya Sibirien). The volume's German front matter and table of contents are not included."
source_note: "Machine OCR, re-run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md) with the Swahili model, replacing an Archive derive whose systematic u-as-n substitution had corrupted nearly every word. Tesseract 5 is the base text, cross-checked against Google Vision; both read the Swahili body closely. Period orthography as printed (bassi, killa, waqati, the sub-dotted emphatic consonants). Page numbers, catchwords, and the occasional German footnote line are dropped; line-end hyphenation is rejoined; the six narrative titles are headings. {STATS} This is machine OCR, not a proofread edition: the flagged lines are where a fluent reader should look first."
---
'''


def load(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def is_swahili_body(line):
    if len(line) < 4:
        return False
    if PAGE_NUM.match(line) or GERMAN.search(line):
        return False
    return True


def assemble(tess, vision):
    pages = sorted(set(tess) & set(vision))
    start = next(p for p in pages if FIRST_HEADING.lower() in tess[p].lower()
                 or FIRST_HEADING.lower() in vision[p].lower())
    # stop before the closing table of contents: the one page that lists
    # several "Safari yangu ya ..." lines together (narrative starts never
    # cluster like that)
    def heading_count(txt):
        return sum(1 for l in clean_lines(txt) if HEADING.match(l))
    end = next((p for p in pages if p > start and heading_count(vision[p]) >= 3),
               pages[-1] + 'z')
    body_pages = [p for p in pages if start <= p < end]
    body = {p: tess[p] for p in body_pages}
    body_v = {p: vision[p] for p in body_pages}
    stats, _ = agreement(body, body_v, make_is_body())

    blocks = []
    cur = []
    carry = ''

    def flush():
        if cur:
            blocks.append(' '.join(cur))
            cur.clear()

    # Paragraph breaks are the OCR's blank lines; page-furniture lines are
    # skipped WITHOUT breaking the paragraph (a paragraph runs across the
    # page turn), headings and blank lines DO break it.
    for p in body_pages:
        for raw in tess[p].splitlines():
            line = re.sub(r'\s+', ' ', raw).strip()
            if not line:
                flush()
                continue
            if HEADING.match(line):
                flush()
                blocks.append('# ' + re.sub(r'^\W+', '', line))
                continue
            if PAGE_NUM.match(line) or GERMAN.search(line):
                continue
            if carry:
                line = carry + line
                carry = ''
            if line.endswith('-'):
                carry = line[:-1]
                continue
            cur.append(line)
    flush()
    stats['body_pages'] = len(body_pages)
    return blocks, stats_sentence(stats), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default='scans/safarizawasuahe00veltgoog')
    ap.add_argument('--out', default='books/sw')
    ap.add_argument('--stats-only', action='store_true')
    args = ap.parse_args()
    tess = load(Path(args.scans) / 'tess')
    vision = load(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out = Path(args.out) / 'Carl Velten' / 'Safari za Wasuaheli.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'velten: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
