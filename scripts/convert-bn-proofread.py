#!/usr/bin/env python3
"""
convert-bn-proofread.py: assemble one markdown book from a bn.wikisource
ProofreadPage collection whose text lives in per-unit sub-pages.

bn.wikisource stores its long works as an index (top) page that carries only
front matter plus a table of contents, with the running text split across one
sub-page per song, chapter, or section. Each sub-page is a thin
`<pages index="...djvu" from=X to=Y/>` transclusion, so the wikitext route
yields nothing usable (see convert-wikisource.py). This walker takes the
rendered HTML of every sub-page (the same action=parse prop=text endpoint that
convert-wikisource-html.py uses), reuses that script's proven strip/convert
pipeline, and concatenates the units under generated headings.

Ordering comes from the top page's table-of-contents link sequence; the
authoritative unit set comes from the allpages API. The two are cross-checked
and any disagreement is reported rather than silently resolved.

Three structures are supported:
  poem          one numbered lyric per sub-page; heading is the sub-page number
                (Gitanjali). A printed unit number at the head of the body is
                de-duplicated against the generated heading.
  flat          one chapter per sub-page; heading is the sub-page label
                (Devdas: প্রথম পরিচ্ছেদ ...).
  part-chapter  two-level `<part>/<chapter>` sub-pages; the part becomes a
                level-1 heading emitted once, the chapter a level-2 heading
                (Kapalkundala: প্রথম খণ্ড/প্রথম পরিচ্ছেদ ...).

Politeness: one request per sub-page with a configurable delay (default 5s),
User-Agent multilingual-classics-markdown/1.0.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"
SCRIPT_DIR = Path(__file__).resolve().parent

# Reuse the audited HTML-to-markdown pipeline rather than re-deriving it.
_spec = importlib.util.spec_from_file_location(
    "cwh", SCRIPT_DIR / "convert-wikisource-html.py"
)
cwh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cwh)

BENGALI_DIGITS = {ord(d): str(i) for i, d in enumerate("০১২৩৪৫৬৭৮৯")}


def bn_to_int(s: str) -> int | None:
    ascii_digits = s.strip().translate(BENGALI_DIGITS)
    return int(ascii_digits) if ascii_digits.isdigit() else None


def api_get(lang: str, params: dict) -> dict:
    params = {**params, "format": "json", "formatversion": "2"}
    url = f"https://{lang}.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            if "429" in str(e):
                time.sleep(15 * (attempt + 1))
                continue
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"API failure for {params.get('page') or params}: {last}")


def fetch_wikitext(lang: str, page: str) -> str:
    data = api_get(lang, {"action": "parse", "page": page, "prop": "wikitext"})
    return data.get("parse", {}).get("wikitext", "")


def fetch_rendered(lang: str, page: str) -> str:
    data = api_get(lang, {
        "action": "parse", "page": page, "prop": "text",
        "disableeditsection": "1", "disabletoc": "1",
    })
    if "error" in data:
        raise SystemExit(f"API error for {page}: {data['error']}")
    return data["parse"]["text"]


def allpages_subpages(lang: str, prefix: str) -> list[str]:
    data = api_get(lang, {
        "action": "query", "list": "allpages",
        "apprefix": prefix, "aplimit": "500",
    })
    return [p["title"] for p in data["query"]["allpages"]]


def toc_order(lang: str, top: str) -> list[str]:
    """Ordered sub-page titles as they appear in the top page's wikitext links.

    Handles absolute links (`[[Top/Unit|label]]`) and relative sub-page links
    (`[[/Unit/]]`). Order is preserved; duplicates are dropped."""
    wt = fetch_wikitext(lang, top)
    prefix = top + "/"
    order: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", wt):
        target = m.group(1).strip()
        if target.startswith("/"):
            target = top + "/" + target.strip("/")
        if not target.startswith(prefix):
            continue
        if target not in seen:
            seen.add(target)
            order.append(target)
    return order


def resolve_order(lang: str, top: str, structure: str) -> list[str]:
    authoritative = set(allpages_subpages(lang, top + "/"))
    order = [t for t in toc_order(lang, top) if t in authoritative]
    missing = authoritative - set(order)
    if missing:
        extras = sorted(missing)
        if structure == "poem":
            extras.sort(key=lambda t: bn_to_int(t.rsplit("/", 1)[-1]) or 1_000_000)
        print(
            f"WARN: {len(missing)} sub-page(s) absent from the TOC order; "
            f"appending sorted: {extras}",
            file=sys.stderr,
        )
        order += extras
    if len(order) != len(authoritative):
        print(
            f"WARN: order length {len(order)} != allpages {len(authoritative)}",
            file=sys.stderr,
        )
    return order


def _rescue_wst_right(m: re.Match) -> str:
    inner = re.sub(r"<[^>]+>", "", m.group(1))  # drop the nested spacer span
    return f"\n\n{inner.strip()}\n\n"


def convert_body(html: str) -> str:
    # Some bn.wikisource pages carry a malformed {{wst-right}} invocation that
    # MediaWiki renders as an ESCAPED literal `<div ...>` with the attribution
    # text trapped in a margin-right style (e.g. the কুমারসম্ভব। epigraph credit
    # in Kapalkundala). Left alone it survives tag-stripping and re-materialises
    # as a literal tag after entity-unescaping. Rescue the trapped text; the
    # markup is discarded.
    html = re.sub(
        r'&lt;div class="wst-right" style="margin-right:(.*?);"&gt;',
        _rescue_wst_right, html, flags=re.DOTALL,
    )
    html = cwh._strip_balanced(html, "div", lambda a: "ws-noexport" in a)
    html = cwh._strip_balanced(html, "div", lambda a: "wikisource-header-template" in a)
    html = cwh.strip_chrome(html)
    # bn.wikisource emits `<br />\n` between verse lines; collapse the pair so a
    # single line break stays a single break and stanza gaps (`</p><p>`) remain
    # the only blank-line boundaries.
    html = re.sub(r"[ \t]*<br\s*/?>[ \t]*\n?", "\n", html)
    html = cwh.convert_headings(html)
    html = cwh.convert_blocks(html)
    html = cwh.convert_inline(html)
    html = cwh.strip_residual_tags(html)
    text = cwh.normalise(html)
    # Source paragraphs carry a leading indent space; drop leading horizontal
    # whitespace per line so nothing trips markdown's 4-space code-block rule.
    text = re.sub(r"(?m)^[ \t]+", "", text)
    return text.strip("\n")


def unit_label(title: str, top: str) -> str:
    return title[len(top) + 1:] if title.startswith(top + "/") else title


def drop_leading_label(body: str, *labels: str) -> str:
    lines = body.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip() in {l.strip() for l in labels if l}:
        lines.pop(0)
    return "\n".join(lines).lstrip("\n")


def build_frontmatter(meta: list[tuple[str, str]]) -> str:
    out = ["---"]
    for k, v in meta:
        out.append(f"{k}: {v}")
    out.append("---")
    out.append("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--lang", default="bn")
    p.add_argument("--top", required=True, help="index (top) page title")
    p.add_argument("--structure", required=True, choices=["poem", "flat", "part-chapter"])
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True)
    p.add_argument("--year", required=True)
    p.add_argument("--source-url", required=True, help="canonical top-page URL (quoted in frontmatter)")
    p.add_argument("--extra", action="append", default=[], metavar="KEY=VALUE",
                   help="extra frontmatter line inserted after year (repeatable); value is quoted")
    p.add_argument("--book-title", default=None, help="H1 title for the body (defaults to --title)")
    p.add_argument("--output", required=True)
    p.add_argument("--delay", type=float, default=5.0)
    p.add_argument("--limit", type=int, default=0, help="cap sub-pages (0 = all; for testing)")
    args = p.parse_args()

    order = resolve_order(args.lang, args.top, args.structure)
    if args.limit:
        order = order[:args.limit]
    print(f"assembling {len(order)} unit(s) from {args.top}", file=sys.stderr)

    parts: list[str] = []
    h1 = args.book_title or args.title
    parts.append(f"# {h1}\n")

    current_part = None
    for i, title in enumerate(order):
        label = unit_label(title, args.top)
        html = fetch_rendered(args.lang, title)
        body = convert_body(html)

        if args.structure == "poem":
            body = drop_leading_label(body, label)
            parts.append(f"## {label}\n\n{body}\n")
        elif args.structure == "flat":
            body = drop_leading_label(body, label)
            parts.append(f"## {label}\n\n{body}\n")
        else:  # part-chapter
            comps = label.split("/", 1)
            part_lbl = comps[0]
            chap_lbl = comps[1] if len(comps) > 1 else ""
            body = drop_leading_label(body, chap_lbl, part_lbl, label)
            if part_lbl != current_part:
                parts.append(f"# {part_lbl}\n")
                current_part = part_lbl
            parts.append(f"## {chap_lbl}\n\n{body}\n")

        if i + 1 < len(order):
            time.sleep(args.delay)

    meta: list[tuple[str, str]] = [
        ("title", args.title),
        ("author", args.author),
        ("language", args.language),
        ("year", args.year),
    ]
    for kv in args.extra:
        k, _, v = kv.partition("=")
        meta.append((k.strip(), f'"{v.strip()}"'))
    meta += [
        ("source", f"Wikisource ({args.lang})"),
        ("source_url", f'"{args.source_url}"'),
        ("license", "Public domain in the United States"),
    ]

    doc = build_frontmatter(meta) + "\n".join(parts).rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    print(f"wrote {dest} ({len(doc.encode('utf-8')):,} bytes, {len(order)} units)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
