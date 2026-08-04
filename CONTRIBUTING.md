# Contributing

Thanks for considering a contribution! This corpus exists because many people made these texts available, and another pair of hands is always welcome.

## Wanted

- **New locales not yet covered**: see the "Still missing" section in [CORPUS.md](CORPUS.md) for the current v1.2+ wishlist (Telugu, Mongolian, Inuktitut, Coptic, Ottoman Turkish, Tibetan, more African languages, etc.).
- **Better picks for locales that carry substitutions**: Premchand in Urdu (if you can find a clean digitised source), Akinyele's *Iwe Itan Ibadan* in Yoruba, secular pre-1929 Amharic literature.
- **Quality-ledger items**: [QUALITY.md](QUALITY.md) lists every flagged book with the identified path to fixing it; several (the Bowen Yoruba proverbs re-transcription especially) are small, well-bounded tasks ideal for a first contribution.
- **Native-reader audits**: if you read any of the corpus's languages fluently, auditing a book against its cited source is the most valuable contribution you can make. The method is described in [QUALITY.md](QUALITY.md) §How to audit a book.
- **Conversion-script improvements**: better OCR cleanup for Internet Archive djvu sources, smarter Wikisource ProofreadPage transclusion walking, new helpers for sources not yet handled would all be useful.
- **Documentation polish**: typo fixes, broken-link reports, clearer language in the curation principles.

## If you don't write code

Most of what's wanted above needs no Python, no git, and no pull request. Any of these can be done from a browser:

- [Tell us about a source](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=new-source.md). A book worth having, and where a clean text of it lives. Someone else can write the converter.
- [Report a mistake in a book](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=content-correction.md). A wrong character, a missing passage, a heading in the wrong place. You don't need to know how to fix it, only where it is.
- [Suggest a language](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=new-locale.md) the corpus should cover, with a canonical work and a note on where it's digitised.
- Read a book in a language you know and say what's wrong with it. This is the most useful thing anyone can do here, and [QUALITY.md](QUALITY.md) §How to audit a book describes how to go about it. Report what you find as a content correction.

If you'd rather not use GitHub at all, contact@tideswellgroup.com reaches me.

## Not accepted

- **Anything published 1929 or later**, with one exception: a work transmitted in manuscript whose author died before 1855 (the US unpublished-works term, life plus 70 years, expired in the 19th century) may qualify, and its file must state that basis in `source_note`. If you are invoking the exception, say so in the PR; everything else is strictly pre-1929 to stay unambiguously in the US public domain.
- **Sacred and liturgical texts of any religion.** This selection is secular, for two reasons: deciding on which texts to include is a decision that belongs inside a tradition rather than to a corpus like this, and because they're the most digitised texts in most languages and would crowd out the literature this corpus exists to sample. Folk tales, national epics, philosophical works and ethical wisdom literature are welcomed.
- **Translations under copyright**. The translator's copyright is separate from the original author's. If the translation isn't pre-1929 too, find a different translation.
- **Bulk dumps**. Each book is a curation decision. If you want to contribute 50 obscure works in one locale, open an issue first to discuss what serves the corpus's diversity goals best.

## How to add a new book

### 1. Source the text

Use a known-good upstream archive:

- **Project Gutenberg** (https://www.gutenberg.org): Latin-script European literature mostly. Plain-text downloads are clean.
- **Wikisource** (per language): the canonical archive for many non-English languages. Quality varies; check for transclusion ("`<pages index=`...") which complicates conversion.
- **Aozora Bunko** (https://www.aozora.gr.jp): Japanese.
- **Project Ben-Yehuda** (https://benyehuda.org): Hebrew.
- **Ganjoor** (https://ganjoor.net): Persian classical poetry.
- **Saga Database** (https://sagadb.org): Icelandic medieval.
- **Internet Archive** (https://archive.org): items unavailable elsewhere. OCR quality varies; expect noise.

### 2. Convert to markdown

Use the appropriate script in `scripts/`. Each accepts `--help`:

```sh
python3 scripts/convert-gutenberg.py --help
python3 scripts/convert-wikisource.py --help
python3 scripts/convert-aozora.py --help
# ... etc.
```

If you're converting from a source not yet supported, please add a new `scripts/convert-<source>.py` following the existing pattern. Each helper writes YAML frontmatter + markdown body and accepts standard CLI args.

If you've found a good source but don't write Python, please [open an issue](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=new-source.md) anyway. Describe the source, the book, and what makes it worth having, and either I or another contributor can write the converter. Finding a clean pre-1929 text in a language nobody has digitised well is incredibly helpful, and it needs someone who knows the language and the literature. You can also reach me at contact@tideswellgroup.com if you'd rather not use GitHub.

### 3. Place the file

```
books/<bcp47-locale>/<Author Name>/<Title>.md
```

The locale tag follows BCP-47 (e.g. `es-MX` for Mexican Spanish, `zh-Hans` for Simplified Chinese, `grc` for Ancient Greek).

### 4. Frontmatter requirements

```yaml
---
title: ...
author: ...
language: <BCP-47 tag>
year: <integer or "c. NNN BCE" quoted string>
source: <repository name>
source_url: <direct URL to the source>
license: Public domain in the United States
---
```

Optional but encouraged: `year_note`, `translator`, `selection_note` for excerpts, `source_note` for caveats. The full field reference, including the presentation-metadata layer and its admission rule, is in [FRONTMATTER.md](FRONTMATTER.md).

### 5. Verify

One command runs every check:

```sh
python3 scripts/preflight.py books/<your-new-file>.md
```

It sorts the results into what you must fix before opening a PR, what needs your judgment and an explanation in the PR, and what is already handled for you. If your book came from Wikisource, re-run it with `--upstream` to compare your file against the live source page as well. That check needs network access, and it catches conversion steps that silently drop punctuation or whole verse sections.

Two of its findings are worth understanding before you see them. Verse flags are leads rather than verdicts: verse lines inside a stanza need two trailing spaces (see [FRONTMATTER.md](FRONTMATTER.md) §Verse), while hard-wrapped prose merges correctly and should be left alone. Soft-wrapped verse renders as a prose wall in every spec-compliant markdown renderer and is the most common conversion mistake here.

When preflight tells you the index is out of date, regenerate it and commit the result:

```sh
python3 scripts/build-manifest.py
```

### 6. Update the documentation

The corpus numbers live in prose in three files, and history shows they drift when only some get updated. The full touchpoint list for adding a book:

- **CORPUS.md**: add a row to the appropriate cluster table. For a new locale, also update the inventory header line, the coverage lists under "Linguistic and script-family coverage", and (if you used a new source route) the provenance table.
- **README.md**: for a new locale, add or extend a coverage-matrix row (and bump its book count; the matrix book counts are machine-checked). For a new language, the headline blockquote and the Overview table also change.
- **CITATION.cff**: only changes when the language count changes (title, abstract, preferred-citation title).
- **QUALITY.md**: add a dated entry to the Resolved log describing what you added and its quality posture (source edition, orthography, any known weaknesses). If your book ships with a known defect or provenance gap, add an Open flag with the defect, the fix path, and what "done" means.

Preflight checks all of this for you and names whatever is still inconsistent. If some of it defeats you, do what you can and say so in the PR. I would much rather have the book with the documentation half-updated than not have the book.

### 7. Open the PR

PR title: `Add <author> <title> (<locale>)` or `New locale: <locale>`.

PR description should answer:

- What did you add?
- Why this book in particular?
- What source did you use, and was the OCR / conversion clean?
- Any caveats (substitutions from a planned pick, religious adjacency, OCR noise)?

## Curation principles (reminder)

The five principles from the README, in short form:

1. Every book is unambiguously in the US public domain: normally pre-1929 publication, with the narrow manuscript-works exception documented above.
2. The selection is secular; the sacred texts of every religion are excluded alike.
3. Each locale carries two or three books, varied in size, genre, and period.
4. Canonical works are preferred over obscure ones.
5. Reference works are accepted only as locale-fillers where literary prose is not digitised.

## Code style for conversion scripts

- Python 3.10+ standard library only. Avoid pip dependencies; the linter and converters should run on any vanilla Python install.
- Each script accepts `--help` and clear CLI args.
- Each script has a module docstring explaining what source it handles and what conventions.
- Each script writes consistent YAML frontmatter via the existing helper functions; copy from a sibling script if unsure.
- Output should pass `lint-corpus.py` with zero errors.

## Style for prose docs

- No em-dashes (the U+2014 character) in committed docs. Use commas, periods, parens, or colons. Em-dashes inside the literary content under `books/` are of course fine, since those are verbatim author voice.
- Be specific. "Some sources" is worse than "Project Gutenberg, Wikisource, and Internet Archive".
- Cite scholarship inline where relevant (e.g. the Kural numbering for the Tirukkural, or a named edition for a manuscript text).

## The individual checks

`scripts/preflight.py` is a wrapper. If you would rather run the checks one at a time, or you are wondering what it just did:

| Script | What it catches | Blocks a PR |
|---|---|---|
| `lint-corpus.py` | 14 classes of rendering-risk pattern: math delimiter imbalance, orphan `<math>` tags, wiki-template debris, malformed frontmatter | Yes |
| `check-verse-breaks.py` | Verse soft-wrapped without two-space hard breaks, which renders as a prose wall | No, every flag needs a human decision |
| `verify-upstream.py` | Marks and whole passages silently dropped during conversion, compared against the live Wikisource page | No, and it needs network access |
| `build-manifest.py --check` | `manifest.json` out of date with the corpus | Yes, and the fix is to run it without `--check` |
| `check-doc-counts.py` | Counts stated in README, CORPUS.md and CITATION.cff drifting from the corpus | Yes |

## Code of conduct

This project follows the [Ruby Code of Conduct](CODE_OF_CONDUCT.md): be tolerant of opposing views, keep your language free of personal attacks, and assume good intentions when interpreting the words of others. Disagreement is welcome; please keep it respectful.

## Reporting

- **Content corrections** (a book has a transcription error): [open an issue](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=content-correction.md) with the file path and the specific line / passage.
- **Attribution, edition, or context corrections**: challenges to a pick, an author attribution (collected oral literature especially), or a source edition are welcome; [open an issue](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=content-correction.md) with the scholarship or source you are drawing on.
- **New sources** (a book or archive worth converting): [open an issue](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=new-source.md) describing the work, where it lives, and what shape the text is in.
- **New locale suggestions**: [open an issue](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=new-locale.md) describing the language, the script, the canonical author/work you'd want to include, and the source you'd source from.
- **Bug reports** (a conversion script broke, the linter flagged a false positive, etc.): use the [bug-report template](https://github.com/tideswellgroup/multilingual-classics-markdown/issues/new?template=bug-report.md).

Thanks for being here.
