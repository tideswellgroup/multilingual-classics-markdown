#!/usr/bin/env python3
"""
convert-la-wikisource.py: build the la cluster from la.wikisource.org.

One book, one source shape:

- Vergil, Aeneis: a typed transcription (no scan backing) spread over
  twelve sub-pages, Aeneis/Liber I through Aeneis/Liber XII. Each page
  carries a {{titulus2}} header naming the edition (J. B. Greenough,
  Bucolics, Aeneid, and Georgics of Vergil, Boston: Ginn & Co., 1900),
  a {{Liber}} previous/next navigation box, and the verse itself in a
  single <poem> block. The verse is macronised, and inside the poem the
  only markup is three templates: {{versus|N}} marginal line numbers,
  {{Versus|N}} (the same template, capitalised, used from Liber II on),
  and a {{r|1|}} anchor on the first line of each book.

  The marginal line numbers are an apparatus rather than text, so they
  are dropped; the book divisions become headings and are what makes the
  file citable. Liber I opens with the four-line "Ille ego, qui quondam"
  pre-proem, numbered A-D rather than 1-4 because it sits outside the
  canonical numbering; it is kept as its own stanza.

  One named correction is applied: at Liber I the transcription writes
  Tydides with U+04EF CYRILLIC SMALL LETTER U WITH MACRON, a homoglyph
  of the intended U+0233 LATIN SMALL LETTER Y WITH MACRON. No other
  Cyrillic codepoint appears in the text.

Usage:
  python3 scripts/convert-la-wikisource.py [--out books/la]

Network: fetches from the la.wikisource.org MediaWiki API on every run.
The API rate-limits anonymous bursts, so requests are paced and retried.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://la.wikisource.org/w/api.php"
UA = "multilingual-classics-markdown/1.0 (https://github.com/tideswellgroup/multilingual-classics-markdown)"

LIBRI = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII"]

# Canonical line count per book, used as the structural completeness check.
# Liber X is 908 in the canonical numbering; Greenough prints 10.872
# ("et furiis agitatus amor et conscia virtus") in square brackets as a
# suspected interpolation from 12.668, and this transcription omits it
# while keeping the surrounding numbering canonical.
CANONICAL = {
    "I": 756, "II": 804, "III": 718, "IV": 705, "V": 871, "VI": 901,
    "VII": 817, "VIII": 731, "IX": 818, "X": 907, "XI": 915, "XII": 952,
}

POEM_RE = re.compile(r"<poem>(.*?)</poem>", re.S)
VERSUS_RE = re.compile(r"\{\{[Vv]ersus\|[^}]*\}\}")
ANCHOR_RE = re.compile(r"\{\{r\|[^}]*\}\}")

FRONTMATTER = {
    "title": "Aeneis",
    "author": "Publius Vergilius Maro",
    "language": "la",
    "year": 1900,
    "source": "Wikisource (la)",
    "source_url": "https://la.wikisource.org/wiki/Aeneis",
    "license": "Public domain in the United States",
    "year_note": (
        "Composed between 29 and 19 BCE and left unrevised at Vergil's death. "
        "The year field is the cited source edition: J. B. Greenough, "
        "Bucolics, Aeneid, and Georgics of Vergil, Boston, Ginn & Co., 1900, "
        "which is the edition la.wikisource names in its page header."
    ),
    "source_note": (
        "Complete in twelve books, 9,895 verses. Checked against the canonical "
        "line counts, which it matches book for book (756, 804, 718, 705, 871, "
        "901, 817, 731, 818, 907, 915, 952). Liber X carries 907 of the "
        "canonical 908 because Greenough brackets 10.872 (et furiis agitatus "
        "amor et conscia virtus) as a suspected interpolation from 12.668 and "
        "this transcription omits it; the surrounding line numbering stays "
        "canonical, so citations still resolve. Liber I opens with the "
        "four-line Ille ego, qui quondam pre-proem, which most editors judge "
        "not to be Vergil's; the source numbers it A-D, outside the canonical "
        "count, and it is kept as its own opening stanza. Orthography is not "
        "uniform across the work: Liber I writes consonantal v (avena, venit) "
        "while Libri II-XII write u (renouare, uidi), an inconsistency "
        "inherited from the source and left as transcribed rather than "
        "normalised by guess. Vowel-quantity macrons are carried throughout "
        "and are an editorial layer that the Greenough print edition does not "
        "have. Wikisource's marginal line numbers are removed. Correction: at "
        "1.471 the source writes Tydides with U+04EF (Cyrillic u with macron), "
        "corrected to U+0233 (Latin y with macron)."
    ),
}
FIELD_ORDER = ["title", "author", "language", "year", "source", "source_url",
               "license", "year_note", "source_note"]

# Named correction: Cyrillic homoglyph in a Latin text.
CORRECTIONS = [("ӯ", "ȳ")]


def fetch_wikitext(page: str) -> str:
    """Fetch one page's wikitext, backing off when the API rate-limits us."""
    url = API + "?" + urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "wikitext",
        "format": "json", "formatversion": "2", "redirects": "1",
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["parse"]["wikitext"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise SystemExit(f"giving up on {page}: the API kept rate-limiting us")


def convert_liber(wikitext: str) -> list[str]:
    """Return the verse lines of one book, apparatus stripped."""
    poems = POEM_RE.findall(wikitext)
    if len(poems) != 1:
        raise SystemExit(f"expected exactly one <poem> block, found {len(poems)}")
    body = poems[0]
    body = VERSUS_RE.sub("", body)
    body = ANCHOR_RE.sub("", body)
    for bad, good in CORRECTIONS:
        body = body.replace(bad, good)
    # Blank lines are stanza breaks and are preserved; a run of them collapses.
    out: list[str] = []
    for raw in body.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line.strip())
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return out


def render(books: dict[str, list[str]]) -> str:
    """Assemble the markdown body, verse lines carrying hard breaks."""
    chunks = []
    for numeral in LIBRI:
        lines = books[numeral]
        parts = [f"# Liber {numeral}", ""]
        for line in lines:
            # A CommonMark hard break: exactly two trailing spaces. Without
            # this the poem renders as a prose wall. Stanza breaks stay bare.
            parts.append(line + "  " if line else "")
        chunks.append("\n".join(parts).rstrip())
    return "\n\n".join(chunks) + "\n"


def yaml_value(value) -> str:
    if isinstance(value, int):
        return str(value)
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def frontmatter() -> str:
    lines = ["---"]
    for key in FIELD_ORDER:
        lines.append(f"{key}: {yaml_value(FRONTMATTER[key])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build the Latin Aeneis from la.wikisource.org.")
    ap.add_argument("--out", default="books/la",
                    help="output directory for the la cluster (default: books/la)")
    ap.add_argument("--pause", type=float, default=3.0,
                    help="seconds between API requests (default: 3.0)")
    args = ap.parse_args()

    books: dict[str, list[str]] = {}
    problems = []
    for i, numeral in enumerate(LIBRI):
        if i:
            time.sleep(args.pause)
        page = f"Aeneis/Liber {numeral}"
        print(f"fetching {page} ...", file=sys.stderr)
        lines = convert_liber(fetch_wikitext(page))
        verses = [l for l in lines if l]
        # The pre-proem sits outside the canonical numbering, so it is not
        # counted when checking this book against its canonical length.
        counted = len(verses)
        if numeral == "I":
            counted -= 4
        if counted != CANONICAL[numeral]:
            problems.append(
                f"Liber {numeral}: {counted} verses, expected {CANONICAL[numeral]}")
        books[numeral] = lines
        print(f"  {counted} verses", file=sys.stderr)

    if problems:
        for p in problems:
            print(f"STRUCTURE: {p}", file=sys.stderr)
        raise SystemExit("structural check failed; refusing to write a short text")

    out_dir = Path(args.out) / FRONTMATTER["author"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{FRONTMATTER['title']}.md"
    target.write_text(frontmatter() + render(books), encoding="utf-8")
    total = sum(len([l for l in v if l]) for v in books.values())
    print(f"wrote {target} ({total} lines of verse)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
