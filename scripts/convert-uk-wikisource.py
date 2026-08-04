#!/usr/bin/env python3
"""
convert-uk-wikisource.py: build the uk cluster from uk.wikisource.org.

Three books, three source shapes:

- Shevchenko, Кобзарь (1840): scan-backed ProofreadPage transclusions,
  one subpage per poem, verse inside div.poem split across page
  boundaries, ornamental Rule_Segment tables, and the edition's rows of
  dots (censorship elisions) printed as text tables. Page-turn joins are
  continuous; within-page paragraph splits become stanza breaks.
- Kotsiubynsky, Тіні забутих предків: ProofreadPage prose from the 1955
  Книгоспілка (New York) Твори vol. 2, with illustration-plate captions
  (dropped, disclosed), asterism section breaks (kept), song verses in
  div.poem (hard breaks), and the edition's Hutsul-glossary notes
  (bracketed numbers pointing to a closing Примітки section, because
  GFM footnote syntax renders literally in the maintainer's markdown
  app, whose render audit gates this corpus).
- Lesia Ukrainka, Лісова пісня: a typed transcription (no scan backing),
  one <poem> block of wikitext; tabs flattened, cast list linearized,
  act headings promoted.

Usage:
  python3 scripts/convert-uk-wikisource.py [--out books/uk]

Network: fetches from the uk.wikisource.org MediaWiki API on every run.
"""
import argparse
import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

API = 'https://uk.wikisource.org/w/api.php'
DOTS_RE = re.compile(r'^[\s.·•…]+$')
ROMAN_RE = re.compile(r'^\*\*([IVXІ]+)\.?\*\*$')
BLOCK_START_UNSAFE = re.compile(r'^(#|>|[-+*] |\d+[.)] |=|`{3})')


def fetch(page, prop):
    q = urllib.parse.urlencode({
        'action': 'parse', 'page': page, 'prop': prop,
        'format': 'json', 'redirects': '1',
    })
    req = urllib.request.Request(
        f'{API}?{q}',
        headers={'User-Agent': 'multilingual-classics-markdown corpus converter'},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)['parse'][prop]['*']


class Walker(HTMLParser):
    """Linear event stream over Wikisource ProofreadPage rendered HTML.

    Events: line, stanza, pagebreak, dots, center, prose, divider, ref.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []
        self.stack = []
        self.in_content = False
        self.content_depth = None
        self.poem_depth = None
        self.center_depth = None
        self.in_p = False
        self.cur = []
        self.prose_kind = None
        self.skip_depth = None
        self.table_depth = None
        self.table_buf = []
        self.table_has_img = False
        self.in_refs = False
        self.cur_ref = None
        self._in_supref = False
        self.loose = []

    def _text(self):
        t = ''.join(self.cur)
        self.cur = []
        return re.sub(r'[ \t ]+', ' ', t).strip()

    def _flush_verse_line(self):
        t = self._text()
        if t:
            self.events.append(('line', t))

    def _flush_loose(self):
        t = re.sub(r'[ \t ]+', ' ', ''.join(self.loose)).strip()
        self.loose = []
        if t:
            self.events.append(('prose', t))

    def _buf(self):
        if self.poem_depth is not None or self.prose_kind is not None or \
           self.in_p or self.cur_ref is not None:
            return self.cur
        return self.loose

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get('class') or '').split()
        style = a.get('style') or ''
        depth = len(self.stack)
        self.stack.append(tag)

        if tag in ('style', 'script'):
            self.skip_depth = depth
            return
        if self.skip_depth is not None:
            return
        if self.table_depth is not None:
            if tag == 'img':
                self.table_has_img = True
            return

        if tag == 'div' and 'prp-pages-output' in classes:
            self.in_content = True
            self.content_depth = depth
            return
        # footnote bodies live after the content div closes
        if tag == 'ol' and 'references' in classes:
            self.in_refs = True
            return
        if self.in_refs and tag == 'li':
            self.cur_ref = a.get('id') or ''
            self.cur = []
            return
        if not self.in_content:
            return

        if 'ws-noexport' in classes or 'pagenum' in classes or \
           'visibility:hidden' in style or 'display:none' in style or \
           'color:transparent' in style:
            self.skip_depth = depth
            return
        if tag == 'table':
            self._flush_loose()
            self.table_depth = depth
            self.table_buf = []
            self.table_has_img = False
            return
        if tag == 'div' and 'poem' in classes:
            self._flush_loose()
            self.poem_depth = depth
            self.cur = []
            return
        if tag == 'div' and ('tiInherit' in classes or 'text-align:center' in style):
            if self.poem_depth is None:
                self._flush_loose()
                self.center_depth = depth
                self.prose_kind = 'center'
                self.cur = []
            return
        if tag == 'p':
            self.in_p = True
            if self.poem_depth is None and self.prose_kind is None and self.cur_ref is None:
                self._flush_loose()
                self.prose_kind = 'prose'
                self.cur = []
            return
        if tag == 'br':
            if self.poem_depth is not None:
                self._flush_verse_line()
            else:
                self.cur.append('\n')
            return
        if tag == 'i':
            self._buf().append('*')
        elif tag == 'b':
            self._buf().append('**')
        elif tag == 'sup' and 'reference' in classes:
            self._buf().append('[')
            self._in_supref = True

    def handle_endtag(self, tag):
        while self.stack:
            t = self.stack.pop()
            depth = len(self.stack)

            if self.skip_depth is not None:
                if depth <= self.skip_depth:
                    self.skip_depth = None
                if t == tag:
                    return
                continue

            if self.table_depth is not None:
                if t == 'table' and depth <= self.table_depth:
                    buf = re.sub(r'[ \t ]+', ' ', ''.join(self.table_buf)).strip()
                    self.table_depth = None
                    if self.table_has_img:
                        self.events.append(('divider', None))
                    elif buf and DOTS_RE.match(buf):
                        self.events.append(('dots', buf))
                    elif buf:
                        self.events.append(('prose', buf))
                    return
                if t == tag and self.table_depth is not None and depth > self.table_depth:
                    return
                continue

            if t != tag:
                continue

            if self.content_depth is not None and depth <= self.content_depth and tag == 'div' \
                    and self.in_content:
                self._flush_loose()
                self.in_content = False
            if tag == 'div' and self.poem_depth is not None and depth <= self.poem_depth:
                self._flush_verse_line()
                self.events.append(('pagebreak', None))
                self.poem_depth = None
            elif tag == 'div' and self.center_depth is not None and depth <= self.center_depth:
                txt = self._text()
                if txt:
                    self.events.append(('center', txt))
                self.center_depth = None
                self.prose_kind = None
            elif tag == 'p':
                self.in_p = False
                if self.poem_depth is not None:
                    self._flush_verse_line()
                    self.events.append(('stanza', None))
                elif self.cur_ref is not None:
                    pass
                elif self.prose_kind == 'prose':
                    txt = self._text()
                    if txt:
                        self.events.append(('prose', txt))
                    self.prose_kind = None
            elif tag == 'li' and self.cur_ref is not None:
                txt = self._text().lstrip('↑ ')
                num = re.sub(r'\D', '', self.cur_ref) or self.cur_ref
                self.events.append(('ref', (num, txt)))
                self.cur_ref = None
            elif tag == 'ol' and self.in_refs:
                self.in_refs = False
            elif tag == 'i':
                self._buf().append('*')
            elif tag == 'b':
                self._buf().append('**')
            elif tag == 'sup' and self._in_supref:
                self._buf().append(']')
                self._in_supref = False
            return

    def handle_data(self, data):
        if self.skip_depth is not None:
            return
        if self.cur_ref is not None:
            self.cur.append(data)
            return
        if not self.in_content:
            return
        if self.table_depth is not None:
            self.table_buf.append(data)
            return
        if self._in_supref:
            self._buf().append(re.sub(r'\D', '', data))
            return
        self._buf().append(data)


def extract(html):
    w = Walker()
    w.feed(html)
    return w.events


def hard_break_paragraph(lines):
    out = []
    for i, ln in enumerate(lines):
        if i == 0 and BLOCK_START_UNSAFE.match(ln):
            ln = '\\' + ln
        out.append(ln + ('  ' if i < len(lines) - 1 else ''))
    return '\n'.join(out)


JUNK_PARA = re.compile(r'^[*\s]+$')


def clean_paras(paras):
    """Drop empty-emphasis junk paragraphs, keep real asterisms (* * *)."""
    return [p for p in paras if p == '* * *' or not JUNK_PARA.match(p)]


def simplify_events(events):
    """Drop page-end stanza markers; page breaks join continuously."""
    out = []
    for i, ev in enumerate(events):
        kind = ev[0]
        if kind == 'stanza':
            nxt = events[i + 1][0] if i + 1 < len(events) else None
            if nxt == 'pagebreak':
                continue
            out.append(('stanza', None))
        elif kind == 'pagebreak':
            continue
        else:
            out.append(ev)
    return out


def assemble_verse_stream(events, heading_first_center=False):
    paras = []
    cur = []

    def close():
        if cur:
            paras.append(hard_break_paragraph(cur))
            cur.clear()

    first_center_seen = False
    for kind, payload in simplify_events(events):
        if kind in ('line', 'dots'):
            cur.append(payload)
        elif kind in ('stanza', 'divider'):
            close()
        elif kind == 'center':
            close()
            if not first_center_seen and heading_first_center:
                first_center_seen = True
                continue
            m = ROMAN_RE.match(payload)
            if m:
                paras.append(f'## {m.group(1)}.')
            else:
                paras.append(payload.strip())
        elif kind == 'prose':
            close()
            paras.append(payload)
    close()
    return paras


KOBZAR_POEMS = [
    'Думы мои, думы мои…', 'Перебендя', 'Катерына', 'Тополя',
    'Думка', 'До Основьяненка', 'Иванъ Пидкова', 'Тарасова ничъ',
]


def kobzar():
    body = []
    for title in KOBZAR_POEMS:
        html = fetch(f'Кобзарь (1840)/{title}', 'text')
        paras = clean_paras(assemble_verse_stream(extract(html), heading_first_center=True))
        body.append(f'# {title.rstrip("…")}'.rstrip())
        body.extend(paras)
    return '\n\n'.join(body) + '\n'


TINI_CAPTIONS = {
    'Вона і перше любила пишно вбиратись…',
    '… і вже останнім зусиллям підняв до неба короткий ціпок: Стій!..',
    'Іван… поплив в легкім гуцульськім танці.',
    'Палагна зверталась до неї, до тої самотньої душеньки мужа.',
}


def tini():
    html = fetch('Твори (Коцюбинський, 1955)/2/Тіні забутих предків', 'text')
    events = extract(html)
    paras = []
    cur = []
    refs = []

    def close():
        if cur:
            paras.append(hard_break_paragraph(cur))
            cur.clear()

    title_seen = False
    for kind, payload in simplify_events(events):
        if kind == 'ref':
            refs.append(payload)
        elif kind == 'line':
            cur.append(payload)
        elif kind in ('stanza', 'divider'):
            close()
        elif kind == 'center':
            close()
            t = payload.strip()
            if t in TINI_CAPTIONS:
                continue
            if t == '* * *':
                paras.append('* * *')
            elif not title_seen and 'ТІНІ ЗАБУТИХ ПРЕДКІВ' in t:
                title_seen = True
            else:
                paras.append(t)
        elif kind == 'prose':
            close()
            paras.append(payload)
    close()
    paras = clean_paras(paras)
    if refs:
        paras.append('## Примітки')
        paras.append('\n'.join(f'{n}. {t}' for n, t in refs))
    return '\n\n'.join(paras) + '\n'


def lisova():
    w = fetch('Лісова пісня', 'wikitext')
    m = re.search(r'<poem>(.*)</poem>', w, re.S)
    raw = m.group(1).split('\n')
    tail = w[m.end():].strip()

    lines = []
    for ln in raw:
        ln = ln.replace('\t', ' ')
        ln = re.sub(r'[  ]+', ' ', ln).strip()
        lines.append(ln)

    # act headings appear twice: as cast-list labels (followed by short
    # name lines) and as body headings (followed within a few lines by a
    # long stage direction). Only the body occurrences become headings.
    body_heads = {}
    cast_heads = set()
    for i, ln in enumerate(lines):
        if re.fullmatch(r'ПРОЛОГ|ДІЯ [IІ]+', ln):
            body_heads[i] = ln
            if not any(len(nxt) > 120 for nxt in lines[i + 1:i + 4]):
                cast_heads.add(i)

    paras = []
    cur = []

    def close():
        if cur:
            paras.append(hard_break_paragraph(cur))
            cur.clear()

    for i, ln in enumerate(lines):
        if ln == 'ЛІСОВА ПІСНЯ' and i < 5:
            continue
        if not ln:
            close()
            continue
        if i in body_heads and i not in cast_heads:
            close()
            paras.append(f'## {ln}')
            continue
        if i in cast_heads:
            close()
            paras.append(f'**{ln}**')
            continue
        if ln == 'Драма-феєрія в 3-х діях':
            close()
            paras.append('*Драма-феєрія в 3-х діях*')
            continue
        if ln.startswith('СПИС ДІЯЧІВ'):
            close()
            paras.append(f'## {ln}')
            continue
        cur.append(ln)
    close()
    if tail:
        paras.append(tail)
    return '\n\n'.join(paras) + '\n'


FRONTMATTER = {
    'kobzar': '''---
title: Кобзарь
title_translit: Kobzar
title_en: The Kobzar
author: Тарас Шевченко
author_translit: Taras Shevchenko
language: uk
year: 1840
source: Wikisource (uk)
source_url: "https://uk.wikisource.org/wiki/%D0%9A%D0%BE%D0%B1%D0%B7%D0%B0%D1%80%D1%8C_(1840)"
license: Public domain in the United States
year_note: "First edition, Saint Petersburg 1840: the original eight works (Думы мои, Перебендя, Катерына, Тополя, Думка, До Основьяненка, Иванъ Пидкова, Тарасова ничъ)."
source_note: "Scan-backed ProofreadPage transcription of the 1840 first edition, which is printed in yaryzhka (the Russian-alphabet orthography of pre-reform Ukrainian publishing); the orthography is preserved verbatim. The edition's rows of dots (censorship elisions) are reproduced as printed. Ornamental rules are dropped; stanza breaks follow the transcription's paragraphing, and page-turn joins are continuous."
---
''',
    'tini': '''---
title: Тіні забутих предків
title_translit: Tini zabutykh predkiv
title_en: Shadows of Forgotten Ancestors
author: Михайло Коцюбинський
author_translit: Mykhailo Kotsiubynsky
language: uk
year: 1912
source: Wikisource (uk)
source_url: "https://uk.wikisource.org/wiki/%D0%A2%D0%B2%D0%BE%D1%80%D0%B8_(%D0%9A%D0%BE%D1%86%D1%8E%D0%B1%D0%B8%D0%BD%D1%81%D1%8C%D0%BA%D0%B8%D0%B9,_1955)/2/%D0%A2%D1%96%D0%BD%D1%96_%D0%B7%D0%B0%D0%B1%D1%83%D1%82%D0%B8%D1%85_%D0%BF%D1%80%D0%B5%D0%B4%D0%BA%D1%96%D0%B2"
license: Public domain in the United States
year_note: "Written 1911, first published in Літературно-науковий вістник, 1912. The transcription base is Твори, vol. 2 (Книгоспілка, New York, 1955), a scan-backed émigré edition."
source_note: "Four illustration-plate captions of the 1955 edition (each quoting a phrase of the text) are omitted; the edition's asterism section breaks are kept as thematic breaks. Song verses within the prose use hard line breaks. The glossary notes explaining Hutsul dialect words are the edition's own: bracketed numbers in the text point to the closing Примітки section."
---
''',
    'lisova': '''---
title: Лісова пісня
title_translit: Lisova pisnia
title_en: The Forest Song
author: Леся Українка
author_translit: Lesia Ukrainka
language: uk
year: 1912
source: Wikisource (uk)
source_url: "https://uk.wikisource.org/wiki/%D0%9B%D1%96%D1%81%D0%BE%D0%B2%D0%B0_%D0%BF%D1%96%D1%81%D0%BD%D1%8F"
license: Public domain in the United States
year_note: "Composed July 1911 (the closing date 25/VII 1911 is the author's); first published in Літературно-науковий вістник, 1912. The Wikisource page dates the work 1911."
source_note: "Typed Wikisource transcription in modern orthography without a stated base edition and without scan backing. Verse indentation is flattened and the two-column cast list is linearized; spaced-out speaker names (М а в к а) follow the transcription. Stage directions are kept in place as prose lines."
---
''',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/uk', help='output directory (default books/uk)')
    args = ap.parse_args()
    out = Path(args.out)

    targets = {
        'kobzar': (out / 'Тарас Шевченко' / 'Кобзарь.md', kobzar),
        'tini': (out / 'Михайло Коцюбинський' / 'Тіні забутих предків.md', tini),
        'lisova': (out / 'Леся Українка' / 'Лісова пісня.md', lisova),
    }
    for key, (path, fn) in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        body = fn()
        path.write_text(FRONTMATTER[key] + body)
        print(f'{key}: {len(body)} chars -> {path}')


if __name__ == '__main__':
    main()
