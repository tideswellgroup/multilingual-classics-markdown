#!/usr/bin/env python3
"""
convert-papadiamantis.py: assemble a selection of Alexandros Papadiamantis
short stories from el.wikisource into one markdown file.

Greek digitisation usually converts polytonic originals to the monotonic
system introduced in 1982, which rewrites the accentuation of a pre-1929
text. This corpus keeps historical orthography, so the converter refuses any
page whose wikitext carries no breathings: a story that arrives monotonic is
a modernised text and is not admitted. The check is mechanical, counting
PSILI, DASIA and PERISPOMENI against TONOS.

Each story becomes an h2 heading carrying its title once, matching the
tr Seçme Hikâyeler selection already in the corpus.

Usage:
  scripts/convert-papadiamantis.py --output books/el/...

Exits 1 if any requested story fails the polytonic check or cannot be fetched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "multilingual-classics-markdown/1.0"
LANG = "el"

# Chosen for canon, register and length rather than for size alone: festival
# Skiathos, the Easter self-portrait, the lyric meditation, the poverty story,
# an Athens setting, and one short widely-anthologised piece.
STORIES = [
    "Στο Χριστό στο Κάστρο",
    "Λαμπριάτικος Ψάλτης",
    "Ρεμβασμός του Δεκαπενταυγούστου",
    "Η Σταχομαζώχτρα",
    "Ο ξεπεσμένος δερβίσης",
    "Το χριστόψωμο",
]

POLYTONIC_MARKS = ("PSILI", "DASIA", "PERISPOMENI")


def fetch_wikitext(page: str) -> str:
    params = {
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
    }
    url = f"https://{LANG}.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # Wikimedia answers an impatient client with 429. Respect Retry-After when
    # it is given and back off geometrically when it is not.
    delay = 15
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))["parse"]["wikitext"]
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 5:
                raise
            wait = int(error.headers.get("Retry-After") or delay)
            print(f"  429 on {page}; waiting {wait}s")
            time.sleep(wait)
            delay *= 2
    raise RuntimeError("unreachable")


def accentuation(text: str) -> tuple[int, int]:
    """Return (polytonic marks, monotonic tonos marks)."""
    poly = tonos = 0
    for ch in text:
        name = unicodedata.name(ch, "")
        if any(mark in name for mark in POLYTONIC_MARKS):
            poly += 1
        elif "TONOS" in name:
            tonos += 1
    return poly, tonos


def clean(wikitext: str) -> str:
    """Reduce the wikitext to prose, keeping the words and dropping apparatus."""
    text = wikitext
    # Header and navigation templates, footers, categories, interwiki links.
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)  # nested, one more pass
    text = re.sub(r"^\[\[(?:Κατηγορία|Category|[a-z]{2,3}):[^\]]*\]\]\s*$", "", text, flags=re.M)
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"</?(?:div|span|center|poem|br)[^>]*>", "", text)
    # Magic words (__NOTOC__ and friends) are page directives, not text.
    text = re.sub(r"__[A-Z]+__", "", text)
    # Internal links: keep the display text. The empty-target form [[|word]] is
    # a typo that occurs in the source and would otherwise survive as markup.
    text = re.sub(r"\[\[\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]|]*)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Unclosed links occur in the source too. By this point every well-formed
    # link is gone, so anything still opening a link is dangling markup.
    text = re.sub(r"\[\[[^\]|]*\|", "", text)
    text = text.replace("[[", "")
    # Emphasis.
    text = re.sub(r"'''''(.+?)'''''", r"***\1***", text, flags=re.S)
    text = re.sub(r"'''(.+?)'''", r"**\1**", text, flags=re.S)
    text = re.sub(r"''(.+?)''", r"*\1*", text, flags=re.S)
    # Wikisource section headings inside a story are apparatus, not the text.
    text = re.sub(r"^=+\s*[^=]*\s*=+\s*$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--output", required=True, help="Path of the markdown file to write.")
    parser.add_argument(
        "--allow-monotonic",
        action="store_true",
        help="Admit a story whose transcription has lost its breathings. Off by default, "
        "because that is a modernised text.",
    )
    args = parser.parse_args()

    parts: list[str] = []
    report: list[str] = []
    failed = False

    for index, title in enumerate(STORIES):
        if index:
            time.sleep(5)  # Wikimedia returns 429 to an unthrottled loop.
        try:
            raw = fetch_wikitext(title)
        except Exception as error:
            print(f"FAILED to fetch {title}: {error}")
            failed = True
            continue
        poly, tonos = accentuation(raw)
        if poly == 0 and not args.allow_monotonic:
            print(f"REFUSED {title}: no breathings, so this transcription is monotonic")
            failed = True
            continue
        body = clean(raw)
        parts.append(f"## {title}\n\n{body}")
        report.append(f"  {title}: {poly} breathings, {tonos} tonos, {len(body):,} chars")

    if failed:
        print("\nNothing written: fix the failures above first.")
        return 1

    frontmatter = "\n".join(
        [
            "---",
            "title: Διηγήματα",
            "title_translit: Diigimata",
            "title_en: Selected Stories",
            "author: Αλέξανδρος Παπαδιαμάντης",
            "author_translit: Alexandros Papadiamantis",
            "language: el",
            'year: "1887-1906"',
            "source: Wikisource (el)",
            'source_url: "https://el.wikisource.org/wiki/Συγγραφέας:Αλέξανδρος_Παπαδιαμάντης"',
            "license: Public domain in the United States",
            'year_note: "Six stories first published between 1887 and 1906 in Athenian '
            "periodicals and newspapers; Papadiamantis died in 1911. The el.wikisource "
            'transcriptions name no print edition."',
            'selection_note: "Six of the roughly ninety stories on el.wikisource, chosen for '
            "canon, register and length: the Skiathos festival pieces (Sto Christo sto Kastro, "
            "Lampriatikos Psaltis), the lyric meditation (Remvasmos tou Dekapentavgoustou), the "
            "poverty story (I Stachomazochtra), an Athens setting (O xepesmenos dervisis) and one "
            "short widely-anthologised piece (To christopsomo). Two stories a reader may expect "
            "are absent for stated reasons: To Moirologi tis Fokias is not on el.wikisource at "
            "all, and Oneiro sto kyma is there only in a monotonic transcription, which this "
            'corpus does not admit."',
            'source_note: "Polytonic throughout, which is the point: most Greek digitisation of '
            "pre-1929 work converts to the monotonic system introduced in 1982, rewriting the "
            "accentuation. The converter refuses any story whose transcription carries no "
            "breathings. Wikisource apparatus is removed: navigation and header templates, "
            "category links, wiktionary glosses (the display word is kept), and two pieces of "
            "malformed link markup in the source, one empty-target link and one unclosed link. "
            'No word of the text is changed."',
            "---",
        ]
    )
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(frontmatter + "\n" + "\n\n".join(parts) + "\n", encoding="utf-8")

    print(f"wrote {out} ({out.stat().st_size:,} bytes)")
    for line in report:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
