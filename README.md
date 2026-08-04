# multilingual-classics-markdown

[![Content: CC0 1.0](https://img.shields.io/badge/content-CC0%201.0-lightgrey.svg)](LICENSE) [![Tooling: MIT](https://img.shields.io/badge/tooling-MIT-lightgrey.svg)](LICENSE-CODE.md) [![Books: 137](https://img.shields.io/badge/books-137-blue.svg)](CORPUS.md) [![Locales: 58](https://img.shields.io/badge/locales-58-blue.svg)](#coverage-matrix)

> A curated corpus of public-domain literary classics in 45 languages across 58 locales, converted to clean markdown with YAML frontmatter, spanning Latin, Cyrillic, Greek, Hebrew, Arabic, Perso-Arabic, Devanagari, Bengali, Tamil, CJK, Thai, Cherokee, three constructed languages, and the historical Englishes from Beowulf to Shakespeare's 1609 Quarto. In total, this repo collects 137 books across 14 language families and 12 script systems.

This repo is intended as a complement to [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown), 
delivering the languages, the historical Englishes (Old English, Middle English, original-spelling Early Modern), and the regional English literatures that modern-spelling English corpora do not carry. It was built so that application developers, NLP researchers, language learners, and typography enthusiasts can drop a real-world multilingual corpus into their workflow as easily as possible. The en-US and modern-spelling en-GB canon, which mlschmitt's project already does well, are deliberately absent.

## Overview

| | |
|---|---|
| **Languages** | 45 languages across 58 locales and 14 language families |
| **Books** | 137 individual works, ~26 MB of markdown. The whole repository clones in seconds (about 14 MiB packed) |
| **Scripts covered** | Latin (with rich diacritics), Cyrillic, Greek, Hebrew, Arabic, Perso-Arabic, Devanagari, Bengali, Tamil, CJK (Han / kana / Hangul), Thai abugida, Cherokee syllabary |
| **License** | Content: CC0 (where public-domain content needs a license at all). Tooling: MIT |
| **Fidelity** | Faithful renditions of named source editions, not critical editions. See [Scholarly use and limitations](#scholarly-use-and-limitations) before citing |
| **Provenance** | Every book carries source URL, original publication year, and license posture in YAML frontmatter |
| **Machine-readable** | `manifest.json` indexes every book, validated in CI against `manifest.schema.json`; `croissant.json` describes the corpus in the [MLCommons Croissant](https://mlcommons.org/working-groups/data/croissant/) format |
| **Verification** | `scripts/lint-corpus.py` checks 14 classes of rendering-risk patterns; 0 errors at last release |
| **Known defects** | Tracked openly in [QUALITY.md](QUALITY.md): every flagged book, the path to fixing it, and the resolved history |

### Choose your path

- **Ingesting this into something?** Start with [`manifest.json`](manifest.json) and its [schema](manifest.schema.json), then [FRONTMATTER.md](FRONTMATTER.md) for what each field means. [`croissant.json`](croissant.json) carries the same description in MLCommons Croissant form.
- **Thinking of citing it?** Read [Scholarly use and limitations](#scholarly-use-and-limitations) first, then [CITATION.cff](CITATION.cff). Known defects are listed openly in [QUALITY.md](QUALITY.md).
- **Just want to look around?** The [coverage matrix](#coverage-matrix) is the map. Good places to start: the [Cherokee Constitution](books/chr), a [vertical-writing Japanese story](books/ja), or [Beowulf in Old English](books/ang).

## Why?

Most public-domain literary corpora are English-only (Standard Ebooks, mlschmitt's project, most of Project Gutenberg's curated picks), and the multilingual sources come in formats that suit neither builders nor scholars: Wikisource lives in MediaWiki wikitext, Project Gutenberg in HTML, TXT, and EPUB, and scholarly archives in TEI XML. Anyone who wants to build an application that handles many languages well has to do the digitisation, conversion, encoding fixup, and curation themselves.

This repo began life as the internationalisation test corpus for a Mac-native markdown writing app I'm building. It grew into something I think is worth sharing: a collection of markdown in many languages with consistent frontmatter, plus the conversion tooling, so that anyone can add books and contribute them back for all to use.

The corpus is intended for:

- Developers of markdown readers, e-readers, and typography tools who need real non-English prose to test against
- NLP researchers who want a literary corpus balanced across script families
- Language learners who want canonical literature alongside translations
- Anyone curious to see how many different writing systems can live in the same plain-text file format

## Coverage matrix

Directory names under `books/` are [BCP-47](https://www.rfc-editor.org/info/bcp47) **language** tags, which trip up anyone
navigating by country code: Greek is `el` (not gr), Japanese `ja` (not jp), Korean
`ko` (not kr), Swedish `sv` (not se), Vietnamese `vi` (not vn), Welsh `cy`, Irish
`ga`, Scottish Gaelic `gd`, Icelandic `is`. Three more conventions worth knowing
before you go looking for a specific book:

- **The historical stages of English are their own languages.** Beowulf is under
  `ang` (Old English), Chaucer under `enm` (Middle English), and Burns under `sco`
  (Scots). `en-GB` holds original-spelling Early Modern English, currently the
  1609 Quarto Sonnets.
- **Chinese splits by script, not country**: `zh-Hans` (Simplified) and `zh-Hant`
  (Traditional), four books each.
- **`la` is the Latin language**, not the Latin script. In the matrix below the
  Script column says "Latin" for most rows because that is the writing system;
  the one row whose Locale is `la` is Vergil, in the language.
- **Regional literatures get regional tags**: Mexican Spanish under `es-MX`,
  Brazilian Portuguese under `pt-BR`, Québécois French under `fr-CA`, Austrian
  German under `de-AT`, and seven regional English literatures from `en-IE` to
  `en-JM` (with `en-GB` and `en-US` reserved for the original-spelling editions).

If you'd like to know more about how these tags work, Wikipedia's [IETF language tag](https://en.wikipedia.org/wiki/IETF_language_tag) article is a good overview.

| Family | Script | Locales | Books |
|---|---|---|---|
| Indo-European, Germanic | Latin | de-DE, de-AT, nl, sv, no | 11 |
| Indo-European, Germanic (English varieties) | Latin | en-GB, en-US, en-IE, en-CA, en-NZ, en-ZA, en-AU, en-IN, en-JM | 14 |
| Indo-European, Germanic (historical English) | Latin (þ ð æ; Middle English spellings) | ang, enm | 2 |
| Indo-European, Germanic | Latin (Scots) | sco | 1 |
| Indo-European, Romance | Latin | es-ES, es-MX, fr-FR, fr-CA, it, pt-PT, pt-BR | 21 |
| Indo-European, Slavic | Cyrillic | ru, uk | 6 |
| Indo-European, Slavic | Latin (ogonek, kreska) | pl | 3 |
| Indo-European, Slavic | Latin (háček, kroužek) | cs | 2 |
| Indo-European, Hellenic | Greek (polytonic) | grc, el | 2 |
| Indo-European, Italic | Latin (macronised) | la | 1 |
| Indo-European, Indo-Iranian | Devanagari | hi | 3 |
| Indo-European, Indo-Iranian | Bengali | bn | 3 |
| Indo-European, Indo-Iranian | Perso-Arabic | fa, ur | 6 |
| Indo-European, Celtic | Latin (with digraphs / accents) | cy, ga, gd | 5 |
| Indo-European, Old Norse | Latin (with þ ð) | is | 3 |
| Afro-Asiatic, Semitic | Hebrew | he | 3 |
| Afro-Asiatic, Semitic | Arabic | ar | 3 |
| Sino-Tibetan, Sinitic | Han (Simplified) | zh-Hans | 4 |
| Sino-Tibetan, Sinitic | Han (Traditional) | zh-Hant | 4 |
| Japonic | Hiragana / Katakana / Han | ja | 5 |
| Koreanic | Hangul (incl. old-hangul and mixed Hanja-Hangul) | ko | 5 |
| Austroasiatic | Latin (Vietnamese) | vi | 3 |
| Kra-Dai | Thai abugida | th | 3 |
| Niger-Congo, Bantu | Latin | sw | 4 |
| Niger-Congo, Yoruboid | Latin (tone marks) | yo | 3 |
| Iroquoian | Cherokee syllabary | chr | 1 |
| Uralic, Finnic | Latin | fi | 3 |
| Turkic | Latin (1928 reform orthography) | tr | 1 |
| Dravidian | Tamil | ta | 3 |
| Austronesian, Polynesian | Latin (period orthography, unmacronised) | haw, mi | 5 |
| Constructed, auxiliary | Latin (with diacritics) | eo, vo, io | 4 |

## Example use cases

### Drop-in test corpus for a markdown application

```sh
git clone https://github.com/tideswellgroup/multilingual-classics-markdown.git
cd multilingual-classics-markdown/books/ja/芥川龍之介/
ls
# 羅生門.md
```

Open the file in your application. Fields are documented in [FRONTMATTER.md](FRONTMATTER.md); the frontmatter declares a full BCP-47 language tag, which carries regional and script subtags where they matter (`ja` here; `es-MX` and `zh-Hans` elsewhere), plus the original publication year (1915), source URL, and license posture. The body is clean markdown.

### Enumerate the corpus programmatically

`manifest.json` at the repo root indexes every book (path, locale, full frontmatter, size, word count) so applications never need to walk the tree and parse frontmatter themselves:

```python
import json

manifest = json.load(open("manifest.json", encoding="utf-8"))
for book in manifest["books"]:
    print(book["locale"], book["title"], book["wordCount"])
```

It is regenerated by `scripts/build-manifest.py` and freshness-checked in CI, so it is always in sync with `books/`.

### Iterate over the entire corpus

```python
from pathlib import Path
import yaml  # pip install pyyaml

for book_md in Path("books").rglob("*.md"):
    text = book_md.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        frontmatter = yaml.safe_load(text[4:end])
        body = text[end + 5:]
        # frontmatter['language'], frontmatter['year'], frontmatter['title'], frontmatter['author']
        # body: the actual markdown text
```

### Validate a converted book before committing

```sh
python3 scripts/lint-corpus.py path/to/my-new-book.md
```

The linter catches encoding errors, unbalanced math delimiters, Wikisource license-template debris, orphan HTML tags, heading-level skips, suspicious Unicode, and several other classes of conversion failure.

## How it was built, and how to extend it

Every book in this repo came from one of these upstream sources:

| Source | What it provided |
|---|---|
| [Project Gutenberg](https://www.gutenberg.org) | Most Latin-script European literature (de, fr, es, ru, fi, pt, it, nl, sv, cs) |
| [Wikisource](https://wikisource.org) (per language) | Eastern European, Indic, Hellenic, and East Asian texts |
| [Aozora Bunko](https://www.aozora.gr.jp) | Japanese classical and modern literature |
| [Project Ben-Yehuda](https://benyehuda.org) | Canonical Hebrew literature |
| [Ganjoor.net](https://ganjoor.net) | Persian classical poetry |
| [sagadb.org](https://sagadb.org) | Icelandic medieval prose |
| [Internet Archive](https://archive.org) | Items unavailable through curated archives (Cherokee, Yoruba, Irish, Scots Gaelic, Mexican Spanish, Volapük, Ido, Esperanto first editions) |
| [africanpoems.net](https://africanpoems.net) | Mwana Kupona's 1858 Swahili didactic poem |

Each source has its own conventions (wikitext templates, Aozora's ruby annotations, Internet Archive's DjVu OCR, Ganjoor's per-poem API). The conversion scripts in `scripts/` know how to handle them. To add a new book:

1. Source the text from one of the upstream archives (see [CONTRIBUTING.md](CONTRIBUTING.md) for sourcing standards)
2. Run the appropriate conversion script (or write a new one for a source the scripts don't yet handle)
3. Verify with `python3 scripts/lint-corpus.py path/to/new-book.md`
4. Open a PR with the new file plus an entry in CORPUS.md

## Curation principles

This corpus is curated rather than exhaustive, and the curation follows five principles:

1. **Every work is unambiguously in the US public domain, and the edition it was transcribed from is named.** These are two separate questions and the corpus answers both.

   The *work* is public domain. Normally that follows from pre-1929 publication. One narrow documented class also qualifies: works transmitted in manuscript whose author died before 1855, where the US unpublished-works term (life plus 70 years) expired in the 19th century. Any such file states this basis in its own `source_note`. Currently one book uses it, the ko court memoir 한중록, first printed 1939.

   The *transmission base*, meaning the edition a transcription was actually made from, is pre-1929 for all but a handful of books. Where a later edition is what reached the corpus, the `year_note` or `source_note` says which one and why. This matters because a modern editor's transcription can carry an editorial layer of its own even when the work beneath it is free. The current exceptions:

   | Book | Work | Transmission base |
   |---|---|---|
   | `pl` Prus, *Kamizelka* | 1882 | *Pisma*, Gebethner i Wolff, 1935 |
   | `uk` Kotsiubynsky, *Тіні забутих предків* | 1912 | *Твори* vol. 2, Книгоспілка, New York, 1955 |
   | `mi` White, *Nga Kauhau Maori o Nehe* | 1887 | NZETC digitisation, 2001 to 2007 |
   | `sw` Mwana Kupona, *Utendi wa Mwana Kupona* | 1858 | Allen, *Tendi*, Heinemann, 1971 |

   The first three reproduce an orthographic recension or a plain digitisation of a text that is itself free, which carries no practical restriction. The fourth is an edited scholarly transcription, is the only book in the corpus where an editorial layer may genuinely subsist, and is flagged in [QUALITY.md](QUALITY.md) for re-sourcing from Alice Werner's 1917 edition.
2. **The selection is secular by default.** The sacred and liturgical texts of every religion are excluded alike, while folk tales, national epics, philosophical-skeptical works, and ethical wisdom literature are included as literary canon.
3. **Each locale carries two or three books**, mixing size and genre where sources permit.
4. **Canonical works are preferred over obscure ones.** Where the choice is between a niche author and a recognised one, the corpus leans canonical.
5. **Reference works are accepted as locale-fillers** only when literary prose is not digitised in clean form. This currently applies to yo and chr, where the pre-1929 corpus is overwhelmingly missionary-religious in nature.

Every substitution from the originally-planned picks is documented in [CORPUS.md](CORPUS.md) for transparency.

## Scholarly use and limitations

This is a convenience corpus rather than a collection of critical editions. Before citing it in scholarship, it is worth understanding what it is and what it is not:

- **Texts come from volunteer digitisation projects** (Wikisource, Project Gutenberg, Internet Archive OCR, and the archives credited below) and inherit those projects' transcription errors. OCR-sourced files carry documented noise; see per-file `source_note` fields and the caveats in [CORPUS.md](CORPUS.md). No text here has been collated against manuscripts or authoritative print editions.
- **Curation involved judgment calls**: which works count as canon, which edition to take, where to excerpt, how to attribute works with complex authorship. CORPUS.md records each locale's choices, substitutions, and known weaknesses. The calls were made to the best of one maintainer's ability and every one of them is open to debate.
- **Attribution of collected oral literature is hard.** Several works passed through colonial-era editors whose names appear on title pages while the source authors and informants went uncredited. Where scholarship identifies those authors, the frontmatter credits them, and these texts remain the cultural heritage of the communities they come from.
- **Year fields follow the cited source edition**, with `year_note` carrying nuance (manuscript versus print date, serial publication, composite works).
- **Corrections and new perspectives are welcome**, especially from native speakers and subject specialists. Open an issue with the content-correction template or send a PR. Disagreement about a pick, an attribution, or an edition is useful information.

### What would make it citable

The limitations above describe where the corpus stands, not where it has to stay. Four things separate it from something a scholar could cite without reservation, and they are listed roughly in order of cost:

1. **An archival deposit with a persistent identifier.** A DOI against an archived snapshot, so a citation resolves to fixed bytes rather than to a moving branch. This is the cheapest item on the list and the one that matters most.
2. **Stable per-book identifiers.** Paths are currently the identity of a book, so a re-attribution that moves a file breaks any citation to it, even though renames land in dedicated commits precisely so they can be traced. An immutable `uid` in the frontmatter would fix that permanently.
3. **A stated editorial method.** A written account of how conversions were made, what was checked by a human and what by a script, and who verified which languages. Parts of this are already scattered through CORPUS.md and QUALITY.md; it wants collecting in one place.
4. **Structural encoding.** Verse lines, speaker attribution, page breaks and an apparatus, which in practice means TEI rather than Markdown. This is a different project with a different cost, and there is no plan to do it. Anyone who needs textual apparatus should go to the source editions instead.

The first three are achievable and intended. The fourth is honestly out of scope, and the corpus would rather say so than imply otherwise.

## Repository layout

```
multilingual-classics-markdown/
├── README.md              # this file
├── CORPUS.md              # full inventory with sourcing notes and caveats
├── QUALITY.md             # the live defect ledger: open flags and resolved history
├── CHANGELOG.md           # what arrived, was replaced, or was revised, per release
├── FRONTMATTER.md         # frontmatter reference: fields, meanings, rules
├── CONTRIBUTING.md        # how to add a new book or locale
├── manifest.json          # machine-readable index of every book
├── manifest.schema.json   # JSON Schema the manifest is validated against in CI
├── croissant.json         # MLCommons Croissant description of the dataset
├── LICENSE                # CC0 1.0 legal text (content)
├── audits/                # dated records of full-corpus review passes
│   ├── README.md          # why they are kept and when a pass happens
│   └── 2026-07-25.md
├── CODE_OF_CONDUCT.md     # Ruby Code of Conduct
├── CITATION.cff           # academic citation metadata
├── LICENSE-CONTENT.md     # CC0 declaration for the book content
├── LICENSE-CODE.md        # MIT license for the conversion scripts
├── books/
│   └── <bcp47-locale>/
│       └── <Author>/
│           └── <Title>.md
├── scripts/
│   ├── lint-corpus.py     # validation pass
│   ├── check-manifest-schema.py # manifest vs its JSON Schema
│   ├── strip-frontmatter.py # mirror the corpus with frontmatter removed
│   ├── verify-upstream.py # fidelity audit against live upstream sources
│   ├── convert-gutenberg.py
│   ├── convert-wikisource.py
│   ├── convert-wikisource-html.py
│   ├── convert-aozora.py
│   ├── convert-rtl-sources.py
│   ├── convert-sagadb.py
│   ├── convert-internet-archive.py
│   └── ... (per-source helpers)
└── .github/
    ├── workflows/
    │   └── lint.yml       # CI lint on push/PR
    └── ISSUE_TEMPLATE/
        ├── new-locale.md
        ├── content-correction.md
        └── bug-report.md
```

## Pinning this corpus

Applications that test against the corpus should consume it as a git submodule rather than copying files, because a hand-copied subset drifts and the drift is invisible until something regresses.

Pin a tag rather than a bare commit. Tags are named `wave-YYYY-MM-DD` after the editing wave they close, and they mark a corpus that has been reviewed end to end. Ordinary commits on `main` do not carry that guarantee, because a wave lands its edits across several commits. Published releases are intended to carry a separate `v<major>.<minor>.<patch>` tag alongside an archival DOI, and the two schemes will not collide; neither exists yet, so today the `wave-*` tags are the only pinnable points.

Paths (`books/<locale>/<author>/<title>.md`) are the identity of a book. There is no separate stable ID, and `manifest.json` keys on the path. Renames are rare and happen when a re-attribution or a source correction makes the old path wrong. When one happens it lands in a commit of its own, with no content edit riding along, so that `git diff --find-renames --diff-filter=R <old-tag> <new-tag> -- books` reports the mapping exactly. Consumers keyed on paths should run that diff when they move a pin.

Rendering problems found in a book (frontmatter that does not parse, structure that does not survive a round trip, hard breaks that vanish) belong in this tracker as a content-correction issue. Name the book path and the tag you found it at, and describe what the renderer received rather than which renderer received it.

## Other relevant projects

- [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown) collects English-only public-domain literary classics. This corpus covers the languages that project does not, so the two repos work well together.

If you find another similar project, please open an issue and I'll add it.

## Citation

If this corpus contributes to your work, please cite it. The repository carries a [`CITATION.cff`](CITATION.cff) file for academic citation generation; most reference managers and academic platforms (Zotero, Mendeley, Zenodo, GitHub itself) pick it up automatically.

```
Powell, S. multilingual-classics-markdown: Public-domain literary classics
in 45 languages [Software]. GitHub. https://github.com/tideswellgroup/multilingual-classics-markdown
```

## Acknowledgements

This repo would not be possible without the work of the hundreds of people who transcribed, proofread, and made texts available:

- **Project Gutenberg** volunteers and the PG Distributed Proofreading Team
- **Per-language Wikisource** editor communities, especially the Welsh, Vietnamese, Thai, Chinese, Hindi, Hebrew, Persian, Urdu, Russian, Greek, and Italian groups
- **Aozora Bunko** volunteers for Japanese classical and modern literature
- **Project Ben-Yehuda** for the canonical Hebrew literature archive
- **Ganjoor** for Persian classical poetry
- **Saga Database** for Icelandic medieval prose
- **Internet Archive** and Google Books for scanning items unavailable elsewhere
- **Project Madurai** volunteers for the Tamil literary etexts
- **NZETC** (Victoria University of Wellington) for the Maori transcriptions, reached through the Internet Archive Wayback Machine after the live host was decommissioned
- **Matt Schmitt** for `classic-books-markdown`, which motivated and informed this work
- The countless authors, editors, and translators whose work is in these files

## License

The license comes in two parts:

- **Content** (everything under `books/`) is released under [CC0 1.0 Universal](LICENSE-CONTENT.md). All texts are public domain in the United States, and the CC0 declaration removes any residual ambiguity for downstream users.
- **Tooling** (everything under `scripts/`) is under the [MIT License](LICENSE-CODE.md).

See the individual license files for full terms.

## Contributing

New locales, new books in existing locales, and improvements to the conversion scripts are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for sourcing standards, conversion expectations, and the PR checklist.

Contributions I would especially welcome:

- **Locales not yet covered**: Telugu and other Dravidian languages beyond Tamil, further Slavic Latin variants beyond Polish and Czech, Mongolian, Inuktitut, Coptic, Ottoman Turkish (ota), more African languages beyond Swahili and Yoruba, and English variants with pre-1929 founding literatures (Ghana via Casely Hayford, the Philippines via Galang)
- **Two famous transcription gaps**: Anne Bradstreet's *The Tenth Muse* (1650) survives online only as black-letter page images, and Claude McKay's *Songs of Jamaica* (1912) is untranscribed; clean transcriptions of either would let the corpus carry them
- **Better picks for locales carrying substitutions**: Premchand in Urdu (the corpus currently has Ghalib, Iqbal, and Mir Taqi Mir; I'd love a clean Premchand-Urdu source), Akinyele's *Iwe Itan Ibadan* if it ever surfaces in clean form, secular pre-1929 Amharic literature
- **Conversion-script improvements** for sources handled clumsily today (OCR cleanup for IA djvu, better Wikisource ProofreadPage transclusion walking)
- ***Ka Moolelo o Hiiakaikapoliopele*** in Hawaiian: the 1905-06 serial lives in the nupepa/ulukau newspaper archives rather than Internet Archive; a contributor with access could bring the great Hiiaka epic here

## Status

This is a v1 release. Expected updates include occasional book additions, source-URL refreshes when upstreams move, and conversion-script additions and improvements.
