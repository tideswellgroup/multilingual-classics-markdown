#!/usr/bin/env python3
"""
convert-ngamahinga-reocr.py: rebuild mi Nga Mahinga from the re-OCR pipeline.

Two-engine re-OCR (REOCR.md) of Grey's Ko Nga Mahinga a Nga Tupuna Maori
(1854), replacing an earlier noisier Internet Archive OCR. The vendored
selection is the opening sequence of Part I: nine legend-cycles from the
cosmogony through the Toi-te-huatahi / Tama-te-kapua stories, each headed
by an all-caps Maori title in the print. The base engine is chosen by
noise (pick_base). Continuous prose; paragraphs reflow on the OCR's blank
lines.

Stdlib only; reads the cached engine outputs (scans/, see REOCR.md).

Usage:
  python3 scripts/convert-ngamahinga-reocr.py [--out books/mi] [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import (clean_lines, make_is_body, agreement, stats_sentence,
                          pick_base, reflow_paragraphs)

SCANS = 'scans/kongamahingaang00greygoog'
LATIN = re.compile(r'[A-Za-zĀ-ſ]')
FIRST_STORY = 'KO NGA TAMA A RANGI'
# an all-caps Maori story title on its own line (letters, spaces, the
# comma/hyphen/period the titles use); at least two words or 5 letters
TITLE = re.compile(r'^[A-Z][A-Z ,.–-]{4,}\.?$')
N_STORIES = 9
PAGE_NUM = re.compile(r'^\W*\d{1,3}\W*$')

FRONTMATTER = '''---
title: Ko Nga Mahinga a Nga Tupuna Maori
author: Wiremu Maihi Te Rangikaheke (Grey, ed.)
language: mi
year: 1854
source: Internet Archive
source_url: "https://archive.org/details/kongamahingaang00greygoog"
license: Public domain in the United States
text_quality: noisy
year_note: "Verbatim 1854 orthography: 19th-century Maori printing did not mark vowel length, so no macrons appear; reproduced as printed."
selection_note: "The opening sequence of Part I (Wahi I): nine legend-cycles, the cosmogony (Ko nga tama a Rangi), the Maui cycle, and the hero legends through Tawhaki, Wahieroa/Rata/Whakatau, Whakatau-potiki, and Toi-te-huatahi/Tama-te-kapua. Grey's 1854 collection runs to roughly 240 pages; the whole exceeds the corpus size guidance."
source_note: "Machine OCR, re-run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md), base engine chosen by measured noise, replacing an earlier noisier Internet Archive OCR. Attribution: these narratives were principally written by Wiremu Maihi Te Rangikaheke of Ngati Rangiwewehi; Grey is the collector and editor. The all-caps story titles are headings; page numbers and line-end hyphenation resolved as in every conversion. {STATS} This is machine OCR, not a proofread edition: the flagged lines are where a fluent reader should look first."
---
'''


def load(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def assemble(tess, vision):
    pages = sorted(set(tess) & set(vision))
    base, cross, base_name = pick_base(tess, vision, LATIN)

    def story_starts_here(txt):
        # the first story title as a standalone line followed by prose (not
        # the table-of-contents entry, which is one line among a list)
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        for i, l in enumerate(lines[:-1]):
            if l.rstrip('.').upper() == FIRST_STORY and any(
                    c.islower() for c in lines[i + 1]) and len(lines[i + 1]) > 25:
                return True
        return False

    start = next(p for p in pages if story_starts_here(base[p]))
    tail = [p for p in pages if p >= start]
    body = {p: base[p] for p in tail}

    raw = reflow_paragraphs(body, tail, heading_re=TITLE, drop_re=PAGE_NUM)
    blocks, stories = [], 0
    for b in raw:
        if b.startswith('\x00'):
            stories += 1
            if stories > N_STORIES:
                break
            blocks.append('## ' + b[1:].rstrip('.').strip())
        else:
            blocks.append(b)

    # agreement over the excerpt's pages: start through the page holding the
    # last story's opening (TOI-te-huatahi) plus its continuation
    last = max((p for p in tail if 'TOI' in base[p].upper()), default=tail[-1])
    sel = [p for p in tail if p <= last]
    stats, _ = agreement({p: base[p] for p in sel},
                         {p: cross[p] for p in sel}, make_is_body())
    stats['base_engine'] = base_name
    stats['stories'] = min(stories, N_STORIES)
    return blocks, stats_sentence(stats), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default=SCANS)
    ap.add_argument('--out', default='books/mi')
    ap.add_argument('--stats-only', action='store_true')
    args = ap.parse_args()
    tess, vision = load(Path(args.scans) / 'tess'), load(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out = Path(args.out) / 'Wiremu Maihi Te Rangikaheke' / 'Ko Nga Mahinga a Nga Tupuna Maori.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'ngamahinga: {len(body)} chars, {raw["stories"]} stories -> {out}')


if __name__ == '__main__':
    main()
