# Content license

Every **work** under `books/` is **public domain in the United States** under current copyright law. In almost every case that follows from publication before January 1, 1929, and where applicable the original author has been dead at least 70 years. Two narrow classes are documented rather than assumed, and both are set out in the README under Curation principles: works transmitted in manuscript whose author died before 1855, and works whose text reaches the corpus through an edition later than 1928.

To remove any residual ambiguity for downstream users, this repository releases the **content collection** (the curation, arrangement, frontmatter metadata, and the markdown rendition of each work) under the **CC0 1.0 Universal Public Domain Dedication**.

## CC0 1.0 Universal

The dedication covers what this repository contributes: the selection and arrangement of the corpus, the frontmatter metadata, the markdown rendition of each text, and the accompanying notes. Those rights are waived to the maximum extent permitted by law. Anyone may copy, modify, distribute and perform them, even for commercial purposes, all without asking permission.

The dedication cannot reach rights this repository does not hold, and does not claim to. Where a text reaches the corpus through a modern edited transcription, any editorial layer subsisting in that transcription belongs to its editor, not to this repository, and the affected book says so in its `source_note`. There is currently one such book, and it is listed in the README and tracked in QUALITY.md. Every other book is a rendition of a source edition that is itself out of copyright.

Full legal text: [LICENSE](LICENSE), or <https://creativecommons.org/publicdomain/zero/1.0/legalcode>

## Per-file provenance

Each book's YAML frontmatter declares:

- `source`: the upstream repository or archive
- `source_url`: the precise URL fetched
- `year`: the publication year of the cited source edition
- `license`: declared as "Public domain in the United States"
- `year_note` and `source_note`, where present: the edition actually transcribed, and the public-domain basis wherever that basis is anything other than straightforward pre-1929 publication

This per-file declaration is the authoritative provenance record. If a particular book turns out to have residual restrictions in your jurisdiction (the world's copyright laws are not uniform), the frontmatter gives you what you need to check.

## What this does not cover

The **tooling** under `scripts/` and the **repository structure** itself (this README, CORPUS.md, CONTRIBUTING.md, etc.) are licensed separately under MIT. See [LICENSE-CODE.md](LICENSE-CODE.md).
