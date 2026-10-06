# Source qualification: Ancient Egyptian and Sumerian

Two qualification passes made on 2026-10-04 for the first texts in Ancient Egyptian hieroglyphs (`egy`) and Sumerian cuneiform (`sux`). Both languages' surviving texts are largely funerary or cultic, so the maintainer exempted them from the secular rule; the corpus's sacred-text exception (README curation principle 2, route recovered-text) now covers them in general. Everything else in the corpus's rules applied: a named pre-1929 edition or the object itself as the base, a licence that permits redistribution, and real Unicode text. A stock Mac failing to render the result was ruled not to be a stop, provided it renders correctly somewhere.

Method as in [2026-10-04-coverage-push.md](2026-10-04-coverage-push.md): licence first, then access, then usability. Licence terms are quoted verbatim; interpretations are labelled. Last verified for every entry: 2026-10-04; the egy entry re-examined 2026-10-06.

## Ancient Egyptian (`egy`), script `Egyp`

| Candidate | Base | Licence | Form | Verdict |
|---|---|---|---|---|
| Book of the Dead spell 17, Papyrus of Ani, transcribed by Raymond Monfort (MDC-texts) | Budge's facsimile (1890) with photographs | "Licence : Creative commons CC-BY" in the file | Manuel de Codage; conversion ours | **Adopted** 2026-10-04 (Ani columns only); **withdrawn from main** 2026-10-06, still in v1.0.0 |
| Autobiography of Ahmose son of Abana, Urk. IV 1 (Mark-Jan Nederhof, St Andrews) | Sethe, *Urkunden der 18. Dynastie* (1927) | None stated for the text; GPL-3.0 on the code repository | Unicode with full layout | **Defer**: no licence stated for the text |
| Sethe, *Aegyptische Lesestuecke* no. 7, typed by Serge Rosmorduc | Sethe 1924 | CC BY in the file | Manuel de Codage | Reference: clean, but medical and magical recipes, and two conversions disagree on about 95 signs |
| Israel Stela | Petrie's plates (1897) | CC BY | Manuel de Codage | Defer: two lines carry corrections from a post-1929 edition |
| Thesaurus Linguae Aegyptiae data | modern | CC BY-SA | no layout | Reject: whole texts cannot be rebuilt from it; its site also serves crawlers decoy records and must not be scraped |
| Sinuhe, Shipwrecked Sailor, Eloquent Peasant (Nederhof) | editions of 1932 and later | various | Unicode | Reject: post-1929 bases; the originals are hieratic |

**The adopted text.** `texts/Book of the dead Chapter 17.gly` in Serge Rosmorduc's MDC-texts (https://github.com/rosmord/MDC-texts), added in 2022 and last changed 2023-06-27. Verbatim from the file: "transcrit par Monfort Raymond", "Licence : Creative commons CC-BY", "Chapitre 17 issu des colonnes 1 à 145 du Papyrus d'Any correspondant aux planches VII à X, complétées par les colonnes 16 à 52 du Papryrus de Nebseny", "Ref: Budge Pap. Ani et collations sur photos". The collection's README: "Regarding the Licenses for the texts in this archive, when a clear license is available, it will be included in the text itself", with CC BY 2.0 linked as its example. The Nebseny columns name no source edition and are not used.

**The conversion and its licences.** The text is in JSesh's Manuel de Codage, not Unicode, so the corpus converts it (`scripts/convert-mdc-hieroglyphs.py`). The sign mappings were chosen for their licences:

- Unicode's Unikemet database (UCD 18.0.0) maps 3,862 JSesh sign codes to code points in its kEH_JSesh field, under the Unicode licence, which permits redistribution with its notice. It ships as `scripts/data/egyptian-jsesh-codes.tsv`. It covers 28 percent of this text's sign tokens, because the rest are typed in JSesh's phonetic shorthand.
- JSesh's own phonetic-code table is in its `signs_description.xml`, under the CeCILL licence (copyleft, GPL-compatible); not copied.
- Mark-Jan Nederhof's hieropy, which converts Manuel de Codage to Unicode, is GPL-3.0; not shipped, and not a dependency. It was run outside the repository as an independent check.
- The phonetic table (126 codes) was written for the converter from the phonetic values of Gardiner's sign list (*Egyptian Grammar*, 1927, public domain). Compared with hieropy, 116 entries agreed at once; the other ten (three read differently, six left open, one added later) were resolved to agree with hieropy, whose tables follow JSesh, the editor the transcriber typed into.

Compared line by line, 153 of 157 converted lines are identical to hieropy's; three differ only at three non-core signs (U+13C26, U+13DDB, U+1419B), which hieropy and NewGardiner leave out by design, and one only in segment marks around a bracketed stack. Ten signs (E5A, F51B, G20A, G20B, G234, G248, N33Av, P67, R31, V87; nineteen occurrences) have no Unicode mapping identified and stand as their sign numbers in braces. A first draft matched F51B and G20A to Unicode characters by name alone; review showed those are different signs (JSesh's F51B is one piece of flesh, Unicode's F051B three), so lookup by name is now allowed only for checked cases.

**Rendering (revised 2026-10-06).** NewGardiner is used by its author's layout software, hierojax and hieropy; its companion font NewGardinerOmni does the layout itself, and NewGardinerOmni2d4 laid out a test line as expected in HarfBuzz 14.5.0. Egyptian Text does not include 34 of the signs this spell uses, and its open licence covers its layout logic rather than the whole font. Testing continues.

**Encoding (2026-10-06).** Most rotated signs are encoded with variation sequences that Unicode does not standardize, and three signs are non-core signs that the fonts tested leave out. The book was withdrawn from main on 2026-10-06 for revision and remains in v1.0.0.

**Rebuild source.** https://raw.githubusercontent.com/rosmord/MDC-texts/98bcf846a7/texts/Book%20of%20the%20dead%20Chapter%2017.gly, SHA-256 7184c26acbf2e4ff20d5df40d520a7f65454cb25d988076fcfd3fea6b10ce6fa, converted with `python3 scripts/convert-mdc-hieroglyphs.py --source <file> --frontmatter <file> --output <file>`, the curated frontmatter taken from the book at v1.0.0 (`git show v1.0.0:"books/egy/Anonymous/Book of the Dead, spell 17.md"`). The converter's rotation mapping has to be fixed first.

**Pending.** Ahmose, a secular autobiography based on Sethe's 1927 edition, would become an egy book if its encoding can be licensed.

## Sumerian (`sux`), script `Xsux`

| Candidate | Base | Licence | Form | Verdict |
|---|---|---|---|---|
| Gudea Cylinders A and B, ORACC ETCSRI Q000377, cuneified | composite by Zólyomi and others, keyed to Edzard, RIME 3/1 (1997) | "Content released under a CC BY-SA 3.0 licence" | Unicode cuneiform from ORACC's conversion | **Defer**: share-alike licence |
| Thureau-Dangin, *Les cylindres de Goudéa* (1905) and TCL 8 (1925) | pre-1929 editions | public domain | transliteration and hand copies in scans | Defer: about 1,370 lines to re-key and convert |
| CDLI P431881, P431882 | Edzard 1997 | CDLI terms of use, not a standard licence | ATF only | Defer |
| ETCSL | modern | all rights reserved | transliteration | Reference |
| SumTablets (Hugging Face) | ORACC | claims CC BY over share-alike material | | Reference |
| CC0 Sumerian King List dataset | built on ETCSL | | | Reject |

ORACC's licensing page (https://oracc.museum.upenn.edu/doc/about/licensing/) says its conditions may be waived; a waiver of the share-alike condition would be needed for Q000377. Rendering is not an obstacle: macOS ships Noto Sans Cuneiform and falls back to it, Windows has Segoe UI Historic, and cuneiform needs no complex shaping. Three signs in the ORACC text are private-use code points that would be replaced and disclosed; 63 signs are editorial restorations that would stay marked.
