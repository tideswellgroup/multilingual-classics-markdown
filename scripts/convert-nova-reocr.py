#!/usr/bin/env python3
"""
convert-nova-reocr.py: rebuild io Nova Horizonti from the re-OCR pipeline.

Two-engine re-OCR (REOCR.md) of the Ido periodical Nova Horizonti,
replacing an earlier legible-but-uncorrected Internet Archive OCR. No
Ido model exists, so both engines run with the Esperanto model as the
nearest relative; they agree on 99% of body lines. The base engine is
chosen by noise (pick_base). Continuous prose with all-caps article
titles; paragraphs reflow on the OCR's blank lines. Conservative
heading detection: an all-caps line becomes a heading only when the
next line is prose, which keeps author and place lines out.

Stdlib only; reads the cached engine outputs (scans/, see REOCR.md).

Usage:
  python3 scripts/convert-nova-reocr.py [--out books/io] [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import (clean_lines, make_is_body, agreement, stats_sentence,
                          pick_base)

SCANS = 'scans/NovaHorizonti'
LATIN = re.compile(r'[A-Za-zÀ-ÿ]')
ALLCAPS = re.compile(r'^[A-ZÀ-Þ][A-ZÀ-Þ .]{4,}$')
PAGE_NUM = re.compile(r'^\W*\d{1,3}\W*$')

FRONTMATTER = '''---
title: Nova Horizonti
author: Various
language: io
year: 1919
source: Internet Archive
source_url: "https://archive.org/details/NovaHorizonti"
license: Public domain in the United States
text_quality: noisy
year_note: "An Ido periodical (literary and popular-science miscellany), 1919."
source_note: "Machine OCR, re-run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md), base engine chosen by measured noise, replacing an earlier legible-but-uncorrected Internet Archive OCR. No Ido model exists, so both engines used the Esperanto model as the nearest relative; they agree closely. Article titles (all-caps lines followed by prose) are promoted to headings; page numbers and line-end hyphenation resolved as in every conversion. German printer colophon and advertisements are period content and stay. {STATS} This is machine OCR, not a proofread edition: the flagged lines are where a fluent reader should look first."
---
'''


def load(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def assemble(tess, vision):
    pages = sorted(set(tess) & set(vision))
    base, cross, base_name = pick_base(tess, vision, LATIN)
    start = next(p for p in pages if 'NOVA HORIZONT' in base[p].upper())
    body_pages = [p for p in pages if p >= start]
    body = {p: base[p] for p in body_pages}
    stats, _ = agreement(body, {p: cross[p] for p in body_pages}, make_is_body())

    blocks, cur, carry = [], [], ''

    def flush():
        if cur:
            blocks.append(' '.join(cur))
            cur.clear()

    for p in body_pages:
        raw = [re.sub(r'[ \t]+', ' ', l).rstrip() for l in base[p].splitlines()]
        # paragraph signal: blank lines where the page has them, else a line
        # ending short of the column width (some pages carry no blank lines,
        # which otherwise joins a whole article into one wall)
        has_blanks = any(not l.strip() for l in raw)
        content = [l for l in raw if l.strip()]
        width = (sorted(len(l) for l in content)[int(len(content) * 0.85)]
                 if content else 60)
        for i, l in enumerate(raw):
            s = l.strip()
            if not s:
                if has_blanks:
                    flush()
                continue
            if PAGE_NUM.match(s):
                continue
            nxt = next((raw[j].strip() for j in range(i + 1, len(raw))
                        if raw[j].strip()), '')
            if ALLCAPS.match(s) and any(c.islower() for c in nxt) and len(nxt) > 25:
                flush()
                blocks.append('## ' + s.rstrip('.').title())
                continue
            if carry:
                s = carry + s
                carry = ''
            if s.endswith('-'):
                carry = s[:-1]
                continue
            cur.append(s)
            if not has_blanks and len(s) < width * 0.68:
                flush()
    flush()
    stats['base_engine'] = base_name
    stats['headings'] = sum(1 for b in blocks if b.startswith('## '))
    return blocks, stats_sentence(stats), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default=SCANS)
    ap.add_argument('--out', default='books/io')
    ap.add_argument('--stats-only', action='store_true')
    args = ap.parse_args()
    tess, vision = load(Path(args.scans) / 'tess'), load(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out = Path(args.out) / 'Various' / 'Nova Horizonti.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'nova: {len(body)} chars, {raw["headings"]} headings -> {out}')


if __name__ == '__main__':
    main()
