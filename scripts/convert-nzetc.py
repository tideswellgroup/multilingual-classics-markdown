#!/usr/bin/env python3
"""
convert-nzetc.py: fetch clean HTML transcriptions from the New Zealand
Electronic Text Collection (NZETC, Victoria University of Wellington) and
convert them to vendor-ready markdown for the i18n-books corpus.

The live nzetc.victoria.ac.nz host has been decommissioned and 301-redirects
into a bot-protected National Library web archive that blocks scripted
fetches. The stable, scriptable route is the Internet Archive Wayback Machine,
which holds clean snapshots of the NZETC page-per-section HTML. We fetch
through Wayback and strip the injected toolbar, then reduce the NZETC TEI-
derived HTML to markdown.

NZETC works are split one section per page (tei-<COLL>-c1-<N>.html) under a
table-of-contents page (tei-<COLL>.html). This tool walks an inclusive range
of section numbers, concatenating each section as a level-2 heading (its
pagesubhead / <h3> title) followed by its body, so a curated run of short
pieces (a selection of waiata, say) lands as a single file.

Structure it understands (verified against tei-GreKong, Grey's 1853
Ko Nga Moteatea):
- <div id="tei-section"> wraps the section body (nav menu sits outside it)
- <h1 class="pagesubhead"> / <h3> carries the piece title
- <p class="lg"> is a stanza (line group); <span class="l"> is a verse line
- <span class="pb"> page-break markers are dropped
- <span class="small-caps">, <i>/<em>/<b>, stray <a> are unwrapped

Follows the structure of convert-wikisource-html.py. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ORIGIN = "nzetc.victoria.ac.nz/tm/scholarly/{page}"
CDX_BULK = ("https://web.archive.org/cdx/search/cdx?url={prefix}&matchType=prefix"
            "&collapse=urlkey&filter=statuscode:200&fl=original,timestamp"
            "&output=text&limit=20000")
RAW = "https://web.archive.org/web/{ts}id_/http://{origin}"
CANONICAL = "https://nzetc.victoria.ac.nz/tm/scholarly/{page}"

# The long horizontal dash occurs in NZETC section titles; kept verbatim in
# vendored text. Written as an escape so no literal sits in this source file.
LONG_DASH = "\u2014"


def _get(url: str, retries: int = 4) -> bytes:
    """GET with backoff. web.archive.org intermittently returns 429/5xx and
    connection resets under repeated hits; retry those transiently."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "multilingual-classics-markdown/1.0",
    })
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError as exc:
            last = exc
        time.sleep(3 * (attempt + 1))
    raise last if last else RuntimeError("request failed")


def snapshot_map(collection: str) -> dict[int, str]:
    """One bulk CDX query for the whole section run, returning {section number:
    snapshot timestamp}. Per-page CDX lookups get throttled to empty responses
    under load; a single prefix query with collapse=urlkey is reliable and
    polite, one capture per section URL."""
    prefix = ORIGIN.format(page=f"tei-{collection}-c1-")
    rows = _get(CDX_BULK.format(prefix=prefix)).decode("utf-8", errors="replace")
    out: dict[int, str] = {}
    for row in rows.splitlines():
        parts = row.split()
        if len(parts) != 2:
            continue
        m = re.search(rf"tei-{re.escape(collection)}-c1-(\d+)\.html$", parts[0])
        if m:
            out[int(m.group(1))] = parts[1]
    return out


def fetch_html(page: str, ts: str) -> str:
    url = RAW.format(ts=ts, origin=ORIGIN.format(page=page))
    return _get(url).decode("utf-8", errors="replace")


def strip_wayback(html: str) -> str:
    """Remove the Wayback toolbar, injected scripts and rewritten-link noise."""
    html = re.sub(r"<!--\s*BEGIN WAYBACK TOOLBAR INSERT\s*-->.*?<!--\s*END WAYBACK TOOLBAR INSERT\s*-->", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div id="wm-ipp-base".*?</div>\s*</div>', "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    return html


def extract_section(html: str) -> tuple[str, str]:
    """Return (title, section_html). Title from pagesubhead if present,
    else the section's own <h3>. Section body is the <div id="tei-section">
    region."""
    title = ""
    m = re.search(r'<h1 class="pagesubhead"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if m:
        raw = re.sub(r"<sup[^>]*>.*?</sup>", "", m.group(1), flags=re.DOTALL)
        title = re.sub(r"<[^>]+>", "", raw).strip().rstrip("* ").strip()
    start = html.find('<div id="tei-section">')
    if start == -1:
        return title, ""
    open_re = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    close_re = re.compile(r"</div\s*>", re.IGNORECASE)
    depth = 0
    i = start
    body_end = len(html)
    while i < len(html):
        no = open_re.search(html, i)
        nc = close_re.search(html, i)
        if not nc:
            break
        if no and no.start() < nc.start():
            depth += 1
            i = no.end()
        else:
            depth -= 1
            i = nc.end()
            if depth == 0:
                body_end = i
                break
    section = html[start:body_end]
    if not title:
        h = re.search(r"<h3[^>]*>(.*?)</h3>", section, re.DOTALL)
        if h:
            title = re.sub(r"<[^>]+>", "", h.group(1)).strip()
    return title, section


def strip_english_apparatus(html: str) -> str:
    """Drop Grey's English editorial footnotes and the <sup>*</sup> reference
    markers that point at them. Footnotes are the only English apparatus inside
    the section and are reliably marked class="footnote"; the section wrapper's
    own lang attribute is inconsistent (some pieces are mis-tagged lang="en"),
    so it must not be used as the signal."""
    html = re.sub(r'<div class="footnote[^"]*"[^>]*>.*?</div>', "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", html, flags=re.DOTALL | re.IGNORECASE)
    return html


def section_to_markdown(section: str) -> str:
    section = strip_english_apparatus(section)
    section = re.sub(r'<span class="pb"[^>]*>.*?</span>', "", section, flags=re.DOTALL)
    section = re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", section, flags=re.DOTALL)
    section = re.sub(r'<span class="l"[^>]*>(.*?)</span>', lambda m: "\n" + m.group(1).strip(), section, flags=re.DOTALL)
    section = re.sub(r'<p class="lg"[^>]*>(.*?)</p>', lambda m: "\n\n" + m.group(1).strip() + "\n\n", section, flags=re.DOTALL)
    section = re.sub(r"<p\b[^>]*>(.*?)</p>", lambda m: "\n\n" + m.group(1).strip() + "\n\n", section, flags=re.DOTALL)
    section = re.sub(r'<span class="small-caps"[^>]*>(.*?)</span>', r"\1", section, flags=re.DOTALL)
    section = re.sub(r"<(i|em)\b[^>]*>(.*?)</\1>", r"*\2*", section, flags=re.DOTALL)
    section = re.sub(r"<(b|strong)\b[^>]*>(.*?)</\1>", r"**\2**", section, flags=re.DOTALL)
    section = re.sub(r"<br\s*/?>", "\n", section)
    section = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", section, flags=re.DOTALL)
    section = re.sub(r"<span\b[^>]*>(.*?)</span>", r"\1", section, flags=re.DOTALL)
    section = re.sub(r"</?div[^>]*>", "", section)
    section = re.sub(r"<[^>]+>", "", section)
    section = unescape(section)
    return section


def unescape(text: str) -> str:
    repls = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
             "&quot;": '"', "&#8203;": "", "&#160;": " ", "&mdash;": LONG_DASH,
             "&rsquo;": "’", "&lsquo;": "‘", "&hellip;": "…"}
    for k, v in repls.items():
        text = text.replace(k, v)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    return text


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build(args) -> None:
    smap = snapshot_map(args.collection)
    print(f"snapshot map: {len(smap)} sections captured", file=sys.stderr)
    pieces: list[str] = []
    kept = 0
    for n in range(args.first, args.last + 1):
        page = f"tei-{args.collection}-c1-{n}.html"
        ts = smap.get(n)
        if ts is None:
            print(f"  skip {page}: no snapshot", file=sys.stderr)
            continue
        try:
            html = fetch_html(page, ts)
        except Exception as exc:
            print(f"  skip {page}: {exc}", file=sys.stderr)
            continue
        html = strip_wayback(html)
        title, section = extract_section(html)
        body = normalise(section_to_markdown(section))
        if len(body.strip()) < 10:
            print(f"  skip {page}: empty body", file=sys.stderr)
            continue
        heading = title if title else f"[{page}]"
        pieces.append(f"## {heading}\n\n{body.strip()}\n")
        kept += 1
        print(f"  {page}: {heading[:60]} ({len(body)} chars)")
        if n != args.last:
            time.sleep(args.delay)

    body_all = "\n\n".join(pieces) + "\n"
    meta = {
        "title": args.title,
        "author": args.author,
        "language": args.language,
        "year": args.year,
        "source": "NZETC (New Zealand Electronic Text Collection), via Internet Archive Wayback Machine",
        "source_url": CANONICAL.format(page=f"{args.collection}.html"),
        "license": "Public domain in the United States",
    }
    if args.year_note:
        meta["year_note"] = args.year_note
    if args.selection_note:
        meta["selection_note"] = args.selection_note
    if args.source_note:
        meta["source_note"] = args.source_note
    out = make_frontmatter(meta) + body_all
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out):,} bytes, {kept} sections, {len(body_all.splitlines()):,} body lines)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--collection", required=True, help="NZETC text id, e.g. GreKong")
    p.add_argument("--first", type=int, required=True, help="first c1 section number")
    p.add_argument("--last", type=int, required=True, help="last c1 section number (inclusive)")
    p.add_argument("--snapshot", default="2019", help="Wayback snapshot prefix (default 2019)")
    p.add_argument("--title", required=True)
    p.add_argument("--author", required=True)
    p.add_argument("--language", required=True, help="BCP-47 language tag for content")
    p.add_argument("--year", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--delay", type=float, default=5.0, help="seconds between fetches")
    p.add_argument("--year-note", default="")
    p.add_argument("--selection-note", default="")
    p.add_argument("--source-note", default="")
    args = p.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
