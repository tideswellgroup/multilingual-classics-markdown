# Audits

This directory holds dated records of full-corpus review passes. Each file `YYYY-MM-DD.md` contains review findings, severity, and resolution.

## Why they are kept

[QUALITY.md](../QUALITY.md) is a live ledger of "what is wrong with this corpus today", and should be read first. These records answer a different question, which is how anyone knows that: this list shows the sampling that was done, the books that came back clean, the severities as they were assigned before anything was fixed, and the claims that were checked and turned out to be wrong.

They are also cited. Several QUALITY.md entries and at least one book's `source_note` point at a specific audit for the detail behind a disclosure, so these files are part of the corpus's provenance chain rather than commentary alongside it.

## When a pass happens

An audit pass is run when the corpus has changed enough to be worth re-checking as a whole, usually when:

- a batch of new books or a new locale has landed
- a conversion script has changed in a way that affects files already converted
- a corpus-wide convention has been introduced or revised, such as the verse hard-break rule or the single-title heading rule
- a re-sourcing or re-OCR wave has replaced text in place

To ensure consistency carries across the corpus, it's run against all files rather than only those that have changed. Most of what these passes find is not damage in the new material, but older material drifting out of line with a convention that has been introduced since they were created.

## How a pass is run

Two lenses are applied per book. A reading lens for content integrity, looking for garbled text, truncation, wrong language, page furniture left in the text, and broken chapter sequences. This is followed by an engineering lens for markdown validity and frontmatter usefulness. Under both, a scripted mechanical sweep runs first over every file, and the reading passes sample openings, endings, interior windows and chapter seams, with full reads for short books. The method is described in [QUALITY.md](../QUALITY.md#how-to-audit-a-book).

For better or worse, the reading passes are made by a language model working from the files (personally, I think it's for the better). These passes are very good at finding structural and mechanical damage that survives conversion, **but** they are of course not a fluent reader of the language. Several books in this corpus are waiting on a native-speaker read, and an audit reporting no findings against one of them does not discharge that. Findings are treated as leads until they are checked against the file, and the record marks which were verified and which were refuted.

## Reading a record

A record is closed once its findings are dispositioned. Items are fixed, accepted as source-faithful, refuted, or deferred with a reason, and the disposition is written into the same file. After that the file is not revised, apart from a status banner at the top noting that the work is done. A later pass gets its own dated file rather than edits to an older one, so the history stays legible.

Anything still open at the end of a pass moves to QUALITY.md, which is where it is tracked from then on. If a finding here contradicts QUALITY.md, QUALITY.md is right and this file is out of date.
