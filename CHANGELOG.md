# Changelog

What arrived, what was replaced, and what was revised, per release.

Entries correspond to tags. `wave-YYYY-MM-DD` tags mark editing waves and are the safe points to pin (see [README](README.md#pinning-this-corpus)). Version tags mark published releases.

The inventory in each entry is generated rather than remembered:

```sh
python3 scripts/changelog-entry.py <previous-tag> <new-tag>
```

Counts inside an entry describe the corpus as it stood at that release and are not updated afterwards.

## v1.0.1

v1.0.1 differs from v1.0.0 in one book: the Ancient Egyptian Book of the Dead, spell 17, has been withdrawn for revision of its encoding, and remains available in v1.0.0. The corpus now has 145 books in 66 locales. The dataset is retitled "multilingual-classics-markdown: Public-domain literary classics in their original languages, curated as markdown with YAML frontmatter", and the citation files give the concept DOI.

## wave-2026-10-06

146 books in 67 locales, to 145 books in 66.

### Removed (1)

- **egy**: Anonymous, *Book of the Dead, spell 17 (Papyrus of Ani)*

Locales no longer present: egy

The Book of the Dead is withdrawn for revision of its encoding. It remains in v1.0.0 and wave-2026-10-05, and its rendering notes in the sources record are revised. The dataset title no longer carries a language count. Since wave-2026-10-05 the repository has also gained its Zenodo DOI, a check that documentation tables render whole, and links to Discussions.

## v1.0.0

The first published release, archived on Zenodo with a DOI. The corpus is unchanged from wave-2026-10-05: 146 books in 67 locales. Since that wave, LICENSE has been reduced to the CC0 legal text so that GitHub detects it, a README table that split when rendered has been repaired, and a lint step now catches that fault.

## wave-2026-10-05

145 books in 66 locales, to 146 books in 67.

### New locales (1)

- **egy**: Anonymous, *Book of the Dead, spell 17 (Papyrus of Ani)*

Ancient Egyptian arrives with spell 17 of the Book of the Dead as it stands in the Papyrus of Ani, in Unicode hieroglyphs. The text is Raymond Monfort's CC BY transcription of Budge's 1890 facsimile, which a new converter turns from JSesh's Manuel de Codage into Unicode, checked line by line against an independent converter. Ten signs with no Unicode mapping identified are written as their sign numbers in braces, and the rubrics' red ink isn't represented. Reading it needs a font such as NewGardiner.

### Curation rules

The secular rule now has a narrow exception, set out in the README's curation principle 2. A sacred text can be admitted if the work was lost and is known only from excavation, rediscovery or decipherment, or if it's the one standard text in a script the corpus can't otherwise carry. Books admitted this way carry a `sacred_text` field, and the linter checks that each one documents its route. The Book of the Dead is the first.

### Method

CORPUS.md now says how the texts were made, including the use of AI models, and that most texts haven't been checked in this corpus by someone who reads the language. The README's "Academic use" section, its contributing list and the Zenodo, Croissant and CITATION.cff descriptions say the same, and ask readers of these languages to check a book against its source.

## wave-2026-10-04

137 books in 58 locales, to 145 books in 66.

### New locales (8)

- **bo**: Anonymous, *Old Tibetan Chronicle*
- **gu**: ગોવર્ધનરામ માધવરામ ત્રિપાઠી, *સરસ્વતીચંદ્ર, ભાગ ૧* (Sarasvatichandra, Part 1)
- **kn**: ಪಂಜೆ ಮಂಗೇಶರಾವ್, *ಕೋಟಿ ಚೆನ್ನಯ* (Koti and Chennaya)
- **ml**: ഒ. ചന്തുമേനോൻ, *ഇന്ദുലേഖ* (Indulekha)
- **mr**: हरि नारायण आपटे, *स्फुट गोष्टी भाग ४ था* (Miscellaneous Stories, Part 4)
- **or**: ଫକୀର ମୋହନ ସେନାପତି, *ଛମାଣ ଆଠଗୁଣ୍ଠ* (Six Acres and a Third)
- **pa**: ਸ਼ਾਹ ਮੁਹੰਮਦ, *ਜੰਗਨਾਮਾ* (The Book of the War)
- **te**: గురజాడ వేంకట అప్పారావు, *కన్యాశుల్కము* (The Bride-Price)

Eight wishlist locales arrive with one book each, and seven new script systems with them: Gurmukhi, Gujarati, Odia, Telugu, Kannada, Malayalam and Tibetan (Marathi is the corpus's second Devanagari language). Each candidate was qualified before it was fetched; [sources/2026-10-04-coverage-push.md](sources/2026-10-04-coverage-push.md) records the picks, the books passed over and why, and why Sinhala, Burmese, Khmer and Lao stay open for now.

Every text was checked to be Unicode in its own script rather than a legacy font encoding, and each book's source_note records how. Several transcriptions carried systematic faults, which are repaired as counted classes and disclosed: Gujarati digits typed for the letters they resemble, an Odia conjunct mis-mapped from the digital edition's font, Malayalam old-font digit letters, and a Kannada digit for the anusvara. The Punjabi *Jangnama* is rebuilt into its four-line stanzas from the 1904 printing's danda marks, with seven slips corrected against the page images. The *Old Tibetan Chronicle* is the corpus's second book under the manuscript-works exception and its second with a scholarly layer it does not own, a CC BY 4.0 transcription from Old Tibetan Documents Online; the README and LICENSE-CONTENT.md say so. Open flags for the gu, pa, or and kn books are in QUALITY.md.

### Tooling

The bn ProofreadPage walker now serves any Wikisource, with new behaviour behind options so the Bengali books rebuild unchanged, and five book-specific converters build on it. `scripts/rebuild-2026-10-books.sh` records the exact command for each new book.


## wave-2026-09-07

137 books in 58 locales, to 137 books in 58.

### Revised text (7 books)

es-MX (1), mi (1), no (1), sw (1), ta (1), tr (1), yo (1)

A strict-YAML frontmatter pass and a Markdown-residue sweep from the 2026-08-04 audit. Three frontmatter values that broke strict YAML are now quoted: colons in the mi and tr source notes, and `language: no` parsing as boolean false. Linter rules FM005 and FM006 were added so the class cannot recur. Body residue: the yo *Vocabulary of the Yoruba Language*'s 39 stray backticks became apostrophes, the es-MX *Tomóchic*'s two stray backticks were removed, and the ta *National Songs*' small-tag pair was removed. Each body change is disclosed in its book's source note; the full account is in QUALITY.md's resolved log.

The sw *Safari za Wasuaheli* takes nine single-character OCR repairs (as-5ubuhi, a$-subuhi, n4, y4, m4'ana, t4laga), each accepted only where the repaired form is attested in the file itself often enough to be the evidence. The period orthography and the nus$ family are deliberately untouched, and the fluent read that closes the book's QUALITY.md flag is still owed.

### Deposit and tooling

`.zenodo.json` carries the description Zenodo reads at release time, count-checked and JSON-gated in CI. The README adds a Croissant badge and three audience bullets. `lint-corpus.py` gains the two frontmatter rules above.

## wave-2026-08-03

134 books in 55 locales, to 137 books in 58.

### Licensing and provenance

The CC0 dedication was rescoped so it no longer claims rights the repository does not hold, and the public-domain rule in the README now separates a work's copyright status from that of the edition it was transcribed from, with the four books whose transmission base postdates 1928 named explicitly. A root `LICENSE` file carrying the CC0 legal text was added so automated license detection reports the content license. `manifest.schema.json` now exists and is validated in CI by `scripts/check-manifest-schema.py`; the manifest had declared a `$schema` reference to a file that was never written.

### Discoverability and tooling

`croissant.json` describes the corpus in the MLCommons Croissant format, which is what Google Dataset Search and the major dataset hubs read; it validates against the `mlcroissant` reference implementation and is JSON-checked in CI. The README gained a fidelity row, a three-way "choose your path" block, license badges and the clone size, and its pinning section no longer describes release tags and a DOI that do not exist. The scholarly-limitations section now states the four things that would make the corpus properly citable, including the one that is out of scope.

`scripts/lint-corpus.py` reported long-line warnings using body-relative line numbers, so the number it printed did not match the file; it now counts the frontmatter. The one book that trips the warning, the it *Decameron*, was checked against its source: the Ciappelletto novella really is a single 25,000-character paragraph in the it.wikisource transclusion, so the structure is faithful and the file now says so in its `source_note` to stop a future editor from "correcting" it.

### New locales (1)

- **la**: Publius Vergilius Maro, *Aeneis*

Latin arrives as the 43rd language and the corpus's first Italic one, with the whole *Aeneid*: twelve books and 9,895 canonically numbered verses, from the la.wikisource transcription of Greenough's 1900 Ginn edition. Every book was checked against its canonical line count before conversion was allowed to write, and the converter still refuses to emit a file if any book comes up short. The canonical total is 9,896. The one departure is Liber X, where Greenough brackets 10.872 as a suspected interpolation and the transcription drops it; the numbering around it stays canonical. A four-line pre-proem numbered A to D sits outside that count, so the file holds 9,899 lines of verse in all. The book ships with an open flag: Liber I writes consonantal v and Libri II-XII write u, an inconsistency inherited from the source and left rather than guessed at.

### New locales (2)

- **no**: Knut Hamsun, *Markens grøde* (1917)
- **el**: Αλέξανδρος Παπαδιαμάντης, *Διηγήματα*, six polytonic stories

Modern Greek was absent until now, and the coverage matrix reported a Greek book that was actually Ancient Greek. Both are now real locales with polytonic texts.

### Corrected

- **grc**: Plato, *Ἀπολογία Σωκράτους* moves from `el` to `grc`. The text is Attic Greek and was filed as Modern Greek, so the corpus reported Greek coverage it did not have.

### Revised text (19 books)

ang (1), ar (1), chr (1), en-JM (1), enm (1), es-MX (1), gd (1), ko (4), mi (2), pl (1), sw (2), vi (1), yo (2)

Frontmatter text update.

## wave-2026-07-26

134 books in 55 locales, unchanged in size. A quality wave rather than a growth one.

Every LOW and COSMETIC finding from the 2026-07-25 sanity pass was dispositioned, and the single-title heading convention was settled and applied: a division carries its title once, as its heading. Five readings inherited from upstream transcriptions were emended with named disclosures, and the record of what was fixed, accepted, refuted or deferred is in [audits/2026-07-25.md](audits/2026-07-25.md).

### Revised text (34 books)

cy (2), en-AU (1), en-CA (1), en-IN (2), en-JM (1), es-ES (2), es-MX (2), fr-FR (2), he (2), hi (2), it (1), ko (2), mi (1), pl (1), pt-BR (1), pt-PT (3), ru (1), sw (2), ta (1), uk (1), ur (2), vi (1)

Notable among them: the Bécquer anthology had 120 headings and named none of its works, so its titles are now headings; both fr-FR novels lost their duplicated chapter titles under the new convention; and two ko books had their `writing-mode` values unquoted after a consumer's string match found 11 of the 13 books that declare it.

## wave-2026-07-25

115 books in 50 locales, to 134 books in 55.

The largest wave since v1.1. Five locales arrived, twelve books joined existing locales, and a two-engine re-OCR pipeline rebuilt five books whose text had been degraded by their original scans.

### New locales (5)

- **cs**: Božena Němcová, *Babička*; Karel Čapek, *R.U.R.*
- **nl**: Frederik van Eeden, *De kleine Johannes*; Multatuli, *Max Havelaar*
- **sv**: August Strindberg, *Röda rummet*; Selma Lagerlöf, *Bannlyst*
- **tr**: Ömer Seyfettin, *Seçme Hikâyeler*
- **uk**: Леся Українка, *Лісова пісня*; Михайло Коцюбинський, *Тіні забутих предків*; Тарас Шевченко, *Кобзарь*

### New books in existing locales (12)

- **chr**: ᏣᎳᎩ ᎠᏰᎵ ᏙᏥᎳᏫᎥ, *ᎦᎫᏍᏛᏗ ᎠᏂᏣᎳᎩ ᎤᏂᎲᎢ* (Constitution of the Cherokee Nation)
- **en-CA**: E. Pauline Johnson, *Flint and Feather*; Stephen Leacock, *Sunshine Sketches of a Little Town*
- **es-MX**: Ignacio Manuel Altamirano, *El Zarco*
- **fr-CA**: Laure Conan, *Angéline de Montbrun*
- **io**: Otto Jespersen, *Historio di nia linguo*
- **it**: Carlo Collodi, *Le avventure di Pinocchio*; Giacomo Leopardi, *I Canti*
- **mi**: Various tribal narrators (John White, ed.), *Nga Kauhau Maori o Nehe*
- **sw**: Edward Steere, *Swahili Tales*; Mzee bin 'Ali bin Kidogo bin il-Qadiri, *Sha'iri la Makunganya*
- **vo**: Various, *Penäds se Volapükagaseds*

### Replaced

Three books were withdrawn in favour of better sources: the Volapük *Volaspodel*, degraded beyond repair, gave way to an anthology of 268 hand-typed gazette pieces; the Cherokee book was narrowed from *Constitution and Laws* to the 1839 Constitution alone; and the Māori *Ko Nga Moteatea* was re-attributed from George Grey to its actual composers.

## v1.1

78 books in 32 locales, to 115 books in 50.

Eighteen locales arrived at once, including the historical stages of English (`ang`, `enm`, `sco`), Bengali, Hebrew, Hawaiian, Māori and Cherokee. This release also introduced the corpus-wide verse convention, which retrofitted two-space hard breaks across every book carrying verse after a review found poems rendering as prose walls.

## v1.0

The initial release, 2026-07-14. 78 books across 32 locales, with the frontmatter provenance layer, the conversion scripts, and the curation principles that still govern what the corpus accepts.
