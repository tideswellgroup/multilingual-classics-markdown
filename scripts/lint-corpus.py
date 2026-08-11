#!/usr/bin/env python3
"""
lint-corpus.py: validation pass over vendored corpus markdown files.

Catches the bug classes we hit during corpus conversion: math delimiter
imbalance, broken \\right\\\\left. patterns from dropped braces, trailing
punctuation after display-math $$, Wikisource license-template debris,
orphan <math> HTML tags, residual wiki templates, missing or malformed
YAML frontmatter.

Usage:
  scripts/lint-corpus.py <path>...           # report findings
  scripts/lint-corpus.py --fix <path>...     # auto-fix safe issues
  scripts/lint-corpus.py --strict <path>...  # warnings become errors

Exits 0 if clean (or --fix succeeded); 1 if unresolved issues remain.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class Issue:
    severity: str
    line: int
    code: str
    message: str
    fix_available: bool = False


@dataclass
class FileReport:
    path: Path
    issues: list[Issue] = field(default_factory=list)
    fixed: list[Issue] = field(default_factory=list)


WIKISOURCE_DEBRIS_STRINGS = [
    "Public domainPublic domainfalsefalse",
    "rule of the shorter term",
    "longest-living author of this work died in",
    "This work is in the **public domain** in the **United States** because it was published before",
    "This work was published before January 1",
]

WIKISOURCE_FOOTER_HEADINGS = re.compile(r"^##\s+(Footnotes|External links|References|See also|Categories)\s*$", re.MULTILINE)


# Per-locale expected Unicode blocks for script-presence verification.
# Each value is a list of (start_codepoint, end_codepoint) inclusive ranges.
# Locales not listed default to Latin and aren't script-presence-checked.
LOCALE_SCRIPT_BLOCKS: dict[str, list[tuple[int, int]]] = {
    "ar": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "fa": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "ur": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "he": [(0x0590, 0x05FF), (0xFB1D, 0xFB4F)],
    "el": [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    "hi": [(0x0900, 0x097F)],
    "ja": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF), (0x3000, 0x303F)],
    "ko": [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],
    "ru": [(0x0400, 0x04FF), (0x0500, 0x052F)],
    "th": [(0x0E00, 0x0E7F)],
    "vi": [(0x0080, 0x024F), (0x1E00, 0x1EFF)],
    "zh-Hans": [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x3000, 0x303F)],
    "chr": [(0x13A0, 0x13FF), (0xAB70, 0xABBF)],
}

# Common HTML tags that shouldn't appear in body text (post-conversion).
# Excludes tags that markdown renderers commonly accept as inline HTML.
HTML_TAGS_OF_CONCERN = re.compile(
    r"<(?:p|div|span|table|tr|td|th|tbody|thead|tfoot|a|img|ul|ol|li|"
    r"section|article|header|footer|nav|aside|figure|figcaption|"
    r"strong|em|b|i|u|s|br|hr|caption|colgroup|col|"
    r"small|big|font|center|sup|sub)(?:\s[^>]*)?>",
    re.IGNORECASE,
)

# Plain scalars that YAML 1.1 parsers coerce to booleans or null instead of
# strings (pyyaml turns `language: no` into False). Values matching these
# must be quoted in frontmatter.
YAML_COERCED_SCALARS = {"y", "yes", "n", "no", "on", "off", "true", "false", "null", "~"}


def check_frontmatter(text: str, path: Path | None = None) -> list[Issue]:
    issues = []
    # classic-books vendored from mlschmitt upstream verbatim; no frontmatter expected
    if path and "classic-books" in str(path):
        return issues
    if not text.startswith("---\n"):
        issues.append(Issue("error", 1, "FM001", "missing YAML frontmatter opener `---`"))
        return issues
    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        issues.append(Issue("error", 1, "FM002", "unterminated YAML frontmatter (no closing `---`)"))
        return issues
    fm = text[4:end_idx]
    required = ["title", "author", "language", "year", "source", "license"]
    for key in required:
        if not re.search(rf"^{key}:", fm, re.MULTILINE):
            issues.append(Issue("warn", 1, "FM003", f"frontmatter missing recommended field: {key}"))
    year_line = re.search(r"^year:\s*(.+)$", fm, re.MULTILINE)
    if year_line:
        v = year_line.group(1).strip()
        if v and v[0] not in '"' and not v.lstrip("-").isdigit():
            issues.append(Issue("warn", 1, "FM004", f"year value {v!r} should be quoted (non-integer)"))
    # The repo's own tooling reads frontmatter with a regex, but external
    # consumers feed these blocks to strict YAML parsers; catch the two ways
    # an unquoted plain scalar silently breaks there.
    for lineno, line in enumerate(fm.split("\n"), start=2):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s+(\S.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).rstrip()
        if value[0] in "\"'":
            continue
        if ": " in value or value.endswith(":"):
            issues.append(Issue(
                "error", lineno, "FM005",
                f"unquoted {key} value contains a colon that breaks strict YAML parsers; quote the value"))
        if value.lower() in YAML_COERCED_SCALARS:
            issues.append(Issue(
                "error", lineno, "FM006",
                f"{key} value {value!r} parses as a YAML boolean/null, not a string; quote it"))
    return issues


def check_math_left_right_balance(text: str, body_start: int) -> list[Issue]:
    issues = []
    body = text[body_start:]
    left_count = len(re.findall(r"\\left[\\.(\[\{|]", body))
    right_count = len(re.findall(r"\\right[\\.)\]\}|]", body))
    if left_count != right_count:
        issues.append(
            Issue(
                "error", 0, "M001",
                f"\\left ({left_count}) / \\right ({right_count}) count mismatch",
            )
        )
    return issues


def check_broken_left_right_delim(text: str, body_start: int) -> list[Issue]:
    """Catch `\\right\\\\left.` pattern (missing } between right and left)."""
    issues = []
    for m in re.finditer(r"\\right\\\\left[\\.]", text):
        line = text.count("\n", 0, m.start()) + 1
        issues.append(
            Issue("error", line, "M002",
                  r"`\right\\left.` pattern (missing `}` delimiter after \right)",
                  fix_available=True)
        )
    return issues


def check_display_math_trailing_junk(text: str) -> list[Issue]:
    """Lines like `$$ math $$ .` or `$$ math $$ ,` - trailing punct breaks the suffix match.
    Use [ \\t] (horizontal whitespace) rather than \\s so the second group can't span
    newlines and false-positive on clean math lines followed by a paragraph."""
    issues = []
    pattern = re.compile(r"^(\$\$ .* \$\$)([.,;:!?]+[ \t]*|[ \t]+\S.*)$", re.MULTILINE)
    for m in pattern.finditer(text):
        if "$$" in m.group(2):
            continue
        line = text.count("\n", 0, m.start()) + 1
        issues.append(
            Issue("warn", line, "M003",
                  "display math `$$ ... $$` followed by trailing content (KaTeX may not match)",
                  fix_available=True)
        )
    return issues


def check_wikisource_debris(text: str) -> list[Issue]:
    issues = []
    for marker in WIKISOURCE_DEBRIS_STRINGS:
        idx = text.find(marker)
        if idx != -1:
            line = text.count("\n", 0, idx) + 1
            issues.append(
                Issue("error", line, "W001",
                      f"Wikisource license-template debris: {marker!r}",
                      fix_available=True)
            )
    for m in WIKISOURCE_FOOTER_HEADINGS.finditer(text):
        end = text.find("\n## ", m.end())
        if end == -1:
            end = len(text)
        section_body = text[m.end():end].strip()
        if any(s in section_body for s in WIKISOURCE_DEBRIS_STRINGS):
            line = text.count("\n", 0, m.start()) + 1
            issues.append(
                Issue("error", line, "W002",
                      f"Wikisource footer-section heading {m.group(1)!r} precedes license debris",
                      fix_available=True)
            )
    return issues


def check_orphan_math_tags(text: str) -> list[Issue]:
    issues = []
    for m in re.finditer(r"<math[^>]*>|</math>", text):
        line = text.count("\n", 0, m.start()) + 1
        issues.append(
            Issue("error", line, "M004",
                  f"orphan {m.group(0)!r} HTML tag (should have been converted to `$...$`)")
        )
    return issues


def check_orphan_wikitext_templates(text: str) -> list[Issue]:
    issues = []
    for m in re.finditer(r"\{\{[^{}\n]{1,200}\}\}", text):
        snippet = m.group(0)
        if "$$" in text[max(0, m.start() - 10):m.start()]:
            continue
        if "$" in snippet:
            continue
        line = text.count("\n", 0, m.start()) + 1
        issues.append(
            Issue("warn", line, "W003",
                  f"orphan wikitext template: {snippet[:60]!r}")
        )
    return issues


def check_empty_center_tags(text: str) -> list[Issue]:
    issues = []
    for m in re.finditer(r"<center[^>]*>\s*</center>", text):
        line = text.count("\n", 0, m.start()) + 1
        issues.append(
            Issue("warn", line, "H001",
                  "empty <center> tag (rendering noise)",
                  fix_available=True)
        )
    return issues


def check_body_non_empty(text: str, body_start: int) -> list[Issue]:
    body = text[body_start:].strip()
    if len(body) < 100:
        return [Issue("error", 0, "B001", f"body is suspiciously short ({len(body)} chars)")]
    return []


def extract_locale(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        return None
    fm = text[4:end_idx]
    m = re.search(r"^language:\s*(\S+)", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def check_script_presence(text: str, body_start: int, locale: str | None) -> list[Issue]:
    """Verify the body contains characters from the expected Unicode block(s)
    for the locale. Catches conversion failures where the source was
    stripped down to ASCII boilerplate."""
    if locale is None or locale not in LOCALE_SCRIPT_BLOCKS:
        return []
    blocks = LOCALE_SCRIPT_BLOCKS[locale]
    body = text[body_start:]
    count = sum(
        1 for ch in body
        if any(start <= ord(ch) <= end for start, end in blocks)
    )
    body_len = max(len(body), 1)
    ratio = count / body_len
    if count < 50:
        return [Issue(
            "error", 0, "S001",
            f"locale {locale}: only {count} chars from expected script blocks "
            f"({ratio:.1%} of body); conversion likely lost the script content"
        )]
    if ratio < 0.05 and count < 500:
        return [Issue(
            "warn", 0, "S002",
            f"locale {locale}: {count} chars from expected script ({ratio:.1%} of body); "
            "ratio is low; verify the body wasn't mostly stripped to ASCII"
        )]
    return []


def check_suspicious_unicode(text: str) -> list[Issue]:
    """Catch characters that signal encoding errors or rendering risks."""
    issues = []
    replacement_count = text.count("�")
    if replacement_count > 0:
        issues.append(Issue(
            "error", 0, "U001",
            f"{replacement_count} U+FFFD REPLACEMENT CHARACTERs present (encoding broken upstream)"
        ))
    # Private Use Area chars (excluding intentional script-PUA like Tengwar/Klingon
    # which we don't have in this corpus)
    pua_count = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    if pua_count > 0:
        issues.append(Issue(
            "warn", 0, "U002",
            f"{pua_count} Private Use Area characters (U+E000-U+F8FF); "
            "may render as tofu without specific font support"
        ))
    return issues


def check_brace_balance_in_math(text: str) -> list[Issue]:
    """Inside $$...$$ blocks (single-line) and $...$ inline math, group braces
    should balance. Skips escaped braces (`\\{`, `\\}`) and treats `\\\\`
    (LaTeX line break) as a non-escape so that `\\\\{...}` row separators
    inside `\\begin{array}` blocks don't get miscounted."""
    issues = []
    for m in re.finditer(r"\$\$([^$\n]+)\$\$", text):
        inner = m.group(1)
        opens = 0
        closes = 0
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                if nxt == "\\":
                    # \\ is a line break, not an escape; consume both
                    i += 2
                    continue
                if nxt in "{}":
                    # \{ or \} is an escaped brace literal, doesn't count
                    i += 2
                    continue
                # \X is a command; skip the backslash and let the next iter
                # handle the command name normally
                i += 1
                continue
            if ch == "{":
                opens += 1
            elif ch == "}":
                closes += 1
            i += 1
        if opens != closes:
            line = text.count("\n", 0, m.start()) + 1
            issues.append(Issue(
                "error", line, "M005",
                f"display math brace imbalance: {opens} open vs {closes} close in `{m.group(0)[:60]}...`"
            ))
    return issues


def check_math_begin_end_balance(text: str, body_start: int) -> list[Issue]:
    """\\begin{X} and \\end{X} should pair up across the document."""
    body = text[body_start:]
    begins = re.findall(r"\\begin\{([a-z*]+)\}", body)
    ends = re.findall(r"\\end\{([a-z*]+)\}", body)
    issues = []
    if len(begins) != len(ends):
        issues.append(Issue(
            "error", 0, "M006",
            rf"\begin{{}} ({len(begins)}) vs \end{{}} ({len(ends)}) count mismatch"
        ))
    # Per-environment match
    from collections import Counter
    b_counts = Counter(begins)
    e_counts = Counter(ends)
    for env in set(b_counts) | set(e_counts):
        if b_counts[env] != e_counts[env]:
            issues.append(Issue(
                "error", 0, "M007",
                rf"\begin{{{env}}} ({b_counts[env]}) vs \end{{{env}}} ({e_counts[env]}) mismatch"
            ))
    return issues


def check_heading_hierarchy(text: str, body_start: int) -> list[Issue]:
    """Heading levels shouldn't skip (e.g. # then ###). Warn on jumps > 1."""
    issues = []
    body = text[body_start:]
    headings = re.findall(r"^(#{1,6})\s+\S", body, re.MULTILINE)
    if not headings:
        return issues
    prev_level = 0
    for h in headings:
        level = len(h)
        if prev_level > 0 and level > prev_level + 1:
            # Skip-level jump; first occurrence only as a warning
            issues.append(Issue(
                "warn", 0, "H002",
                f"heading-level jump from h{prev_level} to h{level} (outline skips a level)"
            ))
            break
        prev_level = level
    return issues


def check_code_fence_balance(text: str, body_start: int) -> list[Issue]:
    """``` fences must come in pairs."""
    body = text[body_start:]
    fence_count = len(re.findall(r"^```", body, re.MULTILINE))
    if fence_count % 2 != 0:
        return [Issue(
            "error", 0, "C001",
            f"odd number of ``` code fences ({fence_count}); rendering will leak code-block styling"
        )]
    return []


def check_html_leakage(text: str, body_start: int) -> list[Issue]:
    """Common HTML tags shouldn't appear in body text. The extension
    preprocessor emits its own HTML for math etc., but raw <p>, <div>,
    <table>, <a>, <img>, <span> etc. usually mean the converter missed
    something."""
    issues = []
    body = text[body_start:]
    seen = {}
    for m in HTML_TAGS_OF_CONCERN.finditer(body):
        tag = m.group(0)[:40]
        seen[tag] = seen.get(tag, 0) + 1
    for tag, count in sorted(seen.items()):
        if count >= 1:
            issues.append(Issue(
                "warn", 0, "X001",
                f"HTML tag {tag!r} appears {count}x in body (would render as literal text in markdown)"
            ))
    return issues


CMARK_TAG = re.compile(
    r"</?([a-zA-Z][a-zA-Z0-9-]*)"
    r"(?:\s+[a-zA-Z_:][a-zA-Z0-9_.:-]*(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s\"'=<>`]+))?)*\s*/?>"
)

# Standard HTML element names: a match on one of these falls to the
# X001 known-tag warning instead. Everything else in tag shape is an
# OCR pseudo-tag.
KNOWN_HTML_ELEMENTS = frozenset("""
a abbr address area article aside audio b base bdi bdo blockquote body br
button canvas caption cite code col colgroup data datalist dd del details
dfn dialog div dl dt em embed fieldset figcaption figure footer form h1 h2
h3 h4 h5 h6 head header hgroup hr html i iframe img input ins kbd label
legend li link main map mark math menu meta meter nav noscript object ol
optgroup option output p param picture pre progress q rp rt ruby s samp
script section select slot small source span strong style sub summary sup
table tbody td template textarea tfoot th thead time title tr track u ul
var video wbr center font
""".split())


def check_pseudo_html_tags(text: str, body_start: int) -> list[Issue]:
    """OCR garbage in raw-HTML tag shape (`<iaci>`, `<Mb>`) parses as an
    inline HTML tag in cmark and is then DROPPED by a fail-closed
    sanitiser: silent content loss in the reader, found by a structural
    render audit on the demoted eo Fundamento scan (2026-07-17).
    Known HTML element names fall to the X001 warning instead; anything
    else in tag shape is an error. The fix is escaping the opening
    bracket (`&lt;`), which renders the literal text the page shows."""
    issues = []
    body = text[body_start:]
    for m in CMARK_TAG.finditer(body):
        name = m.group(1).lower()
        if name in KNOWN_HTML_ELEMENTS:
            continue
        line = body.count("\n", 0, m.start()) + 1
        issues.append(Issue(
            "error", line, "X002",
            f"pseudo-HTML tag {m.group(0)[:40]!r} would be parsed as raw HTML and "
            f"silently dropped by the renderer's sanitiser; escape the '<' as &lt;"
        ))
    return issues


def check_extreme_long_lines(text: str, body_start: int) -> list[Issue]:
    """Lines over ~20k chars usually indicate paragraph-break loss in conversion.

    Line numbers are reported file-relative, counting the frontmatter, so that
    jumping to the reported line in an editor lands on the offending paragraph.
    """
    body = text[body_start:]
    frontmatter_lines = text.count("\n", 0, body_start)
    issues = []
    for i, line in enumerate(body.splitlines(), 1):
        if len(line) > 20000:
            lineno = i + frontmatter_lines
            issues.append(Issue(
                "warn", lineno, "L001",
                f"line {lineno} is {len(line)} chars (very long; may indicate paragraph-break loss)"
            ))
            break  # one warning per file
    return issues


def find_body_start(text: str) -> int:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return end + 5
    return 0


def lint_file(path: Path) -> FileReport:
    report = FileReport(path=path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        report.issues.append(Issue("error", 0, "E001", f"not valid UTF-8: {e}"))
        return report

    body_start = find_body_start(text)
    has_math = "$$" in text or "$" in text[body_start:]
    locale = extract_locale(text)

    report.issues.extend(check_frontmatter(text, path))
    report.issues.extend(check_wikisource_debris(text))
    report.issues.extend(check_orphan_math_tags(text))
    report.issues.extend(check_empty_center_tags(text))
    report.issues.extend(check_body_non_empty(text, body_start))
    report.issues.extend(check_orphan_wikitext_templates(text))
    report.issues.extend(check_script_presence(text, body_start, locale))
    report.issues.extend(check_suspicious_unicode(text))
    report.issues.extend(check_heading_hierarchy(text, body_start))
    report.issues.extend(check_code_fence_balance(text, body_start))
    report.issues.extend(check_html_leakage(text, body_start))
    report.issues.extend(check_pseudo_html_tags(text, body_start))
    report.issues.extend(check_extreme_long_lines(text, body_start))

    if has_math:
        report.issues.extend(check_math_left_right_balance(text, body_start))
        report.issues.extend(check_broken_left_right_delim(text, body_start))
        report.issues.extend(check_display_math_trailing_junk(text))
        report.issues.extend(check_brace_balance_in_math(text))
        report.issues.extend(check_math_begin_end_balance(text, body_start))

    return report


def fix_file(path: Path, report: FileReport) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    n_fixed = 0

    for marker in WIKISOURCE_DEBRIS_STRINGS:
        if marker in text:
            for heading_match in reversed(list(WIKISOURCE_FOOTER_HEADINGS.finditer(text))):
                end = text.find("\n## ", heading_match.end())
                if end == -1:
                    end = len(text)
                section_body = text[heading_match.end():end]
                if any(s in section_body for s in WIKISOURCE_DEBRIS_STRINGS):
                    text = text[:heading_match.start()].rstrip() + "\n"
                    n_fixed += 1
                    break

    new = re.sub(r"\\right\\\\left([\\.])", r"\\right\\}\\left\1", text)
    if new != text:
        n_fixed += text.count(r"\right\\left") - new.count(r"\right\\left")
        text = new

    def strip_trailing(m: re.Match) -> str:
        return m.group(1)
    new = re.sub(r"^(\$\$ .* \$\$)[.,;:!?]+\s*$", strip_trailing, text, flags=re.MULTILINE)
    if new != text:
        n_fixed += text.count("\n") - new.count("\n") + 1
        text = new

    new = re.sub(r"<center[^>]*>\s*</center>", "", text)
    if new != text:
        text = new
        n_fixed += 1

    if text != original:
        path.write_text(text, encoding="utf-8")
        report.fixed = [i for i in report.issues if i.fix_available]
        report.issues = [i for i in report.issues if not i.fix_available]

    return n_fixed


REPO_SCAFFOLD_FILES = {
    "CORPUS.md", "README.md", "MEMORY.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "LICENSE.md", "LICENSE-CONTENT.md",
    "LICENSE-CODE.md", "CHANGELOG.md", "SECURITY.md", "AUTHORS.md",
}


def find_md_files(roots: list[str]) -> list[Path]:
    paths = []
    for root in roots:
        p = Path(root)
        if p.is_file() and p.suffix == ".md":
            paths.append(p)
        elif p.is_dir():
            paths.extend(sorted(p.rglob("*.md")))
    return [
        p for p in paths
        if p.name not in REPO_SCAFFOLD_FILES
        and ".github" not in p.parts
    ]


def run_katex_math_gate(paths: list[str]) -> int:
    """Run the node KaTeX-compatibility gate over the given paths.

    Returns the gate's exit code: 0 clean, 1 failures, 2 environment problem.
    Validates only docs declaring `equation_encoding: KaTeX-compatible ...`,
    so it is a no-op for non-math prose corpora. Skips (returns 0) with a
    notice if node is unavailable, the regex/balance checks here still run.
    """
    if shutil.which("node") is None:
        print("\n[KaTeX gate] node not found; skipping math validation", file=sys.stderr)
        return 0
    script = Path(__file__).with_name("validate-corpus-math.js")
    if not script.exists():
        print("\n[KaTeX gate] validate-corpus-math.js not present; skipping math validation", file=sys.stderr)
        return 0
    print("\n--- KaTeX corpus-math gate ---")
    result = subprocess.run(["node", str(script), *paths])
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="files or directories to lint")
    parser.add_argument("--fix", action="store_true", help="auto-fix safe issues in place")
    parser.add_argument("--strict", action="store_true", help="warnings exit non-zero")
    parser.add_argument("--quiet", action="store_true", help="suppress per-file output for clean files")
    parser.add_argument(
        "--no-katex",
        action="store_true",
        help="skip the KaTeX corpus-math compatibility gate",
    )
    args = parser.parse_args()

    files = find_md_files(args.paths)
    if not files:
        print("no .md files found", file=sys.stderr)
        return 0

    total_errors = 0
    total_warnings = 0
    total_fixed = 0
    files_with_issues = 0

    for path in files:
        report = lint_file(path)

        if args.fix and any(i.fix_available for i in report.issues):
            n = fix_file(path, report)
            total_fixed += n

        errors = [i for i in report.issues if i.severity == "error"]
        warnings = [i for i in report.issues if i.severity == "warn"]
        total_errors += len(errors)
        total_warnings += len(warnings)

        if errors or warnings or report.fixed:
            files_with_issues += 1

        if not args.quiet or errors or warnings or report.fixed:
            try:
                rel = path.relative_to(Path.cwd()) if path.is_absolute() else path
            except ValueError:
                # Absolute path outside the working directory; show it in full
                # rather than raising, so linting a file anywhere still reports.
                rel = path
            if errors or warnings or report.fixed:
                print(f"\n{rel}")
                for issue in report.fixed:
                    print(f"  [FIXED] line {issue.line}: {issue.code} {issue.message}")
                for issue in errors:
                    print(f"  [ERROR] line {issue.line}: {issue.code} {issue.message}")
                for issue in warnings:
                    print(f"  [WARN]  line {issue.line}: {issue.code} {issue.message}")

    print(f"\n--- summary ---")
    print(f"files scanned: {len(files)}")
    print(f"files with issues: {files_with_issues}")
    print(f"errors: {total_errors}")
    print(f"warnings: {total_warnings}")
    if args.fix:
        print(f"auto-fixes applied: {total_fixed}")

    katex_rc = 0 if args.no_katex else run_katex_math_gate(args.paths)

    if total_errors > 0:
        return 1
    if katex_rc != 0:
        return 1
    if args.strict and total_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
