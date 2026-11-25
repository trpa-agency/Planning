# CNEL by zoning district

Replaces the legacy noise layer, `AGIS_TRPA/MapServer/82` Noise Levels, with a table keyed on District ZONING_ID. Built 2026-11-24.

## Why

Layer 82 holds 310 polygons drawn from the 1987 Plan Area Statements and the old Community Plans (Stateline/Ski Run, Tahoe City, Kings Beach, Meyers, and others). It predates every area plan, so its shapes and values are out of date for about 72,500 acres of area plan districts. [Certain]

Two defects in the layer itself:

- Five conservation polygons store 40 while the legend labels the class 45. The plan documents say 25 for three of them (see N01). [Certain]
- The `attainment` field is mostly "?". It is monitoring data and does not belong on a standards layer. It is not carried forward. [Certain]

## Design

- `data/reference/cnel_by_district.csv` holds one row per District ZONING_ID (283 rows, keyed on the post-E04 IDs in `mtb-edits`).
- `scripts/cnel_build_table.py` checks the CSV against District in the version and writes `SDE.District_CNEL` (CNEL, corridor standard, note, basis, source document and page, decision ID, and the legacy value).
- District keeps the geometry. The published noise layer becomes District joined to `SDE.District_CNEL` on ZONING_ID, so there is no second copy of the district shapes to drift.

### CSV columns

| Column | Meaning |
|---|---|
| CNEL | Maximum CNEL for the district, in dBA |
| CORRIDOR_CNEL | Highway or airport corridor standard stated in the same document, as text |
| CNEL_NOTE | Exceptions (shorezone, flight paths, roadless areas, special area footnotes) and document conflicts |
| BASIS | `document` (the document states the district value), `inherited` (a special area or subdistrict takes its parent value because the document sets none), or `legacy` (no document value; carried from layer 82) |
| SOURCE_DOC, SOURCE_PAGE | Citation; the page is the 1-based PDF page |
| LEGACY_CNEL, LEGACY_SHARE | Layer 82 value covering the largest share of the district, and that share |
| CHANGE | `same`, or the legacy and new values where they differ |
| DECISION | Open question for planners (N-series below, or an existing R-series ID) |

## Method

1. Downloaded all 104 plan PDFs from `tests/fixtures/plan_document_links.csv` to `data/raw/plans/` (gitignored) and extracted text with `pdftotext -layout`.
2. Plan Area Statements: read the "Maximum Community Noise Equivalent Level" paragraph from each PAS. The base value and any corridor values come from that paragraph. No PAS sets a separate value for a special area, so `_SA` districts and `154_MF` inherit. 055 and 056 (Carson City halves) come from their own PAS PDFs.
3. Washoe: Development Code Section 110.220.420 (PDF pages 256 and 257). Table 4.10 in the plan narrative groups zones differently; the code section governs.
4. Placer: the Maximum CNEL row in each subdistrict's development standards table (Tables 2.03 to 2.08). The mixed-use matrices (Tables 2.04.A-2, B-2, C-2, and D-2) and the Tahoe Valley and Tourist Core Table 3 were checked against the rendered page, because text extraction misaligns their columns.
5. Meyers, Tahoe Valley, Tourist Core, Round Hill, Bijou/Al Tahoe, and South Y: the plan's CNEL section or table.
6. Overlaid layer 82 on District (EPSG 26910) to record the legacy value per district.

Results: 226 rows from a document, 48 inherited, and 9 legacy. Of the 274 rows with a document value, 241 match layer 82 and 33 change. Among the 126 PAS districts with a document, 122 match; the other four are 116 and the three N01 districts. [Certain]

## Changes from the legacy layer

| District | Legacy | New | Reason |
|---|---|---|---|
| 116 | 60 | 65 | PAS 116 says 65 |
| 121, 139, 143 | 40 | 25 | PAS says 25 (N01) |
| WCTAP_045 and its three special areas | 65 | 60 | Washoe code: Incline Village Commercial is 60 |
| WCTAP_047 | 55 | 45 | Washoe code: Tunnel Creek is 45 |
| WCTAP_053 | 40 | 50 | Washoe code: Incline Meadows is 50 |
| PCAP_MU_TC, PCAP_MU_N | 55 | 65 | Table 2.04.A-2 |
| PCAP_MU_MTC, PCAP_MU_LTC | 55 | 60 | Table 2.04.B-2 |
| PCAP_MU_R | 65 | 55 | Table 2.04.B-2 |
| PCAP_MU_GW, PCAP_MU_CCE, PCAP_MU_GE | 65 | 55 | Table 2.04.C-2 |
| PCAP_MU_CCW | 65 | 60 | Table 2.04.C-2 |
| PCAP_RES_TAHOEVISTA | 65 | 55 | Table 2.03.Z-2 |
| PCAP_RES_CEDAR_SA1 | 50 | 55 | Inherits Cedar Flat (R17) |
| MAP_3 | 65 | 55 | Meyers Section 140 |
| MAP_5 | 55 | 50 | Meyers Section 140 |
| TVAP_TC_C, TVAP_TC_MUC, TVAP_TC_G | 65 | 60 | Tahoe Valley Table 3 (N03) |
| TVAP_TC_OS | 65 | 55 | Tahoe Valley Table 3 |
| TCAP_TSC_C, TCAP_TSC_MU, TCAP_TSC_G | 65 | 60 | Tourist Core Table 3 |
| TCAP_TSC_MUC | 55 | 60 | Tourist Core Table 3 |
| TCAP_TSC_NMX | 65 | 55 | Tourist Core Table 3 |
| 071_SA2 | 55 | 65 | Round Hill CP (N04) |

## Open decisions

| ID | Districts | Question |
|---|---|---|
| N01 | 121, 139, 143, and the Lincoln Park roadless area in 060 | The PAS text says 25 CNEL. Layer 82 stores 40 and labels it 45. Washoe sets 40 for Mount Rose and 45 for Tunnel Creek. Is 25 the adopted standard, or a typo for 45? Stored as 25. |
| N02 | TVAP_EB_CC | Tahoe Valley Table 3 leaves the EB-CC cell blank. Which value applies? Legacy 50 carried for now. |
| N03 | Tahoe Valley districts | Table 3 says 60 for the Town Center districts, 65 for CMX-S, and 55 for TC-NP, TC-HC, and OS. Policy HNS-2.1 (p. 101) says 65 except TC-NP and TC-HC at 55, and the existing conditions text says 60 except TC-HC at 55. Table 3 is used. |
| N04 | 071_SA2 | Chapter II sets 65 with 55 for property abutting residential areas; the Chapter VI target splits Special Area 2 into NE 65 and SW 55. Stored as 65 with a note. Split the district, or keep the note? |
| N05 | 089B_SA1 to SA3 | No Stateline/Ski Run plan document on file (also R10). Legacy values (65, 65, and 55) carried. |
| N06 | PCAP_REC_HOMEWOOD | No table in the Implementing Regulations; needs the Homewood Mountain Resort Master Plan (also R16). Legacy 55 carried. |
| N07 | 098_SA1 to SA4 | The Chapter II statement says 60 for all four; the Chapter VI target table says 65 for 1 to 3 and 55 for 4. Chapter II is used. |
| N08 | SSAP districts | The South Shore Area Plan sets no CNEL; standards come from Douglas County Code (also R15). Legacy values carried. |
| R17 | PCAP_RES_CEDAR_SA1 | Cedar Flat (55) or Watson Creek (50), depending on the Ordinance 95-4 findings. Stored as 55. |

## GeoPackage

`data/cnel/district_cnel.gpkg` (committed, EPSG 26910) has four layers: the two below, plus the corridor layers described under Highway corridors.

- `district_cnel`: District polygons with every CSV column, plus ZONING_DESCRIPTION, PLAN_ID, PLAN_NAME, PLAN_TYPE, LEGACY_SHARE, CHANGE, and PUBLISHED_ZONING_ID (the ID the district carries in the public service today).
- `legacy_noise_levels`: layer 82 as published (310 polygons, CNEL in `CNL`), for comparison.

Rebuild it with `python Zoning/scripts/cnel_export_gpkg.py`. By default it reads the public Zoning service, which still has the pre-E04 IDs, so it adds the WCTAP_ prefix and keeps the old ID in PUBLISHED_ZONING_ID. The public service has no Carson City halves of 055 and 056, so the committed file has 281 districts, and WCTAP_055 and WCTAP_056 are the whole published shapes. Both halves are 50 CNEL, so the map is the same. [Certain] On the server, `--source version` reads District from the connected version instead (283 districts, the real split). Rebuild after any change to the CSV or the district shapes.

## Highway corridors

The GeoPackage also has two corridor layers, built by `src/corridors.py` with the settings in the `corridor` section of `config.yaml`:

- `highway_centerlines`: state route centerlines (US 50, SR 28, SR 89, SR 207, SR 267, and SR 431). The base is Major Highways (`AGIS_TRPA/MapServer/10`). Each segment takes its route from the Streets layer (`DataDownloader_Transportation/MapServer/2`) segments within 20 meters of it, which fixes two problems: Major Highways labels Tahoe City to Dollar Point as SR 89 (it is SR 28), and it leaves Incline's Tahoe Blvd unnamed. Pioneer Trail (6.7 miles) and Lakeshore Blvd (3.1 miles) are county roads and are dropped. Streets fills 6.1 miles of SR 89 and 2.1 miles of US 50 that Major Highways lacks, mostly in South Lake Tahoe. SOURCE and ROUTE_FROM say where each segment and its route came from.
- `noise_corridors`: each route buffered 300 feet each side of the centerline, split by district. CORRIDOR_CNEL is the corridor value the district's document states for that route, EFFECTIVE_CNEL is the corridor value where one is stated and the district value where not, and CORRIDOR_BASIS says which.

Results: 231 pieces covering about 8,100 acres. CORRIDOR_BASIS is "corridor standard" on 5,712 acres, "corridor included in district value" on 193, "override permissible where applicable" on 123, and "no corridor standard in document" on 2,093. [Certain]

Things to know:

- Width: Meyers, Tahoe Valley, and Tourist Core state 300 feet. Tourist Core measures from the road edge; this layer measures from the centerline, so it runs about 6 to 12 meters narrow there. The Plan Area Statements and the other plans give no width, so 300 feet everywhere is an assumption. [Likely]
- No corridor standard: 1,117 of the 2,093 acres are in Placer districts. Most Placer subdistrict tables state no SR 28 or SR 267 value, so those pieces carry the district value. 85 acres are SR 207 in the South Shore districts (N08).
- SR 89 crosses PAS 121 and 143, where the document value is 25 (N01). Those 122 acres show an EFFECTIVE_CNEL of 25 along a state highway, which supports reading 25 as a typo.
- Route buffers overlap by about 51 acres at junctions. A point there falls in two pieces; use the higher EFFECTIVE_CNEL.
- The airport corridor in PAS 117 and 120 (60 CNEL) is not drawn. It needs the airport flight path shapes.

## Not in this table

- Shorezone and lakezone values (55 and 50 in most plans) are in CNEL_NOTE where the document states them.
- The airport flight path standard in PAS 100 is in CNEL_NOTE.

## Run it

1. Dry run on the server: `python Zoning/scripts/cnel_build_table.py`. Expect 283 District IDs, 283 matched, and no stop. Review `outputs/cnel_<time>/changes.csv`, `decisions.csv`, and `cnel_review.gdb` in Pro next to layer 82.
2. Write: set `run.write_to_db: true` and `cnel.create_table: true`, rerun, and restore both. The first run creates `SDE.District_CNEL`, adds GlobalIDs, and registers it as versioned when District is. Creating a table needs a connection with create privileges in SDE.
3. Reconcile and post with the other `mtb-edits` work.
4. Republish: in the map behind `AGIS_TRPA/MapServer`, replace layer 82 with District joined to `SDE.District_CNEL` on ZONING_ID (keep all records), symbolized on CNEL. Keep layer ID 82 if any web map or app references it by ID.

Rerun steps 1 and 2 after any change to the CSV or to District IDs. The script updates changed rows, inserts new ones, and deletes rows for IDs no longer in the CSV.

Tested 2026-11-24 on a file geodatabase copy of District with the E04 IDs and the 055 and 056 split: dry run, first write (283 inserted), repair after a changed value and an orphan row (1 updated, 1 deleted), rerun (283 unchanged), and a stop on pre-E04 IDs (36 districts with no row).
