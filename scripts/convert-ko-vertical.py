#!/usr/bin/env python3
"""
convert-ko-vertical.py: build the two vertical-convention Korean books that the
corpus's shipped generic converters cannot produce end to end on their own.

Both books come from ko.wikisource but need different routes and a shared
post-conversion cleanup the generic scripts do not apply:

  1. 한중록 (Lady Hyegyong's court memoir, 권일) is an inline old-hangul
     transcription, so it goes through the wikitext route
     (convert-wikisource.py). It comes out clean; we run it through the same
     cleanup for consistency and to drop the trailing license heading.

  2. 서유견문 (Yu Kilchun, 1895) lives as ProofreadPage transclusions, so its
     wikitext is only an index; the rendered-HTML route
     (convert-wikisource-html.py) is required. We vendor the author's preface
     (서) plus the whole of 제1편 as one coherent excerpt, so this script also
     concatenates two subpages under one frontmatter block, promotes each part
     title to an h1, and demotes the chapter headings to h2 for a clean outline.

Cleanup shared by both (ko_clean):
  - drop ko.wikisource header-navigation lines (they start with the back arrow),
  - truncate the trailing license section (## 저작권 / ## 라이선스),
  - drop any residual wiki templates (옛한글 display wrappers, PD banners),
  - collapse blank runs.

Nothing is modernized: old-hangul jamo (arae-a and archaic clusters) and the
mixed-script hanja of 서유견문, including the author's 【 】 interlinear notes,
pass through verbatim.

Run from the repo root:  python3 scripts/convert-ko-vertical.py
"""

from __future__ import annotations

import importlib.util
import re
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
DELAY = 5  # seconds between API requests, per corpus fetch etiquette


def _load(modname: str, filename: str):
    spec = importlib.util.spec_from_file_location(modname, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ws = _load("convert_wikisource", "convert-wikisource.py")
wh = _load("convert_wikisource_html", "convert-wikisource-html.py")


LICENSE_HEADING = re.compile(r"^#{1,6}\s*(저작권|라이선스|라이센스|License)\s*$")
NAV_LINE = re.compile(r"^\s*←")
ONLY_TEMPLATE = re.compile(r"^\s*\{\{[^{}]*\}\}\s*$")


def ko_clean(body: str) -> str:
    """Drop ko.wikisource chrome the generic converters leave behind."""
    out: list[str] = []
    for line in body.split("\n"):
        if NAV_LINE.match(line):
            continue
        if LICENSE_HEADING.match(line):
            break  # license section is always last; everything after is chrome
        if ONLY_TEMPLATE.match(line) and ("PD-" in line or "옛한글" in line):
            continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def wikitext_body(lang: str, page: str) -> str:
    wt = ws.fetch_wikitext(lang, page)
    wt = ws.strip_top_metadata(wt)
    wt = ws.strip_bottom_metadata(wt)
    wt = ws.convert_chapter_markers(wt)
    wt = ws.convert_div_blocks(wt)
    wt = ws.convert_inline_markup(wt)
    wt = ws.convert_wikitables(wt)
    wt = ws.convert_simple_templates(wt)
    wt = ws.convert_headings(wt)
    wt = ws.normalise_whitespace(wt)
    return ko_clean(wt)


def html_body(lang: str, page: str) -> str:
    html = wh.fetch_html(lang, page, variant=None)
    html = wh.strip_chrome(html)
    html = wh.convert_headings(html)
    html = wh.convert_blocks(html)
    html = wh.convert_inline(html)
    html = wh.strip_residual_tags(html)
    return ko_clean(wh.normalise(html))


def frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, int):
            lines.append(f"{k}: {v}")
        else:
            esc = str(v).replace('"', "'")
            lines.append(f'{k}: "{esc}"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def write_book(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frontmatter(meta) + body
    path.write_text(out, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(out.encode()):,} bytes, "
          f"{len(body.splitlines()):,} body lines)")


def build_hanjungnok() -> None:
    body = wikitext_body("ko", "한중록/1권")
    meta = {
        "title": "한중록",
        "author": "헌경왕후",
        "language": "ko",
        "year": 1795,
        "year_note": "Composed between 1795 and 1805; the 권일 used here is the 1795 recension (내제 한듕만록). The memoir circulated in manuscript, so the ko.wikisource transcription is the source edition.",
        "source": "Wikisource (ko)",
        "source_url": "https://ko.wikisource.org/wiki/%ED%95%9C%EC%A4%91%EB%A1%9D/1%EA%B6%8C",
        "license": "Public domain in the United States",
        "selection_note": "한중록 survives as a six-part memoir by Lady Hyegyong (헌경왕후, 1735 to 1815). This file includes the first part in full (한듕만록 권일, the 1795 recension addressed to her nephew), running from her birth and entry into the palace to the loss of Crown Prince Sado. Parts 2권 to 6권 are omitted for length; each is a separate ko.wikisource subpage under 한중록.",
        "source_note": "Old-hangul orthography (옛한글) is preserved verbatim, including arae-a (ᄋᆞ) and archaic jamo clusters exactly as printed. ko.wikisource 옛한글 display wrappers and the trailing license box were dropped in conversion; no letterforms were modernized. Public-domain basis: the first print publication was the 1939 문장 (Munjang) serialization, which post-dates the corpus's usual pre-1929 publication line; the work is public domain in the United States on the unpublished-works term instead, the author having died in 1815, so the life plus 70 years term expired in the 19th century. Admitted under the corpus's documented manuscript-works exception for works whose author died before 1855.",
        "writing-mode": "vertical-rl",
    }
    write_book(ROOT / "books/ko/헌경왕후/한중록.md", meta, body)


def build_seoyugyeonmun() -> None:
    seo = html_body("ko", "서유견문/서")
    time.sleep(DELAY)
    p1 = html_body("ko", "서유견문/제1편")

    # Promote each part title to h1; demote 제1편's chapter headings to h2 so the
    # combined file has a clean h1 -> h2 outline.
    seo = seo.replace("**西遊見聞 序**", "# 西遊見聞 序", 1)
    p1 = p1.replace("**西遊見聞 第一編**", "# 西遊見聞 第一編", 1)
    p1 = re.sub(r"^### ", "## ", p1, flags=re.MULTILINE)

    body = seo.rstrip() + "\n\n" + p1.lstrip()

    meta = {
        "title": "서유견문",
        "author": "유길준",
        "language": "ko",
        "year": 1895,
        "year_note": "First published 1895 (개국 504년); the author's preface (서) is dated 개국 498년 (己丑, 1889). Source edition: the 1895 printing scanned on ko.wikisource.",
        "source": "Wikisource (ko)",
        "source_url": "https://ko.wikisource.org/wiki/%EC%84%9C%EC%9C%A0%EA%B2%AC%EB%AC%B8/%EC%A0%9C1%ED%8E%B8",
        "license": "Public domain in the United States",
        "selection_note": "서유견문 runs to twenty 편. This file includes the author's preface (서) together with the whole of 제1편, whose four chapters are 地球 世界의 槪論, 六大洲의 區域, 邦國의 區別, and 世界의 山. The preface is where Yu Kilchun defends his mixed-script (국한문혼용) prose. 제2편 to 제20편 are omitted for length. Parent work: https://ko.wikisource.org/wiki/서유견문 ; preface subpage: https://ko.wikisource.org/wiki/서유견문/서",
        "source_note": "국한문혼용 (mixed Sino-Korean) text: hanja are kept exactly as printed, never romanized or stripped, and the author's double-line interlinear notes stay in 【 】 brackets. Old-hangul jamo (arae-a ᄒᆞ, ᄂᆞᆫ and the like) are preserved verbatim. Each chapter carries a Korean section-title gloss supplied by ko.wikisource (e.g. 지구 세계의 개론) ahead of Yu's original hanja heading (地球 世界의 槪論); both are retained. verify-upstream targets 제1편 (the bulk); the preface was verified separately against its own subpage.",
        "writing-mode": "vertical-rl",
    }
    write_book(ROOT / "books/ko/유길준/서유견문.md", meta, body)


def main() -> int:
    build_hanjungnok()
    time.sleep(DELAY)
    build_seoyugyeonmun()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
