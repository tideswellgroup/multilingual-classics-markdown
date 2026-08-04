---
name: Content correction
about: Report a transcription error, broken markup, or rendering issue in a book
title: 'Content correction: <locale> / <title>'
labels: content-correction
---

## File

- **Path**: `books/<locale>/<author>/<title>.md`
- **Line(s) affected**:

## Issue

What's wrong? Examples:

- Transcription error (a character or word is mis-OCR'd)
- Encoding problem (replacement characters, broken diacritics)
- Markdown structure issue (heading hierarchy, missing paragraph breaks)
- Rendering issue (KaTeX math doesn't parse, raw HTML leaking through, etc.)

## Suggested correction

What should the affected passage read?

## Source for the correction

If you're proposing a correction, please cite where the correct reading comes from (the upstream source URL, a scholarly edition, etc.).

## How critical?

- [ ] Cosmetic (typography artefact)
- [ ] Readability (the passage is recognisable but flawed)
- [ ] Substantive (changes meaning of the passage)
- [ ] Blocking (the file fails to render)
