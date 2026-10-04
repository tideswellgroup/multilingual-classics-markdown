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
  own           one chapter per sub-page that already carries its own
                headings; nothing is generated, the source's are kept
                (Indulekha: ഒന്ന് / പ്രാരംഭം ...).

Despite the name, the walker is not bn-specific: --lang selects the
Wikisource, and the te, ml and other Indic books use it too.

Politeness: one request per sub-page with a configurable delay (default 5s),
User-Agent multilingual-classics-markdown/1.0 with a contact address, and the
server's Retry-After honoured on 429 and 503.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0 (contact@tideswellgroup.com)"
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
        except urllib.error.HTTPError as e:
            last = e
            # Honour the server's Retry-After where it gives one.
            if e.code == 404:
                break  # a missing page will not appear on retry
            retry = e.headers.get("Retry-After", "") if e.headers else ""
            if retry.isdigit():
                time.sleep(min(int(retry), 120))
            elif e.code in (429, 503):
                time.sleep(15 * (attempt + 1))
            else:
                time.sleep(3 * (attempt + 1))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"API failure for {params.get('page') or params}: {last}")


def fetch_wikitext(lang: str, page: str) -> str:
    data = api_get(lang, {"action": "parse", "page": page, "prop": "wikitext"})
    return data.get("parse", {}).get("wikitext", "")


CACHE_DIR: Path | None = None


def _cache_path(lang: str, page: str) -> Path | None:
    if CACHE_DIR is None:
        return None
    key = hashlib.sha256(f"{lang}:{page}".encode("utf-8")).hexdigest()[:24]
    return CACHE_DIR / f"{lang}-{key}.html"


def is_cached(lang: str, page: str) -> bool:
    path = _cache_path(lang, page)
    return path is not None and path.exists()


def fetch_rendered(lang: str, page: str) -> str:
    """Rendered HTML of one page. With --cache, each response is kept on disk
    and reused, so a rerun after a converter fix costs the upstream nothing."""
    cached = _cache_path(lang, page)
    if cached is not None and cached.exists():
        return cached.read_text(encoding="utf-8")
    html = _fetch_rendered(lang, page)
    if cached is not None:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(html, encoding="utf-8")
    return html


def _fetch_rendered(lang: str, page: str) -> str:
    data = api_get(lang, {
        "action": "parse", "page": page, "prop": "text",
        "disableeditsection": "1", "disabletoc": "1",
    })
    if "error" in data:
        raise SystemExit(f"API error for {page}: {data['error']}")
    return data["parse"]["text"]


def allpages_subpages(lang: str, prefix: str, skip_redirects: bool = False) -> list[str]:
    params = {
        "action": "query", "list": "allpages",
        "apprefix": prefix, "aplimit": "500",
    }
    if skip_redirects:
        # Redirects left behind by page moves are not units; counting them
        # would ship a chapter twice (ml Indulekha).
        params["apfilterredir"] = "nonredirects"
    data = api_get(lang, params)
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


def resolve_order(lang: str, top: str, structure: str, skip_redirects: bool = False) -> list[str]:
    authoritative = set(allpages_subpages(lang, top + "/", skip_redirects))
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


def split_emphasis_at_breaks(html: str) -> str:
    """Close and reopen bold and italic at each hard break. CommonMark cannot
    carry emphasis across a hard line break, so <b>a<br>b</b> would render
    with literal asterisks; it becomes <b>a</b><br><b>b</b>."""
    for tag in ("b", "strong", "i", "em"):
        pattern = re.compile(rf"<{tag}(\s[^>]*)?>((?:(?!</{tag}>).)*?)</{tag}>", re.DOTALL)

        def split(m: re.Match, tag: str = tag) -> str:
            inner = m.group(2).replace("\x00\n", f"</{tag}>\x00\n<{tag}>")
            return f"<{tag}>{inner}</{tag}>"

        html = pattern.sub(split, html)
        html = re.sub(rf"<{tag}>(\s*)</{tag}>", r"\1", html)
    return html


def convert_body(html: str, br_hard: bool = False, lines_hard: bool = False) -> str:
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
    # With br_hard, a <br> keeps its meaning as a CommonMark hard break (two
    # trailing spaces); bare newlines in the source paragraph still merge, as
    # they do on the rendered wiki page.
    if br_hard:
        # Emphasis wrapped round a bare break (<i><br /></i>) would strand the
        # source newline after it and open a paragraph break; unwrap it first.
        html = re.sub(r"<(b|strong|i|em)>\s*(<br\s*/?>)\s*</\1>", r"\2", html)
    html = re.sub(r"[ \t]*<br\s*/?>[ \t]*\n?", "\x00\n" if br_hard else "\n", html)
    if br_hard:
        html = split_emphasis_at_breaks(html)
        # A source newline left after a break (<b>a<br /></b>\n<b>b</b>) is
        # inline whitespace in HTML, not a paragraph boundary; keep one line end.
        html = re.sub(
            r"\x00\n[ \t]*\n(?![ \t]*(?:\n|$|</?(?:p|div|center|dl|dd|dt|h\d|table|tr|td|ul|ol|li)\b))",
            "\x00\n", html,
        )
        # Whitespace just inside an emphasis tag (<b> text</b>) leaves a
        # delimiter CommonMark will not read as emphasis; move it outside.
        html = re.sub(r"<(b|strong|i|em)>(\s+)", r"\2<\1>", html)
        html = re.sub(r"(\s+)</(b|strong|i|em)>", r"</\2>\1", html)
    html = cwh.convert_headings(html)
    html = cwh.convert_blocks(html)
    html = cwh.convert_inline(html)
    html = cwh.strip_residual_tags(html)
    text = cwh.normalise(html)
    # Source paragraphs carry a leading indent space; drop leading horizontal
    # whitespace per line so nothing trips markdown's 4-space code-block rule.
    text = re.sub(r"(?m)^[ \t]+", "", text)
    # A hard break before a blank line or at the end of a unit is meaningless.
    text = re.sub(r"(?m)^[ \t]*\x00[ \t]*$", "", text)  # a <br> alone on its line
    text = re.sub(r"\x00(?=\n[ \t]*(\n|$))", "", text)
    text = re.sub(r"\x00$", "", text)
    text = re.sub(r"[ \t]*\x00", "  ", text)
    if lines_hard:
        # A typed (not page-wrapped) transcription: every line end inside a
        # paragraph is the transcriber's, so each one is a hard break.
        text = re.sub(r"(?m)(?<!  )(?<=\S)[ \t]*\n(?=[^\n#])", "  \n", text)
    return text.strip("\n")


def unit_label(title: str, top: str) -> str:
    return title[len(top) + 1:] if title.startswith(top + "/") else title


def drop_leading_label(body: str, *labels: str, repeat: bool = False) -> str:
    """Drop a printed title line at the head of a unit that duplicates its
    generated heading. With repeat, keep dropping while the next non-blank
    line is one of the labels, so a stacked head (book title, then unit
    title) goes too; the bn books were built with a single drop."""
    wanted = {l.strip() for l in labels if l and l.strip()}
    lines = body.split("\n")
    while True:
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines and lines[0].strip() in wanted:
            lines.pop(0)
            if repeat:
                continue
        break
    return "\n".join(lines).lstrip("\n")


def take_printed_head(body: str, n: int) -> tuple[str, str]:
    """Use the unit's printed title as its heading. The first n non-blank
    lines must each be wholly bold (the printed head, possibly set on two
    lines); they are joined by a space, the closing full stop dropped, and
    removed from the body so the title is carried once."""
    lines = body.split("\n")
    head: list[str] = []
    while len(head) < n:
        while lines and not lines[0].strip():
            lines.pop(0)
        m = re.fullmatch(r"\*\*(.+?)\*\*\s*", lines[0]) if lines else None
        if not m:
            raise SystemExit(f"expected a bold printed head, found: {lines[0] if lines else ''!r}")
        head.append(m.group(1).strip())
        lines.pop(0)
    label = " ".join(head).rstrip(" .")
    return label, "\n".join(lines).lstrip("\n")


def repair_digit_slips(text: str, slips: list[str]) -> tuple[str, dict[str, int]]:
    """Repair a native digit typed for the letter it resembles, as a counted
    class: DIGIT=LETTER replaces the digit wherever it touches a letter or
    mark on either side and no other digit. Numerals of two or more digits
    are left alone, but a single digit written straight against a suffix
    (an ordinal such as ൪ാം) would be rewritten, so list every case the rule
    touches before relying on it. Old Malayalam fonts are the classic source
    (൯ for ൻ, ൪ for ർ)."""
    import unicodedata

    def is_letter(ch: str) -> bool:
        return bool(ch) and unicodedata.category(ch)[0] in "LM"

    counts: dict[str, int] = {}
    for spec in slips:
        digit, _, letter = spec.partition("=")
        out = []
        n = 0
        for i, ch in enumerate(text):
            if ch == digit:
                prev = text[i - 1] if i else ""
                nxt = text[i + 1] if i + 1 < len(text) else ""
                if (is_letter(prev) or is_letter(nxt)) and not (prev.isdigit() or nxt.isdigit()):
                    out.append(letter)
                    n += 1
                    continue
            out.append(ch)
        text = "".join(out)
        counts[spec] = n
    return text, counts


def isolate_bold_lines(text: str) -> str:
    """A line that is wholly bold is a printed subhead; give it its own
    paragraph so it does not merge into the text around it."""
    return re.sub(r"(?m)^[ \t]*(\*\*[^\n*]+\*\*)[ \t]*$", r"\n\1\n", text)


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
    p.add_argument("--structure", required=True, choices=["poem", "flat", "part-chapter", "own"])
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
    p.add_argument("--units", default=None,
                   help="explicit sub-page labels in reading order, separated by '|'; "
                        "overrides the TOC walk where the top page does not link its units "
                        "or carries sub-pages that must not ship. LABEL>N takes the unit's "
                        "heading from its first N wholly bold printed lines instead of LABEL")
    p.add_argument("--br-hard", action="store_true",
                   help="render each <br> as a two-space hard break instead of a bare newline")
    p.add_argument("--lines-hard", action="store_true",
                   help="treat every line end inside a paragraph as a hard break; only for "
                        "typed transcriptions that carry no printed line wraps")
    p.add_argument("--cache", default=None, metavar="DIR",
                   help="keep each fetched page's HTML here and reuse it on later runs "
                        "(sub-page listings and the contents page are still read from the API)")
    p.add_argument("--top-unit", default=None, metavar="LABEL|START|STOP",
                   help="also ship part of the top page as a first unit headed LABEL: the "
                        "lines strictly between the line START and the line STOP (front "
                        "matter such as an authorial foreword, without title page or contents)")
    p.add_argument("--digit-slip", action="append", default=[], metavar="DIGIT=LETTER",
                   help="repair a digit typed for the letter it resembles wherever it touches "
                        "a letter and no other digit; counts are reported (repeatable)")
    p.add_argument("--escape-backticks", action="store_true",
                   help="backslash-escape every backtick, for a book whose transcription uses "
                        "the backtick as a real mark (two in a paragraph would open a code span)")
    p.add_argument("--replace", action="append", default=[], metavar="OLD=>NEW",
                   help="a disclosed literal correction, applied to the assembled body; it must "
                        "match exactly once (repeatable)")
    p.add_argument("--skip-redirects", action="store_true",
                   help="leave redirect sub-pages (left by page moves) out of the unit set")
    p.add_argument("--tidy", action="store_true",
                   help="collapse runs of blank lines and drop stray byte-order marks")
    p.add_argument("--dedupe-adjacent", action="store_true",
                   help="drop a paragraph identical to the one before it (a line repeated "
                        "across a page boundary in the transcription); each drop is reported")
    p.add_argument("--frontmatter-from", default=None, metavar="PATH",
                   help="use the YAML block of this file (a .yml or an existing book) instead "
                        "of generating one, so a rebuild keeps the curated frontmatter")
    p.add_argument("--isolate-bold-lines", action="store_true",
                   help="give each wholly bold line (a printed subhead) its own paragraph")
    p.add_argument("--drop-head", action="append", default=[], metavar="TEXT",
                   help="printed head line to strip from the start of every unit when it "
                        "duplicates the book or unit title (repeatable)")
    args = p.parse_args()

    global CACHE_DIR
    if args.cache:
        CACHE_DIR = Path(args.cache)
    printed_heads: dict[str, int] = {}
    if args.units:
        order = []
        for u in (u.strip() for u in args.units.split("|")):
            if not u:
                continue
            label, _, n = u.partition(">")
            title = f"{args.top}/{label.strip()}"
            order.append(title)
            if n:
                printed_heads[title] = int(n)
        authoritative = set(allpages_subpages(args.lang, args.top + "/"))
        absent = [t for t in order if t not in authoritative]
        if absent:
            raise SystemExit(f"--units names sub-pages that do not exist: {absent}")
    else:
        order = resolve_order(args.lang, args.top, args.structure, args.skip_redirects)
    if args.limit:
        order = order[:args.limit]
    print(f"assembling {len(order)} unit(s) from {args.top}", file=sys.stderr)

    parts: list[str] = []
    h1 = args.book_title or args.title
    parts.append(f"# {h1}\n")

    if args.top_unit:
        label, start, stop = (x.strip() for x in args.top_unit.split("|"))
        lines = convert_body(fetch_rendered(args.lang, args.top), br_hard=args.br_hard).split("\n")
        try:
            a = next(i for i, l in enumerate(lines) if l.strip() == start)
            b = next(i for i, l in enumerate(lines) if i > a and l.strip() == stop)
        except StopIteration:
            raise SystemExit(f"--top-unit: START or STOP line not found on {args.top}")
        front = "\n".join(lines[a + 1:b]).strip("\n")
        parts.append(f"## {label}\n\n{front}\n")
        if order and not is_cached(args.lang, order[0]):
            time.sleep(args.delay)

    current_part = None
    for i, title in enumerate(order):
        label = unit_label(title, args.top)
        html = fetch_rendered(args.lang, title)
        body = convert_body(html, br_hard=args.br_hard, lines_hard=args.lines_hard)

        if args.structure == "poem":
            body = drop_leading_label(body, label)
            parts.append(f"## {label}\n\n{body}\n")
        elif args.structure == "own":
            parts.append(f"{body}\n")
        elif args.structure == "flat":
            body = drop_leading_label(body, label, *args.drop_head, repeat=bool(args.drop_head))
            if title in printed_heads:
                label, body = take_printed_head(body, printed_heads[title])
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

        if i + 1 < len(order) and not is_cached(args.lang, order[i + 1]):
            time.sleep(args.delay)  # the pause is for the upstream, not the cache

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

    body = "\n".join(parts)
    if args.isolate_bold_lines:
        body = isolate_bold_lines(body)
    if args.digit_slip:
        body, slip_counts = repair_digit_slips(body, args.digit_slip)
        print(f"digit slips repaired: {slip_counts}", file=sys.stderr)
    for spec in args.replace:
        old, sep, new = spec.partition("=>")
        if not sep or body.count(old) != 1:
            raise SystemExit(f"--replace target must occur exactly once: {old!r}")
        body = body.replace(old, new)
    if args.escape_backticks:
        print(f"backticks escaped: {body.count('`')}", file=sys.stderr)
        body = body.replace("`", "\\`")
    if args.tidy:
        body = body.replace("\ufeff", "")  # stray byte-order marks are page debris
        body = re.sub(r"\n{3,}", "\n\n", body)
    if args.dedupe_adjacent:
        paras = body.split("\n\n")
        kept = [paras[0]]
        for para in paras[1:]:
            if para.strip() and para.strip() == kept[-1].strip():
                print(f"dropped a repeated paragraph: {para.strip()[:60]!r}", file=sys.stderr)
                continue
            kept.append(para)
        body = "\n\n".join(kept)
    if args.frontmatter_from:
        src = Path(args.frontmatter_from).read_text(encoding="utf-8")
        m = re.match(r"---\n.*?\n---\n", src, re.DOTALL)
        if not m:
            raise SystemExit(f"--frontmatter-from: no YAML block in {args.frontmatter_from}")
        fm = m.group(0)
    else:
        fm = build_frontmatter(meta)
    doc = fm + body.rstrip("\n") + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding="utf-8")
    print(f"wrote {dest} ({len(doc.encode('utf-8')):,} bytes, {len(order)} units)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
