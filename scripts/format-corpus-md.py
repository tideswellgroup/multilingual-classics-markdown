#!/usr/bin/env python3
"""
format-corpus-md.py: post-conversion formatting pass for corpus markdown.

Runs after a convert-*.py step has produced a file with YAML frontmatter and a
body. Does three things, any subset, and leaves the frontmatter byte-identical:

  * promote headings: body lines whose trimmed text exactly matches a supplied
    literal (repeatable --heading, or one-per-line --heading-file) become ATX
    headings at --level (default 1). Matching is on the stripped line so a
    centred or indented title still promotes. Idempotent: a line already at the
    target level is left alone.
  * verse spacing (--verse): set one verse line per paragraph, the house
    convention for vendored verse (see the pl Pan Tadeusz selection_note). Every
    run of adjacent non-blank body lines is re-emitted with a blank line between
    each line, so a markdown renderer shows one line per line rather than
    soft-wrapping the stanza into a paragraph. Heading lines and existing blank
    lines are preserved; runs already blank-separated are unchanged.
  * strip trailing marginal line numbers (--strip-linenums): remove a run of
    two-or-more spaces followed by digits at end of line, the reference numbers
    printed in the margin of scholarly verse editions (e.g. the Harrison-Sharp
    Beowulf). Applied before verse spacing.

Not a converter: it never fetches and never invents frontmatter. Bytes outside
the body are untouched.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TRAILING_LINENUM = re.compile(r"[ \t]{2,}\d+[ \t]*$")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_including_fences, body). If there is no frontmatter
    the first element is empty and the whole text is body."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def promote_headings(body: str, headings: set[str], level: int) -> str:
    prefix = "#" * level + " "
    out = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped in headings:
            out.append(prefix + stripped)
        else:
            out.append(line)
    return "\n".join(out)


def promote_by_regex(body: str, pattern: str, level: int) -> str:
    """Promote every body line that fully matches `pattern` to a heading at
    `level`, keeping the line's own text (e.g. numbered-poem markers like
    `1.`). Lines already starting with `#` are left alone."""
    rx = re.compile(rf"^\s*(?:{pattern})\s*$")
    prefix = "#" * level + " "
    out = []
    for line in body.split("\n"):
        if line.lstrip().startswith("#"):
            out.append(line)
        elif rx.match(line):
            out.append(prefix + line.strip())
        else:
            out.append(line)
    return "\n".join(out)


def strip_linenums(body: str) -> str:
    return "\n".join(TRAILING_LINENUM.sub("", line) for line in body.split("\n"))


def hard_breaks(body: str, from_marker: str | None) -> str:
    """Append a two-space hard break to the end of every verse line so a
    CommonMark renderer keeps one line per line instead of merging a stanza
    into a prose paragraph. Blank lines (stanza and poem gaps) and heading lines
    are left untouched. If `from_marker` is given, hard-breaking is off until a
    line whose text equals it is seen, so a prose introduction that precedes the
    verse is left as flowing prose."""
    active = from_marker is None
    out = []
    for line in body.split("\n"):
        s = line.strip()
        if from_marker is not None and s == from_marker:
            active = True
        if active and s and not s.startswith("#"):
            out.append(line.rstrip() + "  ")
        else:
            out.append(line)
    return "\n".join(out)


def versify(body: str) -> str:
    """One line per paragraph. Emit a blank line between adjacent non-blank
    lines; collapse existing multi-blank runs to one; leave heading lines with a
    blank line on either side."""
    lines = body.split("\n")
    out: list[str] = []
    prev_blank = True  # suppress leading blanks
    for line in lines:
        if line.strip() == "":
            if not prev_blank:
                out.append("")
            prev_blank = True
            continue
        if not prev_blank:
            out.append("")  # blank between two consecutive non-blank lines
        out.append(line)
        prev_blank = False
    # trim trailing blanks, restore single trailing newline by caller
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", help="markdown file to format in place")
    p.add_argument("--heading", action="append", default=[], help="literal body line to promote to a heading (repeatable)")
    p.add_argument("--heading-file", help="file of heading literals, one per line")
    p.add_argument("--level", type=int, default=1, help="heading level for promotions (default 1)")
    p.add_argument("--heading-regex", help="promote body lines fully matching this regex to headings at --level")
    p.add_argument("--hard-breaks", action="store_true", help="append two-space hard breaks to verse lines")
    p.add_argument("--hard-break-from", help="only hard-break at/after a line equal to this (protects preceding prose)")
    p.add_argument("--verse", action="store_true", help="one verse line per paragraph")
    p.add_argument("--strip-linenums", action="store_true", help="strip trailing marginal line-reference numbers")
    args = p.parse_args()

    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    headings = set(h.strip() for h in args.heading if h.strip())
    if args.heading_file:
        for line in Path(args.heading_file).read_text(encoding="utf-8").split("\n"):
            if line.strip():
                headings.add(line.strip())

    if args.strip_linenums:
        body = strip_linenums(body)
    if headings:
        body = promote_headings(body, headings, args.level)
    if args.heading_regex:
        body = promote_by_regex(body, args.heading_regex, args.level)
    if args.hard_breaks:
        body = hard_breaks(body, args.hard_break_from)
    if args.verse:
        body = versify(body)

    body = body.strip("\n") + "\n"
    path.write_text(fm + body, encoding="utf-8")
    n_head = sum(1 for line in body.split("\n") if line.startswith("#"))
    print(f"formatted {path}: {len(body):,} body bytes, {n_head} heading line(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
