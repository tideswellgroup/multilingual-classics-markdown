#!/usr/bin/env python3
"""apply-verse-hardbreaks.py: whitespace-only repair of verse/line-structured
markdown where conversion left bare single newlines between lines within a
stanza. CommonMark merges those into a prose wall; the corpus convention is a
two-space hard break on every continuation line inside a stanza, blank lines
between stanzas, headings untouched.

Transformation (body only; YAML frontmatter is preserved byte for byte):
  * every line is right-trimmed of ASCII spaces/tabs (NBSP caesuras survive);
  * a non-blank, non-boundary line that is immediately followed by another
    non-blank, non-boundary line gets exactly two trailing spaces;
  * a line followed by a blank line or a boundary (heading/hr/fence) stays
    clean (no trailing spaces);
  * runs of blank lines collapse to a single blank line.

Boundaries (never get a hard break, never merge): ATX headings (`#`),
thematic breaks (`---`, `***`, `___`), and code fences (```` ``` ````).

Modes:
  --check   report only, do not write (default)
  --apply   write the transformed file
  --paragraphs  treat every non-boundary line as its own paragraph: insert a
                blank line between consecutive non-blank lines instead of a
                hard break (for paragraph-per-line prose, not verse)

Always prints before/after blank-line and hard-break counts and the
non-whitespace invariance result (must be OK).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BOUNDARY_PREFIXES = ("#",)


def is_boundary(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return True
    if s in ("---", "***", "___") or (len(s) >= 3 and set(s) <= {"-"} and s == "-" * len(s)):
        return True
    if s.startswith("```") or s.startswith("~~~"):
        return True
    return False


def is_blank(line: str) -> bool:
    # blank == only ASCII spaces/tabs; an NBSP-bearing line is content.
    return line.strip(" \t") == ""


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def transform_body(body: str, paragraphs: bool) -> str:
    lines = body.split("\n")
    # right-trim ASCII spaces/tabs only
    stripped = [ln.rstrip(" \t") for ln in lines]
    out: list[str] = []
    n = len(stripped)
    prev_blank = True
    for i, cur in enumerate(stripped):
        if is_blank(cur):
            if not prev_blank:
                out.append("")
            prev_blank = True
            continue
        prev_blank = False
        nxt = stripped[i + 1] if i + 1 < n else ""
        joins_next = (not is_blank(nxt)) and (not is_boundary(nxt)) and (not is_boundary(cur))
        if paragraphs:
            out.append(cur)
            if joins_next:
                out.append("")
        else:
            out.append(cur + "  " if joins_next else cur)
    # collapse trailing blank lines, ensure single terminal newline
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n"


def iter_blocks(stripped: list[str]):
    """Yield (start_idx, lines) for each maximal run of non-blank,
    non-boundary lines. Blank and boundary lines break blocks."""
    cur: list[str] = []
    start = 0
    for i, ln in enumerate(stripped):
        if is_blank(ln) or is_boundary(ln):
            if cur:
                yield start, cur
                cur = []
        else:
            if not cur:
                start = i
            cur.append(ln)
    if cur:
        yield start, cur


def classify_block(lines: list[str], prose_min: int, para_min: int, min_verse_lines: int = 2) -> str:
    if len(lines) < 2:
        return "single"
    lens = [len(l) for l in lines]
    if max(lens) > para_min:
        return "para"
    nonlast = lens[:-1]
    mean = sum(nonlast) / len(nonlast)
    if mean >= prose_min:
        return "prose"
    if len(lines) < min_verse_lines:
        # too few lines to trust as verse (likely a wrap artifact); leave as prose
        return "prose"
    return "verse"


def transform_auto(body: str, prose_min: int, para_min: int, report: bool, min_verse_lines: int = 2):
    """Block-classified transform: verse blocks get hard breaks, hardwrap
    prose blocks are left as-is, paragraph-per-line blocks get blank-line
    separators. Returns (new_body, report_lines)."""
    lines = body.split("\n")
    stripped = [ln.rstrip(" \t") for ln in lines]
    # mark each line with an action derived from its block
    action = ["blankish"] * len(stripped)  # blankish|verse|prose|para|single
    reps = []
    for start, blk in iter_blocks(stripped):
        kind = classify_block(blk, prose_min, para_min, min_verse_lines)
        for j in range(start, start + len(blk)):
            action[j] = kind
        if len(blk) >= 2:
            mean = sum(len(l) for l in blk[:-1]) / (len(blk) - 1)
            reps.append(f"  [{kind:6}] lines {start+1}-{start+len(blk)} "
                        f"n={len(blk)} mean={mean:.0f} max={max(len(l) for l in blk)} :: {blk[0][:48]!r}")
    out: list[str] = []
    n = len(stripped)
    prev_blank = True
    for i, cur in enumerate(stripped):
        if is_blank(cur) or is_boundary(cur):
            if is_boundary(cur):
                out.append(cur)
                prev_blank = False
            elif not prev_blank:
                out.append("")
                prev_blank = True
            continue
        prev_blank = False
        nxt = stripped[i + 1] if i + 1 < n else ""
        cont = (not is_blank(nxt)) and (not is_boundary(nxt))
        kind = action[i]
        if kind == "verse" and cont:
            out.append(cur + "  ")
        elif kind == "para":
            out.append(cur)
            if cont:
                out.append("")
        else:  # prose / single -> leave lines as-is (bare newline merges)
            out.append(cur)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n", reps


def nonspace(s: str) -> str:
    return "".join(c for c in s if c not in " \t\n\r")


def count_hardbreaks(body: str) -> int:
    return sum(1 for ln in body.split("\n") if ln.endswith("  ") and ln.strip())


def count_blanklines(body: str) -> int:
    return sum(1 for ln in body.split("\n") if ln.strip(" \t") == "")


def count_bad_trailing(body: str) -> int:
    bad = 0
    for ln in body.split("\n"):
        if not ln.strip():
            continue
        stripped = ln.rstrip(" \t")
        n = len(ln) - len(stripped)
        if n == 1 or n >= 3:
            bad += 1
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--paragraphs", action="store_true")
    ap.add_argument("--auto", action="store_true",
                    help="block-classified: verse->breaks, hardwrap-prose->leave, para->blank-separate")
    ap.add_argument("--report", action="store_true", help="print per-block classification")
    ap.add_argument("--prose-min", type=int, default=58)
    ap.add_argument("--para-min", type=int, default=90)
    ap.add_argument("--min-verse-lines", type=int, default=2)
    args = ap.parse_args()

    p = Path(args.path)
    text = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if args.auto:
        new_body, reps = transform_auto(body, args.prose_min, args.para_min, args.report, args.min_verse_lines)
        if args.report:
            for r in reps:
                print(r)
    else:
        new_body = transform_body(body, args.paragraphs)
    new_text = fm + new_body

    inv_ok = nonspace(text) == nonspace(new_text)
    print(f"file: {p}")
    print(f"  blank lines : {count_blanklines(body)} -> {count_blanklines(new_body)}")
    print(f"  hard breaks : {count_hardbreaks(body)} -> {count_hardbreaks(new_body)}")
    print(f"  bad trailing (1 or 3+ spaces): {count_bad_trailing(body)} -> {count_bad_trailing(new_body)}")
    print(f"  non-whitespace invariance: {'OK' if inv_ok else 'FAILED'}")
    if not inv_ok:
        print("  ABORT: content bytes would change; not writing", file=sys.stderr)
        return 2
    if args.apply:
        p.write_text(new_text, encoding="utf-8")
        print("  written.")
    else:
        print("  (check only; use --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
