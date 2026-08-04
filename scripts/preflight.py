#!/usr/bin/env python3
"""
preflight.py: run every check a contribution needs, and say plainly which
results block a pull request and which are only worth a look.

The corpus has several gates (markdown linting, verse hard breaks, manifest
freshness, documented counts) and a contributor should not
have to know which is which. This script runs them in one go against the
file or files you added or changed, then sorts the results into three
groups: what you must fix, what needs a human judgment and an explanation in
the PR, and what is already handled for you.

Usage:
  scripts/preflight.py books/pl/Adam\\ Mickiewicz/Pan\\ Tadeusz.md
  scripts/preflight.py books/pl/                 # everything under a locale
  scripts/preflight.py                           # the whole corpus
  scripts/preflight.py --upstream <path>         # also check the live source

The upstream fidelity audit is off by default because it fetches the source
page over the network, which is slow and needs you to be online. If the book
came from Wikisource, this script tells you to run it.

Exits 0 when nothing blocks a pull request, 1 otherwise. Advisory findings
do not affect the exit code.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def run(script: str, *args: str) -> tuple[int, str]:
    """Run a sibling script and return its exit code and combined output."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def indent(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(f"    {line}" for line in lines)


def is_wikisource(paths: list[str]) -> bool:
    """True when any target book cites a Wikisource source_url."""
    for raw in paths:
        path = Path(raw)
        candidates = [path] if path.is_file() else sorted(path.rglob("*.md"))
        for book in candidates:
            try:
                head = book.read_text(encoding="utf-8")[:4000]
            except OSError:
                continue
            if "wikisource" in head.lower():
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run every contribution check and report what blocks a PR."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Book files or directories. Defaults to the whole corpus.",
    )
    parser.add_argument(
        "--upstream",
        action="store_true",
        help="Also run the upstream fidelity audit (needs network access).",
    )
    args = parser.parse_args()

    books_root = REPO_ROOT / "books"
    targets = args.paths or [str(books_root)]

    # Every check downstream assumes a path inside books/; lint-corpus.py
    # raises rather than reporting when handed anything else.
    for path in targets:
        resolved = Path(path).resolve()
        if not resolved.exists():
            print(f"preflight: no such file or directory: {path}")
            return 1
        if not resolved.is_relative_to(books_root):
            print(f"preflight: {path} is outside books/")
            print("Books live at books/<locale>/<Author>/<Title>.md; see CONTRIBUTING.")
            return 1

    blocking: list[tuple[str, str]] = []
    advisory: list[tuple[str, str]] = []
    handled: list[str] = []

    print(f"Preflight: {', '.join(targets)}\n")

    # 1. Markdown and frontmatter validity. This one really does block.
    code, out = run("lint-corpus.py", *targets)
    if code:
        blocking.append(
            (
                "The linter found errors in your file",
                out + "\n\nRun scripts/lint-corpus.py --fix to fix the safe ones.",
            )
        )
    else:
        handled.append("The linter is clean.")

    # 2. Verse hard breaks. Every flag needs a human decision, so it never blocks.
    code, out = run("check-verse-breaks.py", *targets)
    if code:
        advisory.append(
            (
                "Possible soft-wrapped verse",
                out
                + "\n\nThese are leads rather than verdicts. Verse lines inside a "
                + "stanza need two trailing spaces; hard-wrapped prose is correct "
                + "as it is. If you leave a flag in place, say why in the PR.",
            )
        )
    else:
        handled.append("No soft-wrapped verse detected.")

    # 3. Machine-readable index. Blocking, but the fix is one command.
    code, out = run("build-manifest.py", "--check")
    if code:
        blocking.append(
            (
                "manifest.json is out of date",
                "Run scripts/build-manifest.py and commit the result.",
            )
        )
    else:
        handled.append("manifest.json is up to date.")

    # 4. Counts stated in prose across README, CORPUS and CITATION.
    code, out = run("check-doc-counts.py")
    if code:
        blocking.append(
            (
                "The documented counts no longer match the corpus",
                out
                + "\n\nThis usually means a book or locale landed without every "
                + "document being updated. If the remaining edits defeat you, do "
                + "what you can and say so in the PR.",
            )
        )
    else:
        handled.append("The counts in README, CORPUS.md and CITATION.cff match.")

    # 6. Upstream fidelity. Opt-in because it goes over the network.
    if args.upstream:
        code, out = run("verify-upstream.py", *targets)
        if code:
            advisory.append(
                (
                    "The upstream check flagged missing marks",
                    out
                    + "\n\nMarks inside editorial apparatus you correctly stripped "
                    + "will show up here. Explain any flag in the PR.",
                )
            )
        else:
            handled.append("The vendored text matches its upstream source.")
    elif is_wikisource(targets):
        advisory.append(
            (
                "This book came from Wikisource",
                "Re-run with --upstream to compare it against the live source "
                "page. That check catches conversion steps that silently drop "
                "punctuation or whole verse sections. It needs network access.",
            )
        )

    if blocking:
        print("Must fix before you open a pull request")
        for title, detail in blocking:
            print(f"\n  {title}")
            print(indent(detail))
        print()

    if advisory:
        print("Worth a look, and explain in the PR if you leave it as it is")
        for title, detail in advisory:
            print(f"\n  {title}")
            print(indent(detail))
        print()

    if handled:
        print("Nothing for you to do here")
        for line in handled:
            print(f"  {line}")
        print()

    if blocking:
        count = len(blocking)
        noun = "thing" if count == 1 else "things"
        print(f"preflight: {count} {noun} to fix before your PR.")
        return 1
    print("preflight: nothing blocking. Open the PR when you're ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
