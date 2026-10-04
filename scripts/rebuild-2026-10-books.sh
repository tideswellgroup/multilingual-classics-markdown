#!/bin/sh
# rebuild-2026-10-books.sh: the exact commands that build the eight books
# added on 2026-10-04 (mr, gu, pa, or, te, kn, ml, bo), so any of them can be
# regenerated from its upstream. Each run reuses the book's own frontmatter,
# which is curated by hand, and rewrites only the body.
#
# Usage: scripts/rebuild-2026-10-books.sh [CACHE_DIR]
# With CACHE_DIR, fetched pages are kept there and reused on later runs.
set -eu
cd "$(dirname "$0")/.."
CACHE="${1:-}"
C=""; [ -n "$CACHE" ] && C="--cache $CACHE"

book() { ls "books/$1"/*/*.md; }

# te: seven act sub-pages; the 1961 reprint's notice sub-page (హెచ్చరిక) is not a unit.
# The transcription types Gurajada's dialect mark as a backtick, so backticks are escaped.
TE="$(book te)"
python3 scripts/convert-bn-proofread.py --lang te --top "కన్యాశుల్కము" --structure flat \
  --units "ప్రథమాంకము|ద్వితీయాంకము|తృతీయాంకము|చతుర్థాంకము|పంచమాంకము|షష్ఠాంకము|సప్తమాంకము" \
  --drop-head "శ్రీ" --drop-head "కన్యాశుల్కము" --br-hard --lines-hard --tidy --dedupe-adjacent \
  --escape-backticks \
  --title x --book-title "కన్యాశుల్కము" --author x --language te --year 1909 --source-url x \
  --frontmatter-from "$TE" --output "$TE" $C

# ml: 22 sub-pages in the contents page's order, carrying their own headings. The one
# replacement undoes a TeX-style ``quotation'' the wiki read as an italic opener.
ML="$(book ml)"
python3 scripts/convert-bn-proofread.py --lang ml --top "ഇന്ദുലേഖ" --structure own --skip-redirects \
  --br-hard --lines-hard --tidy --digit-slip "൯=ൻ" --digit-slip "൪=ർ" \
  --replace '``ആഗ്നോസ്റ്റിസിസം *എന്നു്=>“ആഗ്നോസ്റ്റിസിസം” എന്നു്' \
  --replace 'ഏറ്റവുംക്കതെറ്റായ ഒരു പ്രവൃത്തി അല്ലയോ?*=>ഏറ്റവുംക്കതെറ്റായ ഒരു പ്രവൃത്തി അല്ലയോ?' \
  --title x --book-title "ഇന്ദുലേഖ" --author x --language ml --year 1889 --source-url x \
  --frontmatter-from "$ML" --output "$ML" $C

# mr: the author's foreword from the main page, then six pieces headed with their printed titles.
MR="$(book mr)"
python3 scripts/convert-bn-proofread.py --lang mr --top "स्फुट गोष्टी भाग ४ था" --structure flat \
  --top-unit "दोन शब्द|**दोन शब्द.**|**अनुक्रमणिका.**" \
  --units "सगुणाबाईची आपल्या मुलीस पत्रे>1|उलटीकडून सुरुवात>1|प्राचीन दिल्ली>1|द्रौपदी- चरित्र व शील>2|योग्य वेळी नाही म्हणणे>1|गोविंदरावांचीं आपल्या मुलास पत्रे>1" \
  --br-hard --isolate-bold-lines --tidy \
  --title x --book-title "स्फुट गोष्टी भाग ४ था" --author x --language mr --year 1915 --source-url x \
  --frontmatter-from "$MR" --output "$MR" $C

python3 scripts/convert-koti-chennaya.py --frontmatter "$(book kn)" --output "$(book kn)" $C
python3 scripts/convert-sarasvatichandra.py --frontmatter "$(book gu)" --output "$(book gu)" $C
python3 scripts/convert-chha-mana-atha-guntha.py --frontmatter "$(book or)" --output "$(book or)" $C
PA_CACHE=""; [ -n "$CACHE" ] && PA_CACHE="--cache $CACHE/pa-jangnama.json"
python3 scripts/convert-jangnama.py --frontmatter "$(book pa)" --output "$(book pa)" $PA_CACHE
python3 scripts/convert-otdo.py --frontmatter "$(book bo)" --output "$(book bo)" $C
