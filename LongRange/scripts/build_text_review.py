"""Turn the housing dashboard text review sheet into Word and plain-text versions.

`housing-dashboard-text.md` is the source of truth. Edit that, then run this to
regenerate the two files that go out to reviewers:

    python LongRange/scripts/build_text_review.py

The Markdown is written as blocks of

    **T01 - What it is**
    Now: the current wording
    New:

or, where the label would just repeat itself,

    **T04** Now: Map
    New:

Headings starting with `#` open a section, `###` a sub-group, and a line wrapped in
single asterisks becomes an aside. Everything else is treated as a caption sitting above
the rows that follow it.
"""

import argparse
import logging
import re
import textwrap
from pathlib import Path

import build_review_docx

log = logging.getLogger("build_text_review")

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "LongRange" / "docs"
DEFAULT_MD = DOCS / "housing-dashboard-text.md"
DEFAULT_DOCX = DOCS / "Housing Dashboard - Text Review.docx"
DEFAULT_TXT = DOCS / "housing-dashboard-text.txt"

WRAP = 78


def parse(md_text):
    """Parse the sheet into the block list the writers consume."""
    body = md_text.split("# 1. ", 1)
    if len(body) != 2:
        raise SystemExit("Could not find the first numbered section ('# 1. ...') in the sheet.")
    body = "# 1. " + body[1]
    body = body.split("# Other feedback")[0]

    blocks = []
    lines = body.splitlines()
    for i, raw in enumerate(lines):
        ln = raw.strip()
        if ln.startswith("### "):
            blocks.append({"type": "h2", "text": ln[4:].strip()})
        elif ln.startswith("# "):
            blocks.append({"type": "h1", "text": ln[2:].strip()})
        elif ln.startswith("*") and ln.endswith("*") and not ln.startswith("**"):
            blocks.append({"type": "note", "text": ln.strip("*").strip()})
        elif ln.startswith("**T"):
            m = re.match(r"\*\*(T\d+)(?:\s*[—-]\s*(.+?))?\*\*\s*(?:Now:\s*(.*))?$", ln)
            if not m:
                raise SystemExit(f"Could not read entry on line {i + 1}: {ln}")
            tid, desc, inline_now = m.group(1), (m.group(2) or "").strip(), (m.group(3) or "").strip()
            now = inline_now
            if not now:
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("Now:"):
                    j += 1
                if j >= len(lines):
                    raise SystemExit(f"{tid} has no 'Now:' line.")
                now = lines[j].strip()[4:].strip()
            blocks.append({"type": "entry", "id": tid, "desc": desc, "now": now})
        elif ln.startswith(("Now:", "New:")) or not ln:
            continue
        else:
            blocks.append({"type": "para", "text": ln})

    # The Markdown hard-wraps prose, so a single caption arrives as several lines.
    # Glue consecutive ones back together before the writers lay them out.
    merged = []
    for b in blocks:
        if b["type"] == "para" and merged and merged[-1]["type"] == "para":
            merged[-1]["text"] = f"{merged[-1]['text']} {b['text']}".strip()
        else:
            merged.append(dict(b))
    blocks = [b for b in merged if not (b["type"] == "para" and b["text"].strip() == "---")]

    entries = [b for b in blocks if b["type"] == "entry"]
    ids = [e["id"] for e in entries]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"Duplicate IDs in the sheet: {dupes}")
    blank = [e["id"] for e in entries if not e["now"]]
    if blank:
        raise SystemExit(f"Entries with no current wording: {blank}")
    return blocks


def write_txt(blocks, out_path):
    """Plain-text version, for anyone who would rather reply in an email."""
    def wrap(t, indent="", first=None):
        return textwrap.wrap(t, WRAP, initial_indent=first if first is not None else indent,
                             subsequent_indent=indent) or [""]

    o = ["=" * WRAP, "HOUSING PROGRESS SINCE 2012 - TEXT REVIEW SHEET",
         "Tahoe Living housing dashboard", "=" * WRAP, ""]
    o += wrap("This is every piece of wording on the housing dashboard, in the order you "
              "meet it going down the page. Use it to rewrite any of the text.")
    o += ["", "HOW TO USE THIS", "-" * 15]
    for i, s in enumerate([
        "Open the dashboard side by side with this file.",
        "Work down the list. Type your new wording on the 'New:' line under anything you "
        "want changed.",
        "Leave the 'New:' line empty for anything you are happy with. You do not need to "
        "fill in every line.",
        "Save the file and send it back to Mason. Please keep the ID codes (T01, T02, and "
        "so on) - they are how your changes get applied.",
    ], 1):
        o += wrap(s, indent="   ", first=f"{i}. ")
    o += [""] + wrap("Put anything that doesn't fit the list under OTHER FEEDBACK at the "
                     "end. Rough notes are fine.")
    o += ["", "WHAT THIS SHEET CANNOT CHANGE", "-" * 29]
    for b in [
        "Every number. Unit counts, parcel counts, and years all come from the housing "
        "spreadsheet. If a number looks wrong, note it under OTHER FEEDBACK so we can fix "
        "it in the source data.",
        "Jurisdiction names and filter options. These are generated from the data.",
        "Chart colors, layout, and the order of sections. Ask for those under OTHER FEEDBACK.",
    ]:
        o += wrap(b, indent="   ", first=" - ")

    for b in blocks:
        t = b["type"]
        if t == "h1":
            o += ["", "", "=" * WRAP, b["text"].upper(), "=" * WRAP]
        elif t == "h2":
            o += ["", b["text"], "-" * len(b["text"])]
        elif t == "note":
            o += [""] + wrap("NOTE: " + b["text"], indent="      ")
        elif t == "para" and b["text"].strip() != "---":
            o += [""] + wrap(b["text"])
        elif t == "entry":
            head = f"[{b['id']}]" + (f"  {b['desc']}" if b["desc"] else "")
            o += [""] + wrap(head, indent="       ", first="") + \
                 wrap(b["now"], indent="        ", first="   Now: ") + ["   New: "]

    o += ["", "", "=" * WRAP, "OTHER FEEDBACK", "=" * WRAP, ""]
    o += wrap("Anything else: a section that should move, a chart that does not land, a "
              "project worth featuring, a number that looks wrong, or wording you would "
              "rather discuss than rewrite.")
    o += [""] + ["   ." for _ in range(8)]
    o += ["", "", "Reviewed by: ______________________________", "",
          "Date: _____________________________________", ""]

    txt = re.sub(r"\n{4,}", "\n\n\n", "\n".join(o)).strip() + "\n"
    out_path.write_text(txt, encoding="utf-8", newline="\r\n")
    return txt


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    ap.add_argument("--txt", type=Path, default=DEFAULT_TXT)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    blocks = parse(args.md.read_text(encoding="utf-8"))
    entries = [b for b in blocks if b["type"] == "entry"]
    log.info("Parsed %d entries across %d sections",
             len(entries), sum(1 for b in blocks if b["type"] == "h1"))

    build_review_docx.write_docx(blocks, str(args.docx))
    log.info("Wrote %s (%.1f KB)", args.docx.name, args.docx.stat().st_size / 1024)
    write_txt(blocks, args.txt)
    log.info("Wrote %s (%.1f KB)", args.txt.name, args.txt.stat().st_size / 1024)


if __name__ == "__main__":
    main()
