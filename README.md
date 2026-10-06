# multilingual-classics-markdown

[![Content: CC0 1.0](https://img.shields.io/badge/content-CC0%201.0-lightgrey.svg)](LICENSE) [![Tooling: MIT](https://img.shields.io/badge/tooling-MIT-lightgrey.svg)](LICENSE-CODE.md) [![Books: 146](https://img.shields.io/badge/books-146-blue.svg)](CORPUS.md) [![Locales: 67](https://img.shields.io/badge/locales-67-blue.svg)](#coverage-matrix) [![Metadata: Croissant 1.0](https://img.shields.io/badge/metadata-Croissant%201.0-lightgrey.svg)](croissant.json)

> A curated corpus of public-domain literary classics in 54 languages across 67 locales, converted to clean markdown with YAML frontmatter, spanning Latin, Cyrillic, Greek, Hebrew, Arabic, Perso-Arabic, Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Tibetan, Egyptian hieroglyphs, CJK, Thai, Cherokee, three constructed languages, and the historical Englishes from Beowulf to Shakespeare's 1609 Quarto. In total, this repo collects 146 books across 14 language families and 20 script systems.

This repo is intended as a complement to [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown), 
delivering the languages, the historical Englishes (Old English, Middle English, original-spelling Early Modern), and the regional English literatures that modern-spelling English corpora do not carry. It was built so that application developers, NLP researchers, language learners, and typography enthusiasts can drop a real-world multilingual corpus into their workflow as easily as possible. The en-US and modern-spelling en-GB canon, which mlschmitt's project already does well, are deliberately absent.

## Overview

| | |
|---|---|
| **Languages** | 54 languages across 67 locales and 14 language families |
| **Books** | 146 individual works, ~33 MB of markdown. The whole repository clones in seconds (about 14 MiB packed) |
| **Scripts covered** | Latin (with rich diacritics), Cyrillic, Greek, Hebrew, Arabic, Perso-Arabic, Devanagari, Bengali, Gurmukhi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Tibetan, Egyptian hieroglyphs, CJK (Han / kana / Hangul), Thai abugida, Cherokee syllabary |
| **License** | Content: CC0 (where public-domain content needs a license at all). Tooling: MIT |
| **Fidelity** | Faithful renditions of named source editions, not critical editions. See [Academic use](#academic-use) before citing |
| **Provenance** | Every book carries source URL, original publication year, and license posture in YAML frontmatter |
| **Machine-readable** | `manifest.json` indexes every book, validated in CI against `manifest.schema.json`; `croissant.json` describes the corpus in the [MLCommons Croissant](https://mlcommons.org/working-groups/data/croissant/) format |
| **Verification** | `scripts/lint-corpus.py` checks 14 classes of rendering-risk patterns; 0 errors at last release |
| **Known defects** | Tracked openly in [QUALITY.md](QUALITY.md): every flagged book, the path to fixing it, and the resolved history |

### Choose your path

- **Ingesting this into something?** Start with [`manifest.json`](manifest.json) and its [schema](manifest.schema.json), then [FRONTMATTER.md](FRONTMATTER.md) for what each field means. [`croissant.json`](croissant.json) carries the same description in MLCommons Croissant form.
- **Thinking of citing it?** Read [Academic use](#academic-use) first, then [CITATION.cff](CITATION.cff). Known defects are listed openly in [QUALITY.md](QUALITY.md).
- **Just want to look around?** The [coverage matrix](#coverage-matrix) is the map. Good places to start: the [Cherokee Constitution](books/chr), a [vertical-writing Japanese story](books/ja), or [Beowulf in Old English](books/ang).

## Why?

Most public-domain literary corpora are English-only (Standard Ebooks, mlschmitt's project, most of Project Gutenberg's curated picks), and the multilingual sources come in formats that suit neither builders nor scholars: Wikisource lives in MediaWiki wikitext, Project Gutenberg in HTML, TXT, and EPUB, and scholarly archives in TEI XML. Anyone who wants to build an application that handles many languages well has to do the digitisation, conversion, encoding fixup, and curation themselves.

This repo began life as the internationalisation test corpus for a Mac-native markdown writing app I'm building. It grew into something I think is worth sharing: a collection of markdown in many languages with consistent frontmatter, plus the conversion tooling, so that anyone can add books and contribute them back for all to use.

The corpus is intended for:

- Developers of markdown readers, e-readers, and typography tools who need real non-English prose to test against
- Font and typeface engineers who want running text rather than a specimen sheet: Devanagari and Bengali conjuncts, Thai marks that stack above and below the line, Arabic and Perso-Arabic joining, polytonic Greek, and the Cherokee syllabary
- Accessibility and speech engineers, because every file declares a full BCP-47 language tag in its frontmatter, which is what screen readers and speech synthesisers switch voices on
- Developers of typesetting and document-conversion engines (Pandoc, Typst, LaTeX, EPUB toolchains) who want multi-script input to compile against, including the thirteen Japanese, Korean and Chinese books that declare `writing-mode: vertical-rl`
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
| Indo-European, Indo-Iranian | Devanagari | hi, mr | 4 |
| Indo-European, Indo-Iranian | Bengali | bn | 3 |
| Indo-European, Indo-Iranian | Gurmukhi | pa | 1 |
| Indo-European, Indo-Iranian | Gujarati | gu | 1 |
| Indo-European, Indo-Iranian | Odia | or | 1 |
| Indo-European, Indo-Iranian | Perso-Arabic | fa, ur | 6 |
| Indo-European, Celtic | Latin (with digraphs / accents) | cy, ga, gd | 5 |
| Indo-European, Old Norse | Latin (with þ ð) | is | 3 |
| Afro-Asiatic, Semitic | Hebrew | he | 3 |
| Afro-Asiatic, Semitic | Arabic | ar | 3 |
| Afro-Asiatic, Egyptian | Egyptian hieroglyphs | egy | 1 |
| Sino-Tibetan, Sinitic | Han (Simplified) | zh-Hans | 4 |
| Sino-Tibetan, Sinitic | Han (Traditional) | zh-Hant | 4 |
| Sino-Tibetan, Tibetic | Tibetan (Old Tibetan orthography) | bo | 1 |
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
| Dravidian | Telugu | te | 1 |
| Dravidian | Kannada | kn | 1 |
| Dravidian | Malayalam | ml | 1 |
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
| [Old Tibetan Documents Online](https://otdo.aa-ken.jp) | The *Old Tibetan Chronicle*, transcribed from the Dunhuang manuscript |
| [MDC-texts](https://github.com/rosmord/MDC-texts) | Book of the Dead spell 17 from the Papyrus of Ani, in Manuel de Codage, converted to Unicode hieroglyphs |

Each source has its own conventions (wikitext templates, Aozora's ruby annotations, Internet Archive's DjVu OCR, Ganjoor's per-poem API). The conversion scripts in `scripts/` know how to handle them. To add a new book:

1. Source the text from one of the upstream archives (see [CONTRIBUTING.md](CONTRIBUTING.md) for sourcing standards)
2. Run the appropriate conversion script (or write a new one for a source the scripts don't yet handle)
3. Verify with `python3 scripts/lint-corpus.py path/to/new-book.md`
4. Open a PR with the new file plus an entry in CORPUS.md

## Curation principles

This corpus is curated rather than exhaustive, and the curation follows five principles:

1. **Every work is unambiguously in the US public domain, and the edition it was transcribed from is named.** These are two separate questions and the corpus answers both.

   The *work* is public domain. Normally that follows from pre-1929 publication. One narrow documented class also qualifies: works transmitted in manuscript whose author died before 1855, where the US unpublished-works term (life plus 70 years) expired in the 19th century. Any such file states this basis in its own `source_note`. Currently two books use it: the ko court memoir 한중록, first printed 1939, and the bo *Old Tibetan Chronicle*, a Dunhuang scroll of the ninth or tenth century first printed in 1940.

   The *transmission base*, meaning the edition a transcription was actually made from, is pre-1929 for all but a handful of books. Where a later edition is what reached the corpus, the `year_note` or `source_note` says which one and why. This matters because a modern editor's transcription can carry an editorial layer of its own even when the work beneath it is free. The current exceptions:

   | Book | Work | Transmission base |
   |---|---|---|
   | `pl` Prus, *Kamizelka* | 1882 | *Pisma*, Gebethner i Wolff, 1935 |
   | `uk` Kotsiubynsky, *Тіні забутих предків* | 1912 | *Твори* vol. 2, Книгоспілка, New York, 1955 |
   | `mi` White, *Nga Kauhau Maori o Nehe* | 1887 | NZETC digitisation, 2001 to 2007 |
   | `sw` Mwana Kupona, *Utendi wa Mwana Kupona* | 1858 | Allen, *Tendi*, Heinemann, 1971 |
   | `te` Gurajada, *కన్యాశుల్కము* | 1909 | Kondapalli Veeravenkayya and Sons reprint, Rajahmundry, 1961 |
   | `or` Senapati, *ଛମାଣ ଆଠଗୁଣ୍ଠ* | 1902 | Srujanika and NIT Rourkela digital edition, 2013 |
   | `bo` *Old Tibetan Chronicle* | c. 900 (manuscript) | Old Tibetan Documents Online transcription, CC BY 4.0, revised in batches from 2018 to 2024 |
   | `egy` Book of the Dead, spell 17 | c. 1250 BCE (papyrus), Budge facsimile 1890 | Raymond Monfort's transcription in MDC-texts, CC BY (licence line added 2023) |

   The `pl`, `uk`, `mi`, `te` and `or` books reproduce an orthographic recension, a reprint or a plain digitisation of a text that is itself free, which carries no practical restriction. Three are scholarly transcriptions in which an editorial layer may genuinely subsist. The `sw` book is an edited transcription and is flagged in [QUALITY.md](QUALITY.md) for re-sourcing from Alice Werner's 1917 edition. The `bo` book is a diplomatic reading of the manuscript published by its scholars under CC BY 4.0, which permits redistribution with attribution; the attribution is in the file, and the corpus's CC0 dedication does not reach that layer. The `egy` book is the same case: Raymond Monfort's sign-by-sign transcription of Budge's facsimile, released CC BY.
2. **The selection is secular by default.** The sacred and liturgical texts of every religion are excluded alike, while folk tales, national epics, philosophical-skeptical works, and ethical wisdom literature are included as literary canon. The rule has two reasons: choosing a tradition's scripture is a decision that belongs inside that tradition, and sacred texts are the most digitised in most languages, so they would crowd out the literature the corpus exists to sample.

   A narrow exception admits a sacred, liturgical or cult text where neither reason applies, by one of two routes. Every other rule still holds (publication date or the manuscript exception, a named edition, a usable licence, real Unicode), and every book admitted this way carries a `sacred_text` field naming its route, so it can be filtered out in one line against `manifest.json` ([FRONTMATTER.md](FRONTMATTER.md)).

   - **`recovered-text`**: the work itself was lost to knowledge and is known only from excavation, from the rediscovery of a lost text, or from the decipherment of its script, so it did not come down through any community and admitting it pre-empts no tradition's choice. Ancient Egyptian and Sumerian cult texts qualify this way. Texts kept continuously in libraries and manuscript collections do not, however dead their language: the Old English gospels, the Old High German Tatian, the Old Irish homilies. Text erased and written over in a manuscript kept in a library counts as kept. Nor does a translation or version of a work that was copied without a break in any language qualify, even when its own manuscripts were excavated.
   - **`sole-witness`**: the text is in a script, identified by its ISO 15924 code, that no other book in the corpus represents, because no substantial secular text from before 1929 in that script is available in a form meeting these rules. It must be in a language natively written in that script and ships under that language's locale; a classical language in a borrowed script, such as Pali or Sanskrit in Sinhala or Burmese letters, does not qualify. The route admits at most one book per script. Where several sacred texts could serve, the corpus takes the one scholarship uses as the base text of the language's standard edition or grammar, so it does not choose among scriptures; a translation such as Wulfila's Gothic Bible is acceptable and names its translator in `translator`. The search behind the claim is recorded under [sources/](sources/), naming the locale and the script code in backticks. The test is judged at admission: if a usable secular text in that script appears later, the flagged book stays, and the change is noted in its record.

   The field marks admission by this exception, not religious themes. Devotional lyric (Gitanjali, Hafez), mythology (the Mabinogi), folk legend sung at shrines (*Koti Chennaya*) and the ritual pieces within collected oral literature (the karakia in *Ko Nga Moteatea*) are literature admitted under the normal rule and carry no flag. One book uses the exception so far: the `egy` Book of the Dead, spell 17, by the recovered-text route.
3. **Each locale carries two or three books**, mixing size and genre where sources permit.
4. **Canonical works are preferred over obscure ones.** Where the choice is between a niche author and a recognised one, the corpus leans canonical.
5. **Reference works are accepted** only when literary prose is not digitised in clean form. This currently applies to yo and chr, where the pre-1929 corpus is overwhelmingly missionary-religious in nature. Both locales have secular texts, so the sacred-text exception in principle 2 does not apply to them.

Every substitution from the originally-planned picks is documented in [CORPUS.md](CORPUS.md) for transparency.

## Academic use

This is a convenience corpus rather than a collection of critical editions. Before citing it in scholarship, you should know that:

- **Texts come from volunteer digitisation projects** (Wikisource, Project Gutenberg, Internet Archive OCR, and the archives credited below) and inherit those projects' transcription errors. OCR-sourced files carry documented noise; see per-file `source_note` fields and the caveats in [CORPUS.md](CORPUS.md). No text has been systematically collated against manuscripts or print editions; spot readings against page images are recorded in the notes.
- **Curation involved judgment calls**: which works count as canon, which edition to take, where to excerpt, how to attribute works with complex authorship. CORPUS.md records each locale's choices, substitutions, and known weaknesses.
- **AI models were used in building the corpus.** They helped find sources, convert the texts and repair errors, under my direction and on my responsibility. Changes beyond the repair of transcription slips are recorded in each book's `source_note`, and texts have not been modernised or normalised except where noted. Most texts haven't been checked in this corpus by someone who reads the language. [CORPUS.md](CORPUS.md) §How the texts were made describes the method.
- **Attribution of collected oral literature is hard.** Several works passed through colonial-era editors whose names appear on title pages while the source authors and informants went uncredited. Where scholarship identifies those authors, the frontmatter credits them, and these texts remain the cultural heritage of the communities they come from.
- **Year fields follow the cited source edition**, with `year_note` carrying nuance (manuscript versus print date, serial publication, composite works).

Corrections and new perspectives are welcome, especially from native speakers and subject specialists. Open an issue with the content-correction template or send a PR. I'd like to hear disagreement about a pick, an attribution or an edition.

### What's still needed

Four things would make this corpus easier to cite:

1. **An archival deposit with a persistent identifier.** Each release from v1.0.0 onwards is archived on Zenodo with a DOI, so a citation can point to a fixed version of the corpus rather than one that keeps changing.
2. **Stable per-book identifiers.** A book is currently identified by its path, so moving a file, for example after a re-attribution, breaks any citation to it. A fixed `uid` in each book's frontmatter would solve that.
3. **A stated editorial method.** [CORPUS.md](CORPUS.md) describes how the texts were made, including the use of AI models. It doesn't yet record, for each book, how it was checked and whether someone who reads its language has seen it.
4. **Structural encoding.** Verse lines, speakers, page breaks and a critical apparatus would need TEI rather than Markdown. That's a different project, and I don't plan to take it on.

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
├── .zenodo.json           # deposit metadata Zenodo reads when a release is archived
├── LICENSE                # CC0 1.0 legal text (content)
├── audits/                # dated records of full-corpus review passes
│   ├── README.md          # why they are kept and when a pass happens
│   └── 2026-07-25.md
├── sources/               # qualification records for upstream sources, per acquisition
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

Pin a tag rather than a bare commit. Tags are named `wave-YYYY-MM-DD` after the editing wave they close, and they mark a corpus that has been reviewed end to end. Ordinary commits on `main` do not carry that guarantee, because a wave lands its edits across several commits. Published releases carry a separate `v<major>.<minor>.<patch>` tag and an archival DOI on Zenodo, and the two schemes do not collide. The first release is `v1.0.0`.

Paths (`books/<locale>/<author>/<title>.md`) are the identity of a book. There is no separate stable ID, and `manifest.json` keys on the path. Renames are rare and happen when a re-attribution or a source correction makes the old path wrong. When one happens it lands in a commit of its own, with no content edit riding along, so that `git diff --find-renames --diff-filter=R <old-tag> <new-tag> -- books` reports the mapping exactly. Consumers keyed on paths should run that diff when they move a pin.

Rendering problems found in a book (frontmatter that does not parse, structure that does not survive a round trip, hard breaks that vanish) belong in this tracker as a content-correction issue. Name the book path and the tag you found it at, and describe what the renderer received rather than which renderer received it.

## Other relevant projects

- [`mlschmitt/classic-books-markdown`](https://github.com/mlschmitt/classic-books-markdown) collects English-only public-domain literary classics. This corpus covers the languages that that project does not, so the two repos work well together.

If you find another similar project, please open an issue and I'll add it.

## Citation

If this corpus contributes to your work, please cite it. The repository carries a [`CITATION.cff`](CITATION.cff) file for academic citation generation; most reference managers and academic platforms (Zotero, Mendeley, Zenodo, GitHub itself) pick it up automatically.

```
Powell, S. multilingual-classics-markdown: Public-domain literary classics
in 54 languages [Software]. GitHub. https://github.com/tideswellgroup/multilingual-classics-markdown
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
- **africanpoems.net** for the text of Mwana Kupona's *Utendi*
- **Old Tibetan Documents Online** (ILCAA, Tokyo University of Foreign Studies) for the transcription of the *Old Tibetan Chronicle*, under CC BY 4.0
- **Raymond Monfort** for the transcription of the Book of the Dead, spell 17, published in **Serge Rosmorduc**'s MDC-texts, under CC BY
- **Srujanika** and the **National Institute of Technology, Rourkela**, for the Odia digital edition of *Chha Mana Atha Guntha*
- **Matt Schmitt** for `classic-books-markdown`, which motivated and informed this work
- The countless authors, editors, and translators whose work is in these files

The corpus was built with the help of AI models: Claude (Anthropic), Gemini (Google), ChatGPT (OpenAI) and Mistral (Mistral AI).

## License

The license comes in two parts:

- **Content** (everything under `books/`) is released under [CC0 1.0 Universal](LICENSE-CONTENT.md). All texts are public domain in the United States, and the CC0 declaration removes any residual ambiguity for downstream users.
- **Tooling** (everything under `scripts/`) is under the [MIT License](LICENSE-CODE.md).

See the individual license files for full terms.

## Contributing

New locales, new books in existing locales, and improvements to the conversion scripts are all welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for sourcing standards, conversion expectations, and the PR checklist.

Contributions I would especially welcome:

- **Checking a book against its source, if you read its language.** Most books have only been checked by scripts and AI models. [QUALITY.md](QUALITY.md) lists the books where this is most needed and how to go about it.
- **Locales not yet covered**: Sinhala, Burmese, Khmer and Lao (investigated in October 2026 and left open for want of a qualifying text; see CORPUS.md), further Slavic Latin variants beyond Polish and Czech, Mongolian, Inuktitut, Coptic, Ottoman Turkish (ota), more African languages beyond Swahili and Yoruba, and English variants with pre-1929 founding literatures (Ghana via Casely Hayford, the Philippines via Galang)
- **Two famous transcription gaps**: Anne Bradstreet's *The Tenth Muse* (1650) survives online only as black-letter page images, and Claude McKay's *Songs of Jamaica* (1912) is untranscribed; clean transcriptions of either would let the corpus carry them
- **Better picks for locales carrying substitutions**: Premchand in Urdu (the corpus currently has Ghalib, Iqbal, and Mir Taqi Mir; I'd love a clean Premchand-Urdu source), Akinyele's *Iwe Itan Ibadan* if it ever surfaces in clean form, secular pre-1929 Amharic literature
- **Conversion-script improvements** for sources handled clumsily today (OCR cleanup for IA djvu, better Wikisource ProofreadPage transclusion walking)
- ***Ka Moolelo o Hiiakaikapoliopele*** in Hawaiian: the 1905-06 serial lives in the nupepa/ulukau newspaper archives rather than Internet Archive; a contributor with access could bring the great Hiiaka epic here

## Status

This is a v1 release. Expected updates include occasional book additions, source-URL refreshes when upstreams move, and conversion-script additions and improvements.
