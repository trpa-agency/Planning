"""Build the housing dashboard text-review Word document from text_blocks.json.

Writes raw WordprocessingML with the standard library only, so it needs no
third-party packages. Run:

    python build_review_docx.py <blocks.json> <out.docx>
"""
import json
import sys
import zipfile
from xml.sax.saxutils import escape

BLUE, BLUE_DARK, GREY = "0A7EC2", "075481", "595959"
BORDER = "D9D9D9"
FILL_IN = "FFFDF0"      # pale cream: where reviewers type
SUBHEAD = "EDF4FA"      # pale blue: in-table subheadings
NOTE_FILL = "FFF9E8"    # pale gold: asides

COLS = [2200, 4300, 3580]           # DXA; sums to the 10080 usable width
TOTAL = sum(COLS)
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def run(text, *, bold=False, italic=False, size=22, color=None):
    rpr = "<w:rPr>"
    if bold:
        rpr += "<w:b/>"
    if italic:
        rpr += "<w:i/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(text="", *, bold=False, italic=False, size=22, color=None,
         after=0, before=0, indent=None, border_bottom=None):
    ppr = "<w:pPr>"
    if indent:
        ppr += f'<w:ind w:left="{indent[0]}" w:hanging="{indent[1]}"/>'
    if border_bottom:
        ppr += (f'<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" '
                f'w:color="{border_bottom}"/></w:pBdr>')
    ppr += f'<w:spacing w:before="{before}" w:after="{after}"/></w:pPr>'
    body = run(text, bold=bold, italic=italic, size=size, color=color) if text else ""
    return f"<w:p>{ppr}{body}</w:p>"


def cell(paras, width, fill=None, span=None):
    tcpr = f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>'
    if span:
        tcpr += f'<w:gridSpan w:val="{span}"/>'
    if fill:
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
    tcpr += "</w:tcPr>"
    return f"<w:tc>{tcpr}{''.join(paras)}</w:tc>"


def row(cells, *, header=False, height=None):
    trpr = ""
    if header or height:
        trpr = "<w:trPr>"
        if height:
            trpr += f'<w:trHeight w:val="{height}" w:hRule="atLeast"/>'
        if header:
            trpr += "<w:tblHeader/>"
        trpr += "</w:trPr>"
    return f"<w:tr>{trpr}{''.join(cells)}</w:tr>"


def table(rows, widths):
    borders = "".join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="{BORDER}"/>'
        for e in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (
        f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/>'
        f"<w:tblBorders>{borders}</w:tblBorders>"
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="110" w:type="dxa"/>'
        '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar>'
        f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{''.join(rows)}</w:tbl>"
    )


def header_row():
    labels = ["Where it appears", "Current wording", "Your new wording"]
    return row(
        [cell([para(t, bold=True, color="FFFFFF", size=19)], COLS[i], BLUE)
         for i, t in enumerate(labels)],
        header=True,
    )


def span_row(text, *, bold=False, italic=False, fill=SUBHEAD):
    color = BLUE_DARK if bold else GREY
    return row([cell([para(text, bold=bold, italic=italic, size=19, color=color)],
                     TOTAL, fill, span=3)])


def entry_row(e):
    left = [para(e["id"], bold=True, size=21, color=BLUE_DARK)]
    if e["desc"]:
        left.append(para(e["desc"], size=17, color=GREY))
    return row([
        cell(left, COLS[0]),
        cell([para(e["now"], size=21)], COLS[1]),
        cell([para("")], COLS[2], FILL_IN),
    ], height=340)


def build(blocks):
    out = []
    out.append(para("Housing Progress Since 2012", bold=True, size=40,
                    color=BLUE_DARK, after=60))
    out.append(para("Text review sheet  ·  Tahoe Living housing dashboard",
                    size=24, color=GREY, after=240, border_bottom=BLUE))
    out.append(para("This is every piece of wording on the housing dashboard, in the "
                    "order you meet it going down the page. Use it to rewrite any of "
                    "the text without touching the website.", after=180))

    out.append(para("How to use this", bold=True, size=24, color=BLUE_DARK, after=100))
    steps = [
        "Open the dashboard side by side with this document.",
        "Work down the tables. Type your new wording in the right-hand column of any "
        "line you want changed.",
        "Leave the right-hand column empty for anything you are happy with. You do not "
        "need to fill in every line.",
        "Save the document and send it back to Mason. Please keep the ID codes (T01, "
        "T02, and so on) — they are how your changes get applied.",
    ]
    for i, s in enumerate(steps, 1):
        out.append(para(f"{i}.\t{s}", after=70, indent=(460, 460)))
    out.append(para("Anything that does not fit the tables goes in Other feedback at the "
                    "end. Rough notes are fine, for example “T34 feels too passive” "
                    "or “can the pipeline chart come first?”.", before=100, after=220))

    out.append(para("What this sheet cannot change", bold=True, size=24,
                    color=BLUE_DARK, after=100))
    bullets = [
        "Every number. Unit counts, parcel counts, and years all come from the housing "
        "spreadsheet. If a number looks wrong, note it under Other feedback so it gets "
        "fixed in the source data.",
        "Jurisdiction names and filter options. These are generated from the data.",
        "Chart colours, layout, and the order of sections. Ask for those under Other "
        "feedback.",
    ]
    for b in bullets:
        out.append(para(f"•\t{b}", after=70, indent=(460, 460)))

    rows = []

    def flush():
        if rows:
            out.append(table([header_row()] + rows, COLS))
            out.append(para("", after=200))
            rows.clear()

    for b in blocks:
        if b["type"] == "h1":
            flush()
            out.append(para(b["text"], bold=True, size=26, color=BLUE_DARK,
                            before=260, after=130))
        elif b["type"] == "h2":
            rows.append(span_row(b["text"], bold=True))
        elif b["type"] == "note":
            rows.append(span_row(b["text"], italic=True, fill=NOTE_FILL))
        elif b["type"] == "para":
            if b["text"].strip() != "---":
                rows.append(span_row(b["text"], italic=True))
        elif b["type"] == "entry":
            rows.append(entry_row(b))
    flush()

    out.append(para("Other feedback", bold=True, size=26, color=BLUE_DARK,
                    before=260, after=110))
    out.append(para("Anything else: a section that should move, a chart that does not "
                    "land, a project worth featuring, a number that looks wrong, or "
                    "wording you would rather discuss than rewrite.", after=150))
    out.append(table(
        [row([cell([para("")], TOTAL, FILL_IN)], height=460) for _ in range(8)],
        [TOTAL],
    ))
    out.append(para("", after=240))
    out.append(table([
        row([cell([para("Reviewed by", bold=True, size=21, color=BLUE_DARK)], 2200),
             cell([para("")], 7880, FILL_IN)], height=400),
        row([cell([para("Date", bold=True, size=21, color=BLUE_DARK)], 2200),
             cell([para("")], 7880, FILL_IN)], height=400),
    ], [2200, 7880]))

    sect = ('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
            '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080" '
            'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f"<w:document {W}><w:body>{''.join(out)}{sect}</w:body></w:document>")


STYLES = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>
<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
<w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="202020"/>
</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>
<w:spacing w:after="0" w:line="259" w:lineRule="auto"/>
</w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
<w:name w:val="Normal"/><w:qFormat/></w:style></w:styles>'''

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''


def main():
    blocks = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2]
    document = build(blocks)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", document)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
