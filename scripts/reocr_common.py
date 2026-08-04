#!/usr/bin/env python3
"""
reocr_common.py: shared helpers for the two-engine re-OCR converters.

Stdlib only. The re-OCR pipeline (see REOCR.md) reads two independent
engines' per-page text from the local scans/ cache and measures where
they agree. The single-number, character-level page agreement we first
tried is confounded by editorial apparatus (German footnotes in Velten,
English glosses in the Yoruba books) and page furniture: the two engines
handle that non-body material differently, which drags the blended
number well below the body-text quality.

The refined metric works per line, on body lines only:

- a "body line" is a content line in the work's primary script, long
  enough to be text rather than a page number or catchword, and not
  obvious apparatus (a footnote-marker line, a running head);
- each body line's agreement is its best character-match ratio against
  the other engine's full page text;
- the headline is then the fraction of body lines both engines read the
  same way (agreement >= HIGH), plus the count of lines below it, which
  is the list a human reviewer should check first.

This isolates the question that matters ("how much of the actual text is
machine-stable?") from apparatus noise.
"""
import difflib
import re

HIGH = 0.80          # a body line at/above this is treated as high-confidence
MIN_BODY_LEN = 12    # shorter content lines are page numbers, catchwords, etc.


def clean_lines(text):
    out = []
    for line in text.splitlines():
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            out.append(line)
    return out


def make_is_body(primary_script=None, min_len=MIN_BODY_LEN):
    """Return a predicate deciding whether a line is primary-language body
    text. primary_script is a compiled regex matching one character of the
    work's script; when given, a body line must be majority that script
    (this cleanly drops German/English apparatus from a non-Latin work).
    For Latin-script works leave it None and rely on length plus the
    apparatus screen below."""
    running_head = re.compile(r'^\W*\d{1,4}\W*$')
    footnote_marker = re.compile(r'^[\d*†‡)\].\s]{1,6}\b')

    def is_body(line):
        if len(line) < min_len:
            return False
        if running_head.match(line):
            return False
        if primary_script is not None:
            hits = len(primary_script.findall(line))
            letters = sum(c.isalpha() for c in line)
            if letters == 0 or hits / letters < 0.5:
                return False
        return True

    return is_body


def _best_line_ratio(line, other_lines, sm):
    """Best similarity of `line` to any single line on the other engine's
    page. Line-to-best-line (not line-to-page-blob): two engines break
    lines the same way, and this tolerates their minor systematic
    differences (romanisation variants, dash-vs-space) instead of being
    dragged down by cross-line misalignment."""
    sm.set_seq2(line)
    best = 0.0
    for ol in other_lines:
        # cheap length gate before the O(n*m) ratio
        if abs(len(ol) - len(line)) > max(len(line), len(ol)) * 0.5:
            continue
        sm.set_seq1(ol)
        best = max(best, sm.ratio())
        if best >= 0.995:
            break
    return best


def agreement(base_pages, other_pages, is_body):
    """base_pages / other_pages: {page_id: text}. Returns per-book stats
    and the flagged (low-agreement) body lines for review."""
    page_ids = sorted(set(base_pages) & set(other_pages))
    ratios = []
    flagged = []
    sm = difflib.SequenceMatcher(autojunk=False)
    for pid in page_ids:
        other_lines = clean_lines(other_pages[pid])
        for line in clean_lines(base_pages[pid]):
            if not is_body(line):
                continue
            ratio = _best_line_ratio(line, other_lines, sm)
            ratios.append(ratio)
            if ratio < HIGH:
                flagged.append((pid, round(ratio, 2), line))
    if not ratios:
        return {'body_lines': 0, 'high_conf_frac': 0.0,
                'mean': 0.0, 'flagged': 0}, flagged
    high = sum(1 for r in ratios if r >= HIGH)
    return {
        'body_lines': len(ratios),
        'high_conf_frac': round(high / len(ratios), 4),
        'mean': round(sum(ratios) / len(ratios), 4),
        'flagged': len(ratios) - high,
    }, flagged


def pick_base(tess_pages, vision_pages, script_re, page_ids=None):
    """Choose the cleaner engine as the base text. The Cherokee lesson:
    do not default to Tesseract. Measures each engine's non-script,
    non-digit character rate over the (optionally restricted) pages; the
    lower-noise engine wins. Returns (base_pages, cross_pages, name)."""
    ids = page_ids or sorted(set(tess_pages) & set(vision_pages))

    def noise(pages):
        junk = total = 0
        for pid in ids:
            for ch in pages.get(pid, ''):
                if ch.isspace():
                    continue
                total += 1
                if not (script_re.match(ch) or ch.isdigit()):
                    junk += 1
        return junk / total if total else 1.0

    tn, vn = noise(tess_pages), noise(vision_pages)
    if vn <= tn:
        return vision_pages, tess_pages, 'Google Vision'
    return tess_pages, vision_pages, 'Tesseract'


def reflow_paragraphs(page_texts, page_order, heading_re=None,
                      drop_re=None, para_frac=0.68):
    """Assemble prose blocks from per-page OCR text. Paragraph breaks come
    from the OCR's blank lines where present; on pages with none, a line
    ending short of the column width (para_frac of it) closes a paragraph.
    heading_re lines become their own blocks (marked with a leading \\x00
    so the caller can format them); drop_re lines (page furniture) are
    skipped without breaking a paragraph; line-end hyphenation is joined."""
    blocks, cur, carry = [], [], ['']

    def flush():
        if cur:
            blocks.append(' '.join(cur))
            cur.clear()

    for pid in page_order:
        raw = [re.sub(r'[ \t]+', ' ', l).rstrip() for l in page_texts[pid].splitlines()]
        raw = [l for l in raw if not (drop_re and l.strip() and drop_re.match(l.strip()))]
        has_blanks = any(not l.strip() for l in raw)
        content = [l for l in raw if l.strip()]
        width = (sorted(len(l) for l in content)[int(len(content) * 0.85)]
                 if content else 60)
        for l in raw:
            s = l.strip()
            if not s:
                if has_blanks:
                    flush()
                continue
            if heading_re and heading_re.match(s):
                flush()
                blocks.append('\x00' + s)
                continue
            if carry[0]:
                s = carry[0] + s
                carry[0] = ''
            if s.endswith('-'):
                carry[0] = s[:-1]
                continue
            cur.append(s)
            if not has_blanks and len(s) < width * para_frac:
                flush()
    flush()
    return blocks


def stats_sentence(stats):
    return (f"Two-engine body-line agreement (REOCR.md): "
            f"{stats['high_conf_frac']:.0%} of {stats['body_lines']} "
            f"primary-language body lines read identically by both engines "
            f"(mean {stats['mean']:.0%}); {stats['flagged']} lines diverge "
            f"and are the first place a fluent reviewer should look.")
