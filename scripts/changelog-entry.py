#!/usr/bin/env python3
"""
changelog-entry.py: draft a CHANGELOG section by comparing the corpus at two
git refs.

The corpus changes in waves, and what a reader of the changelog wants to know
is which locales and books arrived, which were replaced, and how much of the
existing text was revised. All of that is derivable from the tree, so it
should not be assembled by hand and it should not be trusted to memory.

This script reads books/ at both refs, matches paths across a rename-aware
diff, and prints a markdown section ready to paste at the top of CHANGELOG.md.
Titles and authors come from manifest.json at the newer ref where it exists,
so the entry names the work rather than the file path.

The prose is still yours. This produces the inventory, not the story.

Usage:
  scripts/changelog-entry.py wave-2026-07-25 wave-2026-07-26
  scripts/changelog-entry.py wave-2026-07-26          # ...to the working tree
  scripts/changelog-entry.py --heading "v1.2" <from> [<to>]

Exits 0 on success, 1 if a ref cannot be read.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    # core.quotePath=false is not optional here: git escapes non-ASCII paths by
    # default, and most of this corpus has non-Latin filenames. Quoted paths do
    # not end in ".md" and were silently dropped from every count.
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "-c", "core.quotePath=false", *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def books_at(ref: str | None) -> set[str]:
    """Paths of every book at a ref, or in the working tree when ref is None."""
    if ref is None:
        root = REPO_ROOT / "books"
        return {
            str(p.relative_to(REPO_ROOT)) for p in root.rglob("*.md") if p.is_file()
        }
    out = git("ls-tree", "-r", "--name-only", ref, "books/")
    return {line for line in out.splitlines() if line.endswith(".md")}


def manifest_at(ref: str | None) -> dict[str, dict]:
    """Book metadata keyed by path, empty when the manifest is unreadable."""
    try:
        raw = (
            (REPO_ROOT / "manifest.json").read_text(encoding="utf-8")
            if ref is None
            else git("show", f"{ref}:manifest.json")
        )
        data = json.loads(raw)
    except (RuntimeError, OSError, json.JSONDecodeError):
        return {}
    return {book["path"]: book for book in data.get("books", [])}


def locale_of(path: str) -> str:
    parts = path.split("/")
    return parts[1] if len(parts) > 2 else "?"


def describe(path: str, meta: dict[str, dict]) -> str:
    book = meta.get(path)
    if not book:
        return f"`{path}`"
    title = book.get("title", "").strip()
    author = book.get("author", "").strip()
    english = book.get("title_en", "").strip()
    label = f"{author}, *{title}*" if author else f"*{title}*"
    # Some titles already carry their English gloss inline; don't repeat it.
    if english and english not in title:
        return f"{label} ({english})"
    return label


def changed_books(from_ref: str, to_ref: str | None, shared: set[str]) -> list[str]:
    """Books present at both refs whose bytes differ."""
    target = [from_ref] if to_ref is None else [from_ref, to_ref]
    out = git("diff", "--name-only", *target, "--", "books/")
    return sorted(p for p in out.splitlines() if p in shared)


def renames(from_ref: str, to_ref: str | None) -> list[tuple[str, str]]:
    target = [from_ref] if to_ref is None else [from_ref, to_ref]
    out = git(
        "diff", "--find-renames", "--diff-filter=R", "--name-status", *target, "--", "books/"
    )
    pairs = []
    for line in out.splitlines():
        fields = line.split("\t")
        if len(fields) == 3:
            pairs.append((fields[1], fields[2]))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Draft a CHANGELOG section from the corpus diff between two refs."
    )
    parser.add_argument("from_ref", help="The earlier ref, usually the previous tag.")
    parser.add_argument(
        "to_ref",
        nargs="?",
        help="The later ref. Defaults to the working tree.",
    )
    parser.add_argument("--heading", help="Section heading. Defaults to the later ref.")
    args = parser.parse_args()

    try:
        before, after = books_at(args.from_ref), books_at(args.to_ref)
    except RuntimeError as error:
        print(f"changelog-entry: {error}")
        return 1

    moved = dict(renames(args.from_ref, args.to_ref))
    added = sorted(p for p in after - before if p not in moved.values())
    removed = sorted(p for p in before - after if p not in moved)
    shared = before & after
    edited = changed_books(args.from_ref, args.to_ref, shared)

    meta_after = manifest_at(args.to_ref)
    meta_before = manifest_at(args.from_ref)

    locales_before = {locale_of(p) for p in before}
    locales_after = {locale_of(p) for p in after}
    new_locales = sorted(locales_after - locales_before)
    lost_locales = sorted(locales_before - locales_after)

    heading = args.heading or args.to_ref or "Unreleased"
    print(f"## {heading}\n")
    print(
        f"{len(before)} books in {len(locales_before)} locales, "
        f"to {len(after)} books in {len(locales_after)}.\n"
    )

    if new_locales:
        print(f"### New locales ({len(new_locales)})\n")
        for locale in new_locales:
            entries = [describe(p, meta_after) for p in sorted(added) if locale_of(p) == locale]
            print(f"- **{locale}**: {'; '.join(entries)}")
        print()

    existing_additions = [p for p in added if locale_of(p) not in new_locales]
    if existing_additions:
        print(f"### New books in existing locales ({len(existing_additions)})\n")
        for path in existing_additions:
            print(f"- **{locale_of(path)}**: {describe(path, meta_after)}")
        print()

    if moved:
        print(f"### Moved or re-attributed ({len(moved)})\n")
        for old, new in sorted(moved.items()):
            print(f"- `{old}` is now `{new}`")
        print()

    if removed:
        print(f"### Removed ({len(removed)})\n")
        for path in removed:
            print(f"- **{locale_of(path)}**: {describe(path, meta_before)}")
        print()

    if lost_locales:
        print(f"Locales no longer present: {', '.join(lost_locales)}\n")

    if edited:
        by_locale: dict[str, int] = {}
        for path in edited:
            by_locale[locale_of(path)] = by_locale.get(locale_of(path), 0) + 1
        summary = ", ".join(f"{loc} ({n})" for loc, n in sorted(by_locale.items()))
        noun = "book" if len(edited) == 1 else "books"
        print(f"### Revised text ({len(edited)} {noun})\n")
        print(f"{summary}\n")

    if not (added or removed or moved or edited):
        print("No change to the corpus itself in this range.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
