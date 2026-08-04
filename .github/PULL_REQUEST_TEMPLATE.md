<!-- Thanks for contributing. The full workflow is in CONTRIBUTING.md; this checklist is the short version. -->

## What does this PR add or change?

<!-- Book title, author, locale; or the fix you're making. -->

## Why this book? (new books only)

<!-- One or two sentences: canon status, what it adds to the locale (genre/period/size variety). -->

## Source

- Upstream archive and URL:
- Was the text clean, or did it need OCR/conversion repair?

## Checklist

- [ ] Pre-1929 publication (or the documented manuscript exception, stated in `source_note`)
- [ ] `python3 scripts/lint-corpus.py books/<file>.md` returns zero errors
- [ ] Verse/drama/line-structured content uses two-space hard breaks (`scripts/check-verse-breaks.py` run; benign warnings explained below)
- [ ] Wikisource-sourced: `scripts/verify-upstream.py` run; flags explained below
- [ ] `python3 scripts/build-manifest.py` re-run and `manifest.json` committed
- [ ] CORPUS.md row added (and README coverage matrix, if this is a new locale)
- [ ] Frontmatter complete per FRONTMATTER.md (`year_note` / `source_note` / `selection_note` where applicable)

## Caveats

<!-- OCR noise, substitutions from a planned pick, religious adjacency, benign linter warnings, anything reviewers should know. -->
