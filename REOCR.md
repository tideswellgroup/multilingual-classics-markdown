# The re-OCR pipeline

How the corpus re-runs optical character recognition for books whose only
digital source is a scan, why it exists, and what it changed. Companion to
[QUALITY.md](QUALITY.md); the per-book outcomes land in the results table at
the bottom as each book completes.

## Why it exists: the Amharic discovery

The corpus took several books from Internet Archive `djvu.txt` derives on
the assumption that they represented the best machine reading of the scans.
For the Cherokee *Constitution and Laws* (1892), a reader review found the
text unreliable from the first line, and the item's own metadata explained
why:

```
ocr: tesseract 5.3.0-1-gd3a4
ocr_detected_lang: am        (confidence 1.0000)
ocr_detected_script: Latin   (confidence 0.9648)
```

The Archive's pipeline had auto-detected a Cherokee-syllabary book as
Amharic in Latin script, with full confidence, and OCR'd it accordingly.
The Cherokee model that Tesseract itself ships was never invoked. A
thirty-second local rerun with `tesseract -l chr` produced structurally real
Cherokee where the derive had produced gibberish.

The general lesson is now part of the audit method: when the OCR itself is
the defect, re-run the OCR properly before asking humans to fix its output.
An upstream derive is only a convenience; its language detection fails
silently, and it fails most confidently on the low-resource scripts this
corpus cares about.

## The pipeline

Per book, all stages cached locally under `scans/` (gitignored: bulky,
refetchable, and never part of the published corpus):

1. **Fetch the scan archive once.** Internet Archive items carry a `_jp2.zip`
   with every page; one download replaces hundreds of page requests. The
   cache is kept so future passes never refetch.
2. **Decode to page images.** `opj_decompress` (OpenJPEG) to grayscale PNG
   for Tesseract; a JPEG derivative for the Vision payload limits.
3. **Engine one: Tesseract 5** with the *correct* language model
   (`tessdata_best`), explicitly selected, never auto-detected.
4. **Engine two: Google Cloud Vision** `DOCUMENT_TEXT_DETECTION` with the
   matching language hint. Runs via a maintainer-side script kept in the
   local cache (it needs private credentials and non-stdlib packages, which
   the repo's contributor tooling rules exclude); its per-page text outputs
   are cached alongside the images.
5. **Agreement analysis.** The two engines are independent systems with
   different failure modes. Agreement between them is therefore a confidence
   signal that requires no fluent reader: where independent engines concur,
   the reading is probably right; where they diverge, the line is flagged.
   This converts "unreliable throughout" into a measured, per-line
   reliability map. The metric is deliberately computed per body line
   rather than per page: a single blended character ratio over a whole page is
   dragged down by editorial apparatus (German footnotes in Velten, English
   glosses in the Yoruba books) and page furniture, which the two engines
   handle differently. `scripts/reocr_common.py` instead takes each
   primary-language body line and scores it against its best-matching line
   on the other engine's page (line-to-best-line, which tolerates the
   engines' minor systematic differences such as romanisation variants),
   then reports the fraction of body lines both engines read identically
   and the count that diverge. The headline is that fraction; the flagged
   lines are the reviewer's worklist.
6. **Assembly** by a committed, stdlib-only converter per book: structural
   conventions applied (headings recovered where the print had them, verse
   hard breaks), the provenance excision rule from QUALITY.md observed, and
   the engine-agreement statistics written into the book's `source_note` and
   the results table below.

## What agreement does and does not claim

Two-engine agreement is evidence rather than verification. Both engines can
misread the same damaged glyph the same way, and neither knows the language.
The honest claim is narrower: agreement measures where machine reading is
stable, and instability reliably marks trouble. A fluent reader remains
the only verification, and the per-line divergence map is what makes a human
review session efficient: check the flagged lines first.

## Results

Campaign status (2026-07-25): of the eight OCR-derived books evaluated, six were rebuilt from the pipeline and shipped (chr, sw Velten, es-MX Tomóchic, mi Nga Mahinga, io Nova Horizonti, yo Crowther); Dennett was assessed and its current text kept (no subdot letters to recover); yo Bowen needs a Yoruba reader (the engines diverge on its archaic orthography, though the re-OCR does recover its diacritics). Google Vision was the cleaner base engine in every case measured.


Agreement is the refined body-line metric: the fraction of primary-language
body lines both engines read identically (see the method above).

| Book | Old text | New pipeline | Body-line agreement | Outcome |
|---|---|---|---|---|
| sw Velten *Safari za Wasuaheli* | IA derive, systematic u-as-n on nearly every word | Tesseract `swa` + Vision `swa` | **99%** (117 of 8,496 lines flagged) | Rebuilt and shipped. `text_quality: noisy`. The u-as-n corruption is gone; the two engines agree on nearly all the Swahili body. |
| chr *Constitution* | IA derive, misdetected as Amharic in Latin script | Tesseract `chr` + Vision `chr` | **89%** (1,031 of 9,461 lines flagged) | Rebuilt and shipped. `text_quality: alpha`. Right script, coherent Cherokee, 790 article headings recovered, but visibly imperfect: a disclosed provisional text rather than a clean edition. |
| yo Bowen *Yoruba Proverbs* | IA derive, diacritics destroyed | pipeline `yor`, proverb pages 56-63 | 76% overall, but the flagged lines are the Yoruba proverb text itself | Not rebuilt. The re-OCR recovers the subdot vowels and tone marks the old text lost, but the two engines diverge on Bowen's archaic orthography where it matters most. This confirms the standing verdict that the book needs a Yoruba reader, who now has better raw material. Flag stays. |
| es-MX *Tomóchic* | IA derive of the 1906 scan | pipeline over the 1911 Michigan scan, Vision base | **97%** (244 of 8,339 lines flagged) | Rebuilt and shipped. `text_quality: noisy`. Chapter V and the heading structure recovered; base engine auto-picked as Vision. |
| yo Crowther *Vocabulary* | IA derive, diacritics destroyed | pipeline `yor`, Vision base | **93%** (546 of 8,896 lines flagged) | Rebuilt and shipped. `text_quality: noisy`. Entry-based assembly (bolded headwords); the subdot vowels and tone marks the old OCR destroyed are recovered. |
| yo Dennett *My Yoruba Alphabet* | IA derive | pipeline `yor`, Vision base | 77% (256 of 1,125 lines flagged) | Assessed and not adopted. The primer is predominantly English and its author deliberately avoids subdot letters, so the diacritic recovery that justifies the other yo re-OCRs does not apply; the re-OCR was not a clear improvement over the current text and was not shipped. |
| mi *Nga Mahinga* | IA derive | pipeline `mri`, Vision base | **99%** (54 of 6,507 lines flagged) | Rebuilt and shipped. `text_quality: noisy`. Nine-story Part-I excerpt preserved. |
| io *Nova Horizonti* | IA derive | pipeline `epo` hint, Vision base | **99%** (24 of 4,023 lines flagged) | Rebuilt and shipped. `text_quality: noisy`. Article headings recovered (the old file was flat). |
