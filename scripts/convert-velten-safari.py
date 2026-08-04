#!/usr/bin/env python3
"""
convert-velten-safari.py: convert the OCR plain text of Carl Velten's
"Safari za Wasuaheli" (1901), a collection of first-person travel narratives
told by Swahili informants on the East African coast, to vendor-ready
markdown for the multilingual-classics-markdown corpus.

Source: Internet Archive djvu.txt OCR of the Google Books scan. The OCR is
noisy (German Fraktur preface, scanner artefacts, page-break debris).
Strategy: skip the Google boilerplate and German preface; keep the Swahili
narrative body from the first "Safari yangu" heading to the German index
("Inhaltsverzeichniss"). Promote "Safari yangu ..." headings to H1.
Leave embedded German page-number debris and footnote letters in place
(removing them risks eating Swahili text given the OCR quality).
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path


SAFARI_HEADING_RX = re.compile(r"^(Safari\s+yang[uan]\s+ya\s+.+?)\s*$", re.MULTILINE)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "multilingual-classics-markdown/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8")


def slice_body(text: str) -> str:
    # Locate first "Safari yangu" heading line; that begins the Swahili body.
    m = SAFARI_HEADING_RX.search(text)
    if not m:
        raise ValueError("could not locate first 'Safari yangu' heading")
    body = text[m.start():]
    # Stop before the German index/back matter.
    for marker in ("Orda ya khabari", "Inhaltsverzeichniss", "Berichtigungen", "Druckfehler"):
        idx = body.find(marker)
        if idx != -1:
            body = body[:idx]
            break
    return body


def promote_headings(body: str) -> str:
    return SAFARI_HEADING_RX.sub(lambda m: f"# {m.group(1).strip()}", body)


def normalise_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of >2 blank lines to exactly one blank.
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing spaces on each line.
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip() + "\n"


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--url",
        default="https://archive.org/download/safarizawasuahe00veltgoog/safarizawasuahe00veltgoog_djvu.txt",
    )
    p.add_argument("--output", required=True)
    args = p.parse_args()

    raw = fetch_text(args.url)
    body = slice_body(raw)
    body = promote_headings(body)
    body = normalise_whitespace(body)

    meta = {
        "title": "Safari za Wasuaheli",
        "author": "Carl Velten (editor); Sleman bin Mwenyi Tshande, Selim bin Abakari, Mtoro bin Mwenyi Bakari, Abdallah bin Rashid (narrators)",
        "language": "sw",
        "year": 1901,
        "source": "Internet Archive (Google Books scan)",
        "source_url": "https://archive.org/details/safarizawasuahe00veltgoog",
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + body
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {len(body.splitlines()):,} body lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
