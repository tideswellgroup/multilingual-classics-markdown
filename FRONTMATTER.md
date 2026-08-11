# Frontmatter reference

Books in this corpus open with a YAML frontmatter block between `---` fences. This file documents what the fields mean, why they exist, and the rules for adding new ones. For iterating over frontmatter programmatically, see the Python recipe in the [README](README.md#iterate-over-the-entire-corpus); to obtain the corpus without any frontmatter, see [`scripts/strip-frontmatter.py`](scripts/strip-frontmatter.py) below.

## Why frontmatter

The frontmatter does three jobs, in priority order:

1. **Provenance**: every book carries its source URL, edition dates, and license posture, machine-readably. This is the backbone of the corpus's scholarly-use commitments (see README §Scholarly use and limitations).
2. **Curation transparency**: excerpts, substitutions, disclosed corrections, and orthography caveats live in the file they describe, and in CORPUS.md.
3. **Presentation hints**: a small, principled set of fields that record typographic conventions a renderer may honour.

## The provenance layer

| Key | Required | Type | Meaning |
|---|---|---|---|
| `title` | yes | string | The work's title, in its own language and orthography |
| `author` | yes | string | The author, in their own language where the source gives it. For collected oral literature this may carry combined attribution, e.g. principal author plus editor; see the mi books for the pattern |
| `language` | yes | string | BCP-47 tag, carrying region and script subtags where relevant (`es-MX`, `zh-Hans`, `pt-BR`) |
| `year` | yes | integer or quoted string | Publication year of the cited source edition. Non-integer forms (`"c. 500"`) are quoted strings |
| `source` | yes | string | The upstream repository name (see CORPUS.md §Provenance) |
| `source_url` | yes | quoted string | Direct URL to the source |
| `license` | yes | string | `Public domain in the United States` for every book here. For the rare manuscript-works exception (author dead before 1855, first print post-1929), the `source_note` must state the unpublished-works PD basis explicitly |
| `year_note` | optional | string | First-publication vs transcription-base edition, serial publication, manuscript dating |
| `translator` | optional | string | Only where a translation is included; the translation itself must also be pre-1929 |
| `selection_note` | optional | string | Required whenever the file is an excerpt, explaining what's included and/or omitted, and why |
| `source_note` | optional | string | Source caveats: OCR noise tier, named corrections, retrieval route (e.g. Wayback snapshots), attribution uncertainty |
| `language_note` | optional | string | Tag rationale where the BCP-47 choice needs defending (see the grc and enm books) |
| `text_quality` | optional | string | Present only on books whose text is known to fall short of the corpus's normal fidelity bar, so a consumer can filter them out machine-readably. Two values: `noisy` (machine OCR or otherwise unproofread, with disclosed residual character noise, but readable and structurally sound) and `alpha` (known substantial problems, provisional, treat as a placeholder pending repair). Absent by default, meaning the text meets the bar: a typed or proofread source, or OCR that has been read and cleaned. Books carrying this field have a matching open flag in [QUALITY.md](QUALITY.md) noting the defect and the path |

Values follow the source: titles and authors are never romanised or modernised in these fields. Corrections are named in `source_note`.

The `text_quality` field is conservative. Most OCR-origin books in the corpus don't carry that tag because they were read and repaired in the audit waves, so the field marks only what is *still* below the bar and flagged. An NLP or eval user can exclude provisional text with a one-line filter, and a reader application could surface a "machine OCR, unverified" banner where one is warranted, rather than presenting every book as trustworthy. See CORPUS.md §Text-quality tiers for the current membership of each tier.

## The discovery layer

Optional aids for readers who cannot read the title's script. They never replace the canonical fields above; `title` and `author` stay in the work's own orthography.

| Key | Required | Type | Meaning |
|---|---|---|---|
| `title_translit` | optional | string | Standard romanization of the title (e.g. `Rashomon`, `Divan-e Ghalib`, `Tirukkural`). Plain ASCII-friendly forms, not scholarly diacritic transliteration |
| `title_en` | optional | string | The work's established English title where one exists (`The Overcoat`, `The Art of War`), or a plain gloss where none does. A finding aid rather than a fresh translation |
| `author_translit` | optional | string | Conventional romanized author name (`Natsume Soseki`, `Sholem Aleichem`) |

Every book whose title is in a non-Latin script carries these; Latin-script books omit them.

## The presentation layer

These optional fields record a typographic convention of the work, and are added only when the convention is not derivable from the content.

| Key | Values | Meaning |
|---|---|---|
| `writing-mode` | `vertical-rl`, `horizontal-tb` | The work's conventional writing direction, in the CSS `writing-mode` value space. Classical and Meiji-era CJK works declare `vertical-rl` (see the CORPUS.md writing-mode note for the full declared/absent matrix across ja, zh-Hant, zh-Hans, ko); absence means horizontal |

The layer is small and likely to stay that way, because:

- **No `dir`.** Base text direction derives from `language` (`ar`, `he`, `fa`, `ur` are right-to-left by definition), so declaring it would add a second source of truth. `writing-mode` is different: plenty of Japanese content is correctly horizontal, so verticality is an authorial convention.
- **No renderer-specific keys.** Theme pins, font choices, and similar belong to applications rather than to a corpus. The corpus stays renderer-neutral: a vertical-capable renderer honors `writing-mode`, everything else ignores it, and the file loses nothing either way.

## Verse and line-structured content

Markdown merges bare single newlines into spaces when rendered, so line
structure that carries meaning must be encoded explicitly. The corpus
convention: every verse line within a stanza ends with a CommonMark hard
break (exactly two trailing spaces); stanzas and poems are separated by
blank lines; dictionary entries and similar line-per-unit content use the
same hard breaks. Two accepted variants exist: the th poems and the mi
waiata use line-per-paragraph (each verse line blank-separated), an airier
style kept where the conversion predates the convention and renders
correctly. Hard-wrapped prose (source text wrapped at a column width) is
deliberately left to merge, which is its correct rendering. Check a
contribution with `scripts/check-verse-breaks.py`, whose flags are leads
that need human judgment.

## Headings and chapter titles

A structural division (part, book, chapter, poem, act) carries its title once, as a markdown heading. When a conversion restores headings from an edition's table of contents, the title as printed at the chapter head is not kept as a duplicate first body line. Where the table of contents and the chapter head word the title differently, the chapter-head reading wins and the heading carries it. Anything the printed title line carries beyond the words (a footnote marker, an attribution) moves into the heading so no linkage is lost. Removals under this rule are disclosed in the book's source_note as duplication removal. The convention was settled on 2026-07-26, when the two fr-FR novels, the last books showing both forms, were deduplicated; the QUALITY.md log records this.

## Rules for consumers

- Treat unknown keys as data to preserve rather than as errors.
- Key lookup should be case-insensitive; the corpus itself is consistently lowercase.
- Parse the block as YAML rather than matching strings against the raw text. Scalar quoting is not normalised across the corpus, so a value may be written bare or quoted and mean the same thing. A consumer grepping for `writing-mode: vertical-rl` in July 2026 found 11 of the 13 books that declare it, because two of the ko books wrote the value quoted; both were unquoted on 2026-07-26, but the general point stands for every field.
- Every field here is additive and stable: keys are never renamed. A change to these rules would be a breaking change and versioned accordingly.
- The `title` field is canonical; the filename is a short, filesystem-friendly form of it (drops subtitles, parentheticals, and punctuation that ages badly in paths). When they differ, trust `title`. Display code should never derive titles from filenames.
- Heading text within a book is not unique: anthologies repeat poem titles, chapter numerals restart per part, and Gaelic pibroch movements (URLAR, SIUBHAL) recur by design. Apps generating heading anchors must deduplicate slugs (the standard `-1`, `-2` suffix convention works).
- For programmatic enumeration, prefer `manifest.json` at the repo root (regenerated by `scripts/build-manifest.py`, freshness-checked in CI) over walking the tree.

## Setting and changing fields

Edit the YAML block directly, keeping the field order of neighboring books where reasonable, then verify:

```sh
python3 scripts/lint-corpus.py books/<your-file>.md
```

The linter checks frontmatter presence, required fields, and quoting of non-integer years. It also errors on two ways an unquoted value breaks a strict YAML parser: a value containing `: ` is a YAML syntax error, and a value that YAML 1.1 reads as a boolean or null (`no`, `yes`, `on`, `off`, `true`, `false`, `null`) comes back as the wrong type (`language: no` parses as `False`, not the Norwegian language code). Quote any such value. The [CONTRIBUTING](CONTRIBUTING.md) PR checklist covers the rest.

## Using the corpus without frontmatter

Most real-world markdown has no frontmatter, so applications testing against this corpus often need the bare-text path too. Rather than shipping a duplicate content set (which would drift), you can generate one:

```sh
python3 scripts/strip-frontmatter.py --output ../books-no-frontmatter
```

This mirrors `books/` into the output directory with every frontmatter block removed and the body byte-identical. Point your no-frontmatter tests there. You'll need to regenerate whenever you pull a corpus update.
