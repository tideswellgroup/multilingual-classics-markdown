# Changelog

What arrived, what was replaced, and what was revised, per release.

Entries correspond to tags. `wave-YYYY-MM-DD` tags mark editing waves and are the safe points to pin (see [README](README.md#pinning-this-corpus)). Version tags mark published releases.

The inventory in each entry is generated rather than remembered:

```sh
python3 scripts/changelog-entry.py <previous-tag> <new-tag>
```

Counts inside an entry describe the corpus as it stood at that release and are not updated afterwards.

## Unreleased

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
