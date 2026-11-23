# CLAUDE.md: TRPA Zoning Service QA

Context for Claude Code. Read this whole file before changing code. Last updated 2026-11-23.

Owner: Mason Bindl, Senior GIS Analyst, TRPA (mason.bindl@trpa.gov).

## 0. Where this lives and what's active

This is the `Zoning/` folder of the `trpa-agency/Planning` repo, not a standalone `zoning-qa` repo. It is the home for zoning edits to TRPA GIS (District, PermissibleUses, Special_Designation, and parcel zoning attributes), plus the QA pipeline that checks them.

Paths moved from the handoff bundle (section 14):

- `fixtures/` is now `tests/fixtures/`. Read every `fixtures/...` reference in this file as `tests/fixtures/...`.
- `snapshot_2026-11-20/` is now `data/raw/snapshot_2026-11-20/` (gitignored).
- `prototype/` and `fix_package/` sit at the folder root, unchanged.

Active work: staff edit requests are tracked in `docs/EDIT_REQUESTS.md` (E-series IDs). Read it before any SDE edit. It sets the order: the WCTAP zoning ID rename (E04) runs last, because every fix in the package uses the old IDs.

SDE edit workflow: edits are made from a clone of this repo on the server, in a named version, alongside Alyssa's edit version. Confirm whether the data is traditionally versioned or branch versioned before you create versions. Branch versioning allows only one level of versions under DEFAULT. Details are in `docs/EDIT_REQUESTS.md`.

Relationship behavior: District relates to PermissibleUses and Special_Designation through simple, not composite, relationships keyed on ZONING_ID. Deleting a District feature nulls the key on its related rows; it does not delete them. Two District features that share a ZONING_ID share the same related rows. Snapshot related rows by GlobalID before any District delete or key change.

## 1. What this repo is for

TRPA publishes zoning through `https://maps.trpa.org/server/rest/services/Zoning/MapServer`. The goal is a repeatable Python QA that checks four things against the adopted plan documents and the jurisdiction boundaries:

1. The District polygons (layer 0).
2. The zoning ID stored on each parcel (layer 1). This is only an overlay copy, so it should agree with the District polygon that covers most of the parcel.
3. The Permissible Use table (layer 6). One row per district and use, with status, density, and unit.
4. The Special Designation table (layer 7).

The first full pass ran in a claude.ai session from 2026-11-20 to 2026-11-23. It produced a fix package, `TRPA_Zoning_QA_Fixes_2026-11-20.zip`, with a 43-step ArcGIS Pro editing guide, a fix geodatabase, CSVs, and decision lists. The fixes have not been posted to SDE as of this writing.

This repo turns that one-time pass into a maintained pipeline. That means a rerunnable extract, parsers per document, a comparison, QA reports, and generated fix files.

### Status at handoff

| Area | State |
|---|---|
| Service integrity checks (keys, orphans, duplicates, vocabulary, geometry) | Done |
| Boundary checks (TRPA boundary, Local Plan layer, jurisdictions) | Done |
| Plan Area Statement use lists and densities, 94 PDFs | Done |
| Area plans: Washoe, Placer, Meyers, Tahoe Valley, Tourist Core (use lists only) | Done |
| Community plans: Round Hill, Bijou/Al Tahoe, South Y (use lists only) | Done |
| Parcel ZONING_ID overlay check | Done |
| South Shore Area Plan (179 rows) | Not done, needs Douglas County Code Chapter 20.703 (R15) |
| PCAP_REC_HOMEWOOD | Not done, needs Homewood Mountain Resort Master Plan (R16) |
| Area plan and community plan densities | Not done |
| Special Designation content against documents | Not done; only integrity checks were run |
| Fixes tested in ArcGIS Pro | Not done; only applied to a pandas copy of the table |

### The uncomfortable part

The prototype code in `prototype/` was written fast, for one run, in a Linux sandbox. It has one-letter variable names, hardcoded page numbers and x positions, and hand-entered lists mixed into the logic. Do not promote it as is. Rebuild it to the TRPA data engineering conventions (section 13), and use the prototype outputs in `fixtures/` as regression tests. A rebuilt parser is correct when it reproduces those rows, or when every difference has been read against the PDF page and the new answer is shown to be right.

## 2. Working rules for Claude in this repo

- Follow the `trpa-data-engineering` skill: `config.yaml` for paths, URLs, pages, and run parameters; `.env` for secrets; standard `logging` to console and `logs/`; numbered notebooks first, then scripts; `docs/METHODS.md` and `docs/CHANGELOG.md`.
- Never put credentials in code or config. SDE access goes through a `.sde` connection file whose path is in `config.yaml`.
- Every SDE write is gated by `run.write_to_db` (default `false`) and runs in a version.
- A comparison mismatch is a candidate, not a finding. It becomes a fix only after someone reads the PDF page. Every fix row carries a source citation with the document and page number.
- Prefer flagging over guessing. If a document is ambiguous, it becomes a decision row (R-series), not a fix.
- ID columns are strings: APN, ZONING_ID, PLAN_ID. Zoning IDs have leading zeros (`019`, `032B`) and suffixes (`_SA1`, `_MF`).
- Writing style for docs and reports: Microsoft Writing Style Guide, no em-dashes, Oxford commas, no symbols in body text, tight and direct, plain language for leadership audiences. Tag key claims as [Certain], [Likely], or [Guessing].

## 3. Sources

### Services

| Service and layer | What it is | Rows on 2026-11-20 | Notes |
|---|---|---|---|
| Zoning/MapServer/0 District | Polygons, key ZONING_ID | 281 | Native SR is EPSG 26910; the service displays in 3857. Pull with `outSR=26910`. |
| Zoning/MapServer/1 Parcel | Parcel attributes, key APN | 61,275 | Returns null geometry for every feature. Use for attributes only. |
| Zoning/MapServer/6 Permissible Use | Table, key Zoning_ID | 10,812 | Related 1 to many from District. |
| Zoning/MapServer/7 Special Designation | Table, key ZONING_ID | 515 | Related 1 to many from District. |
| LocalPlan/MapServer/0 | Parcel polygons | 61,275 | Use this for parcel geometry. Its ZONING_ID matched Zoning layer 1 on every APN. |
| LocalPlan/MapServer/1 | Plan boundaries, field `File_URL` | 105 | The link to each plan PDF. 96 PAS, 6 area plans, 3 community plans. |
| LocalPlan/MapServer/3 and /5 | Special area attribute layers | 76 and 6 | Pulled, not used in comparisons. |
| Boundaries/MapServer/0, 4, 10 | Local Plan, TRPA Boundary, Jurisdictions Combined | | Jurisdictions look like generalized Census county lines. Do not treat small crossings as zoning errors. |

The Parcels/MapServer service also returns null geometry. [Certain]

### Schemas

Permissible Use (layer 6): `OBJECTID`, `Zoning_ID`, `Category`, `Subcategory`, `Use_Type`, `Use_Status`, `Density` (Integer, so fractional densities cannot be stored), `Unit`, `Notes`, `GlobalID`, editor tracking fields, and `Zoning_Description`, `Plan_Name`, `Plan_Type`. The last three are 100 percent null.

Special Designation (layer 7): `OBJECTID`, `ZONING_ID`, `ZONING_DESCRIPTION`, `PLAN_TYPE`, `SPECIAL_DESIGNATION` (150), `NOTES` (250), `GlobalID`, editor tracking.

District (layer 0): `OBJECTID`, `ZONING_ID`, `ZONING_DESCRIPTION`, `PLAN_ID`, `PLAN_NAME`, `PLAN_TYPE`, `SPECIAL_AREA_NAME`, `SPECIAL_AREA_NUMBER`, `OVERLAY`, `ACRES`, `DESIGN_GUIDELINES_HYPERLINK`, `GlobalID`, editor tracking.

Parcel (layer 1): `APN` (16), `JURISDICTION` (4), `PLAN_ID` (8), `PLAN_NAME` (40), `ZONING_ID` (50), `ZONING_DESCRIPTION`, `TOWN_CENTER`, `WITHIN_TRPA_BNDY`, `PARCEL_ACRES`, `STATUS`, and others.

Field name case differs: `Zoning_ID` in Permissible Use, `ZONING_ID` everywhere else.

SDE names, from the service relationships: `SDE.District`, `SDE.PermissibleUses`, `SDE.Special_Designation`. The Parcel feature class name in SDE was assumed to be `SDE.Parcel`. Confirm it.

### Service gotchas

- District PLAN_ID for Tahoe Valley is `TVAP`; the Local Plan layer and 467 parcels use `110` (R09).
- The Local Plan layer has `019` Martis Peak as its own PAS. District folds ZONING_ID `019` into WCTAP.
- District OVERLAY has four encodings of empty: a space, an empty string, null, and similar.
- `Unit` has about 25 spellings for about 8 real units. Use the spelling most common in the table for new values, for example "persons per acre", and "NA" for empty Unit and Notes.
- `Category` has "Public Service" (7 rows) and "Public Services" (2,534 rows).

## 4. Plan documents

The PDF for each plan comes from `File_URL` on LocalPlan layer 1. Nobody has confirmed each link is the current adopted version as amended.

Plan Area Statements follow `https://www.trpa.gov/wp-content/uploads/documents/archive/2/<PLAN_ID>.pdf`, with two exceptions:

- `089` is at `.../documents/archive/089.pdf` (no `/2/`).
- `089B` Stateline/Ski Run has no PDF; its File_URL is the trpa.gov home page. Districts 089B_SA1 to SA3 cannot be checked.

Area plans and community plans:

| PLAN_ID | Plan | File_URL | Use table location (1-based PDF page) | Layout |
|---|---|---|---|---|
| WCTAP | Washoe County Tahoe Area Plan | https://www.trpa.gov/wp-content/uploads/documents/WCTAP_Final_Full.pdf | Development Code Article 220 inside the PDF (amended Dec 17, 2025), one table per regulatory zone, about pages 170 to 210 | One-column list |
| PCAP | Placer County Tahoe Basin Area Plan | https://www.trpa.gov/wp-content/uploads/documents/Final-TBAP_Implement-Regs_Feb_2021.pdf | Tables 2.03 to 2.08, each named like `TABLE 2.06.A-1` | One-column lists; matrices for the mixed-use groups (2.04) and Lake Forest Commercial (2.05.C) |
| MAP | Meyers Area Plan | https://www.trpa.gov/wp-content/uploads/documents/archive/2/MeyersAreaPlan_Final_March2018_Combined.pdf | Table 2-1, pages 25 to 27 | Dense matrix, P and CUP |
| 110 (TVAP) | Tahoe Valley Area Plan | https://www.trpa.gov/wp-content/uploads/TRPATahoeValleyAreaPlan_Amended2024.pdf | Table 1, pages 189 to 191 | Dense matrix, A and S, footnotes |
| TCAP | Tourist Core Area Plan | https://www.trpa.gov/wp-content/uploads/FINAL-TCAP-DEC-2024-TRPA-Version-1.pdf | Table 1, pages 180 to 182 | Dense matrix; one column covers TSC-MUC and its Special Area 1 |
| SSAP | South Shore Area Plan | https://www.trpa.gov/wp-content/uploads/documents/archive/SSAP.pdf | Uses are set by Douglas County Development Code Chapter 20.703, not this PDF | Not parsed |
| 071 | Round Hill Community Plan | https://www.trpa.gov/wp-content/uploads/documents/archive/2/RH-cp.pdf | Chapter II (Nov 1993) | Prose lists like a PAS |
| 098 | Bijou/Al Tahoe Community Plan | https://www.trpa.gov/wp-content/uploads/documents/archive/2/Bijou-Al_Tahoe_CP.pdf | Permissible Uses Matrix (Oct 1995) | Sparse matrix with blank cells and indentation |
| 113 | South Y Industrial Tract Community Plan | https://www.trpa.gov/wp-content/uploads/documents/archive/2/SouthYIndustrialTractCP.pdf | Chapter II matrix (March 2003), around page 36 | One-column list with Allowed, Special Use, or No |

The full PAS link table is in `fixtures/plan_document_links.csv`, and the district to document crosswalk is in `fixtures/district_links.csv`. Put page ranges and column positions in `config.yaml`, not in code.

## 5. Comparison method

### Pipeline shape

1. Extract: pull service layers with paging (`resultOffset`, `resultRecordCount=2000`, `orderByFields=OBJECTID`). Pull District geometry with `outSR=26910`. Download every PDF from File_URL.
2. Parse: convert each document's use table into tidy rows. The columns are `zone`, `label` (PDF wording), `raw` (status cell as printed), `category`, `page`, `foot`, and `basis`.
3. Normalize: map each PDF label to one or more service `Use_Type` values.
4. Compare on (ZONING_ID, normalized use).
5. Review: a human reads every mismatch against the page and marks it as a fix, an artifact, or a decision.
6. Build fixes: generate update, delete, and insert CSVs plus a file geodatabase from the reviewed set.

### Issue classes from the compare step

- `missing from service`: the PDF permits the use; the table has no row.
- `in service, not in PDF`: the table has a row; the PDF does not list the use.
- `in service, PDF says not permitted`: the PDF marks the use with a dash or "No".
- `status mismatch`: both have it; the statuses differ.

When one use has split rows in the PDF (for example, multiple family dwelling with four units or less versus more than four), all their statuses are kept, and the service status matches if it equals any of them.

### Use name normalization

- `key()`: lowercase, strip punctuation, fold hyphen and "non" variants, and drop a plural "s" on words longer than 3 letters.
- Vocabulary: the target is the set of distinct `Use_Type` values already in the service, keyed by `key()`.
- Alias maps: about 225 PDF wordings map to service names for the PAS (`normalize.py` ALIAS plus EXTRA in `plan_diff2.py`). There are also plan-specific maps in `fixtures/alias_map.json` (13 entries) and `fixtures/alias_098.json` (22 entries).
- MULTI expansions: one PDF phrase becomes several uses. For example, "structural and nonstructural fish and wildlife habitat management" becomes four uses, and "sensitive and uncommon plant management" becomes two.
- KIT folding: hotel and timeshare kitchen-share variants (such as "less than 10 percent" and "10 percent or more") fold to the parent use for list checks. They are matched exactly for density checks.
- Strip "(Section ...)", "(see ...)", "(Nevada only)", asterisks, and the section sign before matching.
- Treat these as one controlled vocabulary tied to Code of Ordinances Chapter 21 plus each area plan's own terms. Store it in a CSV under `config/` or `data/reference/`, not in a Python dict.

### Status maps by plan

| Plan | Codes |
|---|---|
| Plan Area Statements | A is Allowed, S is Special Use |
| WCTAP | A is Allowed; S and AR are Special Use (Washoe Code 110.220.130 says AR is processed as a TRPA special use) |
| PCAP | A is Allowed, C is Administrative Review, MUP is Minor Use, CUP is Conditional Use |
| MAP | P is Allowed, CUP is Conditional Use |
| TVAP, TCAP | A is Allowed, S is Special Use |
| 113 | Allowed, Special Use, or No |

Status parsing reads the leading letters of the cell. Only a cell that matches `^Al(/\d+)?$` has "Al" converted to "A1", so "Allowed" stays intact (a past bug).

### Special area rules

| Plan | Rule |
|---|---|
| PAS | "plus the following additions" means the General List plus those uses. A special area list without that phrase replaces the General List. A category that says "those uses listed on the General List" pulls that category in. |
| WCTAP | A special area list is "independent and complete, not supplemental" (Code 110.220.130), except where it says "Same as General List" for a category or "As above" for a use. |
| PCAP | A special area gets the base list. Rows marked "Limited to Special Area #1" belong only to the special area. |
| TCAP | One column covers TSC-MUC and TSC-MUC Special Area 1. Footnote 9 uses are not permitted in Special Area 1; the rest of the column applies to it. |
| 071 | Special Area 2 resource management is "Same as Special Area #1". |
| 098 | Matrix districts 1 to 4 map to 098_SA1 to 098_SA4 (confirmed by a 99 percent match). |
| PCAP_RES_CEDAR_SA1 | Follows Cedar Flat only if the TRPA Ordinance 95-4 findings were made; otherwise Watson Creek applies. Built as Cedar Flat (R17). |

Tahoe Valley and Tourist Core were rewritten in December 2024 with consolidated categories, defined in each plan's Table 2. The service mixes the new names with old Code names, so those 17 districts are fixed by full replacement: A05 deletes and A06 inserts, carrying Density, Unit, and Notes from any old row for the same use.

### Parsers by document type

All PDF parsing uses `pdfplumber` word coordinates, `pdftotext -layout` text split on form feeds, or both. Page numbers are 1-based PDF page indexes.

| Parser (prototype file) | Used for | How it works |
|---|---|---|
| `pas_parse.py` | 94 PAS, 071 | Finds the section from `PERMISSIBLE USES:` to `MAXIMUM DENSITIES` in pdftotext text, splits General List and Special Area blocks, and reads category headers and `use (A)` or `use (S)` items from prose lists. |
| `pas_density2.py` | PAS densities | Parses the Maximum Densities table, including bullet rows for hotel units with and without kitchens. |
| `list_parse.py` | WCTAP, PCAP one-column tables, 113 | Row regex for a label plus a status code, with optional asterisk footnotes. It handles a status printed on its own line or above its label, "Same as General List" and "As above" markers, and wrapped labels (continuation accepted only if the joined text is a known use). It keeps prev, current, and next lines as context. |
| `matrix_parse.py` | TVAP, TCAP, MAP, PCAP matrices | Groups words into lines (y tolerance 4.0), sorts by x0, and assigns each status token to the nearest column center. Labels are text left of `label_max_x`. Strips header text and superscript footnote digits. Token regex: `^(TRPA\|CUP\|MUP\|AR\|Al\|A\|S\|P\|T\|X\|N\|C\|M\|[-–—]+)(footnote suffix)?$`. |
| `sparse_parse.py` | Matrices with blank cells | Like matrix_parse, but label fragments attach to the nearest token line by vertical distance, checked by `is_use`. |
| `indent_parse.py` | 098 | The row-start indent is the most common label x0, not the minimum (using the minimum dropped rows). |

Column positions for the dense matrices (x center in PDF points; config candidates):

- TVAP, pages 189 to 191, label_max_x 280: TC_C 290, TC_MUC 321, TC_G 352, TC_NP 384, TC_HC 416, EB_CC 446, CMX_S 481, TC_OS 514.
- TCAP, pages 180 to 182, label_max_x 235, stop at "SHOREZONE" or "Tolerance District": TSC_C 248, TSC_MU 280, TSC_MUC 320, TSC_NMX 352, TSC_G 384, TSC_G_SA1 424, REC_TOURIST 464, OS 500.
- MAP, pages 25 to 27, label_max_x 255: MAP_1 280, MAP_2 336, MAP_3 396, MAP_4 452, MAP_5 512.

The WCTAP zone header regex: `^\s*(?:PERMISSIBLE USES\s*[–-]\s*)?([A-Z0-9 .]+?) REGULATORY ZONE(\s+SPECIAL(\s+AREA)?\s*#?\s*(\d)?)?\s*$`. Zone names map to ZONING_ID through District ZONING_DESCRIPTION. Stop at `Section 110.220.x ... Special Policies`. Drop Shorezone and Tolerance categories.

The PCAP table header regex: `TABLE (2\.0[3-8]\.[A-Z]+)-1:?\s*(?:LAND USE REGULATIONS\s*[—-]\s*)?(.+?)\s*$`. Subdistrict names map to ZONING_ID by the tail of ZONING_DESCRIPTION, plus a manual map of 36 names in `run_pcap.py` (for example "granlibakken" is PCAP_TOR, "kingsbeachindustrial" is PCAP_COM/PS_KINGS).

### Rows read by hand

Some rows are hand entered because the layout defeats the parser. Keep them in a reviewed CSV with a page citation, not in code.

- WCTAP `048` residential and tourist rows: labels wrap three levels deep (code pages 220-37 and 220-38). There are 11 rows, including multiple family dwelling four units or less in the Town Center as A, and more than four units as AR.
- `032B` multiple family dwelling note: "Four units or less: Allowed. More than four units: Administrative Review, processed as a TRPA special use (Washoe Code 110.220.130)."

### Known parser artifacts

These were read against the page; the service is right. Do not re-flag them.

- WCTAP: `046` four fish and wildlife habitat rows; `048` multiple family dwelling and nonstructural wildlife habitat; `054_SA1` hotel.
- PCAP: `PCAP_MU_CCW`, `PCAP_MU_GW`, `PCAP_MU_NC` hotel; `PCAP_RES_TAHOEPINES` professional offices.
- 113: Schools, Business and Vocational.
- TCAP: 9 rows where the comparison label truncates to "Water Quality Improvements and Watershed" (the full name ends in "Management").
- PAS: `097_SA1` multiple family dwelling (the PDF scopes it to Special Area 1).

## 6. Results at handoff

### Use list comparison

| Plan | Rows compared | Match | Fixes |
|---|---|---|---|
| Plan Area Statements (126 of 129 districts) | 4,372 | 4,339 | 27 confirmed errors in 21 districts (F01 to F23) |
| Washoe County Tahoe Area Plan | 1,388 | 1,199 | 15 status, 2 deletes, 165 inserts |
| Placer County Tahoe Basin Area Plan | 3,568 | 3,524 | 12 status, 7 deletes, 15 inserts |
| Meyers Area Plan | 183 | 180 | 3 inserts in MAP_1 |
| Round Hill CP | 156 | 155 | 1 status |
| Bijou/Al Tahoe CP | 239 | 236 | 2 status, 1 delete |
| South Y Industrial Tract CP | 62 | 60 | 1 decision |
| Tahoe Valley and Tourist Core | n/a | n/a | Full replacement, 614 rows |

PAS densities: 250 match and 10 are wrong (099_SA1 swaps, missing bed and breakfast and employee housing densities, a 114_SA3 value on the wrong row, and unit spellings in 154, 154_MF, and 155).

Washoe districts `032B`, `035_SA1`, `055`, and `056` have no rows in the service but full tables in the county code. They account for 158 of the 165 Washoe inserts.

### Integrity findings

- 5 districts had no use rows: PCAP_REC_HOMEWOOD, 055, 056, 035_SA1, and 032B.
- 33 rows had a null Zoning_ID, including 1 fully null row. These are leftover Tahoe Valley and Tourist Core rows, deleted by A05.
- 2 rows used Zoning_ID "45", which matches no district (F21 changes it to 045).
- 11 duplicate district and use pairs (22 rows).
- Special Designation: 34 duplicate rows (F24 deletes 33; R05 holds one pair), and 10 districts have no row at all.

### Geometry findings

- 3 invalid District geometries (F25) and 36 multipart.
- Overlaps: 111_SA2 and TVAP_TC_NP (6.439 acres, F26), 030 and 040 (0.521 acres, F27), and 114 and 114_SA1 (0.012 acres, F28).
- A 1.045 acre hole inside Tahoe Valley (F29).
- A 4,157 acre uncovered block at the south end of the Region (El Dorado and Alpine), with no plan in the Local Plan layer either. A 24 acre gap inside SSAP. About 10 to 11 acres of district area outside the TRPA boundary in slivers. All are in R06.
- WCTAP districts cover 3,421 acres in Carson City. 055 and 056 are each about 42 percent across the line (R18).

### Parcel overlay findings

- 59,998 of 60,036 parcels with a ZONING_ID match the district with the largest overlap (99.94 percent).
- 35 split parcels carry the minority district, most near 50/50. 34 are in R07; the 35th (023-221-058) sits in the F26 overlap.
- 1,026 parcels are split across districts by more than 5 percent of their area. Parcel-based use lookups will be wrong for part of each.
- 221 parcels inside the TRPA boundary have a blank ZONING_ID.

## 7. Fix catalog

Fix IDs are referenced in the guide, the geodatabase layer names, and the CSVs. Keep these IDs stable in the rebuilt pipeline so the guide and any partial posting stay traceable.

| ID | Target | Action | Rows | Summary |
|---|---|---|---|---|
| F01 to F11 | PermissibleUses | Update | 27 | PAS status, use name, density, and unit fixes (057, 058, 111, 155, 099, 116, 114, 154) |
| F12 to F14 | PermissibleUses | Delete | 5 | Rows the PAS does not support (100, 111, 089_SA1) |
| F15 to F19 | PermissibleUses | Insert | 10 | Missing PAS uses (103, 127, 146, 149, 151) |
| F20 to F22 | PermissibleUses | Delete or update | 13 | Duplicates, null row, and the "45" Zoning_ID |
| F23 | PermissibleUses | Update | 39 | Ranch Pasture Management becomes Range Pasture Management (every PAS says "range") |
| F24 | Special_Designation | Delete | 33 | Duplicates |
| F25 | District | Repair geometry | 3 | Self-touching polygons |
| F26 to F29 | District | Clip and fill | 4 | Overlaps and the Tahoe Valley hole |
| F34 | District | Recalculate ACRES | All | After geometry edits |
| F30 to F33 | Parcel | Update | 46 | ZONING_ID and PLAN_ID corrections |
| A01 | PermissibleUses | Update | 30 | Area plan and community plan status fixes |
| A02 | PermissibleUses | Delete | 9 | Rows the documents do not support |
| A03, A04 | PermissibleUses | Insert | 25 and 158 | Missing Washoe uses; A04 fills the four empty Washoe districts |
| A05 | PermissibleUses | Delete | 630 | All Tahoe Valley and Tourist Core rows plus orphan rows |
| A06 | PermissibleUses | Insert | 614 | Tahoe Valley and Tourist Core rows from the 2024 tables |

Expected PermissibleUses row counts during posting: 10,812 at start, 10,805 after Part 1, 10,166 after A02 and A05, and 10,963 after the A03, A04, and A06 inserts. Special_Designation ends at 482. The verification check on a copy found no null Zoning_ID and no duplicate district and use pairs.

The fix rows use OBJECTIDs from the published service. Check that they match SDE before posting; if they do not, use the GlobalID queries in `docs/SQL_BY_GLOBALID.md` in the package.

## 8. Open decisions

These are questions for planners, not code bugs. Do not resolve them in code. Carry them as review rows.

| ID | Subject | Question |
|---|---|---|
| R01 | 073 multiple family dwelling | The PDF says A only on lots designated multi-density. Store Allowed and keep the condition in Notes? |
| R02 | 154 and 154_MF | PAS 154 has no special areas, but the service splits it. Merge 154_MF into 154, or document the basis for the split? |
| R03 | 112 null Use_Type row | Staff note says skiing facilities is not a recognized use. Leave null, store the PDF term, or map to Downhill Ski Facilities? |
| R05 | Special Designation 381 and 398 | Same designation, one with "Bonus Units for Affordable Housing Only". Keep 398 and delete 381? |
| R06 | 26 coverage gaps and slivers | Which zoning applies, or is the TRPA boundary layer generalized? |
| R07 | 34 split parcels | Each carries the district covering less of it. Confirm intended zoning. |
| R08 | 154_MF plan ID | Parcels carry PLAN_ID 155, but the district is 83 percent inside the PAS 154 boundary. Settle with R02. |
| R09 | Tahoe Valley plan ID | District uses TVAP; the plan layer and 467 parcels use 110. Pick one. |
| R10 | PDF defects | 079 lists single family dwelling and 118 lists transportation routes with no status. 089B has no PDF. |
| R11 | PCAP_COM/PS_KINGS single family dwelling | Code lists it only as accessory to a commercial use, with no permit code. Keep as Allowed with a note, or remove? |
| R12 | PCAP_MU_R, MU_TOR, MU_WREC fish habitat (6 rows) | The table lists wildlife habitat management but no fish habitat rows. Plan omission, or delete? |
| R13 | 113 open space line | "Allowed in all areas of the region" has no status code. Add as Allowed? |
| R14 | Tahoe Valley religious assembly | The 2024 table has no Religious Assembly row; old rows allowed it in 7 districts. Confirm before A05 and A06. |
| R15 | South Shore Area Plan | Needs Douglas County Code Chapter 20.703 to check 179 rows. |
| R16 | PCAP_REC_HOMEWOOD | Needs the Homewood Mountain Resort Master Plan. The district has no rows. |
| R17 | PCAP_RES_CEDAR_SA1 | Cedar Flat or Watson Creek, depending on Ordinance 95-4 findings. |
| R18 | 055 and 056 | Washoe tables applied to polygons about 42 percent in Carson City. |

R04 (orphan rows) was retired; A05 deletes them.

## 9. Spatial decision rules

- All spatial math in EPSG 26910. Acres are planar (square meters divided by 4,046.8564224).
- Overlaps: the Local Plan boundary layer decides which plan owns the area. When both districts are in the same plan, the special area or the smaller, more detailed district keeps its line.
- Gaps: fill only where a parcel in the gap already carries a zoning ID. Every other gap goes to review.
- Duplicates: keep the lower OBJECTID, unless that copy has nulls the other does not.
- Parcels: a parcel's zoning is the district covering most of its area. Parcels already split near 50/50 go to review, not to a fix.
- Clean polygons with `buffer(0)` before overlay. Ignore overlaps under 0.01 acres in reports. After fixes, each fixed pair overlaps by less than 1 square meter.

## 10. Bugs already hit (do not repeat)

- Parcel share was always 1 because `X.area` was read after the overlay replaced geometry. Compute and store parcel area in its own column (`parea`) before the overlay.
- pyogrio rejects `OBJECTID` and `GlobalID` as output field names in a file geodatabase. Write `TARGET_OBJECTID` and `TARGET_GLOBALID`.
- Mixed Polygon and MultiPolygon failed to write. Use `promote_to_multi=True`.
- The "Al" to "A1" fix broke "Allowed". Restrict it to `^Al(/\d+)?$`.
- Triple-asterisk footnotes dropped rows. Allow `\s*\*+` after the label.
- PCAP "Limited to Special Area #1" detection drifted across page breaks and leaked onto later rows. Check only the row's own line, a "#1" tail on it, or a complete note on a notes-only previous line.
- The 098 base indent used the minimum x0 and dropped rows. Use the most common x0.
- Matrix header text glued onto labels, and superscript footnotes came out of order. Sort words by x0, strip headers, and strip footnote digits.
- Page citations were off by one in five places (058, 111, 127, 089). Compute page numbers from form-feed page breaks or pdfplumber page index, never by counting lines.
- Count claims drifted (16 parcels that were 15; 4,374 compared rows that were 4,372). Generate every number in a report from code, not by hand.

## 11. What to build next, in order

1. Repo skeleton to TRPA conventions, `config.yaml`, logging, and `.env.example`.
2. `01_extract`: service pulls with paging and the District pull in 26910, PDF download with a manifest (URL, size, SHA-256, download date), and text extraction. Detect when a PDF changes.
3. Reference data: a controlled vocabulary CSV, alias CSV, MULTI expansions, status maps per plan, and special-area rules, all as data files.
4. `02_parse`: one parser module per layout type, configured per document from `config.yaml`. Regression tests against `fixtures/*_pdf_rows.csv`.
5. `03_compare_qa`: use list compare, PAS density compare, integrity checks, geometry checks, and the parcel overlay. Output a mismatch CSV with page citations, and an `artifacts.csv` and `decisions.csv` that the compare step reads so reviewed rows are not re-flagged.
6. `04_fixes`: build fix CSVs and the geodatabase from reviewed rows, with stable fix IDs. Optional arcpy apply script with dry run by default.
7. After the 2026-11-20 package is posted: rerun against the live service. The expected result is no mismatches beyond the artifacts and open decisions.
8. New coverage: area plan and community plan densities; SSAP once Chapter 20.703 is in hand; Special Designation content against the documents; a check that each File_URL is the current adopted version.

## 12. Environment

- Python: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`. Do not clone the environment unless a package would break it; document any clone in `environment.md`.
- Packages the prototype used: pandas, geopandas, shapely 2, pyogrio, pdfplumber, pyyaml, and python-dotenv. Check which are already in arcgispro-py3 and install the rest from conda-forge.
- pdftotext is part of poppler. It is not in arcgispro-py3 on Windows. [Likely] The text-based parsers (`pas_parse`, `list_parse`) were built on `pdftotext -layout` output. Choose one: install poppler (conda-forge `poppler`), or move those parsers to `pdfplumber.extract_text(layout=True)`. If you switch extractors, rerun the regression tests, because whitespace and line breaks will differ.
- The prototype wrote intermediates with pickle because pyarrow was missing. Use Parquet in the repo if pyarrow is available in arcgispro-py3.
- Network: the REST services are public. PDFs come from trpa.gov.

## 13. Proposed repo layout

```
zoning-qa/
  CLAUDE.md                  this file
  README.md
  config.yaml                service URLs, layer ids, output SR, document pages and column x positions, run flags
  .env.example               none needed today; keep for SDE or portal tokens later
  environment.md
  notebooks/
    01_extract.ipynb
    02_parse.ipynb
    03_compare_qa.ipynb
    04_fixes.ipynb
  scripts/
    run_qa.py                promoted runner
    apply_fixes_arcpy.py     dry run by default, gated by run.write_to_db
  src/
    io.py                    load_config, load_secrets, get_logger
    rest.py                  paged ArcGIS REST pulls
    pdf_text.py              download, hash, text and word extraction
    parse_pas.py             PAS prose lists and densities
    parse_list.py            one-column tables (WCTAP, PCAP, 113)
    parse_matrix.py          dense and sparse matrices (TVAP, TCAP, MAP, PCAP 2.04 and 2.05.C, 098)
    normalize.py             key(), alias, multi, kitchen fold, using data/reference
    compare.py               use and density compare, issue classes
    spatial.py               geometry, overlap, gap, jurisdiction, and parcel overlay checks
    fixes.py                 fix CSVs and file geodatabase writer
    qa.py                    reusable checks from the skill
  data/
    reference/               committed: vocabulary.csv, aliases.csv, multi.csv, status_maps.csv, special_area_rules.csv, artifacts.csv, decisions.csv, manual_rows.csv
    raw/                     gitignored: service snapshots, PDFs, text
    processed/               gitignored
  tests/
    fixtures/                committed: prototype pdf_rows CSVs and expected diffs
    test_parsers.py
    test_normalize.py
  outputs/                   gitignored
  logs/                      gitignored
  docs/
    METHODS.md
    CHANGELOG.md
```

Mapping from the prototype:

| Prototype | New home |
|---|---|
| `pull.py` | `src/rest.py`, `01_extract` |
| `spatial.py`, `parcel_overlay.py` | `src/spatial.py` |
| `pas_parse.py`, `pas_density2.py`, `pas_diff.py` | `src/parse_pas.py`, `src/compare.py` |
| `list_parse.py`, `run_wctap.py`, `run_pcap.py` | `src/parse_list.py` plus config entries |
| `matrix_parse.py`, `sparse_parse.py`, `indent_parse.py`, `run_dense.py` | `src/parse_matrix.py` plus config entries |
| `normalize.py`, `plan_diff2.py` | `src/normalize.py`, `src/compare.py`, and `data/reference/*.csv` |
| `build_*_fixes.py`, `build_replacement.py`, `write_gdb.py`, `write_guide.py` | `src/fixes.py`, `04_fixes` |
| ARTIFACT and RULING sets in `build_area_fixes.py` | `data/reference/artifacts.csv` and `decisions.csv` |
| `cite.py`, `ctx.py` | A page lookup helper in `src/pdf_text.py` |

## 14. What is in this handoff bundle

| Path | Contents |
|---|---|
| `CLAUDE.md` | This file |
| `prototype/` | All prototype code from both working folders, unchanged |
| `fixtures/*_pdf_rows.csv` | Parsed PDF rows per plan (WCTAP, PCAP, MAP, TVAP, TCAP, 071, 098, 113) |
| `fixtures/out_*_diff.csv` | Comparison outputs before review |
| `fixtures/pas_*.csv`, `PAS_QA_findings.csv` | PAS raw uses, densities, and findings |
| `fixtures/alias_map.json`, `alias_098.json` | Plan-specific aliases |
| `fixtures/plan_document_links.csv`, `district_links.csv` | Document crosswalk |
| `fixtures/replacement_tvap_tcap.csv` | The A06 replacement rows |
| `snapshot_2026-11-20/` | Service table snapshots (Permissible Use, Special Designation, District attributes) used as the "before" state; put under `data/raw/` |
| `fix_package/` | The fix CSVs and docs from the delivered zip (`EDIT_GUIDE.md`, `METHODS.md`, `SQL_BY_GLOBALID.md`, `CHANGELOG.md`) |

The fix geodatabase, PDFs, and parcel geometry are not in the bundle. The geodatabase is in the delivered zip. Rerun `01_extract` for the rest.

## 15. Glossary

- PAS: Plan Area Statement. Older TRPA district documents, one PDF per plan ID.
- Area plan: a local plan adopted by a county or city and found in conformance by TRPA. It replaces the PAS for its area.
- Community plan: an older plan for a commercial core, now mostly folded into area plans.
- Special area: a subarea of a district with its own use list, stored as `<ZONING_ID>_SA<n>`.
- A, S: Allowed and Special Use in TRPA Code terms.
- SDE: the agency enterprise geodatabase behind the service.
