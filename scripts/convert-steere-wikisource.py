#!/usr/bin/env python3
"""
convert-steere-wikisource.py: build sw Steere from multilingual Wikisource.

Replaces the earlier Internet Archive OCR selection with the
human-proofread, scan-backed Wikisource transcription of the Swahili
side of Steere's Swahili Tales (London: Bell & Daldy, 1870;
Index:Swahili tales.djvu). All 22 secular pieces are taken in the
printed order; the 23rd, Mwanzo wa utenzi wa Ayubu (the opening of the
Utenzi of Job), is excluded under the corpus's secular rule and the
exclusion is disclosed in the selection_note.

Reuses the ProofreadPage HTML walker from convert-uk-wikisource.py.

Usage:
  python3 scripts/convert-steere-wikisource.py [--out books/sw]

Network: fetches from the wikisource.org MediaWiki API on every run.
"""
import argparse
import importlib.util
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'convert_uk_wikisource', SCRIPTS / 'convert-uk-wikisource.py')
_uk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_uk)
extract = _uk.extract
hard_break_paragraph = _uk.hard_break_paragraph
clean_paras = _uk.clean_paras
simplify_events = _uk.simplify_events

API = 'https://wikisource.org/w/api.php'

# Printed order (book TOC); Mwanzo wa utenzi wa Ayubu deliberately absent.
PIECES = [
    'Kisa cha punda wa dobi',
    'Sultani Darai',
    'Kisa cha Kihindi',
    'Hekaya ya Mohammadi Mtepetevu',
    'Mifano',
    'Sultani Majinuni',
    'Mwalimu Goso',
    'Uza ghali, si uza rakhisi',
    'Kititi, na fisi, na simba',
    'Kisa cha Hassibu karim ad dini na Sultani wa nyoka',
    'Kisa cha mwewe na kunguru',
    'Sungura na simba',
    'Pepo aliyedanganywa na mtoto wa sultani',
    'Ao rathi, ao mali',
    'Mtu ayari na hamali',
    'Tumbako',
    'Vitendawili',
    'Nyani, na simba, na nyoka',
    'Simba na kulungu',
    'Hadithi ya Liongo',
    'Mashairi ya Liongo',
    'Utumbuizo wa Gungu',
]


def fetch_html(page):
    q = urllib.parse.urlencode({
        'action': 'parse', 'page': page, 'prop': 'text',
        'format': 'json', 'redirects': '1',
    })
    req = urllib.request.Request(
        f'{API}?{q}',
        headers={'User-Agent': 'multilingual-classics-markdown corpus converter'})
    for attempt in range(5):
        try:
            time.sleep(3)  # stay well inside the API's rate limits
            with urllib.request.urlopen(req) as r:
                return json.load(r)['parse']['text']['*']
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < 4:
                time.sleep(20 * (attempt + 1))
                continue
            raise


def assemble(events, title):
    paras = ['# ' + title]
    cur = []

    def close():
        if cur:
            paras.append(hard_break_paragraph(cur))
            cur.clear()

    first_center_skipped = False
    for kind, payload in simplify_events(events):
        if kind in ('line', 'dots'):
            cur.append(payload)
        elif kind in ('stanza', 'divider'):
            close()
        elif kind == 'center':
            close()
            # the page's own printed title header duplicates our heading
            if not first_center_skipped and payload.strip('* .').upper() == \
                    title.upper().rstrip('.'):
                first_center_skipped = True
                continue
            paras.append(payload.strip())
        elif kind == 'prose':
            close()
            paras.append(payload)
    close()
    return clean_paras(paras)


FRONTMATTER = '''---
title: Swahili Tales
title_translit: Hadithi za Kiswahili
author: Edward Steere
language: sw
year: 1870
source: Wikisource (multilingual)
source_url: "https://wikisource.org/wiki/Swahili_Tales"
license: Public domain in the United States
year_note: "London: Bell & Daldy, 1870. Tales told by natives of Zanzibar, collected and edited by Steere; the book prints Swahili and English on facing pages, and only the Swahili text is included."
selection_note: "All 22 secular pieces in the printed order: the tales, Mifano (proverbs), Vitendawili (riddles), and the Liongo cycle (Hadithi ya Liongo, Mashairi ya Liongo, Utumbuizo wa Gungu). Mwanzo wa utenzi wa Ayubu (the opening of the Utenzi of Job) is omitted under the corpus's secular-content rule."
source_note: "Human-proofread, scan-backed Wikisource transcription (Index:Swahili tales.djvu; 257 pages proofread, 2 validated), replacing an earlier Internet Archive OCR selection that carried heavy uncorrected noise. Period orthography preserved (bassi, killa, thahabu, fetha). Verse in the Liongo poems uses hard line breaks. The earlier invented Swahili title Hadithi za Wasuaheli was corrected to the printed title."
---
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/sw', help='output directory (default books/sw)')
    args = ap.parse_args()
    out = Path(args.out) / 'Edward Steere' / 'Swahili Tales.md'
    out.parent.mkdir(parents=True, exist_ok=True)

    blocks = []
    for title in PIECES:
        html = fetch_html(f'Swahili Tales/{title}')
        blocks.extend(assemble(extract(html), title))
        print(f'  fetched: {title}')
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER + body)
    print(f'steere: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
