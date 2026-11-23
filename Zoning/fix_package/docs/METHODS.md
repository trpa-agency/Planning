# Methods: zoning QA fixes

Owner: mason.bindl@trpa.gov
Last reviewed: 2026-11-20

## Purpose

This package turns the zoning QA findings into edits for SDE. It covers the Permissible Use and Special Designation tables, the District polygons, and the zoning attributes stored on parcels. It only proposes edits that the plan documents or the data itself support. Use rows were checked for 94 Plan Area Statements, five area plans (Washoe, Placer, Meyers, Tahoe Valley, Tourist Core), and three community plans (Round Hill, Bijou/Al Tahoe, South Y Industrial Tract). The South Shore Area Plan was not checked (decision R15).

## Data sources

| Source | Type | Notes |
|---|---|---|
| Zoning/MapServer layers 0, 1, 6, 7 | ArcGIS REST, pulled 2026-11-20 | District, Parcel attributes, Permissible Use, Special Designation |
| LocalPlan/MapServer layer 0 | ArcGIS REST | Parcel geometry; the Zoning service Parcel layer returns null geometry |
| LocalPlan/MapServer layer 1 | ArcGIS REST | Plan boundaries and the File_URL link to each plan PDF |
| Boundaries/MapServer layers 4 and 10 | ArcGIS REST | TRPA boundary and jurisdictions, for the review gaps layer |
| 94 Plan Area Statement PDFs | trpa.gov, via File_URL | Source of every use, status, and density check |

Live edit dates were rechecked on 2026-11-20 at 7:30 p.m. and had not changed since the snapshot.

## How fixes were found

1. Each PDF was converted to text with pdftotext in layout mode. The Permissible Uses section was parsed into the general list and each special area list. A list that says "plus the following additions" adds to the general list. A list without it replaces the general list. A category that reads "those uses listed on the General List" pulls that category in.
2. About 225 PDF wordings were mapped to the use names in the table. Combined phrases were split into their parts.
3. Each district's expected list was compared to the service. Every mismatch was then read against the PDF text by hand before becoming a fix. Page numbers come from the PDF page breaks.
4. Densities were parsed from each Maximum Densities table, including the bullet rows for hotel units with and without kitchens, and compared the same way.
5. Spatial checks ran in EPSG 26910, the District feature class's native projection, with District geometry pulled in that projection to avoid reprojection error.

## Area plans and community plans

Each document has its own table layout, so each got its own parser, and every flagged row was read against the page before it became a fix.

| Plan | Source | Layout | Rule for special areas |
|---|---|---|---|
| Washoe County Tahoe Area Plan | Development Code Article 220, Dec 17, 2025 | One table per regulatory zone | Code section 110.220.130: a special area list is "independent and complete, not supplemental," except where it says "Same as General List" or "As above" |
| Placer County Tahoe Basin Area Plan | Implementing Regulations, Feb 2021 | One-column tables per subdistrict; matrices for the mixed-use groups and Lake Forest Commercial | A special area gets the base list; rows marked "Limited to Special Area #1" belong only to the special area |
| Meyers Area Plan | Table 2-1, March 2018 | Matrix, P and CUP | None |
| Tahoe Valley Area Plan | Table 1, amended Dec 18, 2024 | Matrix, A and S, footnotes | None |
| Tourist Core Area Plan | Table 1, Dec 2024 | Matrix; one column covers TSC-MUC and its Special Area 1 | Footnote 9 uses are not permitted in TSC-MUC Special Area 1 |
| Round Hill Community Plan | Chapter II, Nov 1993 | Prose lists like a Plan Area Statement | Special Area 2 resource management is "Same as Special Area #1" |
| Bijou/Al Tahoe Community Plan | Permissible Uses Matrix, Oct 1995 | Matrix with blank cells; districts 1 to 4 | Districts 1 to 4 map to 098_SA1 to 098_SA4 (confirmed by a 99 percent match) |
| South Y Industrial Tract Community Plan | Chapter II matrix, March 2003 | List with Allowed, Special Use, or No | None |

Status codes map as follows. Washoe: A is Allowed, S and AR are Special Use (the code says AR is processed as a TRPA special use). Placer: A is Allowed, C is Administrative Review, MUP is Minor Use, CUP is Conditional Use. Meyers: P is Allowed, CUP is Conditional Use.

Tahoe Valley and Tourist Core were rewritten in December 2024 with consolidated categories defined in each plan's Table 2. The service mixes those names with older Code names, so both plans are fixed by replacing their rows from the 2024 tables (A05 and A06), carrying density, unit, and notes from any old row for the same use.

## Decision rules

- **Overlaps:** the plan boundary layer decides which plan owns the area. When both districts are in the same plan, the special area or the smaller, more detailed district keeps its line.
- **Gaps:** filled only where a parcel in the gap already carries a zoning ID. Every other gap is listed for review (R06).
- **Duplicates:** the lower OBJECTID is kept, unless that copy has nulls the other does not.
- **Parcels:** a parcel's zoning is the district covering most of its area. Parcels already split near 50/50 are listed for review (R07), not changed.
- **Spelling:** new and changed values use the spelling most common in the table, for example "persons per acre" and "NA" for empty Unit and Notes.

## Verification

After all fixes in Parts 1 and 1B are applied to a copy of the live table, the table has 10,963 rows, no rows without a Zoning_ID, and no duplicate district and use pairs. Rerunning every comparison leaves only listed decisions and rows checked by hand as parser artifacts: 7 in Washoe, 11 in Placer, 2 in South Y, and 9 Tourist Core rows where the comparison side truncates "Water Quality Improvements and Watershed Management".


The table fixes were applied to a copy of the live table and the full comparison was rerun. Of 4,366 compared use rows, 4,358 match. Every remaining mismatch is a pending ruling (R01 to R03), a problem in the PDF itself (079, 118), or one known parser false positive (097_SA1, where the PDF scopes multiple family dwellings to Special Area 1). The remaining density flags are timeshare rows whose density the PDF sets "per the limitations in this table", or rows already checked by hand (067_SA2, 072, 073_SA1).

The polygon fixes were checked so that each fixed pair overlaps by less than 1 square meter, every replacement shape is valid, and the Tahoe Valley parcel 032-141-018 is covered after F29.

## Known caveats

- OBJECTIDs come from the published service. Guide step 3 checks that they match SDE; if not, use the GlobalID queries.
- The jurisdictions layer appears generalized, so small boundary crossings were not treated as zoning errors.
- Densities were checked only for the Plan Area Statements. Area plan and community plan densities sit in separate tables and were not compared.
- The South Shore Area Plan (179 rows) and PCAP_REC_HOMEWOOD were not checked because their governing documents are not linked (R15, R16).
