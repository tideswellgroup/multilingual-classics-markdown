#!/usr/bin/env python3
"""
convert-hawaiian-bilingual.py: extract the Hawaiian-language text from a
bilingual (Hawaiian + facing English) Internet Archive djvu.txt OCR source
and vendor it as markdown for the i18n-books corpus.

The Bishop Museum bilingual editions (Beckwith's Laieikawai 1918, the
Fornander Collection memoirs 1916-1920) print an English translation and the
Hawaiian original on facing pages. A linear OCR dump therefore alternates
English page / Hawaiian page. This helper separates the two by alphabet: the
Hawaiian alphabet is a e i o u h k l m n p w (plus the okina), so a paragraph
of Hawaiian carries almost none of the consonants b c d f g j q r s t v x y z,
while English is saturated with them. Each blank-line-delimited block is scored
by its ratio of those foreign consonants to all letters; blocks below the
threshold are kept, the rest dropped. Running page headers, Google scan
boilerplate, bare page numbers and the "Digitized by Google" footers are
stripped by pattern first so they cannot pollute the classifier.

The OCR is passed through otherwise unedited, matching the corpus precedent for
Internet Archive items (see convert-internet-archive.py). Expect residual OCR
noise; document its level in the vendored file's source_note.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Consonants absent from the Hawaiian alphabet. A high share of these in a
# block is the signal that the block is English (or Latin scan boilerplate).
FOREIGN = set("bcdfgjqrstvxyz")


def foreign_ratio(block: str) -> tuple[float | None, int]:
    letters = [c for c in block.lower() if c.isalpha()]
    if not letters:
        return None, 0
    foreign = sum(1 for c in letters if c in FOREIGN)
    return foreign / len(letters), len(letters)


def normalise_open_quote(text: str) -> tuple[str, int]:
    """Restore the opening double-quote that the Google OCR renders as '^^'.

    In the Beckwith 1918 setting the raised opening quotation mark is misread
    as a pair of carets while the matching closing mark is captured correctly
    as a straight double-quote. The artifact is fully systematic (every '^^'
    sits at the start of a line of direct speech, a comma or line start before
    it and a capital after) and its target is verifiable from the closing marks
    already present, so it is normalised to a straight double-quote rather than
    passed through. This is the only text substitution the converter makes; no
    other OCR correction is applied.
    """
    fixed, n = re.subn(r"\^\^\s*", '"', text)
    return fixed, n


def strip_junk_lines(text: str, drop_patterns: list[re.Pattern]) -> str:
    """Remove scan boilerplate, running headers, page numbers and footers
    line by line so they do not skew the per-block language score."""
    kept = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            kept.append("")
            continue
        # Google scan footer / provenance lines.
        if re.fullmatch(r"(Digitized by|Google|Original from|UNIVERSITY OF .*|Go{2,}gle)", s):
            continue
        # Bare page numbers or roman-numeral-only lines.
        if re.fullmatch(r"[\divxlcIVXLC.,;:\-\s]{1,8}", s):
            continue
        if any(p.search(s) for p in drop_patterns):
            continue
        kept.append(line)
    return "\n".join(kept)


def is_heading(block: str, heading_patterns: list[re.Pattern]) -> bool:
    return any(p.search(block.strip()) for p in heading_patterns)


def extract_hawaiian(
    text: str,
    threshold: float,
    heading_patterns: list[re.Pattern],
) -> tuple[str, dict]:
    blocks = re.split(r"\n\s*\n", text)
    out = []
    stats = {"kept": 0, "dropped": 0, "headings": 0}
    for block in blocks:
        b = block.strip()
        if not b:
            continue
        if is_heading(b, heading_patterns):
            # Promote a section/chapter marker to an H1 heading.
            heading = re.sub(r"\s+", " ", b)
            out.append(f"# {heading}")
            stats["headings"] += 1
            continue
        r, length = foreign_ratio(b)
        if r is None:
            continue
        # Short fragments are held to a stricter bar; long prose to the main one.
        limit = threshold if length >= 20 else min(threshold, 0.06)
        if r < limit:
            out.append(re.sub(r"[ \t]+\n", "\n", block.strip()))
            stats["kept"] += 1
        else:
            stats["dropped"] += 1
    body = "\n\n".join(out)
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    return body, stats


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if v is None:
            continue
        already_quoted = isinstance(v, str) and len(v) >= 2 and v[0] == '"' and v[-1] == '"'
        if isinstance(v, str) and not already_quoted and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def slice_body(text: str, start: str | None, end: str | None) -> str:
    if start:
        i = text.find(start)
        if i == -1:
            print(f"WARNING: start marker not found: {start!r}", file=sys.stderr)
        else:
            text = text[i:]
    if end:
        j = text.find(end)
        if j == -1:
            print(f"WARNING: end marker not found: {end!r}", file=sys.stderr)
        else:
            text = text[:j]
    return text


def build(args) -> None:
    raw = Path(args.input).read_text(encoding="utf-8", errors="replace")
    raw = slice_body(raw, args.start_marker, args.end_marker)
    quotes_fixed = 0
    if args.fix_open_quote:
        raw, quotes_fixed = normalise_open_quote(raw)
    drop_patterns = [re.compile(p) for p in args.drop_line_regex] if args.drop_line_regex else []
    heading_patterns = [re.compile(p) for p in args.heading_regex] if args.heading_regex else []
    cleaned = strip_junk_lines(raw, drop_patterns)
    body, stats = extract_hawaiian(cleaned, args.threshold, heading_patterns)

    meta = {
        "title": args.title,
        "author": args.author,
        "language": "haw",
        "year": args.year,
        "source": args.source,
        "source_url": f'"{args.source_url}"',
        "license": "Public domain in the United States",
    }
    if args.year_note:
        meta["year_note"] = f'"{args.year_note}"'
    if args.selection_note:
        meta["selection_note"] = f'"{args.selection_note}"'
    if args.source_note:
        meta["source_note"] = f'"{args.source_note}"'

    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(
        f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines) "
        f"kept={stats['kept']} dropped={stats['dropped']} headings={stats['headings']} "
        f"open_quotes_normalised={quotes_fixed}"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, help="Local djvu .txt path")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--year", required=True)
    p.add_argument("--source", default="Internet Archive")
    p.add_argument("--source-url", required=True, help="IA /details/ page URL for citation")
    p.add_argument("--output", required=True)
    p.add_argument("--threshold", type=float, default=0.13,
                   help="Max foreign-consonant ratio for a block to count as Hawaiian")
    p.add_argument("--fix-open-quote", action="store_true",
                   help="Normalise the systematic '^^' opening-quote OCR artifact to a straight double-quote")
    p.add_argument("--start-marker", default=None, help="Trim source to first occurrence of this substring")
    p.add_argument("--end-marker", default=None, help="Trim source before this substring")
    p.add_argument("--drop-line-regex", action="append", default=[],
                   help="Regex; matching lines are removed before classification (repeatable)")
    p.add_argument("--heading-regex", action="append", default=[],
                   help="Regex; matching blocks become H1 headings (repeatable)")
    p.add_argument("--year-note", default=None)
    p.add_argument("--selection-note", default=None)
    p.add_argument("--source-note", default=None)
    args = p.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
