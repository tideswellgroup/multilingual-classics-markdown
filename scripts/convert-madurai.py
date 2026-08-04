#!/usr/bin/env python3
"""
convert-madurai.py: fetch a Project Madurai UTF-8 etext (HTML) and convert
it to vendor-ready markdown for the multilingual-classics-markdown corpus.

Project Madurai (https://www.projectmadurai.org) publishes clean Unicode
etexts of Tamil literary works. The HTML is a thin wrapper: a provenance
header block closed by an <hr>, then the work as plain text with <br> line
breaks and coloured <h2>/<h3> section headers, then a trailing <hr> footer.

This converter is tuned for the Tirukkural moolam etext (pm0001), whose
body is a run of kural couplets grouped under numbered section headers.
Structure it emits:

  <h3> heading, one integer   -> #   heading   (Pal / book)
  <h3> heading, two integers  -> ##  heading   (Iyal / section)
  <h3> heading, three integers-> ### heading   (Adhigaram / chapter)
  couplet: metrical lines with a trailing kural number after the second line
                              -> a two-line stanza, running number in ()

Headings are lifted structurally out of the <h3> blocks rather than matched
by number pattern, so the etext's occasional typo'd numbers (e.g. "2,3.6",
"3..2. 9") are still recognised as headings; the number is rebuilt from the
integers it contains ("2.3.6", "3.2.9").

Each kural is emitted as two metrical lines joined by a markdown hard line
break (two trailing spaces) so the couplet stays a grouped unit rather than
reflowing to prose, with a blank line between successive kurals. The kural
venba is always two lines; where the source wraps one metrical line with a
stray <br>, the physical lines before the numbered closing line are rejoined
so the output is always exactly two lines.

The number in parentheses is a running 1..N counter, the canonical kural
numbering. The trailing number the source prints after each couplet marks a
boundary, but a few of those printed numbers are data-entry typos in the
etext (781 keyed as "7811", 1298 as "12983", 72 repeating 71); propagating
them would emit impossible kural numbers, so the value is regenerated from
the running count and only the boundary is taken from the source mark.

Not a general Project Madurai parser: it recognises the numbered
Pal/Iyal/Adhigaram heading idiom and the trailing-number couplet idiom the
didactic verse etexts use.

Usage:
  scripts/convert-madurai.py --url <etext-url> --title T --author A \
      --language ta --year Y --output books/ta/.../file.md
"""

from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"

# Sentinel prefix marking a line lifted out of an <h3> section header.
HEAD = "\x01"
TAMIL = "஀-௿"
# Leading numbering of a heading: digits, dots, commas, spaces. Handles the
# etext's occasional typos "2,3.6" and "3..2. 9" as well as clean "1.1.1".
RE_HEADNUM = re.compile(r"^[\d.,\s]+")
# Debris: a line with no Tamil letter and no word character (e.g. a stray ">").
RE_DEBRIS = re.compile(r"^[^\w" + TAMIL + r"]+$")
# A closing couplet line ends with whitespace runs then the kural number.
RE_CLOSE = re.compile(r"^(.*\S)\s+(\d+)\s*$")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def strip_wrapper(raw: str) -> str:
    """Return the work body: from the first <h3> section header (everything
    before it is the provenance header and title) to the last <hr> (the footer
    follows it). The Project Madurai header carries several <hr> rules of its
    own, so anchoring on the first section block is more reliable than counting
    rules."""
    h3 = re.search(r"(?i)<h3\b", raw)
    if not h3:
        sys.stderr.write("[warn] no <h3> section header found; using whole body\n")
        return raw
    rules = [m.start() for m in re.finditer(r"(?i)<hr\b[^>]*>", raw)]
    end = next((r for r in reversed(rules) if r > h3.start()), len(raw))
    return raw[h3.start():end]


def _clean(fragment: str) -> list[str]:
    """Strip tags/entities from an HTML fragment and return its non-empty,
    whitespace-normalised lines (<br> already turned into newlines upstream)."""
    text = htmllib.unescape(re.sub(r"<[^>]+>", "", fragment))
    lines = []
    for line in text.splitlines():
        line = line.replace("\xa0", " ").strip()
        if line:
            lines.append(re.sub(r"\s{2,}", " ", line))
    return lines


def to_lines(body: str) -> list[str]:
    """Flatten the HTML body to plain text lines. Lines from an <h3> section
    header are prefixed with the HEAD sentinel; every other line is couplet
    text."""
    # Repair the etext's occasional unclosed <font ...> tag (a "<font color=..."
    # with no closing '>' before the newline). Left as-is, tag stripping would
    # span the newline and swallow the heading text that follows it.
    body = re.sub(r"<font\b[^>]*(?=\n)", lambda m: m.group(0) + ">", body)
    body = re.sub(r"(?i)<br\s*/?>", "\n", body)
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"(?is)<h3\b[^>]*>(.*?)</h3>", body):
        out.extend(_clean(body[pos:m.start()]))
        out.extend(HEAD + line for line in _clean(m.group(1)))
        pos = m.end()
    out.extend(_clean(body[pos:]))
    return out


def parse_heading(line: str) -> tuple[str, str]:
    """Split a heading line into a normalised dotted number and its text.
    Rebuilds the number from the integers in the leading numeric run so typos
    like '2,3.6' and '3..2. 9' become '2.3.6' and '3.2.9'."""
    m = RE_HEADNUM.match(line)
    nums = re.findall(r"\d+", m.group(0)) if m else []
    text = line[m.end():].strip() if m else line
    return ".".join(nums), text


def convert(url: str, title: str, author: str, language: str, year: str,
            source_url: str, year_note: str | None = None,
            source_note: str | None = None,
            heading_fixes: dict[str, str] | None = None) -> tuple[str, int]:
    raw = fetch(url)
    lines = to_lines(strip_wrapper(raw))
    fixes = heading_fixes or {}

    md: list[str] = []
    pending: list[str] = []  # metrical lines accumulated for the current kural
    kural_count = 0

    def flush() -> None:
        nonlocal kural_count
        if not pending:
            return
        kural_count += 1
        # The kural venba is two lines: the last physical line is the second
        # metrical line; anything before it is the first (rejoining any stray
        # mid-line wrap the source introduced).
        line1 = " ".join(pending[:-1]) if len(pending) > 1 else pending[0]
        line2 = pending[-1] if len(pending) > 1 else ""
        stanza = line1 if not line2 else f"{line1}  \n{line2}"
        md.append(f"{stanza} ({kural_count})")
        md.append("")
        pending.clear()

    for line in lines:
        bare = line[len(HEAD):] if line.startswith(HEAD) else line
        if bare == title or bare.rstrip(".").endswith("முற்றிற்று"):
            continue  # work-title repeat (h2 or h3) or "... முற்றிற்று" colophon
        if line.startswith(HEAD):
            head = bare
            flush()
            dotted, text = parse_heading(head)
            # A disclosed emendation: correct a heading the etext mistranscribed
            # (verified against the same etext's closing colophon). Applied only
            # to the named section number; recorded in the frontmatter note.
            text = fixes.get(dotted, text)
            marker = "#" * min(max(dotted.count(".") + 1, 1), 3)
            md += ["", f"{marker} {dotted} {text}".rstrip(), ""]
            continue
        if RE_DEBRIS.match(line):
            continue  # stray ">" and similar tag debris
        close = RE_CLOSE.match(line)
        if close:
            pending.append(close.group(1))
            flush()
        else:
            pending.append(line)
    flush()

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(md)).strip() + "\n"

    year_field = year if year.isdigit() else f'"{year}"'
    front = f"---\ntitle: {title}\nauthor: {author}\n"
    front += f"language: {language}\nyear: {year_field}\n"
    if year_note:
        front += f'year_note: "{year_note}"\n'
    front += f'source: Project Madurai\nsource_url: "{source_url}"\n'
    if source_note:
        front += f'source_note: "{source_note}"\n'
    front += "license: Public domain in the United States\n---\n\n"
    return front + text, kural_count


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a Project Madurai etext to corpus markdown.")
    ap.add_argument("--url", required=True, help="Project Madurai UTF-8 HTML etext URL")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--language", required=True, help="BCP-47 language tag")
    ap.add_argument("--year", required=True)
    ap.add_argument("--year-note")
    ap.add_argument("--source-note")
    ap.add_argument("--fix-heading", action="append", default=[], metavar="DOTTED=TEXT",
                    help="correct a mistranscribed section heading, e.g. 2.2=அமைச்சியல் "
                         "(disclose the correction in --source-note)")
    ap.add_argument("--source-url", help="source_url for frontmatter (defaults to --url)")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    heading_fixes = dict(pair.split("=", 1) for pair in args.fix_heading)
    md, n = convert(
        args.url, args.title, args.author, args.language, args.year,
        args.source_url or args.url, args.year_note, args.source_note,
        heading_fixes,
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    sys.stderr.write(f"[ok] wrote {out} ({n} couplets, {len(md.encode('utf-8'))} bytes)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
