#!/usr/bin/env python3
"""
convert-mdc-hieroglyphs.py: convert a JSesh / Manuel de Codage (MdC)
hieroglyphic transcription into Unicode Egyptian hieroglyphs, and build the
egy book of the Book of the Dead, chapter 17, from the Papyrus of Ani.

Source: Raymond Monfort's transcription in Serge Rosmorduc's MDC-texts
collection (`texts/Book of the dead Chapter 17.gly`), which states
"Licence : Creative commons CC-BY" and "Ref: Budge Pap. Ani et collations
sur photos": Budge's facsimile of the Papyrus of Ani (British Museum, 1890;
2nd ed. 1894), checked against photographs.

Sign codes come from two tables, neither copied from a copyleft source:

- Gardiner-style codes (G17A, D54, Aa1) map to code points through the
  kEH_JSesh field of Unicode's own Unikemet database, shipped as
  scripts/data/egyptian-jsesh-codes.tsv under the Unicode licence.
- Phonetic codes (n, pr, anx), which JSesh accepts as shorthand for a sign,
  map through PHONETIC below: 126 codes. The table was written for this
  converter from the phonetic values of Gardiner's sign list (Egyptian
  Grammar, 1927), then compared with an independent converter, Mark-Jan
  Nederhof's hieropy (run outside this repository and not shipped): 116
  codes agreed at once. The other ten, three read differently, six left open
  and one added later (N), were resolved to agree with hieropy, whose tables
  follow JSesh, the editor the transcriber typed into; each is marked below.

Layout follows the Unicode Standard's Egyptian format controls: `:` stacks
(VERTICAL JOINER), `*` sets side by side (HORIZONTAL JOINER), and a
vertical group inside a horizontal one is wrapped in BEGIN/END SEGMENT. A
ligature (`&`, or `&&&` with a parenthesised group) becomes an insertion of
the smaller sign or group into a corner of the larger, as LIGATURES records
for each of the 23 ligatures the chapter uses. `\\R90` is a rotation, given
by VARIATION SELECTOR-1; a bare `\\` is a horizontal mirror; `\\80` and the
like are size hints with no Unicode equivalent and are dropped. `[[`/`]]`
become square brackets around restored signs.

Known defect: this mapping mostly produces rotation sequences that Unicode
does not standardize. Fix it before reuse.

Not represented, and disclosed in the book: the red ink of the rubrics
(`$r`/`$b`), Monfort's column numbers, his "sic" annotations, and a
trailing `_` on some signs of one line (an editor's mark with no Unicode
form). Signs Unicode does not encode are written as their sign number in
braces, {G234}, never replaced by a sign that resembles them; that covers
signs for which no Unicode mapping has been identified, which may include
signs Unicode encodes under another number.

The output was checked line by line against hieropy's conversion of the
same lines, outside this repository, since hieropy is GPL-licensed; the
converter itself needs only the standard library. --extract-unikemet
regenerates scripts/data/egyptian-jsesh-codes.tsv from a new Unikemet.txt.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CODES_TSV = SCRIPT_DIR / "data" / "egyptian-jsesh-codes.tsv"

VJ, HJ = "\U00013430", "\U00013431"
SEG_OPEN, SEG_CLOSE = "\U00013437", "\U00013438"
MIRROR = "\U00013440"
VS = {"R90": "\uFE00", "R180": "\uFE01", "R270": "\uFE02"}
INSERT = {
    "ts": "\U00013432",  # top start
    "bs": "\U00013433",  # bottom start
    "te": "\U00013434",  # top end
    "be": "\U00013435",  # bottom end
    "m": "\U00013439",   # middle
    "t": "\U0001343A",   # top
    "b": "\U0001343B",   # bottom
}

# Phonetic shorthand to Gardiner number. Entries marked "JSesh" were left
# open or read differently in the first draft and are resolved to agree with
# hieropy, whose tables follow JSesh.
PHONETIC = {
    "A": "G1", "i": "M17", "y": "Z4", "a": "D36", "w": "G43", "b": "D58",
    "p": "Q3", "f": "I9", "m": "G17", "n": "N35", "r": "D21", "h": "O4",
    "H": "V28", "x": "Aa1", "X": "F32", "z": "O34", "s": "S29", "S": "N37",
    "q": "N29", "k": "V31", "g": "W11", "t": "X1", "T": "V13", "d": "D46",
    "D": "I10", "l": "E23", "W": "Z7",
    "M": "Aa15",      # JSesh
    "N": "S3",        # JSesh: the red crown
    "Ax": "G25", "Axt": "N27", "DA": "U28", "Dd": "R11", "Dr": "M36",
    "Dw": "N26", "HA": "M16", "HAt": "F4", "HD": "T3", "Hb": "W3",
    "Hn": "M2", "Hp": "Aa5", "HqA": "S38", "Hr": "D2", "Htp": "R4",
    "Hw": "F18", "Hwt": "O6", "SA": "M8",
    "Sm": "N40",      # JSesh
    "Sms": "T18", "Sn": "V7", "Sw": "H6", "TA": "G47", "Tz": "S24",
    "Xr": "T28", "aA": "O29", "aHA": "D34", "aHa": "P6",
    "ab": "D59",      # JSesh; the first draft had the horn, F16
    "anx": "S34", "aq": "G35", "bnr": "M30", "dwA": "N14", "gm": "G28",
    "grg": "U17", "iAb": "R15",
    "iAt": "N30",     # JSesh
    "ib": "F34", "ii": "M18", "imi": "Z11", "imnt": "R14", "in": "K1",
    "ini": "W25",     # JSesh
    "ir": "D4",
    "iry": "A47",     # JSesh
    "iwn": "O28", "iz": "M40", "kA": "D28", "mH": "V22", "md": "S43",
    "mi": "W19", "mn": "Y5", "ms": "F31", "mw": "N35A", "mwt": "G14",
    "nD": "Aa27", "nH": "G21", "nTr": "R8", "nTrw": "R8A", "nb": "V30",
    "nfr": "F35", "niwt": "O49", "nm": "T34",
    "nn": "M22B",     # JSesh; the first draft had M22A
    "ns": "F20", "nw": "W24", "pA": "G40", "pH": "F22",
    "pXr": "F46",     # JSesh
    "pr": "O1", "pt": "N1", "qd": "Aa28", "ra": "N5", "rd": "D56",
    "rwD": "T12", "sn": "T22", "snD": "G54", "st": "Q1", "sw": "M23",
    "tA": "N16", "ti": "U33", "tm": "U15", "tp": "D1", "tr": "M6",
    "wA": "V4",
    "wD": "V24",      # JSesh; the first draft had V25
    "wa": "T21", "wab": "D60", "wn": "E34", "wp": "F13", "wr": "G36",
    "xa": "N28", "xpr": "L1", "xrw": "P8", "xt": "M3", "zA": "G39",
    "zS": "Y3",
}

# Signs Unikemet's JSesh column omits, matched to a Unicode character by
# name only after checking that JSesh and Unicode mean the same sign. A bare
# name match is not enough: JSesh's F51B is one piece of flesh and Unicode's
# F051B three, and JSesh's G20A is not Unicode's G020A, so both of those
# stay unmapped.
BY_UNICODE_NAME = {"D34": "D034"}  # arms holding shield and axe (aHA)

# Numerals are not JSesh sign codes but keyboard digits; they are mapped by
# Unicode character name, the strokes JSesh draws for them.
NUMERALS = {"2": "Z004A", "3": "Z002A", "4": "Z015C"}

# Ligatures: the Gardiner names joined by '&' (a parenthesised group written
# as GROUP), mapped to (index of the core sign, insertion place). The places
# follow the forms these ligatures take in hieratic-derived hieroglyphic
# writing; they agree with hieropy's conversion, which follows JSesh, on all
# 23. None has yet been compared with the facsimile (see QUALITY.md, egy).
LIGATURES = {
    "I10&D46": (0, "bs"), "G17A&Z4": (0, "te"), "G53&Z1": (0, "te"),
    "G191&X1&Z4": (0, "bs"), "G25&Aa1": (0, "te"), "G1&X1": (0, "te"),
    "I10&O34&I9": (0, "b"), "G43&Z4": (0, "te"), "X1&G43": (1, "bs"),
    "F20&O34": (0, "b"), "G43&X1": (0, "te"), "I10&T3": (0, "bs"),
    "I10&S43": (0, "bs"), "G38&Z1": (0, "te"), "I10&I9": (0, "bs"),
    "I10&Y1": (0, "bs"), "Aa1&D237": (0, "ts"), "D197&P8": (0, "m"),
    "G17&Z4": (0, "te"), "I10&X1&Z1": (0, "bs"), "I10&S29": (0, "bs"),
    "G36&X1": (0, "te"), "N29&U1": (1, "ts"),
    "I10&GROUP": (0, "bs"),
}


def load_codes() -> dict[str, str]:
    codes = {}
    for line in CODES_TSV.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        code, cp = line.split("\t")
        codes[code] = chr(int(cp[2:], 16))
    return codes


CODES = load_codes()


class ConversionError(Exception):
    pass


# Signs Unicode does not encode. Each is written as its sign number in
# braces ({G234}), visible and searchable, rather than replaced by a sign
# that resembles it; the book lists them.
UNENCODED: list[str] = []


def sign_char(code: str) -> tuple[str, str]:
    """Return (Gardiner name, character) for an MdC sign code."""
    if code in NUMERALS:
        return code, unicodedata.lookup("EGYPTIAN HIEROGLYPH " + NUMERALS[code])
    name = PHONETIC.get(code, code)
    if name in CODES:
        return name, CODES[name]
    if name in BY_UNICODE_NAME:
        return name, unicodedata.lookup("EGYPTIAN HIEROGLYPH " + BY_UNICODE_NAME[name])
    UNENCODED.append(name)
    return name, "{" + name + "}"


# --- parsing --------------------------------------------------------------

TOKEN = re.compile(r"""
    (?P<open>\[\[) | (?P<close>\]\]) | (?P<lp>\() | (?P<rp>\)) |
    (?P<lig>&&&|&) | (?P<vj>:) | (?P<hj>\*) | (?P<sep>-) |
    (?P<sign>[A-Za-z0-9]+)(?P<mods>(?:\\R?\d*)*)_?
""", re.VERBOSE)


def tokenize(s: str) -> list[tuple[str, str, str]]:
    out, pos = [], 0
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue
        m = TOKEN.match(s, pos)
        if not m:
            raise ConversionError(f"cannot read {s[pos:pos + 20]!r}")
        kind = m.lastgroup if m.lastgroup != "mods" else "sign"
        if m.group("sign"):
            kind = "sign"
        out.append((kind, m.group(0), m.group("mods") or ""))
        pos = m.end()
    return out


class Parser:
    """items := item ('-' item)* ; item := '[[' | ']]' | vert
    vert := hor (':' hor)* ; hor := lig ('*' lig)* ; lig := atom ('&' atom)*
    atom := SIGN | '(' items ')'"""

    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    def peek(self):
        return self.t[self.i][0] if self.i < len(self.t) else None

    def take(self, kind):
        if self.peek() != kind:
            raise ConversionError(f"expected {kind}, found {self.peek()}")
        self.i += 1
        return self.t[self.i - 1]

    def items(self, stop=None):
        out = []
        while self.peek() is not None and self.peek() != stop:
            k = self.peek()
            if k == "sep":
                self.i += 1
            elif k in ("open", "close"):
                out.append(("bracket", "[" if k == "open" else "]"))
                self.i += 1
            else:
                out.append(self.vert())
        return out

    def vert(self):
        parts = [self.hor()]
        while self.peek() == "vj":
            self.i += 1
            parts.append(self.hor())
        return parts[0] if len(parts) == 1 else ("v", parts)

    def hor(self):
        parts = [self.lig()]
        while self.peek() == "hj":
            self.i += 1
            parts.append(self.lig())
        return parts[0] if len(parts) == 1 else ("h", parts)

    def lig(self):
        parts = [self.atom()]
        while self.peek() == "lig":
            self.i += 1
            parts.append(self.atom())
        return parts[0] if len(parts) == 1 else ("lig", parts)

    def atom(self):
        if self.peek() == "lp":
            self.i += 1
            inner = self.items(stop="rp")
            self.take("rp")
            signs = [x for x in inner if x[0] != "bracket"]
            if len(signs) != 1:
                raise ConversionError("a parenthesised group must hold one group")
            if len(inner) == 1:
                return inner[0]
            return ("bracketed", inner)
        _, text, mods = self.take("sign")
        code = text[: len(text) - len(mods)].rstrip("_") if mods else text.rstrip("_")
        return ("sign", code, mods)


# --- serialising ----------------------------------------------------------

def emit(node) -> str:
    kind = node[0]
    if kind == "sign":
        _, char = sign_char(node[1])
        mods = re.findall(r"\\(R?\d*)", node[2])
        # A variation selector must follow its sign directly; the mirror
        # control comes after it. Bare numbers are size hints with no
        # Unicode equivalent.
        rotation = "".join(VS[m] for m in mods if m in VS)
        mirror = MIRROR if "" in mods else ""
        return char + rotation + mirror
    if kind == "v":
        return VJ.join(emit(c) for c in node[1])
    if kind == "h":
        return HJ.join(SEG_OPEN + emit(c) + SEG_CLOSE if c[0] == "v" else emit(c) for c in node[1])
    if kind == "lig":
        names = [sign_char(c[1])[0] if c[0] == "sign" else "GROUP" for c in node[1]]
        key = "&".join(names)
        if key not in LIGATURES:
            raise ConversionError(f"ligature {key} has no entry in LIGATURES")
        core_i, place = LIGATURES[key]
        rest = [c for i, c in enumerate(node[1]) if i != core_i]
        # Several signs inserted at the top, bottom or middle are stacked;
        # at a corner they sit side by side.
        inserted = rest[0] if len(rest) == 1 else ("v" if place in ("t", "b", "m") else "h", rest)
        body = emit(inserted)
        if len(rest) > 1 or inserted[0] in ("v", "h"):
            body = SEG_OPEN + body + SEG_CLOSE
        return emit(node[1][core_i]) + INSERT[place] + body
    if kind == "bracketed":
        return "".join(x[1] if x[0] == "bracket" else emit(x) for x in node[1])
    raise ConversionError(f"unknown node {kind}")


def convert_line(mdc: str) -> str:
    """One line of MdC (column numbers, ink and line-end marks already
    removed) to a line of Unicode hieroglyphs, groups separated by nothing,
    brackets kept."""
    nodes = Parser(tokenize(mdc)).items()
    return "".join(n[1] if n[0] == "bracket" else emit(n) for n in nodes)


def clean(mdc_line: str) -> str:
    s = re.sub(r"\|\d+", "", mdc_line)
    s = s.replace("|(sic)", "").replace("(sic)", "").replace("|sic", "")
    s = re.sub(r"\$[rb]", "", s)
    return s.rstrip("!").strip("-")


# --- the book ---------------------------------------------------------------

PLATE = re.compile(r"^\+l-?Planche[- ](\w+)")
ROMAN = {"VII": "VII", "8": "VIII", "9": "IX", "10": "X"}


def build(gly: str) -> tuple[str, dict]:
    lines = gly.split("\n")
    out, stats, skipping = [], {"lines": 0, "signs": 0}, False
    for raw in lines:
        if raw.startswith("++") or not raw.strip():
            continue
        if raw.startswith("+"):
            if "Partie-manquante" in raw:
                skipping = True
                out += ["", "[…]", ""]
                continue
            if "Reprise-colonne" in raw:
                skipping = False
                continue
            m = PLATE.match(raw)
            if m:
                out += ["", f"## Plate {ROMAN[m.group(1)]}", ""]
            continue
        if skipping:
            continue
        text = convert_line(clean(raw))
        if text:
            out.append(text + "  ")
            stats["lines"] += 1
            stats["signs"] += sum(1 for c in text if unicodedata.category(c) == "Lo")
    body = "\n".join(out)
    body = re.sub(r"  \n(?=\n|$)", "\n", body + "\n")
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    return body, stats


def extract_unikemet(unikemet: Path, licence: Path) -> int:
    rows, version, seen = [], "Unikemet", set()
    for line in unikemet.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Unikemet-"):
            version = line[2:].strip()
        parts = line.split("\t")
        if len(parts) == 3 and parts[1] == "kEH_JSesh":
            for code in parts[2].split():
                if code not in seen:
                    seen.add(code)
                    rows.append(f"{code}\t{parts[0]}")
    notice = ["# " + x if x else "#" for x in licence.read_text(encoding="utf-8").strip().split("\n")]
    header = [
        "# egyptian-jsesh-codes.tsv: JSesh sign codes and the Unicode code points they denote,",
        f"# extracted from the kEH_JSesh field of {version} in the Unicode Character",
        "# Database (https://www.unicode.org/Public/UCD/latest/ucd/Unikemet.txt) by",
        "# scripts/convert-mdc-hieroglyphs.py --extract-unikemet. Where Unikemet gives one",
        "# code for several code points, the first is kept. Distributed under the",
        "# Unicode licence, whose notice follows.",
        "#",
    ] + notice + ["#", "# code\tcode point"]
    CODES_TSV.write_text("\n".join(header + rows) + "\n", encoding="utf-8")
    print(f"wrote {CODES_TSV}: {len(rows)} codes from {version}", file=sys.stderr)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", help="the .gly file")
    p.add_argument("--frontmatter", help="a .yml block, or the existing book itself")
    p.add_argument("--output")
    p.add_argument("--extract-unikemet", metavar="UNIKEMET_TXT",
                   help="rewrite scripts/data/egyptian-jsesh-codes.tsv from this Unikemet.txt "
                        "and the Unicode licence text in --unicode-license, then exit")
    p.add_argument("--unicode-license", metavar="LICENSE_TXT")
    args = p.parse_args()
    if args.extract_unikemet:
        return extract_unikemet(Path(args.extract_unikemet), Path(args.unicode_license))
    if not (args.source and args.frontmatter and args.output):
        p.error("--source, --frontmatter and --output are required")
    gly = Path(args.source).read_text(encoding="utf-8")
    body, stats = build(gly)
    fm = Path(args.frontmatter).read_text(encoding="utf-8")
    block = re.match(r"---\n.*?\n---\n", fm, re.DOTALL)
    fm = block.group(0) if block else fm.rstrip("\n") + "\n"
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(fm + body, encoding="utf-8")
    print(f"wrote {args.output}: {stats['lines']} lines, {stats['signs']} signs; "
          f"unencoded {len(UNENCODED)}: {sorted(set(UNENCODED))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
