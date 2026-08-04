#!/usr/bin/env python3
"""
convert-krestomatio.py: convert Project Gutenberg #8224 (Fundamenta
Krestomatio, L. L. Zamenhof, 1903) to vendor-ready markdown.

Replaces the demoted Archive.org OCR scan of Fundamento de Esperanto
(2026-07-17): the render audit showed the sanitiser silently dropping
OCR pseudo-tags from that copy, and its prose was OCR-garbled
throughout. The Krestomatio is the foundational Esperanto literary
anthology by the same author, and Gutenberg's edition is typed by the
Distributed Proofreading Team, not OCR.

Handling specific to this edition:
  * The plain text uses the x-system (cx gx hx jx sx ux); Esperanto has
    no letter x, so digraph conversion to proper diacritics is lossless
    and deterministic. Case variants (Cx, CX, ...) are covered because
    caps headings carry them (ANTAUXPAROLO).
  * Body starts at ANTAUXPAROLO: the pages before it are period
    publisher advertisements from the scan source, not authorial text.
  * Verse is indented >= 8 spaces (prose paragraphs indent 3); indented
    runs become hard-broken stanza lines per the corpus convention
    (FRONTMATTER.md, Verse).
  * Standalone ALL-CAPS lines are piece titles (## ); a Roman-numeral
    line directly before one is a part marker (# I. EKZERCOJ). Caps
    lines ending in a comma are signatures, not titles.
  * [Ilustrajxo: ...] placeholders and dotted-leader TOC lines are
    production artifacts and are dropped.

Usage:
  scripts/convert-krestomatio.py [--source FILE] [--output PATH]

With no --source, fetches the Gutenberg UTF-8 text. Verify afterwards
with lint-corpus.py and check-verse-breaks.py.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://www.gutenberg.org/ebooks/8224.txt.utf-8"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "books/eo/Ludwik Lejzer Zamenhof/Fundamenta Krestomatio.md"
)

GUT_START = re.compile(r"^\s*\*+\s*START OF (THE|THIS) PROJECT GUTENBERG.*\*+\s*$", re.IGNORECASE | re.MULTILINE)
GUT_END = re.compile(r"^\s*\*+\s*END OF (THE|THIS) PROJECT GUTENBERG.*\*+\s*$", re.IGNORECASE | re.MULTILINE)

# x-system digraphs, longest-case-first so CX beats Cx at the same spot.
X_SYSTEM = [
    ("CX", "Ĉ"), ("Cx", "Ĉ"), ("cx", "ĉ"),
    ("GX", "Ĝ"), ("Gx", "Ĝ"), ("gx", "ĝ"),
    ("HX", "Ĥ"), ("Hx", "Ĥ"), ("hx", "ĥ"),
    ("JX", "Ĵ"), ("Jx", "Ĵ"), ("jx", "ĵ"),
    ("SX", "Ŝ"), ("Sx", "Ŝ"), ("sx", "ŝ"),
    ("UX", "Ŭ"), ("Ux", "Ŭ"), ("ux", "ŭ"),
]

ROMAN = re.compile(r"^[IVXLCDM]+\.?$")
TOC_LEADER = re.compile(r"\.\s+\.\s+\.")
ILLUSTRATION = re.compile(r"^\s*\[Ilustra(jx|ĵ)o[^\]]*\]\s*$")

VERSE_INDENT = 8

# ASCII-art formula signatures (the astronomy article in part V draws
# multi-line fractions): numbered equations, fraction bars, and
# single-letter definitions. Such groups become fenced code blocks so
# the line layout survives; merged into prose they are gibberish.
EQ_NUMBERED = re.compile(r"^\s*\(?\d+\)\s*[^.]*=")
EQ_FRACTION_BAR = re.compile(r"-{5,}")
EQ_DEFINITION = re.compile(r"^\s*[A-Za-z]'?\s+=\s+")


def is_formula_group(group: list[str]) -> bool:
    if not group or len(group) > 12:
        return False
    text = "\n".join(group)
    if "=" not in text:
        return False
    return any(
        EQ_NUMBERED.match(line) or EQ_FRACTION_BAR.search(line) or EQ_DEFINITION.match(line)
        for line in group
    )


def fetch(source: str | None) -> str:
    if source:
        return Path(source).read_text(encoding="utf-8")
    req = urllib.request.Request(URL, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def x_to_diacritics(text: str) -> str:
    for digraph, letter in X_SYSTEM:
        text = text.replace(digraph, letter)
    return text


def is_caps_title(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 60:
        return False
    if not re.search(r"[A-ZĈĜĤĴŜŬ]", s):
        return False
    if s != s.upper():
        return False
    if s.endswith((",", ";")):
        return False  # signature lines (L. ZAMENHOF,)
    if ROMAN.match(s):
        return False
    return True


def convert(text: str) -> str:
    start = GUT_START.search(text)
    end = GUT_END.search(text)
    if not start or not end:
        raise ValueError("Gutenberg START/END markers not found")
    body = text[start.end() : end.start()]
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = x_to_diacritics(body)

    lines = body.split("\n")

    # Body proper starts at the ANTAŬPAROLO heading; everything before
    # it is publisher advertisement pages.
    for i, line in enumerate(lines):
        if line.strip() == "ANTAŬPAROLO":
            lines = lines[i:]
            break
    else:
        raise ValueError("ANTAŬPAROLO heading not found")

    # Blank-delimited formula groups become code fences before the
    # line classifier runs, so their internal alignment is untouched.
    fenced: set[int] = set()
    group_start = None
    for i, line in enumerate(lines + [""]):
        if line.strip():
            if group_start is None:
                group_start = i
        else:
            if group_start is not None:
                group = lines[group_start:i]
                if is_formula_group(group):
                    fenced.update(range(group_start, i))
                group_start = None

    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if i in fenced:
            j = i
            while j < len(lines) and j in fenced:
                j += 1
            block = lines[i:j]
            margin = min(len(b) - len(b.lstrip(" ")) for b in block if b.strip())
            out.append("```")
            out.extend(b[margin:].rstrip() for b in block)
            out.append("```")
            i = j
            continue

        if ILLUSTRATION.match(line) or TOC_LEADER.search(line) or stripped == "ENHAVO":
            i += 1
            continue

        # Half-title repetitions of the book's own title carry no
        # structure the frontmatter doesn't already state.
        if stripped in ("FUNDAMENTA KRESTOMATIO", "DE LA LINGVO", "ESPERANTO") and out:
            i += 1
            continue

        # Part marker: a Roman numeral with its caps title on the next
        # non-blank line.
        if ROMAN.match(stripped):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_caps_title(lines[j]):
                out.append(f"# {stripped.rstrip('.')}. {lines[j].strip()}")
                i = j + 1
                continue
            out.append(f"## {stripped.rstrip('.')}")
            i += 1
            continue

        if stripped == "ANTAŬPAROLO":
            out.append("# ANTAŬPAROLO")
            i += 1
            continue

        if is_caps_title(line):
            out.append(f"## {stripped}")
            i += 1
            continue

        # Verse: deep indentation. Emit stripped of indent, with the
        # corpus two-space hard break while the stanza continues.
        indent = len(line) - len(line.lstrip(" "))
        if stripped and indent >= VERSE_INDENT:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            nxt_indent = len(nxt) - len(nxt.lstrip(" "))
            nxt_is_verse = bool(nxt.strip()) and nxt_indent >= VERSE_INDENT and not is_caps_title(nxt)
            out.append(stripped + ("  " if nxt_is_verse else ""))
            i += 1
            continue

        # Prose. This edition indents every paragraph's FIRST line by a
        # few spaces (continuation lines are flush left), so a shallow
        # indent directly after a non-blank line is a paragraph break
        # the blank-line structure alone does not carry (the KVITANCO
        # receipt's dateline lines, for example).
        indent_shallow = 0 < indent < VERSE_INDENT
        if indent_shallow and out and out[-1].strip() and not out[-1].startswith("#"):
            out.append("")
        out.append(stripped)
        i += 1

    text_out = "\n".join(out)
    text_out = re.sub(r"\n{3,}", "\n\n", text_out).strip() + "\n"

    frontmatter = "\n".join([
        "---",
        "title: Fundamenta Krestomatio",
        "author: Ludwik Lejzer Zamenhof",
        "language: eo",
        "year: 1903",
        "source: Project Gutenberg",
        f'source_url: "{URL}"',
        "license: Public domain in the United States",
        'source_note: "Gutenberg #8224, DPT-proofread; x-system digraphs converted to diacritics (Esperanto has no letter x, so the mapping is lossless)."',
        "---",
        "",
    ])
    return frontmatter + text_out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", help="local copy of the Gutenberg text (skips fetch)")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = p.parse_args()

    result = convert(fetch(args.source))
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(result, encoding="utf-8")
    body_lines = result.count("\n")
    print(f"wrote {dest} ({len(result):,} bytes, {body_lines:,} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
