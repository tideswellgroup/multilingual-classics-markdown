#!/usr/bin/env python3
"""
convert-chr-reocr.py: assemble the chr Constitution and Laws from the
re-OCR pipeline's cached engine outputs.

Reads the per-page outputs of two independent OCR engines from the local
scans/ cache (see REOCR.md: Tesseract 5 with the chr model in
scans/tess/, Google Vision with the chr hint in scans/vision/), computes
their line-level agreement as a confidence signal, and assembles the
book from the base engine's text with:

- the front-matter excision rule applied (pages before the body anchor
  are copy apparatus and scan furniture: covers, calibration cards, the
  hand-lettered replacement title leaf, library stamps);
- running heads and bare page numbers stripped (standard conversion
  furniture, as in every other book);
- line-end hyphenation rejoined;
- paragraphs opening with an article marker promoted to headings;
- per-page and whole-book agreement statistics printed for REOCR.md and
  the source_note.

Stdlib only; the engine outputs it reads are produced by maintainer-side
tooling documented in REOCR.md.

Usage:
  python3 scripts/convert-chr-reocr.py [--scans scans] [--out books/chr]
                                       [--stats-only]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reocr_common import clean_lines, make_is_body, agreement, stats_sentence

# The book is excerpted to the 1839 Constitution alone (a coherent, canonical
# founding document) rather than the full 349-page Constitution-and-Laws
# compilation. In the 1892 volume the Constitution runs from its own title and
# Act-of-Union preamble to Sequoyah's 1839 ratification signatures, after which
# the 1866 Amended Constitution begins. START_ANCHOR sits in the preamble; the
# excerpt starts at the top of that page (the printed Constitution title) and
# ends at the page beginning with END_ANCHOR (the Amended Constitution).
START_ANCHOR = 'ᏥᏚᏙᎥ ᏣᎳᎩ ᎠᏰᎵ ᎤᏙᏢᏒ'    # "this is the Constitution of the Cherokee Nation"
END_ANCHOR = 'ᎪᏢᎯᏌᏅᎯ ᎦᎫᏍᏛᏗ'             # "Amended Constitution" (1866), first line of the next section
# The Constitution's own title line, the first printed line of the excerpt.
# Translation: "Constitution of the Cherokees". Emitted as the book's H1.
TITLE_LINE = 'ᎦᎫᏍᏛᏗ, ᎠᏂᏣᎳᎩ ᎤᏂᎲᎢ'
# The Constitution has two levels of division, which the OCR often runs
# inline with surrounding text rather than onto their own lines:
#   ᏓᏓᎯᏢ + a Roman numeral = an Article (six of them, I-VI)
#   ᎤᏓᏡᎬ + an Arabic numeral = a Section, renumbering within each Article
# Both marker words are OCR-spelled many ways; both are normalised to their
# canonical form in the headings. ARTICLE_ROMAN limits the numeral to the
# real article range so stray Roman-looking noise is not promoted.
ARTICLE = re.compile(r'(ᏓᏓ[Ꭰ-Ᏼ]{1,3})\s+([IVX]{1,4})(?![A-Za-z])\.?')
SECTION = re.compile(r'(ᎤᏓ[Ꭰ-Ᏼ]{1,3}Ꮬ?)\s+(\d{1,3})[.,]')
SYLLABARY = re.compile(r'[Ꭰ-Ᏼ]')
RUNNING_HEAD = re.compile(r'^[Ꭰ-Ᏼ .,]{0,24}\s*\d{1,3}\s*$|^\d{1,3}\s+[Ꭰ-Ᏼ .,]{0,24}$')
# the printed running head is the word ᎦᎫᏍᏛᏗ ("Constitution") alone at the
# page top; drop it when a whole line is just that word plus punctuation
# (the word also occurs inside section text, which is kept)
RUNHEAD_WORD = re.compile(r'^ᎦᎫᏍᏛᏗ\s*[.,]?\s*$')

FRONTMATTER = '''---
title: ᎦᎫᏍᏛᏗ ᎠᏂᏣᎳᎩ ᎤᏂᎲᎢ (Constitution of the Cherokee Nation)
title_en: Constitution of the Cherokee Nation
author: ᏣᎳᎩ ᎠᏰᎵ ᏙᏥᎳᏫᎥ (Cherokee National Council)
language: chr
year: 1892
year_note: "The 1839 Constitution, adopted at Tahlequah on the reunification of the eastern and western Cherokees; text from the 1892 printing (Parsons, Kansas). Secular civic content, explicitly selected over the abundant pre-1929 Cherokee scripture corpus per chr curation guidance."
source: Internet Archive
source_url: "https://archive.org/details/constitutionlaws0000vari"
license: Public domain in the United States
text_quality: alpha
selection_note: "The 1839 Constitution alone, excerpted from the 349-page Constitution and Laws of the Cherokee Nation (1892): printed pages 8 to 20 (Internet Archive scan leaves 14 to 26 of 358, BookReader images 15 to 27). The Constitution is a coherent standalone founding document: it runs from its title and Act-of-Union preamble through Sequoyah's 1839 ratification signatures, at which the printed volume turns to the 1866 Amended Constitution and then decades of session laws, none of which is included here. The full compilation is a statutory reference, not a work."
source_note: "Machine OCR, re-run 2026-07-25 by the corpus's two-engine pipeline (REOCR.md) after the Archive's own derive proved to have misdetected the book as Amharic in Latin script: Google Vision with the Cherokee hint is the base text (it reads the syllabary body about a third cleaner than Tesseract), cross-checked against Tesseract 5 with the Cherokee model; agreement statistics below. STILL UNVERIFIED BY A FLUENT READER: two engines agreeing is stability, not truth, and lines where they diverge are the first places a reviewer should look. The Constitution's two-level structure is recovered: its six Articles (ᏓᏓᎯᏢ I to VI, H2) and their Sections (ᎤᏓᏡᎬ, renumbering within each Article, H3), both markers normalised to canonical form and split out even where the OCR runs them inline with the surrounding text; the numerals are the OCR's own, so a few carry recognisable OCR slips (for example one Section 15 read as 5). Running heads, page numbers, and line-end hyphenation are resolved as in every conversion. The closing delegate signatories, printed in three columns, are rendered as a headerless three-column table (cell order follows the OCR reading order, since the exact print position is not recoverable from line-order OCR). {STATS}"
---
'''


def load_pages(d):
    return {p.stem: p.read_text() for p in sorted(Path(d).glob('*.txt'))
            if not p.stem.startswith('_')}


def _clean_para(text):
    # strip leading OCR dash noise, then escape an ordered-list trigger so
    # markdown does not eat a leading "N."
    text = re.sub('^[-*+' + chr(0x2013) + chr(0x2014) + r']\s+', '', text).strip()
    return re.sub(r'^(\d+)\.', r'\1\\.', text)


def split_divisions(para):
    """Split one paragraph into a two-level outline at the Article (ᏓᏓᎯᏢ +
    Roman) and Section (ᎤᏓᏡᎬ + Arabic) markers, wherever they occur, since
    the OCR runs them inline. Marker words are normalised to canonical."""
    marks = []
    for m in ARTICLE.finditer(para):
        marks.append((m.start(), m.end(), '## ᏓᏓᎯᏢ ' + m.group(2) + '.'))
    for m in SECTION.finditer(para):
        marks.append((m.start(), m.end(), '### ᎤᏓᏡᎬ ' + m.group(2) + '.'))
    marks.sort()
    if not marks:
        return [_clean_para(para)] if para.strip() else []
    out = []
    pre = para[:marks[0][0]]
    if pre.strip():
        out.append(_clean_para(pre))
    for i, (s, e, heading) in enumerate(marks):
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(para)
        out.append(heading)
        body = para[e:nxt]
        if body.strip():
            out.append(_clean_para(body))
    return out


def signatory_table(names):
    """Render the delegate signatories as a headerless three-column table,
    matching the three-column layout of the printed signature block. Cells
    follow the OCR reading order (the exact print position of each name is
    not recoverable from line-order OCR); Latin-only OCR debris is dropped."""
    clean = []
    for n in names:
        n = n.strip().rstrip('.,;')
        if SYLLABARY.search(n):
            clean.append(n)
    rows = [clean[i:i + 3] for i in range(0, len(clean), 3)]
    out = ['|  |  |  |', '|---|---|---|']
    for r in rows:
        r = r + [''] * (3 - len(r))
        out.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(out)


def assemble(tess, vision):
    # Vision is the base text: it reads the syllabary body markedly cleaner
    # than Tesseract (about a third less non-syllabary noise). Tesseract is
    # the cross-check engine for the agreement metric.
    base, cross = vision, tess
    pages = sorted(set(base) & set(cross))
    start = next(p for p in pages if START_ANCHOR in base[p])
    end = next(p for p in pages if p > start and END_ANCHOR in base[p])
    body_pages = [p for p in pages if start <= p < end]
    tess = base   # the assembly loop below reads from `tess`
    body = {p: base[p] for p in body_pages}
    body_v = {p: cross[p] for p in body_pages}

    # refined two-engine agreement over syllabary body lines
    stats, _flagged = agreement(body, body_v, make_is_body(SYLLABARY))

    # collect all body lines (title line dropped, page furniture filtered)
    all_lines = []
    title_done = False
    for p in body_pages:
        lines = [re.sub(r'\s+', ' ', r).strip() for r in tess[p].splitlines()]
        lines = [l for l in lines if SYLLABARY.search(l)
                 and not RUNNING_HEAD.match(l) and not RUNHEAD_WORD.match(l)]
        if not lines:
            continue
        if not title_done:
            title_done = True
            lines = lines[1:]      # drop the OCR'd title line; H1 emitted below
        all_lines.extend(lines)

    # the closing signature block is the maximal trailing run of short
    # name-lines (the delegate signatories, printed in three columns); split
    # it off so it is not reflowed into a paragraph
    sig_start = len(all_lines)
    while sig_start > 0 and len(all_lines[sig_start - 1].split()) <= 3 \
            and len(all_lines[sig_start - 1]) <= 24:
        sig_start -= 1
    if len(all_lines) - sig_start < 12:      # too short to be the block
        sig_start = len(all_lines)
    body_lines, sig_lines = all_lines[:sig_start], all_lines[sig_start:]

    # reflow the body into paragraphs on the short-line signal
    PARA_FRAC = 0.68
    lengths = sorted(len(l) for l in body_lines)
    width = lengths[int(len(lengths) * 0.85)] if lengths else 60
    paras, cur, carry = [], [], ''

    def flush():
        if cur:
            paras.append(' '.join(cur))
            cur.clear()

    for l in body_lines:
        if carry:
            l = carry + l
            carry = ''
        if l.endswith('-'):
            carry = l[:-1]
            continue
        cur.append(l)
        if len(l) < width * PARA_FRAC:
            flush()
    flush()

    blocks = ['# ' + TITLE_LINE]
    for para in paras:
        blocks.extend(split_divisions(para))
    if sig_lines:
        blocks.append(signatory_table(sig_lines))
    stats['signatories'] = len(sig_lines)

    stats['start_page'] = start
    stats['body_pages'] = len(body_pages)
    stats['articles'] = sum(1 for b in blocks if b.startswith('## '))
    stats['sections'] = sum(1 for b in blocks if b.startswith('### '))
    return blocks, stats_sentence(stats), stats


FREEZE_SENTINEL = 'Hand-maintained baseline'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument('--scans', default='scans')
    ap.add_argument('--out', default='books/chr')
    ap.add_argument('--stats-only', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='regenerate the baseline even if the target file has '
                         'been frozen for hand maintenance (this discards hand edits)')
    args = ap.parse_args()
    out = Path(args.out) / 'Cherokee National Council' / 'Constitution.md'
    # Freeze guard: once the shipped file is being hand-corrected against the
    # scan, this converter must not clobber those edits. It produced the
    # baseline and is kept for provenance; regenerating is now a deliberate,
    # --force-only act that resets the file to a fresh machine baseline.
    if out.exists() and FREEZE_SENTINEL in out.read_text()[:2000] and not args.force:
        print(f'{out} is frozen for hand maintenance ("{FREEZE_SENTINEL}" in its '
              f'source_note); refusing to overwrite. Re-run with --force only to '
              f'discard hand edits and rebuild the machine baseline.')
        return
    tess = load_pages(Path(args.scans) / 'tess')
    vision = load_pages(Path(args.scans) / 'vision')
    blocks, stats, raw = assemble(tess, vision)
    print(stats)
    print(raw)
    if args.stats_only:
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    body = '\n\n'.join(blocks) + '\n'
    out.write_text(FRONTMATTER.replace('{STATS}', stats) + body)
    print(f'chr: {len(body)} chars -> {out}')


if __name__ == '__main__':
    main()
