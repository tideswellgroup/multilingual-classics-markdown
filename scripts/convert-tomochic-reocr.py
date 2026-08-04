#!/usr/bin/env python3
"""
convert-tomochic-reocr.py: rebuild es-MX Tomóchic from the re-OCR pipeline.

Replaces the raw 1906 Google Books OCR with a two-engine pass (REOCR.md)
over the better 1911 Bouret fifth-edition scan (the repair base named in
the old QUALITY.md flag). Frías's novel is continuous Spanish prose in
short chapters headed by a standalone Roman numeral; the old text had
lost chapter V and carried no headings. The base engine is chosen by
noise (pick_base), not assumed.

Stdlib only; reads the cached engine outputs (scans/, see REOCR.md).

Usage:
  python3 scripts/convert-tomochic-reocr.py [--out books/es-MX] [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import (clean_lines, make_is_body, agreement, stats_sentence,
                          pick_base, reflow_paragraphs)

SCANS = 'scans/agn0784.0001.001.umich.edu'
LATIN = re.compile(r'[A-Za-zÀ-ÿ]')
CHAPTER = re.compile(r'^[IVXLC]{1,6}\.?$')
# page furniture: the running head (TOMOCHIC / TOMÓCHIC, with OCR variants)
# and bare page numbers
DROP = re.compile(r'^(TOM[OÓ]CHIC\.?|\d{1,3}|[IVXLC]{1,6} TOM[OÓ]CHIC.*)$', re.I)

FRONTMATTER = '''---
title: "Tomóchic: Novela histórica mexicana"
author: Heriberto Frías
language: es-MX
year: 1893
source: Internet Archive
source_url: "https://archive.org/details/agn0784.0001.001.umich.edu"
license: Public domain in the United States
text_quality: noisy
year_note: "First serialised 1893 in El Demócrata; text from the 1911 Bouret fifth edition (corregida y aumentada), the 600 DPI Michigan scan."
source_note: "Machine OCR, run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md) over the 1911 fifth-edition scan, replacing an earlier raw Google Books OCR of the 1906 scan that carried pervasive noise, lost chapter V, and had no headings. Base engine chosen by measured noise; cross-checked against the other engine. The standalone Roman-numeral chapter markers are promoted to headings (recovering chapter V, which the old text had lost); the sequence is largely right but, being read from ambiguous standalone numerals, carries occasional gaps and spurious entries that a proofreader would settle. Running heads, page numbers, and line-end hyphenation resolved as in every conversion. {STATS} This is machine OCR, not a proofread edition: the flagged lines are where a fluent reader should look first."
---
'''


def load(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def assemble(tess, vision):
    pages = sorted(set(tess) & set(vision))
    base, cross, base_name = pick_base(tess, vision, LATIN)
    # body starts at the first chapter numeral; ends at the last page with
    # substantial Latin text (drop trailing scan furniture)
    start = next(p for p in pages
                 if any(CHAPTER.match(l) for l in clean_lines(base[p])))
    body_pages = [p for p in pages if p >= start]
    while body_pages and len(LATIN.findall(base[body_pages[-1]])) < 200:
        body_pages.pop()
    body = {p: base[p] for p in body_pages}
    stats, _ = agreement(body, {p: cross[p] for p in body_pages}, make_is_body())

    raw_blocks = reflow_paragraphs(body, body_pages, heading_re=CHAPTER, drop_re=DROP)
    blocks = []
    for b in raw_blocks:
        if b.startswith('\x00'):
            num = b[1:].rstrip('.')
            blocks.append(f'## {num}')
        else:
            blocks.append(b)
    stats['base_engine'] = base_name
    stats['body_pages'] = len(body_pages)
    stats['chapters'] = sum(1 for b in blocks if b.startswith('## '))
    return blocks, stats_sentence(stats), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default=SCANS)
    ap.add_argument('--out', default='books/es-MX')
    ap.add_argument('--stats-only', action='store_true')
    args = ap.parse_args()
    tess, vision = load(Path(args.scans) / 'tess'), load(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out = Path(args.out) / 'Heriberto Frías' / 'Tomóchic.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'tomochic: {len(body)} chars, {raw["chapters"]} chapters -> {out}')


if __name__ == '__main__':
    main()
