"""Fail if the text review sheet no longer matches the dashboard page.

The sheet is what reviewers mark up, so a page whose wording has moved on sends
them to comment on text that is no longer there. That happened in Oct. 2026:
three commits changed the page, the sheet was not regenerated, and Karen Fink
reviewed a stale copy.

    python LongRange/scripts/check_text_review.py

Exits non-zero and lists the offending entries when any "Now:" line in the sheet
is missing from the page.
"""

import html
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SHEET = REPO_ROOT / "LongRange" / "docs" / "housing-dashboard-text.md"
PAGE = REPO_ROOT / "LongRange" / "html" / "multifamily-housing.html"

# Entries the reader sees assembled at runtime, so they never appear in the
# source as one literal string. Checking them would always fail.
ASSEMBLED = {
    "T22": "hover note built from a template with unit counts spliced in",
    "T39": "link label that toggles between two wordings",
    "T40": "record counter whose numbers are filled in",
    "T71": "milestone, year and label stored separately",
    "T72": "milestone, year and label stored separately",
    "T73": "milestone, year and label stored separately",
    "T133": "milestone, year and label stored separately",
    "T83": "featured card figure, value and label stored separately",
    "T84": "featured card figure, value and label stored separately",
    "T88": "featured card figure, value and label stored separately",
    "T89": "featured card figure, value and label stored separately",
    "T93": "featured card figure, value and label stored separately",
    "T94": "featured card figure, value and label stored separately",
    "T121": "pop-up column headings, joined with separators",
    "T124": "footer credit, part of it a link",
}

ENTRY = re.compile(r"\*\*(T\d+)(?:[^*]*)\*\*\s*\n?Now: (.+)")


def main() -> int:
    if not SHEET.exists() or not PAGE.exists():
        print(f"check_text_review: missing {SHEET if not SHEET.exists() else PAGE}")
        return 1

    page = html.unescape(PAGE.read_text(encoding="utf-8"))
    entries = ENTRY.findall(SHEET.read_text(encoding="utf-8"))
    if not entries:
        print("check_text_review: no entries found in the sheet, is it intact?")
        return 1

    drift = [(tid, text.strip()) for tid, text in entries
             if tid not in ASSEMBLED and text.strip() not in page]

    if drift:
        print(f"\ncheck_text_review: {len(drift)} of {len(entries)} sheet entries are no "
              f"longer on the page.\n")
        for tid, text in drift:
            print(f"  {tid:<6} {text[:92]}")
        print(
            "\nThe sheet goes out to reviewers, so it has to match what they see.\n"
            f"Update {SHEET.relative_to(REPO_ROOT)} to the current wording, drop entries\n"
            "for anything removed, then regenerate:\n\n"
            "    python LongRange/scripts/build_text_review.py\n\n"
            "To commit anyway, pass --no-verify.\n"
        )
        return 1

    print(f"check_text_review: all {len(entries)} sheet entries match the page.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
