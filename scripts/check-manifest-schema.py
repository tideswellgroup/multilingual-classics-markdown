#!/usr/bin/env python3
"""
check-manifest-schema.py: validate manifest.json against manifest.schema.json.

manifest.json declares a $schema reference. This gate makes the reference
mean something: it resolves the schema, validates the document, and reports
every violation rather than only the first.

The schema is deliberately strict. additionalProperties is false on the book
object, so a frontmatter key that appears in the corpus without being added
to the schema and documented in FRONTMATTER.md fails here. That is the point:
the manifest, the schema and the frontmatter reference are meant to describe
the same thing, and this is what keeps them honest.

Usage:
  python3 scripts/check-manifest-schema.py            # verify, exit 1 on violation
  python3 scripts/check-manifest-schema.py --quiet    # print nothing on success

Requires: jsonschema (pip install jsonschema)

Exit codes: 0 clean, 1 validation failed, 2 IO/parse error or missing dependency.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "manifest.json"
SCHEMA = REPO_ROOT / "manifest.schema.json"


def fail(message: str, code: int = 2) -> int:
    print(f"check-manifest-schema: {message}", file=sys.stderr)
    return code


def describe(error) -> str:
    """Render one jsonschema ValidationError as a single readable line."""
    location = "/".join(str(part) for part in error.absolute_path) or "(root)"
    # For a book entry, the path alone is more useful than the array index.
    return f"  {location}: {error.message}"


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv

    try:
        import jsonschema
    except ImportError:
        return fail(
            "the jsonschema package is required (pip install jsonschema)"
        )

    for path in (MANIFEST, SCHEMA):
        if not path.exists():
            return fail(f"{path.relative_to(REPO_ROOT)} not found")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"could not parse JSON: {exc}")

    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        return fail(f"manifest.schema.json is not a valid schema: {exc.message}")

    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))

    if errors:
        print(
            f"check-manifest-schema: {len(errors)} violation(s) in manifest.json",
            file=sys.stderr,
        )
        for error in errors:
            print(describe(error), file=sys.stderr)
        return 1

    if not quiet:
        book_count = len(manifest.get("books", []))
        print(f"check-manifest-schema: manifest.json valid ({book_count} books)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
