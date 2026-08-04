#!/usr/bin/env python3
"""
convert-haw-gutenberg.py: build the haw cluster from Project Gutenberg.

Replaces the earlier Google Books OCR texts with Distributed
Proofreaders transcriptions:

- Ka Moolelo o Laieikawai: the Hawaiian-text section of PG etext 13603
  (Beckwith's 1918 bilingual edition, reprinting the 1863 Honolulu
  text): the OLELO HOAKAKA foreword through (HOPENA). The
  transcription drops the MOKUNA X heading; it is restored here by
  alignment with the English Chapter X opening sentence, and the
  restoration is disclosed in the source_note.
- Ka Moolelo o Umi: the Hawaiian "KA MOOLELO NO UMI" section of PG
  etext 72686 (Fornander Collection vol. 1 = Bishop Museum Memoirs
  vol. IV, 1916-17), ending before the KIHAPIILANI legend.

Verse (mele) is set off in the source by leading indentation and is
emitted with hard line breaks; prose paragraphs keep the source's hard
wrapping (markdown merges it). ALL-CAPS section lines become headings.

Usage:
  python3 scripts/convert-haw-gutenberg.py [--out books/haw]

Network: fetches the two PG plain-text files on every run.
"""
import argparse
import re
import urllib.request
from pathlib import Path

PG = {
    'laieikawai': 'https://www.gutenberg.org/cache/epub/13603/pg13603.txt',
    'umi': 'https://www.gutenberg.org/cache/epub/72686/pg72686.txt',
}

MOKUNA_X_ANCHOR = 'A no keia olelo a kona kaikauhine opiopio, alaila i aku o Aiwohikupua,'


def fetch(url):
    req = urllib.request.Request(
        url, headers={'User-Agent': 'multilingual-classics-markdown corpus converter'})
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')


def slice_between(lines, start_pred, end_pred):
    start = next(i for i, l in enumerate(lines) if start_pred(l))
    end = next(i for i in range(start + 1, len(lines)) if end_pred(lines[i]))
    return lines[start:end]


def paragraphs(lines):
    paras, cur = [], []
    for l in lines:
        if l.strip():
            cur.append(l)
        elif cur:
            paras.append(cur)
            cur = []
    if cur:
        paras.append(cur)
    return paras


def is_verse(para):
    return all(re.match(r'\s{2,}\S', l) for l in para)


def is_columnar(para):
    """Aligned multi-column block (the Umi genealogy table): deep indent
    and at least one line with three space-separated columns."""
    return all(re.match(r'\s{4,}\S', l) for l in para) and \
        any(len(re.split(r'\s{2,}', l.strip())) >= 3 for l in para)


def table_rows(paras):
    """Merge consecutive columnar paragraphs into markdown table lines.

    Cells are sliced at the header's column start positions, so brace
    continuation marks and short rows keep their columns."""
    lines = [l for para in paras for l in para]
    header = lines[0]
    starts = [m.start() for m in re.finditer(r'\S+\.', header)]

    def cells(line):
        # boundaries sit 2 columns left of each header word, so brace
        # continuation marks stay with the column they annotate
        bounds = [s - 2 for s in starts[1:]] + [len(line) + 200]
        out = []
        pos = 0
        for b in bounds:
            out.append(re.sub(r'\s+', ' ', line[pos:b]).strip())
            pos = b
        return out

    rows = [cells(l) for l in lines]
    out = ['| ' + ' | '.join(rows[0]) + ' |',
           '|' + '---|' * len(starts)]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(out)


def hard_break(lines):
    out = [re.sub(r'\s+', ' ', l).strip() for l in lines]
    return '\n'.join(l + ('  ' if i < len(out) - 1 else '') for i, l in enumerate(out))


def caps_heading(text):
    return re.fullmatch(r"[A-Z][A-Z0-9 .,:;'()\[\]-]+", text) is not None


def render(paras, heading_level='##', mokuna_merge=False):
    """Emit markdown blocks. ALL-CAPS one-liners become headings; a
    MOKUNA number line followed by a caps subtitle merges into one
    heading when mokuna_merge is set."""
    out = []
    i = 0
    while i < len(paras):
        p = paras[i]
        text = ' '.join(l.strip() for l in p)
        if is_columnar(p):
            group = [p]
            while i + 1 < len(paras) and is_columnar(paras[i + 1]):
                i += 1
                group.append(paras[i])
            out.append(table_rows(group))
            i += 1
            continue
        if len(p) == 1 and caps_heading(text):
            if mokuna_merge and re.fullmatch(r'MOKUNA [IVXL]+\.?', text) \
                    and i + 1 < len(paras):
                nxt = ' '.join(l.strip() for l in paras[i + 1])
                if len(paras[i + 1]) <= 2 and caps_heading(nxt):
                    out.append(f'{heading_level} {text} {nxt}')
                    i += 2
                    continue
            out.append(f'{heading_level} {text}')
        elif is_verse(p):
            out.append(hard_break(p))
        else:
            out.append(re.sub(r'\s+', ' ', text).strip())
        i += 1
    return out


def laieikawai():
    lines = fetch(PG['laieikawai']).splitlines()
    body = slice_between(
        lines,
        lambda l: l.strip() == 'OLELO HOAKAKA',
        lambda l: l.strip() == '(HOPENA)')
    # restore the dropped MOKUNA X heading at its aligned anchor
    for i, l in enumerate(body):
        if l.strip() == MOKUNA_X_ANCHOR:
            body[i:i] = ['MOKUNA X', '']
            break
    else:
        raise SystemExit('laieikawai: MOKUNA X anchor not found')
    paras = paragraphs(body)
    out = render(paras)
    out.append('(HOPENA)')
    return '\n\n'.join(out) + '\n'


def umi():
    lines = fetch(PG['umi']).splitlines()
    body = slice_between(
        lines,
        lambda l: l.strip().startswith('KA MOOLELO NO UMI:'),
        lambda l: l.strip() == 'KIHAPIILANI.')
    body = body[1:]  # printed work title; the frontmatter carries it
    paras = paragraphs(body)
    out = render(paras, mokuna_merge=True)
    return '\n\n'.join(out) + '\n'


FRONTMATTER = {
    'laieikawai': '''---
title: Ka Moolelo o Laieikawai
title_en: The Story of Laieikawai
author: S. N. Haleole
language: haw
year: 1918
source: Project Gutenberg
source_url: "https://www.gutenberg.org/ebooks/13603"
license: Public domain in the United States
year_note: "First published Honolulu 1863 (Whitney); this text follows the Hawaiian side of Martha Beckwith's 1918 bilingual edition (Bureau of American Ethnology 33rd Annual Report), which reprints the 1863 text."
source_note: "Human-proofread Distributed Proofreaders transcription (the complete Hawaiian section of PG etext 13603: the OLELO HOAKAKA foreword and all 34 mokuna through HOPENA), replacing an earlier Google Books OCR. One disclosed correction: the transcription drops the MOKUNA X heading, restored here by alignment with the English Chapter X opening sentence. Mele are set with hard line breaks. Period orthography: no okina or kahako are marked, as in the 1863 printing."
---
''',
    'umi': '''---
title: Ka Moolelo o Umi
title_en: The Story of Umi
author: Anonymous
language: haw
year: 1917
source: Project Gutenberg
source_url: "https://www.gutenberg.org/ebooks/72686"
license: Public domain in the United States
year_note: "Bernice Pauahi Bishop Museum Memoirs Vol. IV (Fornander Collection of Hawaiian Antiquities and Folk-lore, vol. 1), issued in parts 1916-1917; the Umi narrative is from Fornander's 19th-century collection."
source_note: "Human-proofread Distributed Proofreaders transcription (the complete Hawaiian KA MOOLELO NO UMI section of PG etext 72686, mokuna I-XII with the Kamakau editorial insert, ending before the Kihapiilani legend), replacing an earlier Google Books OCR that garbled headings and truncated at mokuna IX. Mele and genealogy lines are set with hard line breaks. Period orthography preserved."
---
''',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--out', default='books/haw', help='output directory (default books/haw)')
    args = ap.parse_args()
    out = Path(args.out)
    targets = {
        'laieikawai': (out / 'S. N. Haleole' / 'Ka Moolelo o Laieikawai.md', laieikawai),
        'umi': (out / 'Anonymous' / 'Ka Moolelo o Umi.md', umi),
    }
    for key, (path, fn) in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        body = fn()
        path.write_text(FRONTMATTER[key] + body)
        print(f'{key}: {len(body)} chars -> {path}')


if __name__ == '__main__':
    main()
