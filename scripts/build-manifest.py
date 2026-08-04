#!/usr/bin/env python3
"""
build-manifest.py: generate manifest.json, the machine-readable corpus index.

CORPUS.md is the human inventory; manifest.json is the same information
for programs, so an application or pipeline can enumerate the corpus
without walking the tree and parsing 128 frontmatter blocks itself.
One record per book: locale, path, frontmatter fields, size, and a
rough word count.

Standard library only, deterministic output (sorted by path, stable
key order, LF endings), so regenerating on any machine produces the
same bytes for the same corpus.

Usage:
  scripts/build-manifest.py            # (re)write manifest.json
  scripts/build-manifest.py --check    # exit 1 if manifest.json is stale
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOKS_ROOT = REPO_ROOT / "books"
MANIFEST = REPO_ROOT / "manifest.json"

# Flat scalar frontmatter fields, in output order. Unknown fields are
# carried through after these, sorted, so new conventions are not lost.
KNOWN_FIELDS = [
    "title",
    "title_translit",
    "title_en",
    "author",
    "author_translit",
    "language",
    "year",
    "year_note",
    "translator",
    "source",
    "source_url",
    "source_note",
    "selection_note",
    "edition_note",
    "language_note",
    "license",
    "writing-mode",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    fields: dict[str, str] = {}
    for line in text[4:end].split("\n"):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        fields[key] = value
    return fields


def year_numeric(raw: str) -> int | None:
    """Best-effort numeric year for sorting; BCE becomes negative."""
    m = re.search(r"(\d{1,4})", raw)
    if not m:
        return None
    value = int(m.group(1))
    if "BCE" in raw or raw.lstrip().startswith("-"):
        return -value
    return value


def build() -> dict:
    books = []
    for path in sorted(BOOKS_ROOT.rglob("*.md"), key=lambda p: str(p.relative_to(REPO_ROOT))):
        rel = path.relative_to(REPO_ROOT)
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        body_start = text.find("\n---\n", 4)
        body = text[body_start + 5 :] if body_start >= 0 else text
        record: dict = {
            "path": str(rel),
            "locale": rel.parts[1],
        }
        for key in KNOWN_FIELDS:
            if key in fm:
                record[key] = fm[key]
        for key in sorted(fm):
            if key not in record:
                record[key] = fm[key]
        yn = year_numeric(fm.get("year", ""))
        if yn is not None:
            record["yearNumeric"] = yn
        record["sizeBytes"] = path.stat().st_size
        record["wordCount"] = len(body.split())
        books.append(record)

    locales = sorted({b["locale"] for b in books})
    return {
        "$schema": "./manifest.schema.json",
        "corpus": "multilingual-classics-markdown",
        "bookCount": len(books),
        "localeCount": len(locales),
        "locales": locales,
        "books": books,
    }


def render(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    manifest = render(build())
    if "--check" in sys.argv[1:]:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if current != manifest:
            print("manifest.json is stale; regenerate with scripts/build-manifest.py")
            return 1
        print(f"manifest.json is fresh ({json.loads(manifest)['bookCount']} books)")
        return 0
    MANIFEST.write_text(manifest, encoding="utf-8")
    data = json.loads(manifest)
    print(f"wrote manifest.json: {data['bookCount']} books, {data['localeCount']} locales")
    return 0


if __name__ == "__main__":
    sys.exit(main())
