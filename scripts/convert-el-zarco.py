#!/usr/bin/env python3
"""
convert-el-zarco.py: build es-MX El Zarco from es.wikisource.

A wrapper over convert-wikisource-collection.py (the Bharati pattern):
runs the collection walk over the 25 chapter sub-pages, then applies
the book-specific cleanup the generic walker cannot know about:

- strips the trailing "Capítulo N" navigation line each chapter page
  carries at its foot;
- enriches the bare "Capítulo I" headings with the chapter names the
  index page gives (Yautepec, El terror, ...);
- replaces the frontmatter with the corrected bibliography: the
  Wikisource index dates the work 1869, but El Zarco (subtitled
  Episodios de la vida mexicana en 1861-63) was written 1885-1888 and
  first published posthumously in 1901, which is the year that makes
  it pre-1929.

Usage:
  python3 scripts/convert-el-zarco.py [--out books/es-MX]

Network: fetches from the es.wikisource API on every run.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

CHAPTER_NAMES = [
    'Yautepec', 'El terror', 'Las dos amigas', 'Nicolás', 'El Zarco',
    'La entrevista', 'La adelita', 'Quién era el Zarco', 'El búho',
    'La fuga', 'Doña Antonia', 'La carta', 'El comandante', 'Pilar',
    'El amor bueno', 'Un ángel', 'La agonía', 'Entre los bandidos',
    'Xochimancas', 'El primer día', 'La orgía', 'Martín Sánchez Chagollán',
    'El asalto', 'El presidente Juárez', 'El albazo',
]
ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
          'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX',
          'XX', 'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV']

FRONTMATTER = '''---
title: El Zarco
author: Ignacio Manuel Altamirano
language: es-MX
year: 1901
source: Wikisource (es)
source_url: "https://es.wikisource.org/wiki/El_Zarco"
license: Public domain in the United States
year_note: "Subtitled Episodios de la vida mexicana en 1861-63. Written 1885-1888, first published posthumously in 1901 (Altamirano died 1893, so the work is public domain worldwide). The Wikisource index's 1869 date is not the publication year and is corrected here."
source_note: "Typed Wikisource transcription without scan backing or a stated base edition (the same provenance tier as the uk Лісова пісня, and flagged alongside it as a re-source candidate should a scan-backed edition appear). Each chapter page's trailing navigation line is stripped, and the index's chapter names are joined to the chapter numbers in headings; the transcription's text is otherwise verbatim."
---
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/es-MX', help='output directory (default books/es-MX)')
    args = ap.parse_args()
    out = Path(args.out) / 'Ignacio Manuel Altamirano' / 'El Zarco.md'
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tf:
        tmp = Path(tf.name)
    subprocess.run([
        sys.executable, str(SCRIPTS / 'convert-wikisource-collection.py'),
        '--lang', 'es', '--index', 'El Zarco',
        '--title', 'El Zarco', '--author', 'Ignacio Manuel Altamirano',
        '--language', 'es-MX', '--year', '1901',
        '--source-url', 'https://es.wikisource.org/wiki/El_Zarco',
        '--output', str(tmp), '--delay', '4',
    ], check=True)

    text = tmp.read_text()
    tmp.unlink()
    body = text.split('---', 2)[2].lstrip('\n')

    # strip the per-chapter trailing navigation line ("Capítulo 7")
    body = re.sub(r'\n+Capítulo \d+\n', '\n', body)

    # join the index's chapter names to the numbered headings
    for roman, name in zip(ROMANS, CHAPTER_NAMES):
        body = body.replace(f'## Capítulo {roman}\n', f'## Capítulo {roman}. {name}\n', 1)

    out.write_text(FRONTMATTER + body)
    print(f'el-zarco: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
