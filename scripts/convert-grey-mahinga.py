#!/usr/bin/env python3
"""
convert-grey-mahinga.py: extract a curated selection of the major Maori prose
legends from Sir George Grey's "Ko nga mahinga a nga tupuna Maori" (London,
1854; the Maori-language original of what Grey later Englished as "Polynesian
Mythology"). Source is the Google/Internet Archive OCR of the 1854 first
edition (djvu.txt). Maori-only; there is no English apparatus in this edition.

This is a bespoke single-work extractor in the style of convert-mwana-kupona.py
and convert-iqbal-bang-e-dara.py: it fetches the IA djvu.txt, cuts the section
between two heading markers, drops page-number and signature debris, joins the
hard-wrapped OCR lines back into paragraphs, and re-marks the printed all-caps
legend headings as level-2 markdown headings.

The OCR is noisy (typical of a 19th-century scan: stray ^ for commas, l for i,
digits for letters). Following the corpus posture for OCR-class sources it is
passed through with light structural cleanup only; no Maori spelling or
orthography is modernised, and in particular no macrons are introduced (the
1854 edition marked none). Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _get(url: str, retries: int = 4) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    import time
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            last = exc
            time.sleep(3 * (attempt + 1))
    raise last if last else RuntimeError("request failed")


def load_text(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        return _get(source)
    return Path(source).read_text(encoding="utf-8", errors="replace")


def select(text: str, start_marker: str, stop_marker: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    start = None
    stop = len(lines)
    for i, ln in enumerate(lines):
        if start is None and ln.strip() == start_marker:
            start = i
        elif start is not None and ln.strip() == stop_marker:
            stop = i
            break
    if start is None:
        raise SystemExit(f"start marker not found: {start_marker!r}")
    return "\n".join(lines[start:stop])


PAGE_NUM = re.compile(r"^\s*\d{1,4}\s*$")
SIGNATURE = re.compile(r"^\s*[A-Z]\s?\d{1,3}\s*$")  # printer's gathering marks like "A 2"


def is_heading(line: str) -> bool:
    """A printed legend heading is a short line whose letters are (almost) all
    upper case. Body text is predominantly lower case, so this separates the
    two cleanly."""
    s = line.strip().rstrip(".")
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 3 or len(s) > 55:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) >= 0.8


def to_markdown(block: str) -> str:
    out: list[tuple[str, str]] = []
    para: list[str] = []

    def flush_para() -> None:
        if not para:
            return
        text = ""
        for piece in para:
            if not text:
                text = piece
            elif text.endswith("-"):
                text += piece  # keep hyphenated compound joined across the line break
            else:
                text += " " + piece
        out.append(("p", text.strip()))
        para.clear()

    for raw in block.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_para()
            continue
        if PAGE_NUM.match(stripped) or SIGNATURE.match(stripped):
            continue
        if is_heading(stripped):
            flush_para()
            # Strip page-number bleed (a leading "10 ...") and line-break hyphens
            # off the heading line; leave the rest of the OCR verbatim.
            head = re.sub(r"^\d{1,4}\s+", "", stripped).strip().rstrip(".-").strip()
            out.append(("h", head))
            continue
        para.append(stripped)
    flush_para()

    # Rejoin paragraphs that the OCR split at a page break: if a paragraph does
    # not close on sentence punctuation and the next one opens lower case, they
    # are one paragraph interrupted by a dropped page number.
    merged: list[tuple[str, str]] = []
    for kind, txt in out:
        if (kind == "p" and merged and merged[-1][0] == "p"
                and not re.search(r"[.!?\"'”’]\s*$", merged[-1][1])
                and txt[:1].islower()):
            merged[-1] = ("p", merged[-1][1].rstrip() + " " + txt.lstrip())
        else:
            merged.append((kind, txt))

    # Drop a heading with no body under it (the selection can end on a printed
    # heading whose narrative falls after the stop marker).
    while merged and merged[-1][0] == "h":
        merged.pop()

    rendered: list[str] = []
    for kind, txt in merged:
        if not txt:
            continue
        rendered.append(f"## {txt}" if kind == "h" else txt)
    body = "\n\n".join(rendered)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build(args) -> None:
    raw = load_text(args.source)
    block = select(raw, args.start_marker, args.stop_marker)
    body = to_markdown(block)
    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "Internet Archive (Google-digitised 1854 first edition)",
        "source_url": args.detail_url,
        "license": "Public domain in the United States",
    }
    if args.year_note:
        meta["year_note"] = args.year_note
    if args.selection_note:
        meta["selection_note"] = args.selection_note
    if args.source_note:
        meta["source_note"] = args.source_note
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    headings = body.count("\n## ") + (1 if body.startswith("## ") else 0)
    print(f"wrote {dest} ({len(out):,} bytes, {headings} headings, {len(body.splitlines()):,} body lines)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, help="IA djvu.txt URL or local path")
    p.add_argument("--detail-url", required=True, help="IA /details/ page URL for citation")
    p.add_argument("--start-marker", required=True, help="exact line that opens the selection")
    p.add_argument("--stop-marker", required=True, help="exact line that ends the selection (excluded)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True)
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--year-note", default="")
    p.add_argument("--selection-note", default="")
    p.add_argument("--source-note", default="")
    args = p.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
