#!/usr/bin/env python3
"""
convert-volapuk-anthology.py: build the vo anthology from Wikisource.

No complete typed pre-1929 Volapük book exists anywhere, but the
multilingual Wikisource community has hand-typed hundreds of short
pieces from the movement's period gazettes (Volapükabled zenodik,
Volapükabled Tälik, Kosmopolan, Nunal, and others, 1875-1901), each
carrying a {{Fonät}} source template naming gazette, year, issue, and
page. This converter assembles every mainspace item whose cited source
predates 1929 into one chronological anthology, excluding religious
items per the corpus's secular rule (the exclusion count is written
into the selection_note).

Conversion: bold/italic wiki markup carried over (including the
period's intraword morpheme bolding), {{sp|x}} letter-spacing emphasis
rendered as italic, centered divs flattened to their own lines, the
{{Fonät}} citation rendered as an italic line under each item's
heading, remaining templates dropped.

Usage:
  python3 scripts/convert-volapuk-anthology.py [--out books/vo]
                                               [--cached vo-pages.json]
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://wikisource.org/w/api.php'
UA = {'User-Agent': 'multilingual-classics-markdown corpus converter'}
RELIGIOUS = re.compile(
    r'\bhüm\b|\bpsalm|jesu|kristu|\bgod[aä]?\b|kirik|relig|bibel|prayer|klod\b',
    re.I)

FRONTMATTER = '''---
title: Penäds se Volapükagaseds
title_en: Pieces from the Volapük Gazettes
author: Various
language: vo
year: "1875-1901"
source: Wikisource (multilingual)
source_url: "https://wikisource.org/wiki/Category:Volap%C3%BCk"
license: Public domain in the United States
year_note: "An anthology of short pieces from the Volapük movement's period gazettes, chiefly Volapükabled zenodik (Schleyer's central gazette, 1881 onward), Volapükabled Tälik, Kosmopolan, Nunal, and the Volapük gaseds of the 1890s. Every piece's own citation (gazette, year, issue, page) is printed beneath its heading."
selection_note: "Selection rule: every mainspace item on multilingual Wikisource whose Fonät source template cites a pre-1929 gazette ({N_TOTAL} items), minus {N_RELIGIOUS} religious items excluded under the corpus's secular rule and {N_APPARATUS} items excluded for carrying modern comparative apparatus or unconvertible markup, ordered chronologically by cited year. Assembled by the corpus, not reproducing any single printed volume."
source_note: "Hand-typed transcriptions by the Wikisource Volapük community, item-level source citations throughout; no scan backing on individual items. The period typography's intraword morpheme bolding is preserved; letter-spacing emphasis is rendered as italics. Replaces the earlier Volaspodel, an OCR text of an 1892-93 periodical volume whose systematic garble could not be repaired (see QUALITY.md resolved log)."
---
'''


def api(**kw):
    kw.update(format='json')
    q = urllib.parse.urlencode(kw)
    req = urllib.request.Request(f'{API}?{q}', headers=UA)
    for attempt in range(5):
        try:
            time.sleep(6)
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < 4:
                time.sleep(30 * (attempt + 1))
                continue
            raise


def fetch_all_pages():
    members, cont = [], {}
    while True:
        d = api(action='query', list='categorymembers',
                cmtitle='Category:Volapük', cmlimit='500', cmnamespace='0', **cont)
        members += [m['title'] for m in d['query']['categorymembers']]
        if 'continue' in d:
            cont = {'cmcontinue': d['continue']['cmcontinue']}
        else:
            break
    pages = {}
    for i in range(0, len(members), 50):
        d = api(action='query', prop='revisions', rvprop='content',
                rvslots='main', titles='|'.join(members[i:i + 50]))
        for p in d['query']['pages'].values():
            if 'revisions' in p:
                pages[p['title']] = p['revisions'][0]['slots']['main']['*']
    return pages


def parse_fonat(w):
    m = re.search(r'\{\{\s*Fonät(.*?)\}\}', w, re.S)
    if not m:
        return None
    fields = dict(re.findall(r'(\w+)\s*=\s*([^\n|}]+)', m.group(1)))
    try:
        yel = int(fields.get('yel', '9999'))
    except ValueError:
        return None
    return {'gased': fields.get('gased', '').strip(), 'yel': yel,
            'num': fields.get('nüm', '').strip(), 'pads': fields.get('pads', '').strip()}


def to_markdown(w):
    w = re.sub(r'\{\{\s*Fonät.*?\}\}', '', w, flags=re.S)
    w = re.sub(r'\[\[Category:[^\]]*\]\]', '', w)
    w = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', w)
    # poem blocks become hard-break verse
    def poem(m):
        lines = [l.strip() for l in m.group(1).splitlines() if l.strip()]
        return '\n\n' + '\n'.join(
            l + ('  ' if i < len(lines) - 1 else '')
            for i, l in enumerate(lines)) + '\n\n'
    w = re.sub(r'<poem[^>]*>(.*?)</poem>', poem, w, flags=re.S)
    # the transcribers' editorial notes (misprint flags, German glosses)
    # become inline brackets; bare named refs and section markers drop
    w = re.sub(r'<ref[^>]*/>', '', w)
    w = re.sub(r'<ref[^>/]*>(.*?)</ref>', r' [\1]', w, flags=re.S)
    w = re.sub(r'</?references[^>]*>', '', w)
    w = re.sub(r'</?sup[^>]*>', '', w)
    # wikitext list markers must not collide with markdown headings
    w = re.sub(r'^#+\s*', '- ', w, flags=re.M)
    w = re.sub(r'^\*+\s*', '- ', w, flags=re.M)
    w = re.sub(r'\{\{sp\|([^}]*)\}\}', r'*\1*', w)
    w = re.sub(r'\{\{sup\|([^}]*)\}\}', r'\1', w)
    w = re.sub(r'\{\{[^{}]*\}\}', '', w, flags=re.S)   # remaining templates
    w = re.sub(r'<div[^>]*align\s*=\s*.?center[^>]*>(.*?)</div>',
               lambda m: '\n\n' + m.group(1).strip() + '\n\n', w, flags=re.S)
    w = re.sub(r'</?(big|small|div|span|center)[^>]*>', '', w)
    w = w.replace('<br>', '  \n').replace('<br/>', '  \n').replace('<br />', '  \n')
    w = re.sub(r"'''(.*?)'''", r'**\1**', w, flags=re.S)
    w = re.sub(r"''(.*?)''", r'*\1*', w, flags=re.S)
    paras = []
    for p in re.split(r'\n\s*\n', w):
        lines = [re.sub(r'[ \t]+', ' ', l).lstrip(':').strip()
                 for l in p.splitlines()]
        # drop empty and purely ornamental lines (asterisk rows, nbsp runs)
        lines = [l for l in lines
                 if l and not re.fullmatch(r'[*\s]+', l.replace('&nbsp;', ' '))]
        if not lines:
            continue
        if len(lines) == 1:
            paras.append(lines[0])
        else:
            # multi-line blocks are intentional line units (officer lists,
            # addresses, verse): hard-break every line
            paras.append('\n'.join(
                l + ('  ' if i < len(lines) - 1 else '')
                for i, l in enumerate(lines)))
    return [p for p in paras if p and not re.fullmatch(r'[*\s]+', p)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/vo')
    ap.add_argument('--cached', default=None,
                    help='path to a pre-fetched {title: wikitext} JSON dump')
    args = ap.parse_args()
    out = Path(args.out) / 'Various' / 'Penäds se Volapükagaseds.md'
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.cached:
        pages = json.load(open(args.cached))
    else:
        pages = fetch_all_pages()

    items = []
    n_religious = 0
    n_apparatus = 0
    for title, w in pages.items():
        f = parse_fonat(w)
        if not f or f['yel'] > 1928:
            continue
        if RELIGIOUS.search(title) or RELIGIOUS.search(w[:2000]):
            n_religious += 1
            continue
        if '{|' in w:   # wikitable: modern comparative apparatus, not period text
            n_apparatus += 1
            continue
        items.append((f['yel'], f['gased'], f['num'], title, w, f))
    items.sort(key=lambda x: (x[0], x[1], x[2], x[3]))

    blocks = []
    n_markup = 0
    kept = 0
    for yel, gased, num, title, w, f in items:
        paras = to_markdown(w)
        if any(re.search(r'<[a-zA-Z/]', p) for p in paras):
            n_markup += 1   # residual raw markup: excluded rather than shipped broken
            continue
        kept += 1
        blocks.append(f'# {title}')
        cite = f"*{gased}, {yel}" + (f", nüm {num}" if num else '') + \
               (f", p. {f['pads']}" if f['pads'] else '') + '*'
        blocks.append(cite)
        blocks.extend(paras)
    n_apparatus += n_markup

    fm = FRONTMATTER.replace('{N_TOTAL}', str(kept + n_religious + n_apparatus)) \
                    .replace('{N_RELIGIOUS}', str(n_religious)) \
                    .replace('{N_APPARATUS}', str(n_apparatus))
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(fm + body)
    print(f'anthology: {kept} items kept ({n_religious} religious, '
          f'{n_apparatus} apparatus/markup excluded), {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
