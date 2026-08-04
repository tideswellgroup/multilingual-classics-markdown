#!/usr/bin/env python3
"""
convert-makunganya.py: build the sw Makunganya poem from Wikisource.

Sha'iri la Makunganya (1898): a 348-line Swahili eyewitness verse
account of the German campaign against Hassan Omari Makunganya at
Kilwa, by Mzee bin 'Ali bin Kidogo bin il-Qadiri, as printed in Hans
Zache's "Das Makunganya-Lied" (MSOS, Berlin 1898). Multilingual
Wikisource carries a typed transcription: stanza-number lines (1-6,
7-12, ...) with colon-indented verse lines beneath. Stanza numbers
become bold markers; verse lines take hard breaks. The transcription
mixes hyphen and dash characters in the stanza markers; both are
normalised to a plain hyphen. (The dash characters are built from
codepoints below to keep this source file dash-free per house style.)

Usage:
  python3 scripts/convert-makunganya.py [--out books/sw]
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

# U+2014 em dash, U+2013 en dash, plus the ASCII hyphen
DASHES = chr(0x2014) + chr(0x2013) + '-'

FRONTMATTER = '''---
title: Sha'iri la Makunganya
title_en: The Makunganya Poem
author: Mzee bin 'Ali bin Kidogo bin il-Qadiri
language: sw
year: 1898
source: Wikisource (multilingual)
source_url: "https://wikisource.org/wiki/Sha%27iri_la_Makunganya"
license: Public domain in the United States
year_note: "Eyewitness verse account of the 1895 German campaign against Hassan Omari Makunganya at Kilwa, as printed in Hans Zache, Das Makunganya-Lied, Mittheilungen des Seminars für Orientalische Sprachen, Berlin 1898."
source_note: "Typed Wikisource transcription without scan backing; the printed stanza numbering (1-6, 7-12, ... 344-348) is preserved as bold markers, with the transcription's mixed dash characters normalised to hyphens. Arabic-derived orthography as printed (Bismillahi, kutakallam, khabari)."
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
    w = re.sub(r'^>.*$', '', w, flags=re.M)
    stanza_marker = re.compile(r'\d+\s*[' + DASHES + r']\s*\d+')
    out = []
    stanza = []

    def close():
        if stanza:
            out.append('\n'.join(
                l + ('  ' if i < len(stanza) - 1 else '')
                for i, l in enumerate(stanza)))
            stanza.clear()

    for line in w.splitlines():
        s = line.strip()
        if not s:
            close()
            continue
        if stanza_marker.fullmatch(s):
            close()
            out.append('**' + re.sub(r'\s*[' + DASHES + r']\s*', '-', s) + '**')
        elif s.startswith(':'):
            text = re.sub(r"'''(.*?)'''", r'**\1**', s.lstrip(':').strip())
            stanza.append(text)
        else:
            close()
            out.append(re.sub(r"'''(.*?)'''", r'**\1**', s))
    close()
    return '\n\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/sw')
    args = ap.parse_args()
    out = Path(args.out) / "Mzee bin 'Ali bin Kidogo" / "Sha'iri la Makunganya.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = to_markdown(fetch("Sha'iri la Makunganya"))
    out.write_text(FRONTMATTER + body)
    print(f'makunganya: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
