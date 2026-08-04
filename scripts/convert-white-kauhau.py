#!/usr/bin/env python3
"""
convert-white-kauhau.py: build mi Nga Kauhau Maori o Nehe from NZETC.

The Maori-language part of John White's The Ancient History of the
Maori, Vol. I (Government Printer, 1887): Nga Kauhau Maori o Nehe,
Upoko I-XII, typed TEI-derived HTML digitised by Waikato University
and hosted by NZETC under CC BY-SA 3.0 NZ. The live NZETC host was
decommissioned in 2024; sections are fetched from Internet Archive
Wayback Machine raw snapshots (the same retrieval route as the sister
volume Ko Nga Moteatea).

Extraction: only the div.chapter[lang="mi"] subtree of each section.
h2/h3 become headings, p.lg.verse blocks (span.l lines) become
hard-break verse, other paragraphs prose; page-break markers and site
chrome are dropped. Vols VII on are excluded on purpose: they are
manuscripts first published 2001-2007 and still in US copyright.

Usage:
  python3 scripts/convert-white-kauhau.py [--out books/mi]
"""
import argparse
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

WAYBACK = ('https://web.archive.org/web/2019id_/'
           'http://nzetc.victoria.ac.nz/tm/scholarly/tei-Whi01Anci-t1-body-d2-d{n}.html')
SECTIONS = range(2, 14)  # d2..d13 = Upoko I..XII

FRONTMATTER = '''---
title: Nga Kauhau Maori o Nehe
title_en: The Maori Recitals of Ancient Times
author: Various tribal narrators (John White, ed.)
language: mi
year: 1887
source: NZETC (New Zealand Electronic Text Collection), via Internet Archive Wayback Machine
source_url: "https://nzetc.victoria.ac.nz/tm/scholarly/tei-Whi01Anci.html"
license: Public domain in the United States
year_note: "The Maori-language part of The Ancient History of the Maori, His Mythology and Traditions, Vol. I (Horo-Uta or Taki-Tumu Migration), Wellington: Government Printer, 1887. Verbatim 1887 orthography: no macrons, as printed."
selection_note: "Vol. I complete (Upoko I-XII). The English part of the volume is not included, matching the corpus's language-locale rule. Later volumes may follow; Vols VII on are excluded on principle, being manuscripts first published 2001-2007 and so still in US copyright."
source_note: "Typed TEI transcription (Waikato University digitisation, 2001; NZETC hosting under Creative Commons Attribution-Share Alike 3.0 New Zealand). Attribution: narratives collected from named tribal sources; White is compiler and editor, not author, matching the attribution posture of Ko Nga Moteatea. Retrieved from Wayback Machine snapshots of the decommissioned NZETC host; source_url is the canonical NZETC table of contents."
---
'''


class MiExtract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.in_mi = None       # depth of div.chapter[lang=mi]
        self.skip = None        # depth below which content is skipped
        self.blocks = []
        self.cur = []
        self.mode = None        # 'h2' | 'h3' | 'prose' | 'verse'
        self.verse_lines = []

    def _flush_line(self):
        t = re.sub(r'\s+', ' ', ''.join(self.cur)).strip()
        self.cur = []
        return t

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get('class') or '').split()
        depth = len(self.stack)
        self.stack.append(tag)
        if self.skip is not None:
            return
        if self.in_mi is None:
            # keyed on the section id: Upoko XII's div is mis-tagged lang="en"
            # in the TEI even though its content is Maori
            if tag == 'div' and 'chapter' in classes and \
                    (a.get('id') or '').startswith('tei-Whi01Anci-t1-body-d2-'):
                self.in_mi = depth
            return
        if ('pb' in classes) or ('menu' in classes) or ('text-nav' in classes):
            self.skip = depth
            return
        if tag in ('h2', 'h3', 'h4'):
            self.mode = 'h2' if tag == 'h2' else 'h3'
            self.cur = []
        elif tag == 'p':
            if 'verse' in classes or 'lg' in classes:
                self.mode = 'verse'
                self.verse_lines = []
                self.cur = []
            else:
                self.mode = 'prose'
                self.cur = []
        elif tag == 'br' and self.mode == 'verse':
            pass  # line ends are span.l boundaries, handled on span close
        elif tag == 'i':
            self.cur.append('*')

    def handle_endtag(self, tag):
        while self.stack:
            t = self.stack.pop()
            depth = len(self.stack)
            if self.skip is not None:
                if depth <= self.skip:
                    self.skip = None
                if t == tag:
                    return
                continue
            if t != tag:
                continue
            if self.in_mi is not None and depth <= self.in_mi and tag == 'div':
                self.in_mi = None
            elif tag == 'span' and self.mode == 'verse':
                line = self._flush_line()
                if line:
                    self.verse_lines.append(line)
            elif tag in ('h2', 'h3', 'h4') and self.mode in ('h2', 'h3'):
                text = self._flush_line()
                if text:
                    marker = '##' if self.mode == 'h2' else '###'
                    self.blocks.append(f'{marker} {text}')
                self.mode = None
            elif tag == 'p' and self.mode == 'verse':
                if self.verse_lines:
                    self.blocks.append('\n'.join(
                        l + ('  ' if i < len(self.verse_lines) - 1 else '')
                        for i, l in enumerate(self.verse_lines)))
                self.mode = None
            elif tag == 'p' and self.mode == 'prose':
                text = self._flush_line()
                if text:
                    self.blocks.append(text)
                self.mode = None
            elif tag == 'i':
                self.cur.append('*')
            return

    def handle_data(self, data):
        if self.skip is not None or self.in_mi is None:
            return
        if self.mode is not None:
            self.cur.append(data)


def fetch(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'multilingual-classics-markdown corpus converter'})
    for attempt in range(5):
        try:
            time.sleep(4)
            with urllib.request.urlopen(req) as r:
                return r.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as err:
            if err.code in (429, 503) and attempt < 4:
                time.sleep(20 * (attempt + 1))
                continue
            raise


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/mi')
    ap.add_argument('--cache-dir', default=None,
                    help='directory holding pre-fetched d<N>.html section files '
                         '(used instead of live Wayback fetches when present)')
    args = ap.parse_args()
    out = Path(args.out) / 'John White' / 'Nga Kauhau Maori o Nehe.md'
    out.parent.mkdir(parents=True, exist_ok=True)

    blocks = []
    for n in SECTIONS:
        cached = Path(args.cache_dir) / f'd{n}.html' if args.cache_dir else None
        if cached and cached.exists():
            html = cached.read_text(errors='replace')
        else:
            html = fetch(WAYBACK.format(n=n))
        p = MiExtract()
        p.feed(html)
        blocks.extend(p.blocks)
        print(f'  upoko d{n}: {len(p.blocks)} blocks')
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER + body)
    print(f'kauhau: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
