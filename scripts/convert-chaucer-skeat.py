#!/usr/bin/env python3
"""
convert-chaucer-skeat.py: build the Middle English enm corpus book from the
Skeat 1900 reading text on English Wikisource (Canterbury Tales (ed. Skeat)).

That transcription is the clean Oxford Chaucer verse: verbatim Middle English
orthography inside a single <poem> block, with the print edition's critical
apparatus kept on a separate notes page (so it never enters the body). Marginal
line references travel as {{Line|N}} templates and small-caps names as {{sc|X}};
neither is present in the rendered reading text. The generic Wikisource
converter drops short {{sc|X}} words (they don't look like prose), so this
dedicated pass exists to preserve them.

Fetches the Prologue and Knight pages, extracts the verse from each <poem>
(everything after </poem> -- the Variae Lectiones apparatus -- is discarded),
strips the line-reference templates, unwraps small-caps and centring templates,
keeps the authentic rubrics (Here biginneth ...; Explicit ... Sequitur ...;
Here is ended ...), promotes the two sections and the Knight's four part-rubrics
to headings, and writes one vendor-ready markdown file with frontmatter.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"
BASE = "https://en.wikisource.org/w/api.php"


def fetch(page: str) -> str:
    q = urllib.parse.urlencode(
        {"action": "parse", "page": page, "prop": "wikitext", "format": "json", "formatversion": "2"}
    )
    req = urllib.request.Request(f"{BASE}?{q}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["parse"]["wikitext"]


def poem_body(wikitext: str) -> str:
    # Extract each <poem> block separately and join. A tale page can carry more
    # than one (e.g. the Nun's Priest tale plus its short epilogue), with the
    # Variae Lectiones apparatus sitting BETWEEN them; matching per block, not
    # greedily from the first <poem> to the last </poem>, keeps that apparatus out.
    blocks = re.findall(r"<poem>(.*?)</poem>", wikitext, re.DOTALL)
    if not blocks:
        raise ValueError("no <poem> block found")
    return "\n\n".join(blocks)


def clean(text: str) -> str:
    # drop marginal line-reference templates in every form: {{Line|860}},
    # {{Line|(10)}}, {{Line|'''Knight'''.}}
    text = re.sub(r"\{\{Line\|[^{}]*\}\}", "", text)
    # unwrap presentational templates, keeping their text
    text = re.sub(r"\{\{larger\|([^{}]*)\}\}", r"\1", text)
    text = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", text)
    # {{smaller block|...}} / {{smaller|...}} wrap real text (e.g. the Nun's
    # Priest epilogue set in a smaller font); keep their content
    text = re.sub(r"\{\{smaller block\|(.*?)\}\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\{\{smaller\|(.*?)\}\}", r"\1", text, flags=re.DOTALL)
    # {{c|...}} centres a line; may nest, so unwrap iteratively
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{c\|([^{}]*)\}\}", r"\1", text)
    # any remaining simple templates ({{rule}}, {{gap}} ...) -> drop
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # refs, if any leaked inside the poem
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    # wiki emphasis: bold before italic
    text = re.sub(r"'''([^']+?)'''", r"**\1**", text)
    text = re.sub(r"''([^']+?)''", r"*\1*", text)
    # internal links [[a|b]] -> b, [[a]] -> a
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("&nbsp;", " ")
    # collapse runs of spaces the caesura templates left behind
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")


PART_RUBRIC = re.compile(r"^\*{0,2}(Explicit .*?Sequitur .*?)\*{0,2}\s*$")


def promote_part_rubrics(body: str) -> str:
    out = []
    for line in body.split("\n"):
        m = PART_RUBRIC.match(line.strip())
        if m:
            out.append("## " + m.group(1).strip())
        else:
            out.append(line)
    return "\n".join(out)


# (wikisource page under "Canterbury Tales (ed. Skeat)/", H1 heading for the file)
SECTIONS = [
    ("Prologue", "The Prologue"),
    ("Miller", "The Milleres Tale"),
    ("Nuns Priest", "The Nonne Preestes Tale"),
]


def main() -> int:
    import sys

    blocks = []
    for page, title in SECTIONS:
        text = promote_part_rubrics(clean(poem_body(fetch(f"Canterbury Tales (ed. Skeat)/{page}"))))
        blocks.append(f"# {title}\n\n{text}")
        print(f"  {page}: {len(text.splitlines())} body lines", file=sys.stderr)

    fm = (
        "---\n"
        "title: The Canterbury Tales\n"
        "author: Geoffrey Chaucer\n"
        "language: enm\n"
        "year: 1900\n"
        "source: Wikisource (en)\n"
        'source_url: "https://en.wikisource.org/wiki/Canterbury_Tales_(ed._Skeat)"\n'
        "license: Public domain in the United States\n"
        'year_note: "Composed in the late fourteenth century. The text here follows Walter W. Skeat\'s reading edition, The Complete Works of Geoffrey Chaucer, Oxford 1900, as transcribed on English Wikisource."\n'
        'selection_note: "Excerpt: the General Prologue complete, then two complete tales with their linking prologues, the Miller\'s Tale and the Nun\'s Priest\'s Tale. Three registers of Middle English in one file: the portrait catalogue of the Prologue, a bawdy fabliau, and a mock-heroic beast fable. The Miller\'s Tale is frankly bawdy; that is canonical Chaucer and it is kept unabridged. The remaining tales are omitted."\n'
        'source_note: "Verbatim Middle English orthography of Skeat\'s text is preserved (thorn is not used by this edition; forms such as shoures sote, y-ronne, the ye spelling and final-e endings stand as printed). The marginal line-reference numbers are removed and small-caps names are unwrapped to plain text; the separate Variae Lectiones critical apparatus is not included. No spelling is modernized."\n'
        "---\n"
    )
    body = "\n\n".join(blocks) + "\n"
    out = Path("books/enm/Geoffrey Chaucer/The Canterbury Tales.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + body, encoding="utf-8")
    nhead = sum(1 for line in body.split("\n") if line.startswith("#"))
    print(f"wrote {out} ({len(fm+body):,} bytes, {len(body.splitlines())} body lines, {nhead} headings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
