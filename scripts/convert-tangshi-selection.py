#!/usr/bin/env python3
"""
convert-tangshi-selection.py: build a rule-based slice of 唐詩三百首 (the 1763
蘅塘退士 anthology) by walking its zh.wikisource index and fetching each poem's
own page.

The index (唐詩三百首) is a table of contents whose entries link out to one
page per poem, so neither shipped converter fits: this is a multi-page walk
that must, per poem, (a) pick the 唐詩三百首 reading when a page carries several
textual traditions under ===version=== subheads, (b) resolve the
{{另|甲|乙}} variant-character template to its printed reading 甲, and
(c) keep the poem's line structure. Traditional characters are preserved (no
variant route). Author and title come from the index entry, which already
gives the clean display form.

Selection is section-based: pass one or more --section names present in the
index (e.g. 五言絕句 七言絕句); every poem listed under them is included, in
index order, so the slice is reproducible and self-describing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "multilingual-classics-markdown/1.0"


def fetch_wikitext(page: str, retries: int = 6) -> str:
    params = {"action": "parse", "page": page, "prop": "wikitext",
              "format": "json", "formatversion": "2"}
    url = "https://zh.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            if "error" in data:
                raise SystemExit(f"API error for {page}: {data['error']}")
            return data["parse"]["wikitext"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt + 1 < retries:
                wait = 30 * (attempt + 1)
                print(f"  429 on {page}; backing off {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise SystemExit(f"exhausted retries for {page}")


def parse_section(index_wt: str, section: str) -> list[tuple[str, str, str]]:
    """Return (author, page, display) for each '# author [[page|display]]'
    entry under the named == section == of the index."""
    m = re.search(rf"^==\s*{re.escape(section)}\s*==\s*$", index_wt, re.MULTILINE)
    if not m:
        raise SystemExit(f"index section {section!r} not found")
    after = index_wt[m.end():]
    nxt = re.search(r"^==\s*\S.*?\s*==\s*$", after, re.MULTILINE)
    block = after[: nxt.start()] if nxt else after
    entries = []
    for line in block.splitlines():
        lm = re.match(r"#\s*(\S+?)\s*\[\[([^\]]+)\]\]", line)
        if not lm:
            continue
        author = lm.group(1)
        link = lm.group(2)
        if "|" in link:
            page, display = link.split("|", 1)
        else:
            page = display = link
        display = re.sub(r"<[^>]+>", "", display).strip()
        entries.append((author, page.strip(), display))
    return entries


def extract_poem(poem_page_wt: str) -> str:
    """Pull the 唐詩三百首 reading from a poem page and clean it to bare verse."""
    # Prefer the transcludable region if the page marks one.
    oi = re.search(r"<onlyinclude>(.*?)</onlyinclude>", poem_page_wt, re.DOTALL)
    region = oi.group(1) if oi else poem_page_wt

    # If several textual traditions are stacked under ===version=== subheads,
    # take the anthology's own reading; otherwise keep the whole region.
    version_heads = list(re.finditer(r"===\s*(.+?)\s*===", region))
    if version_heads:
        chosen = None
        for i, vh in enumerate(version_heads):
            start = vh.end()
            end = version_heads[i + 1].start() if i + 1 < len(version_heads) else len(region)
            if "唐詩三百首" in vh.group(1):
                chosen = region[start:end]
                break
        if chosen is None:
            chosen = region[version_heads[0].end():
                            (version_heads[1].start() if len(version_heads) > 1 else len(region))]
        region = chosen

    pm = re.search(r"<poem>(.*?)</poem>", region, re.DOTALL)
    text = pm.group(1) if pm else region

    # Clean apparatus.
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text)
    # Variant-character template -> printed (first) reading.
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{另\|([^|{}]*)\|[^{}]*\}\}", r"\1", text)
    # Drop any other templates (commentary, {{唐詩三百首}}, {{*|…}}).
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Wiki links -> display text.
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Residual inline HTML.
    text = re.sub(r"<templatestyles[^>]*/?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(small|sub|sup|b|i|center|div|span|poem|onlyinclude)\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    # Line-wise trim; keep verse line breaks, drop blank lines.
    lines = [ln.strip() for ln in text.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def make_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str) and ("\n" in v or ":" in v):
            v = f'"{v}"'
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# Offline self-test of extract_poem on captured fixtures.
def _selftest() -> int:
    jingyesi = """{{header|title=靜夜思}}
<onlyinclude>
===李太白全集===
<poem>
牀前看月光，
疑是地上霜。
</poem>
===唐詩三百首===
<poem>
牀前明月光，
疑是地上霜。
舉頭望明月，
低頭思故鄉。
</poem>
</onlyinclude>"""
    dengguan = """<templatestyles src="x.css" />
<center><div class="Kaiti">
<onlyinclude><poem>
白日依山盡，黃河入海流。<small><small><ref>note</ref></small></small>
欲窮千里目，更上一{{另|層|重}}樓。
</poem></onlyinclude>
</div></center>"""
    fengqiao = """{{header}}{{唐詩三百首}}
<onlyinclude>
<poem>
月落烏啼霜滿天，江楓漁火對愁眠。
姑蘇城外寒山寺，夜半鐘聲到客船。
</poem>
</onlyinclude>"""
    a = extract_poem(jingyesi)
    assert a == "牀前明月光，\n疑是地上霜。\n舉頭望明月，\n低頭思故鄉。", repr(a)
    b = extract_poem(dengguan)
    assert b == "白日依山盡，黃河入海流。\n欲窮千里目，更上一層樓。", repr(b)
    c = extract_poem(fengqiao)
    assert c == "月落烏啼霜滿天，江楓漁火對愁眠。\n姑蘇城外寒山寺，夜半鐘聲到客船。", repr(c)
    print("selftest ok")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", default="唐詩三百首")
    p.add_argument("--section", action="append", help="index section to include, repeatable")
    p.add_argument("--delay", type=float, default=5.0)
    p.add_argument("--output")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()

    if args.selftest:
        return _selftest()
    if not args.section or not args.output:
        raise SystemExit("--section and --output are required")

    index_wt = fetch_wikitext(args.index)
    time.sleep(args.delay)

    parts = []
    total_poems = 0
    for section in args.section:
        entries = parse_section(index_wt, section)
        print(f"section {section}: {len(entries)} poems", file=sys.stderr)
        parts.append(f"# {section}")
        for author, page, display in entries:
            wt = fetch_wikitext(page)
            poem = extract_poem(wt)
            if not poem:
                print(f"  WARNING empty poem: {page}", file=sys.stderr)
            parts.append(f"## {display}\n{author}\n\n{poem}")
            total_poems += 1
            print(f"  {display} ({author}) {len(poem)} chars", file=sys.stderr)
            time.sleep(args.delay)

    meta = {
        "title": "唐詩三百首",
        "author": "孫洙",
        "language": "zh-Hant",
        "year": 1763,
        "source": "Wikisource (zh)",
        "source_url": "https://zh.wikisource.org/wiki/%E5%94%90%E8%A9%A9%E4%B8%89%E7%99%BE%E9%A6%96",
        "license": "Public domain in the United States",
    }
    out = make_frontmatter(meta) + "\n\n".join(parts) + "\n"
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest} ({len(out.encode('utf-8')):,} bytes, {total_poems} poems)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
