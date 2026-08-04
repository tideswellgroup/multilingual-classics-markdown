#!/usr/bin/env python3
"""
convert-io-historio.py: build io Jespersen from multilingual Wikisource.

Otto Jespersen's Historio di nia linguo (1912): a complete original Ido
work (the history of the language's own creation, written by a member
of the Delegation committee), hand-typed on multilingual Wikisource.
Plain-paragraph wikitext; the {{header}} template is dropped and bold
and italic markup carried over.

Usage:
  python3 scripts/convert-io-historio.py [--out books/io]
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

FRONTMATTER = '''---
title: Historio di nia linguo
title_en: The History of Our Language
author: Otto Jespersen
language: io
year: 1912
source: Wikisource (multilingual)
source_url: "https://wikisource.org/wiki/Historio_di_nia_linguo"
license: Public domain in the United States
year_note: "Written and published 1912 (signed Gentofte, June 1912); Jespersen sat on the 1907 Delegation committee the essay recounts, making this both an original Ido literary text and a primary historical source."
source_note: "Hand-typed Wikisource transcription without scan backing or a stated base edition. Wikisource categorises it among original Ido works; the text is complete through Jespersen's signature line."
---
'''


def fetch(page):
    q = urllib.parse.urlencode({'action': 'parse', 'page': page,
                                'prop': 'wikitext', 'format': 'json', 'redirects': '1'})
    req = urllib.request.Request(
        f'https://wikisource.org/w/api.php?{q}',
        headers={'User-Agent': 'multilingual-classics-markdown corpus converter'})
    time.sleep(3)
    with urllib.request.urlopen(req) as r:
        return json.load(r)['parse']['wikitext']['*']


def to_markdown(w):
    w = re.sub(r'\{\{header.*?\}\}', '', w, flags=re.S)
    w = re.sub(r'\[\[Category:[^\]]*\]\]', '', w)
    w = re.sub(r'^>.*$', '', w, flags=re.M)          # breadcrumb line
    w = re.sub(r"'''(.*?)'''", r'**\1**', w, flags=re.S)
    w = re.sub(r"''(.*?)''", r'*\1*', w, flags=re.S)
    w = w.replace('<br>', '  \n').replace('<br/>', '  \n').replace('<br />', '  \n')
    paras = [re.sub(r'\s+', ' ', p).strip() for p in re.split(r'\n\s*\n', w)]
    return '\n\n'.join(p for p in paras if p) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/io')
    args = ap.parse_args()
    out = Path(args.out) / 'Otto Jespersen' / 'Historio di nia linguo.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    body = to_markdown(fetch('Historio di nia linguo'))
    out.write_text(FRONTMATTER + body)
    print(f'historio: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
