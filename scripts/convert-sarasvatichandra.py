#!/usr/bin/env python3
"""
convert-sarasvatichandra.py: build the gu book Sarasvatichandra, Part 1
(Govardhanram Tripathi) from its gu.wikisource transcription of the 1922
eighth edition (Index `Saraswati Chandra Part 1.pdf`).

The book lives in sub-pages of `સરસ્વતીચંદ્ર ભાગ ૧`, each a ProofreadPage
transclusion. Rendered HTML is taken through the walker in
convert-bn-proofread.py (shared strip pipeline, cache, polite fetch), and
the book-specific work is:

1. Units. The English PREFACE, the first-edition preface and the
   third-edition note ship ahead of the 21 chapters. The title page
   (પ્રવેશ) is not shipped, and neither are two front pages that are
   religious rather than literary: Panchadashi verses on prarabdha, quoting
   the Gita (पञ्चदशीના શ્લોક), and the benedictory verse
   મંગલપુષ્પાંજલિ.
2. Footnotes. Each printed page's notes render as a reference list in the
   middle of the text. They become Markdown footnotes, collected at the end
   of their chapter. The printed note sign the transcription keeps beside
   the link (`*`, `૧`) is dropped from the running text, since the footnote
   marker replaces it; the note itself keeps its printed numbering.
3. Headings. Chapter heads are printed on two bold lines (number, then
   title), and chapter 1 repeats the book title above them. The heading
   carries both lines once, as `પ્રકરણ N. title`. The number is generated
   from the chapter's position, because the transcription's own numerals
   carry the slips described below (`પ્રક૨ણ ૩`, `પ્રકરણ ૧પ`), and each
   generated number is checked against the printed one.
4. Two transcription slips are repaired as classes, and counted:
   - an independent vowel followed by a vowel sign, typed for the single
     vowel the pair resembles: `અ` + `ા` for `આ` (U+0A85 U+0ABE for
     U+0A86), and likewise `એા` for `ઓ`, `ઐા` and `ઐૌ` for `ઔ`, and a
     doubled `આા`. They look alike in print, but the split forms defeat
     search and collation.
   - the digit `૨` for the letter `ર`, which it resembles, wherever it
     touches a Gujarati letter or sign and no other digit (`કા૨ણ`, `૨હી`,
     `૨ત્ન`). The book has no ordinals of the `૨જો` kind; every
     word-initial case was read and is the letter. On the same evidence
     `૫` is repaired to `પ` (`૫ણ`), `૯` to the half form `લ્` it is always
     standing for (`ચા૯યું`, `ક૯પના`), and `૦` to `o` inside English words
     (`n૦vel`); `૦` after a Gujarati word is the abbreviation sign and
     stays.
5. Drop caps, rendered as a bold first letter or syllable opening a
   paragraph (`**ન**વીનચંદ્ર`, `**મ્હો**ટાં`), are set as plain text.
6. The chapter 21 sub-page repeats the last paragraphs of chapter 20 above
   its head; they are dropped after checking that chapter 20 carries them.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("walker", SCRIPT_DIR / "convert-bn-proofread.py")
walker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(walker)

LANG = "gu"
TOP = "સરસ્વતીચંદ્ર ભાગ ૧"
TITLE = "સરસ્વતીચંદ્ર"
FRONT = [
    "PREFACE",
    "પ્રથમ આવૃત્તિની પ્રસ્તાવના.",
    "ત્રીજી આવૃત્તિ સંબંધે પ્રાસંગિક સૂચના.",
]
CHAPTERS = [
    "સુવર્ણપુરનો અતિથિ", "બુદ્ધિધનનું કુટુંબ", "બુદ્ધિધન", "બુદ્ધિધન (અનુસંધાન)",
    "બુદ્ધિધન (અનુસંધાન સંપૂર્તિ)", "રાજેશ્વરમાં રાજખટપટ", "વાડામાં લીલા", "અમાત્યને ઘેર",
    "ઉન્મત્તપણાનું પરિણામ", "ખટપટનાં શસ્ત્ર અને કારભારીયોની યુદ્ધકળા", "દરબારમાં જવાની તૈયારીયો",
    "રાજા, રાજદરબાર અને રાજકારભાર", "રસ્તામાં", "સૌભાગ્યનો સંપૂર્ણચંદ્ર", "સરસ્વતીચંદ્ર",
    "બુદ્ધિધન અને સૌભાગ્યદેવી", "પ્રમાદધન અને કુમુદસુંદરી", "કારભારી અને કારભાર : દિગ્દર્શન",
    "રાત્રિસંસાર : જવેનિકાનું છેદન અને વિશુદ્ધિનું શોધન", "રજા લીધી", "ચાલ્યો",
]
GU_DIGITS = "૦૧૨૩૪૫૬૭૮૯"
GU_LETTER_OR_SIGN = r"[\u0A81-\u0A83\u0A85-\u0AB9\u0ABC-\u0ACD]"
GU_VOWEL_SIGN = r"[\u0ABE-\u0ACD]"


def gu_num(n: int) -> str:
    return "".join(GU_DIGITS[int(d)] for d in str(n))


# A footnote link. The note id is taken from the link target, not from the
# link's own id, because a named note cited twice has one target and several
# link ids. The link body may not run past a </sup>: an unbounded match here
# once backtracked across a whole poem and swallowed it.
REF = re.compile(
    r'<sup id="cite&#95;ref-[^"]+" class="reference"><a href="#cite_note-([^"]+)">'
    r'(?:(?!</sup>).)*?</a></sup>',
    re.DOTALL,
)


def lift_footnotes(html: str, unit: int) -> tuple[str, list[tuple[str, str]]]:
    """Replace reference links with [^key] markers and pull the reference
    lists out of the flow. Returns the HTML and (key, note-html) pairs."""
    def key(ref_id: str) -> str:
        return f"{unit}-{ref_id}"

    # A printed note sign wrapped round the link: <sup>*<sup ref/></sup>.
    html = re.sub(
        r"<sup>[^<]{0,4}(" + REF.pattern + r")</sup>",
        lambda m: f"[^{key(m.group(2))}]", html, flags=re.DOTALL,
    )
    # A printed note sign typed as text just before the link (સ્વામિની.. *<sup>).
    html = re.sub(r"\*\s*(?=" + REF.pattern + ")", "", html, flags=re.DOTALL)
    html = REF.sub(lambda m: f"[^{key(m.group(1))}]", html)

    notes: list[tuple[str, str]] = []
    for li in re.finditer(r'<li id="cite&#95;note-([^"]+)">(.*?)</li>', html, re.DOTALL):
        if any(k == key(li.group(1)) for k, _ in notes):
            continue
        text = re.search(r'<span class="reference-text">(.*)</span>', li.group(2), re.DOTALL)
        notes.append((key(li.group(1)), text.group(1) if text else ""))
    # One list at a time: a page without notes renders an empty reflist div,
    # and a lazy match from it ran on to the next list's </ol>, deleting the
    # text between them.
    one_list = r'<ol class="references">(?:(?!</ol>).)*</ol>'
    html = re.sub(
        r'(<hr\s*/?>\s*)?<div class="reflist"[^>]*>\s*(?:' + one_list + r'\s*)?</div>',
        "", html, flags=re.DOTALL,
    )
    html = re.sub(r"(<hr\s*/?>\s*)?" + one_list, "", html, flags=re.DOTALL)
    if 'class="reflist"' in html or 'class="references"' in html:
        raise SystemExit(f"unit {unit}: a reference list survived")
    return html, notes


def note_text(fragment: str) -> str:
    md = walker.convert_body(f"<p>{fragment}</p>", br_hard=True)
    return re.sub(r"\s*\n\s*", " ", md).strip()


# Independent vowel + vowel sign, typed for the single vowel the pair looks
# like. Every such pair in the book is one of these.
SPLIT_VOWELS = {
    "\u0A85\u0ABE": "\u0A86",  # અ + ા  for  આ
    "\u0A86\u0ABE": "\u0A86",  # આ + ા  for  આ (the sign doubled)
    "\u0A8F\u0ABE": "\u0A93",  # એ + ા  for  ઓ
    "\u0A90\u0ABE": "\u0A94",  # ઐ + ા  for  ઔ
    "\u0A90\u0ACC": "\u0A94",  # ઐ + ૌ  for  ઔ
}
# The digit ૨ typed for the letter ર: a ૨, or a run of them (અર૨૨૨૨,
# પ૨૨ાજ્ય), touching a Gujarati letter or sign and no other digit. The book has no ordinals of the ૨જો kind, which this
# would otherwise catch; every word-initial case (૨હી, ૨ત્ન, ૨જા) is ર.
DIGIT_RA = re.compile(
    r"(?<=" + GU_LETTER_OR_SIGN + r")૨+(?![૦-૯])|(?<![૦-૯])૨+(?=" + GU_LETTER_OR_SIGN + r")"
)


def _touching(digit: str) -> re.Pattern:
    return re.compile(
        r"(?<=" + GU_LETTER_OR_SIGN + r")" + digit + r"(?![૦-૯])"
        r"|(?<![૦-૯])" + digit + r"(?=" + GU_LETTER_OR_SIGN + r")"
    )


# Two more digits typed for the letters they resemble, on the same evidence
# (every case touching a letter was listed and read): ૫ for પ (૫ણ, આ૫વી),
# and ૯ for the half form લ્, always before a consonant (ચા૯યું, ક૯પના).
DIGIT_PA = _touching("૫")
DIGIT_HALF_LA = _touching("૯")
# Gujarati ૦ for Latin o inside the English preface (n૦vel, ૦wn). Elsewhere
# ૦ after a word is the abbreviation sign (અલક૦, ઈ૦ સ૦) and stays.
ZERO_IN_LATIN = re.compile(r"(?<=[A-Za-z])૦|૦(?=[A-Za-z])")


def repair(text: str, counts: dict[str, int]) -> str:
    for split, whole in SPLIT_VOWELS.items():
        counts["split vowels"] += text.count(split)
        text = text.replace(split, whole)
    counts["૨ to ર"] += sum(len(m) for m in DIGIT_RA.findall(text))
    text = DIGIT_RA.sub(lambda m: "ર" * len(m.group(0)), text)
    counts["૫ to પ"] += len(DIGIT_PA.findall(text))
    text = DIGIT_PA.sub("પ", text)
    counts["૯ to લ્"] += len(DIGIT_HALF_LA.findall(text))
    text = DIGIT_HALF_LA.sub("લ્", text)
    counts["૦ to o"] += len(ZERO_IN_LATIN.findall(text))
    text = ZERO_IN_LATIN.sub("o", text)
    # A drop cap: a short bold cluster opening a paragraph (**મ્હો**ટાં, **આ** સમયે).
    drop = re.compile(r"(?m)^\*\*([\u0A81-\u0AFF]{1,4})\*\*(?=[\u0A81-\u0AFF ])")
    counts["drop caps"] += len(drop.findall(text))
    return drop.sub(r"\1", text)


def first_line_heading(body: str) -> tuple[str, str]:
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    head = lines.pop(0).strip().strip("*").strip().rstrip(" .")
    return head, "\n".join(lines).lstrip("\n")


NUM_LINE = re.compile(r"\*\*\s*પ્રક[ર૨]ણ\s+(\S+?)\.\*\*\*?(\[\^[^\]]+\])?")
TITLE_LINE = re.compile(r"(\[\^[^\]]+\])?\*?\*\*(.+?)\*\*(.*)")


def chapter_heading(body: str, n: int, label: str, previous: str) -> tuple[str, str]:
    """Take the two printed head lines (number, title) as the heading. Text
    standing above the number line is accepted only when the previous
    chapter already carries it: the ch. 21 sub-page's transclusion starts on
    a page it shares with ch. 20 and repeats that chapter's last paragraphs."""
    lines = body.split("\n")
    k = next((i for i, l in enumerate(lines) if NUM_LINE.fullmatch(l.strip())), None)
    if k is None:
        raise SystemExit(f"chapter {n}: no printed number line")
    above = [l.strip() for l in lines[:k] if l.strip()]
    if n == 1 and above == [f"**{TITLE}.**"]:
        above = []  # book title repeated above chapter 1
    for l in above:
        if l not in previous:
            raise SystemExit(f"chapter {n}: text above the head is not in chapter {n - 1}: {l[:60]!r}")
    num = NUM_LINE.fullmatch(lines[k].strip())
    if num.group(1).replace("પ", "૫") != gu_num(n):
        raise SystemExit(f"chapter {n}: printed number {num.group(1)!r} does not match")
    rest = lines[k + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    t = TITLE_LINE.fullmatch(rest.pop(0).strip()) if rest else None
    if not t:
        raise SystemExit(f"chapter {n}: no bold title line")
    title = (t.group(2).strip() + " " + t.group(3).strip()).strip().rstrip(" .,\u2013")
    # A note hung on the printed number or title moves to the end of the heading.
    note = (num.group(2) or "") + (t.group(1) or "")
    return f"પ્રકરણ {gu_num(n)}. {title}{note}", "\n".join(rest).lstrip("\n")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--frontmatter", required=True, help="file holding the YAML block, fences included: a .yml, or the existing book itself")
    p.add_argument("--output", required=True)
    p.add_argument("--cache", default=None, metavar="DIR")
    p.add_argument("--delay", type=float, default=1.5)
    args = p.parse_args()
    if args.cache:
        walker.CACHE_DIR = Path(args.cache)

    counts = {"split vowels": 0, "૨ to ર": 0, "૫ to પ": 0, "૯ to લ્": 0, "૦ to o": 0, "drop caps": 0}
    sections: list[str] = []
    previous = ""
    units = [(u, None) for u in FRONT] + [(u, i + 1) for i, u in enumerate(CHAPTERS)]
    for idx, (unit, chap) in enumerate(units):
        if idx and not walker.is_cached(LANG, f"{TOP}/{unit}"):
            time.sleep(args.delay)
        html = walker.fetch_rendered(LANG, f"{TOP}/{unit}")
        html, notes = lift_footnotes(html, idx + 1)
        body = walker.convert_body(html, br_hard=True)
        if chap:
            heading, body = chapter_heading(body, chap, unit, previous)
        else:
            heading, body = first_line_heading(body)
        previous = body
        heading, body = repair(heading, counts), repair(body, counts)
        out = f"## {heading}\n\n{body.strip()}\n"
        if notes:
            out += "\n" + "\n".join(f"[^{k}]: {repair(note_text(v), counts)}" for k, v in notes) + "\n"
        sections.append(out)

    body = f"# {TITLE}\n\n" + "\n".join(sections)
    # Verse quoted as consecutive centred bold lines (one <center> per line in
    # the source) would merge into one line; keep each on its own.
    body = re.sub(r'(?m)^("?\*\*[^\n]*\*\*)\n(?="?\*\*)', r"\1  \n", body)
    body = body.replace("\ufeff", "")
    # Three backticks are OCR specks at line ends ("best in the `"); two on
    # one line would open a Markdown code span.
    counts["stray backticks"] = body.count("`")
    body = re.sub(r"[ \t]*`", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    refs = set(re.findall(r"\[\^([^\]]+)\](?!:)", body))
    defs = set(re.findall(r"(?m)^\[\^([^\]]+)\]:", body))
    if refs != defs:
        raise SystemExit(f"footnote mismatch: unreferenced {sorted(defs - refs)}, undefined {sorted(refs - defs)}")
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)  # a .yml, or an existing book
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(fm + body, encoding="utf-8")
    print(f"wrote {dest}: {len(units)} units, {len(defs)} footnotes, repairs {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
