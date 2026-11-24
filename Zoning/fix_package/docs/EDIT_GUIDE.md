# Zoning QA fixes: ArcGIS Pro editing guide

Prepared November 20, 2026. Edits are based on the live Zoning MapServer as of that date and on the plan documents linked in LocalPlan layer 1: 94 Plan Area Statements, five of the six area plans, and all three community plans. The South Shore Area Plan could not be checked because its use table lives in Douglas County Development Code Chapter 20.703, which is not linked (decision R15).

Each step names its fix ID (F01 and so on), how many rows or features it changes, and how sure we are. Certain means the PDF text or the table itself proves it. Likely means strong evidence that a planner should glance at before posting. Decisions (R01 to R10) are listed at the end and are not edits.

## What is in this package

| Item | Use |
|---|---|
| `data/Zoning_QA_Fixes_2026-11-20.gdb` | Every fix as a table or feature class, in NAD 1983 UTM Zone 10N (the District feature class projection) |
| `data/csv/` | The same fixes as CSV files, for review in Excel |
| `docs/EDIT_GUIDE.md` | This guide |
| `docs/SQL_BY_GLOBALID.md` | Backup selection queries keyed on GlobalID |
| `docs/METHODS.md` | How the fixes were found and checked |
| `scripts/replace_district_shapes.py` | Optional Python window snippet for Part 3, Method B |
| `src/` | The Python that built the fixes, for rerunning or auditing |

## Summary of edits

| Part | Layer | Edits | Rows after |
|---|---|---|---|
| 1 | PermissibleUses, Plan Area Statements | 60 rows updated (67 field changes), 17 deleted, 10 added | 10,805 (from 10,812) |
| 1B | PermissibleUses, area and community plans | 30 rows updated, 639 deleted, 797 added | 10,963 |
| 2 | Special_Designation | 33 duplicates deleted | 482 (from 515) |
| 3 | District | 3 repaired, 3 clipped, 1 gap filled, ACRES recalculated | 281 (unchanged) |
| 4 | Parcel | 21 parcels updated (46 field changes) | 61,275 (unchanged) |

## Part 0. Before you start

### Step 1. Connect and add the layers

In a new map in ArcGIS Pro, add these from the SDE connection: District, Parcel, the PermissibleUses table, and the Special_Designation table. Then add every layer and table from `Zoning_QA_Fixes_2026-11-20.gdb` (Catalog pane, browse to the folder, drag the geodatabase items into the map).

### Step 2. Work in a version, or back up first

If the zoning data is versioned, create and switch to a named version such as `zoning_qa_fixes_2026_11_20` (Data tab on any of the four layers, Versioning). If it is not versioned, export all four to a backup file geodatabase first with Export Features and Export Table. Either way you can undo the whole set.

### Step 3. Confirm row counts and IDs match this package

Open each attribute table and check the record count: District 281, PermissibleUses 10,812, Special_Designation 515, Parcel 61,275. Then run Select By Attributes on PermissibleUses with this clause:
```sql
OBJECTID = 3789
```
It should select one row: Zoning_ID 057, Use_Type Selection Cut, Use_Status Allowed. If it does not, the SDE OBJECTIDs differ from the published service. Use the GlobalID queries in `SQL_BY_GLOBALID.md` for every selection below instead.

### Step 4. Start editing

On the Edit tab, confirm editing is enabled for the SDE workspace. Save edits after each part (Edit tab, Save). If a selection count does not match the guide, stop and check before calculating.

## Part 1. PermissibleUses table

For each step: open the PermissibleUses table, click Select By Attributes, switch to SQL mode, paste the clause, apply, and check the selection count. Then right-click the field header, choose Calculate Field, set the expression type to Python 3, paste the expression, and run it. Calculate Field only changes the selected rows.

### Step 5. F01: set Use_Status to Special Use (1 row)

Districts: 057. PDF lists selection cut (S). Source: PAS 057 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/057.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (3789)
```
Calculate Field, field `Use_Status`:
```python
"Special Use"
```

### Step 6. F01: set Use_Status to Allowed (1 row)

Districts: 057. PDF lists special cut (A). Source: PAS 057 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/057.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (3786)
```
Calculate Field, field `Use_Status`:
```python
"Allowed"
```

### Step 7. F02: set Use_Type to Fuels Treatment Management (1 row)

Districts: 058_SA1. Glenbrook has no Special Area 1 use list; general list has fuels treatment/management (A). Row is mislabeled. Source: PAS 058 PDF p2 (trpa.gov/wp-content/uploads/documents/archive/2/058.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (5437)
```
Calculate Field, field `Use_Type`:
```python
"Fuels Treatment Management"
```

### Step 8. F03: set Use_Status to Allowed (5 rows)

Districts: 111_SA1, 111_SA2, 112, 112_SA1, 112_SA2. General list: schools - kindergarten through secondary (A); special areas add to the general list. Source: PAS 111 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/111.pdf); PAS 112 PDF p2 (trpa.gov/wp-content/uploads/documents/archive/2/112.pdf). Confidence: Certain.

Select (expect 5):
```sql
OBJECTID IN (740, 772, 649, 650, 651)
```
Calculate Field, field `Use_Status`:
```python
"Allowed"
```

### Step 9. F04: set Use_Status to Allowed (1 row)

Districts: 111_SA2. Special Area 2 additions: multiple family dwellings (A). Source: PAS 111 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/111.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (767)
```
Calculate Field, field `Use_Status`:
```python
"Allowed"
```

### Step 10. F05: set Use_Type to Multiple Family Dwelling and Use_Status to Special Use (1 row)

Districts: 155. Standard use name; row was entered as Multi-Family Dwelling. PDF lists multiple family dwelling (S). Source: PAS 155 PDF p2 (trpa.gov/wp-content/uploads/documents/archive/2/155.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (14031)
```
Calculate Field, field `Use_Type`:
```python
"Multiple Family Dwelling"
```
Calculate Field, field `Use_Status`:
```python
"Special Use"
```

### Step 11. F06: set Density to 15 and Unit to units per acre (1 row)

Districts: 099_SA1. Multiple family dwellings 15 units per acre; values were swapped with multi-person. Unit swapped with multi-person row. Source: PAS 099 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/099.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (3566)
```
Calculate Field, field `Density`:
```python
15
```
Calculate Field, field `Unit`:
```python
"units per acre"
```

### Step 12. F06: set Density to 25 and Unit to persons per acre (1 row)

Districts: 099_SA1. Multi-person dwellings 25 people per acre; values were swapped with multiple family. Unit swapped with multiple family row. Source: PAS 099 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/099.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (3312)
```
Calculate Field, field `Density`:
```python
25
```
Calculate Field, field `Unit`:
```python
"persons per acre"
```

### Step 13. F07: set Density to 10 and Unit to units per acre (2 rows)

Districts: 099_SA1, 114_SA1. Bed and breakfast facilities 10 units per acre. Unit for the density above. Source: PAS 099 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/099.pdf); PAS 114 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/114.pdf). Confidence: Certain.

Select (expect 2):
```sql
OBJECTID IN (3313, 2376)
```
Calculate Field, field `Density`:
```python
10
```
Calculate Field, field `Unit`:
```python
"units per acre"
```

### Step 14. F08: set Density to 15 and Unit to units per acre (1 row)

Districts: 116. Employee housing 15 units per acre. Unit for the density above. Source: PAS 116 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/116.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (12748)
```
Calculate Field, field `Density`:
```python
15
```
Calculate Field, field `Unit`:
```python
"units per acre"
```

### Step 15. F09: set Density to null and Unit to NA (1 row)

Districts: 114_SA3. No density applies to public health and safety facilities; 8 units per acre belongs to Special Area 3 multiple family dwellings, which already carries it. Clear unit with the density. Source: PAS 114 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/114.pdf). Confidence: Certain.

Select (expect 1):
```sql
OBJECTID IN (804)
```
Calculate Field, field `Density`:
```python
None
```
Calculate Field, field `Unit`:
```python
"NA"
```

### Step 16. F10: set Unit to unit per parcel (2 rows)

Districts: 154, 154_MF. Single family dwelling 1 unit per parcel. Source: PAS 154 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/154.pdf). Confidence: Certain.

Select (expect 2):
```sql
OBJECTID IN (2163, 10717)
```
Calculate Field, field `Unit`:
```python
"unit per parcel"
```

### Step 17. F11: set Unit to persons per acre (2 rows)

Districts: 155. 25 people per acre; stored as units per acre. Uses the table's standard spelling. Source: PAS 155 PDF p3 (trpa.gov/wp-content/uploads/documents/archive/2/155.pdf). Confidence: Certain.

Select (expect 2):
```sql
OBJECTID IN (2195, 2197)
```
Calculate Field, field `Unit`:
```python
"persons per acre"
```

### Step 18. F21: set Zoning_ID to 045 (1 row)

Districts: 45. "45" matches no district; 045 has every other timeshare variant but this one. Source: Table integrity. Confidence: Likely.

Select (expect 1):
```sql
OBJECTID IN (5652)
```
Calculate Field, field `Zoning_ID`:
```python
"045"
```

### Step 19. F23: set Use_Type to Range Pasture Management (39 rows)

39 rows in 39 districts. Every PAS says range pasture management; Ranch is a typo. Confidence: Likely. The full list is in `F01_F23_PermissibleUse_Updates`.

Select (expect 39):
```sql
OBJECTID IN (592, 1036, 1080, 1177, 1329, 1376, 1413, 1630, 1702, 1820, 1956, 2035, 2106, 2151, 2432, 2473, 2697, 2929, 3564, 3763, 3834, 3900, 4107, 4181, 4588, 4656, 4696, 5129, 5434, 5901, 7271, 7309, 7453, 8287, 8938, 8977, 9089, 10093, 10096)
```
Calculate Field, field `Use_Type`:
```python
"Range Pasture Management"
```

### Step 20. Delete 17 rows (F12, F13, F14, F20, F21, F22)

These rows are either not in the PDF or are exact duplicates, an all-null row, and the second copy of the "45" row. Reasons per row are in `F12_F22_PermissibleUse_Deletes`.

| Fix | OBJECTID | Zoning_ID | Use_Type | Confidence |
|---|---|---|---|---|
| F12 | 3516 | 100 | Reforestation | Certain |
| F13 | 2403 | 111_SA1 | Nursing and Personal Care | Certain |
| F13 | 2404 | 111_SA1 | Residential Care | Certain |
| F14 | 2976 | 089_SA1 | Eating and Drinking Places | Certain |
| F14 | 2977 | 089_SA1 | Vehicle Storage and Parking | Certain |
| F20 | 10579 | 038_SA1 | Sport Assembly | Certain |
| F20 | 10196 | 044_SA1 | Time Sharing (Hotel/Motel Design) less than 10% of units with kitchens | Certain |
| F20 | 9952 | 045_SA3 | Collection Stations | Certain |
| F20 | 9911 | 045_SA3 | Regional Public Health and Safety Facilities | Certain |
| F20 | 9906 | 045_SA3 | Religious Assembly | Certain |
| F20 | 14030 | 054_SA1 | Employee Housing | Certain |
| F20 | 2364 | 116 | Auto, Mobile Home and  Vehicle Dealers | Certain |
| F20 | 9289 | PCAP_COM/PS_FAIRWAY | Threshold-Related Research Facilities | Certain |
| F20 | 9214 | PCAP_RES_FAIRWAYNORTHEAST | Threshold-Related Research Facilities | Certain |
| F20 | 9242 | PCAP_RES_TAVERN | Threshold-Related Research Facilities | Certain |
| F21 | 9208 | 45 | Time Sharing (Residential Design) 10% or more units with kitchens | Likely |
| F22 | 12762 |  |  | Certain |

Select (expect 17):
```sql
OBJECTID IN (3516, 2403, 2404, 2976, 2977, 10579, 10196, 9952, 9911, 9906, 14030, 2364, 9289, 9214, 9242, 9208, 12762)
```
With the rows selected, on the Edit tab click Delete. Record count should drop to 10,795.

### Step 21. Add 10 rows (F15 to F19)

Open the Append tool (Analysis tab, Tools, search Append).

- Input Datasets: `F15_F19_PermissibleUse_Inserts` from the fixes geodatabase
- Target Dataset: the SDE PermissibleUses table
- Field Matching Type: Use the field map to reconcile field differences
- Field Map: Zoning_ID, Category, Subcategory, Use_Type, Use_Status, Density, Unit, and Notes map by name. Leave Zoning_Description, Plan_Name, and Plan_Type empty, as every existing row has them empty. FIX_ID, CONFIDENCE, SOURCE, and REASON have no target and are dropped.

Rows being added:

| Fix | Zoning_ID | Category | Subcategory | Use_Type | Use_Status | Density | Unit |
|---|---|---|---|---|---|---|---|
| F15 | 103 | Tourist Accommodation | Tourist Accommodation | Time Sharing (Hotel/Motel Design) less than 10% of units with kitchens | Special Use | 40 | units per acre |
| F15 | 103 | Tourist Accommodation | Tourist Accommodation | Time Sharing (Hotel/Motel Design) 10% or more units with kitchens | Special Use | 15 | units per acre |
| F16 | 127 | Public Services | Linear Public Facilities | Transmission and Receiving Facilities | Special Use |  | NA |
| F16 | 128 | Public Services | Linear Public Facilities | Transmission and Receiving Facilities | Special Use |  | NA |
| F17 | 146 | Public Services | General | Cultural Facilities | Special Use |  | NA |
| F18 | 149 | Resource Management | Timber Management | Thinning | Allowed |  | NA |
| F18 | 151 | Resource Management | Timber Management | Thinning | Allowed |  | NA |
| F19 | 151 | Public Services | General | Local Post Office | Special Use |  | NA |
| F19 | 154 | Public Services | General | Local Post Office | Special Use |  | NA |
| F19 | 154_MF | Public Services | General | Local Post Office | Special Use |  | NA |

Record count should be 10,805. Notes is "NA" on the new rows except the two timeshare rows, which carry the same note as the existing 103 timeshare rows. Save edits.

## Part 1B. PermissibleUses table: area plans and community plans

Do Part 1 first. These steps use the same Select By Attributes and Calculate Field pattern. Sources are the Washoe County Development Code Article 220 (Dec 17, 2025), the Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), the Meyers Area Plan (March 2018), the Tahoe Valley Area Plan (amended Dec 18, 2024), the Tourist Core Area Plan (Dec 2024), and the Round Hill (1993), Bijou/Al Tahoe (1995), and South Y Industrial Tract (2003) community plans. Page numbers for every row are in the A tables in the geodatabase.

### Step 22. A01: set Use_Status to Allowed (15 rows)

| OBJECTID | Zoning_ID | Use_Type | Now | Source |
|---|---|---|---|---|
| 10403 | 034 | Single Family Dwelling | Special Use | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 210 |
| 9482 | 036 | Multiple Family Dwelling | See note | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 199 |
| 9992 | 042 | Day Use Areas | Special Use | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 202 |
| 9993 | 042 | Riding and Hiking Trails | Special Use | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 202 |
| 10074 | 042 | Single Family Dwelling | Special Use | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 202 |
| 9912 | 045_SA1 | Regional Public Health and Safety Facilities | Special Use | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 177 |
| 10713 | 054_SA1 | Business Support Services | null | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 188 |
| 7730 | PCAP_MU_TOR | Publicly Owned Assembly and Entertainment | Minor Use | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 143 |
| 6818 | PCAP_MU_VC_HOMEWOOD | Repair Services | Minor Use | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 187 |
| 9222 | PCAP_RES_KINGS | Employee Housing | null | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 63 |
| 8231 | PCAP_RES_ROCKY | Beach Recreation | Minor Use | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 82 |
| 9315 | PCAP_TOR | Multi-Person Dwelling | Minor Use | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 264 |
| 6303 | PCAP_TOR | Multiple Family Dwelling | Minor Use | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 264 |
| 3173 | 098_SA2 | Local Assembly and Entertainment | Special Use | Bijou/Al Tahoe Community Plan matrix (Oct 1995), page 26 |
| 3258 | 098_SA4 | Multiple Family Dwelling | See note | Bijou/Al Tahoe Community Plan matrix (Oct 1995), page 25 |

Select (expect 15):
```sql
OBJECTID IN (10403, 9482, 9992, 9993, 10074, 9912, 10713, 7730, 6818, 9222, 8231, 9315, 6303, 3173, 3258)
```
Calculate Field, field `Use_Status`:
```python
"Allowed"
```

### Step 23. A01: set Use_Status to Special Use (9 rows)

| OBJECTID | Zoning_ID | Use_Type | Now | Source |
|---|---|---|---|---|
| 10707 | 045_SA1 | Nursing and Personal Care | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 176 |
| 9938 | 045_SA1 | Printing and Publishing | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 177 |
| 10708 | 045_SA1 | Residential Care | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 176 |
| 9770 | 045_SA1 | Service Stations | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 176 |
| 9684 | 045_SA3 | Health Care Services | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 177 |
| 10226 | 045_SA3 | Sanitation Salvage Cut | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 178 |
| 10003 | 046 | Rural Sports | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 204 |
| 10004 | 046 | Sport Assembly | Allowed | Washoe County Development Code Article 220, Tahoe Area (Dec 17, 2025), page 204 |
| 4958 | 071_SA1 | Collection Stations | Allowed | Round Hill Community Plan (Nov 1993), Chapter II |

Select (expect 9):
```sql
OBJECTID IN (10707, 9938, 10708, 9770, 9684, 10226, 10003, 10004, 4958)
```
Calculate Field, field `Use_Status`:
```python
"Special Use"
```

### Step 24. A01: set Use_Status to Minor Use (3 rows)

| OBJECTID | Zoning_ID | Use_Type | Now | Source |
|---|---|---|---|---|
| 5866 | PCAP_CONS_BURTON | Employee Housing | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 223 |
| 6654 | PCAP_MU_TC | Employee Housing | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 116 |
| 5726 | PCAP_REC_64ACRE | Employee Housing | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 238 |

Select (expect 3):
```sql
OBJECTID IN (5866, 6654, 5726)
```
Calculate Field, field `Use_Status`:
```python
"Minor Use"
```

### Step 25. A01: set Use_Status to Conditional Use (3 rows)

| OBJECTID | Zoning_ID | Use_Type | Now | Source |
|---|---|---|---|---|
| 6512 | PCAP_MU_NT | Amusements and Recreation Services | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 117 |
| 6558 | PCAP_MU_REC | Amusements and Recreation Services | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 117 |
| 6677 | PCAP_MU_TC | Amusements and Recreation Services | Allowed | Placer County Tahoe Basin Area Plan Implementing Regulations (Feb 2021), page 117 |

Select (expect 3):
```sql
OBJECTID IN (6512, 6558, 6677)
```
Calculate Field, field `Use_Status`:
```python
"Conditional Use"
```

### Step 26. A02: delete 9 rows the documents do not support

| OBJECTID | Zoning_ID | Use_Type | Reason |
|---|---|---|---|
| 9787 | 054_SA1 | Food and Beverage Retail Sales | Use is not in this district's list in the document |
| 10314 | 054_SA1 | Outdoor Amusements | Use is not in this district's list in the document |
| 5830 | PCAP_CONS_BLACKWOOD | Allowed in all Areas of the Region | Use is not in this district's list in the document |
| 7608 | PCAP_MU_MTC | Water Quality Improvements and | Use is not in this district's list in the document |
| 7764 | PCAP_MU_WREC | Watershed Management | Use is not in this district's list in the document |
| 6058 | PCAP_RES_DOLLAR | Allowed in all Areas of the Region | Use is not in this district's list in the document |
| 9057 | PCAP_RES_LAKEFOREST | Personal Services | Use is not in this district's list in the document |
| 9165 | PCAP_RES_TAVERN | Industrial Services | Use is not in this district's list in the document |
| 9350 | 098_SA1 | Public Utility Centers | Document marks this use as not permitted in this district |

Select (expect 9):
```sql
OBJECTID IN (9787, 10314, 5830, 7608, 7764, 6058, 9057, 9165, 9350)
```
Delete, then save.

### Step 27. A05: delete all Tahoe Valley and Tourist Core rows, plus the orphan rows (630 rows)

Both plans were rewritten in December 2024 with consolidated use categories (for example "Forest and Timber Resource Management" covers reforestation, thinning, and the other timber uses). The service mixes the new names with the old Code names and has status errors, so the cleanest fix is to replace every row for these 17 districts from the 2024 tables (step A06). The 32 rows with no Zoning_ID are Tahoe Valley and Tourist Core template rows and go too. Confidence: Certain for the 17 districts, Likely for the orphans. Confirm decision R14 first.

Select (expect 630):
```sql
Zoning_ID IN ('TCAP_OS', 'TCAP_REC_TOURIST', 'TCAP_TSC_C', 'TCAP_TSC_G', 'TCAP_TSC_G_SA1', 'TCAP_TSC_MU', 'TCAP_TSC_MUC', 'TCAP_TSC_MUC_SA1', 'TCAP_TSC_NMX', 'TVAP_CMX_S', 'TVAP_EB_CC', 'TVAP_TC_C', 'TVAP_TC_G', 'TVAP_TC_HC', 'TVAP_TC_MUC', 'TVAP_TC_NP', 'TVAP_TC_OS') OR Zoning_ID IS NULL
```
Delete, then save. Record count should be 10,166.

### Step 28. A03, A04, and A06: add 797 rows

- A03 (25 rows): uses the documents list that the service is missing, across Washoe, Placer, Meyers, and the community plans.
- A04 (158 rows): full use lists for four Washoe districts that have no rows at all: 032B Crystal Bay Tourist, 035_SA1 Crystal Bay Condominiums Special Area, 055 East Shore, and 056 Marlette Lake (see decision R18 for 055 and 056).
- A06 (614 rows): the complete 2024 Tahoe Valley and Tourist Core tables. Density, Unit, and Notes carry over from the old row where the same use existed; footnote text from the tables is added to Notes. TCAP_TSC_MUC_SA1 excludes the uses footnote 9 says are not permitted there.

Run Append with Input Datasets `A03_A06_PermissibleUse_Inserts`, Target Dataset the SDE PermissibleUses table, and Field Matching Type "Use the field map". Map Zoning_ID, Category, Subcategory, Use_Type, Use_Status, Density, Unit, and Notes by name; leave the rest unmapped.

Record count should be 10,963. Save edits.

## Part 2. Special_Designation table


### Step 29. F24: delete 33 duplicate rows

Every one is a second copy of a Transfer of Development Rights receiving area (multi-family residential units) row for the same district with the same notes. The lower OBJECTID copy is kept. Confidence: Certain.

Select (expect 33):
```sql
OBJECTID IN (187, 220, 224, 227, 243, 244, 246, 250, 253, 256, 261, 265, 266, 267, 268, 269, 275, 276, 279, 282, 396, 397, 480, 481, 482, 491, 493, 494, 504, 505, 506, 509, 511)
```
Delete, then check the record count is 482. Save edits.

## Part 3. District feature class


### Step 30. F25: repair three self-touching polygons

Shapely flags these as ring self-intersections. The repair changes area by zero square meters. Esri validation sometimes allows self-touching rings, so check first.

| OBJECTID | ZONING_ID |
|---|---|
| 91 | TVAP_CMX_S |
| 172 | PCAP_RES_KINGSWOODWEST |
| 416 | 046 |

Select (expect 3) on District:
```sql
OBJECTID IN (91, 172, 416)
```
Run Check Geometry (Esri validation method) on the District layer. If it reports problems for these features, run Repair Geometry on the District layer with the selection active, Validation Method Esri, and Delete Features with Null Geometry unchecked. If Check Geometry reports nothing, skip the repair.

The next three steps remove district overlaps. Method A uses the Clip edit tool and the clip polygons in `F26_F29_District_ClipAndFill`. Method B swaps in the finished shapes from `F26_F29_District_ReplacementShapes` with a short Python script. Use one method, not both.

### Step 31. F26: clip 111_SA2 where it overlaps TVAP_TC_NP (6.439 acres)

Overlap lies 100 percent inside the Tahoe Valley Area Plan boundary (LocalPlan layer 1) and the 15 parcels mostly inside it already carry PLAN_ID 110. Confidence: Likely.

1. In the District layer, select only 111_SA2 (OBJECTID 152):
```sql
OBJECTID = 152
```
2. On the Edit tab, open Modify, then Clip. Choose Discard (remove the area inside the clipping feature) and a buffer distance of 0.
3. Click the F26 polygon in the `F26_F29_District_ClipAndFill` layer as the clipping feature, then click Clip.
4. Check that 111_SA2 lost about 6.439 acres and TVAP_TC_NP is unchanged.

### Step 32. F27: clip 030 where it overlaps 040 (0.521 acres)

142 edge slivers along the shared boundary; the smaller, more detailed district 040 keeps its line. Confidence: Likely.

1. In the District layer, select only 030 (OBJECTID 402):
```sql
OBJECTID = 402
```
2. On the Edit tab, open Modify, then Clip. Choose Discard (remove the area inside the clipping feature) and a buffer distance of 0.
3. Click the F27 polygon in the `F26_F29_District_ClipAndFill` layer as the clipping feature, then click Clip.
4. Check that 030 lost about 0.521 acres and 040 is unchanged.

### Step 33. F28: clip 114 where it overlaps 114_SA1 (0.012 acres)

6 edge slivers; the special area keeps its line, base district is clipped. Confidence: Likely.

1. In the District layer, select only 114 (OBJECTID 48):
```sql
OBJECTID = 48
```
2. On the Edit tab, open Modify, then Clip. Choose Discard (remove the area inside the clipping feature) and a buffer distance of 0.
3. Click the F28 polygon in the `F26_F29_District_ClipAndFill` layer as the clipping feature, then click Clip.
4. Check that 114 lost about 0.012 acres and 114_SA1 is unchanged.

### Step 34. F29: fill the 1.045 acre hole in Tahoe Valley and give it to TVAP_TC_G

Hole in district coverage inside the Tahoe Valley Area Plan boundary; parcel 032-141-018 in it is stored as TVAP_TC_G. Confidence: Likely.

1. In the `F26_F29_District_ClipAndFill` layer, select the F29 polygon. On the Edit tab, click Copy.
2. Open the Paste menu, choose Paste Special, and pick the SDE District layer as the target. A new District feature with empty attributes appears.
3. Select the new feature and TVAP_TC_G (OBJECTID 174) together. On the Edit tab, open Modify, then Merge.
4. In the Merge pane, choose to keep the attributes of OBJECTID 174 (TVAP_TC_G) and merge into it. The pasted feature is removed and the District count returns to 281.

**Method B for steps F26 to F29.** Instead of Clip and Merge, open the Python window in Pro with editing started and run `scripts/replace_district_shapes.py` (instructions are at the top of the file). It replaces the shape of 111_SA2, 030, 114, and TVAP_TC_G by GlobalID with the shapes in `F26_F29_District_ReplacementShapes` and prints the before and after acres.

### Step 35. F34: recalculate ACRES for every district

Six districts already had an ACRES value more than 1 percent off their shape (TVAP_TC_G, TVAP_TC_OS, TVAP_TC_C, PCAP_REC_HOMEWOOD, PCAP_RES_CHAMBERS, and 040), and steps F26 to F29 changed four more. The stored values match planar area in UTM Zone 10N for the other 275, so use that method.

Clear the selection on District. Run Calculate Geometry Attributes with Input Features District, Field ACRES, Property Area, Area Unit Acres (US survey or international, whichever matches your existing values; they differ by about 4 parts per million), and Coordinate System NAD 1983 UTM Zone 10N. Expected new values for the edited districts:

| ZONING_ID | ACRES before | ACRES after |
|---|---|---|
| 111_SA2 | 78.51 | 72.07 |
| 030 | 8,092.59 | 8,087.51 |
| 114 | 125.73 | 125.72 |
| TVAP_TC_G | 66.78 | 60.87 |

### Step 36. Check the District edits

Run Check Geometry on District and confirm no new problems. Run Count Overlapping Features on District; any area with a count of 2 or more should be under one square meter. Save edits.

## Part 4. Parcel feature class

Parcel ZONING_ID is an overlay of the District layer. If your process rebuilds it from District, rerun that process after Part 3 instead of these steps, then spot check the APNs below. Use these steps only if the parcel fields are edited by hand.

Separate issue for whoever publishes the service: the Parcel layer in Zoning/MapServer and the Parcels/MapServer layer return null geometry for every feature. LocalPlan/MapServer layer 0 returns geometry normally.

### Step 37. F30: update 15 parcels to TVAP_TC_NP

Parcel lies in the F26 overlap that Tahoe Valley keeps. Confidence: Likely.

Select on Parcel (expect 15):
```sql
APN IN ('023-221-028', '023-221-058', '023-221-053', '023-221-052', '023-221-035', '023-221-020', '023-221-050', '023-221-046', '023-221-023', '023-221-045', '023-221-013', '023-221-024', '023-221-017', '023-221-012', '023-221-018')
```
Calculate Field, field `ZONING_ID`:
```python
"TVAP_TC_NP"
```
Calculate Field, field `ZONING_DESCRIPTION`:
```python
"Tahoe Valley Area Plan - Town Center Neighborhood Professional"
```

### Step 38. F31: update 1 parcel to TVAP_TC_OS

Parcel is 100 percent inside TVAP_TC_OS. Confidence: Likely.

Select on Parcel (expect 1):
```sql
APN IN ('032-141-003')
```
Calculate Field, field `ZONING_ID`:
```python
"TVAP_TC_OS"
```
Calculate Field, field `ZONING_DESCRIPTION`:
```python
"Tahoe Valley Area Plan - Open Space"
```

### Step 39. F31: update 1 parcel to TVAP_TC_G

Parcel is 100 percent inside TVAP_TC_G. Confidence: Likely.

Select on Parcel (expect 1):
```sql
APN IN ('032-192-005')
```
Calculate Field, field `ZONING_ID`:
```python
"TVAP_TC_G"
```
Calculate Field, field `PLAN_ID`:
```python
"110"
```
Calculate Field, field `PLAN_NAME`:
```python
"TAHOE VALLEY AREA PLAN"
```
Calculate Field, field `ZONING_DESCRIPTION`:
```python
"Tahoe Valley Area Plan - Town Center Gateway District"
```

### Step 40. F32: update 1 parcel to 067

Blank ZONING_ID; 71 percent inside 067. Confidence: Likely.

Select on Parcel (expect 1):
```sql
APN IN ('1318-09-810-113')
```
Calculate Field, field `ZONING_ID`:
```python
"067"
```
Calculate Field, field `ZONING_DESCRIPTION`:
```python
"Marla Bay/Zephyr Heights"
```

### Step 41. F32: update 1 parcel to 082

Blank ZONING_ID; 54 percent inside 082. Confidence: Likely.

Select on Parcel (expect 1):
```sql
APN IN ('1319-19-717-015')
```
Calculate Field, field `ZONING_ID`:
```python
"082"
```
Calculate Field, field `PLAN_ID`:
```python
"082"
```
Calculate Field, field `PLAN_NAME`:
```python
"UPPER KINGSBURY"
```
Calculate Field, field `ZONING_DESCRIPTION`:
```python
"Upper Kingsbury"
```

### Step 42. F33: update 1 parcel to the plan of their district

PLAN_ID disagrees with its own ZONING_ID 101. Confidence: Certain.

Select on Parcel (expect 1):
```sql
APN IN ('025-360-019')
```
Calculate Field, field `PLAN_ID`:
```python
"101"
```
Calculate Field, field `PLAN_NAME`:
```python
"Bijou Meadows"
```

### Step 43. F33: update 1 parcel to the plan of their district

PLAN_ID disagrees with its own ZONING_ID 100. Confidence: Certain.

Select on Parcel (expect 1):
```sql
APN IN ('031-103-002')
```
Calculate Field, field `PLAN_ID`:
```python
"100"
```
Calculate Field, field `PLAN_NAME`:
```python
"Truckee Marsh"
```

Save edits. If you are in a version, reconcile and post it. Then let the QA owner know so the checks can be rerun against the posted data.

## Part 5. Decisions needed before more edits

These rows are prepared in `R01_R05_Pending_Rulings`, `R07_Pending_SplitParcels`, and `R06_Review_CoverageGaps` but should not be applied until someone decides.

| ID | Item | Question |
|---|---|---|
| R01 | 073 Multiple Family Dwelling | PDF says (A) only on lots designated multi-density. Store Allowed and keep the condition in Notes? |
| R02 | 154 and 154_MF | PAS 154 has no special areas, yet the service splits it into 154 and 154_MF. Merge 154_MF into 154 and add these uses, or keep the split and document its basis? |
| R03 | 112 skiing facilities row | Staff note says skiing facilities is not a recognized use and needs a PAS amendment. Leave null, store the PDF term, or map to Downhill Ski Facilities? |
| R05 | PCAP_MUN_DH special designation | 398 is the same designation with "Bonus Units for Affordable Housing Only". Keep 398 and delete 381? |
| R06 | 26 coverage gaps and slivers | The largest is 4,157 acres at the south end of the Region with no district or plan. A 24 acre gap sits inside the South Shore Area Plan. About 10 acres of district area lies outside the TRPA boundary. Which zoning applies, or is the TRPA boundary layer generalized? |
| R07 | 34 split parcels | Each spans two districts and carries the one covering less of it. Confirm the intended zoning. |
| R08 | 154_MF plan ID | The 154_MF parcels carry PLAN_ID 155 (Tahoma Commercial), but the district is 83 percent inside the PAS 154 boundary. Settle with R02. |
| R09 | Tahoe Valley plan ID | District uses PLAN_ID TVAP; the plan layer and 467 parcels use 110. Pick one. |
| R11 | PCAP_COM/PS_KINGS single family dwelling | Code lists single family dwellings only as accessory to a commercial use, with no permit code. Keep as Allowed with a note, or remove? |
| R12 | Fish habitat rows in PCAP_MU_R, MU_TOR, MU_WREC | North Tahoe East table lists wildlife habitat management but no fish habitat rows. Plan omission, or delete the service rows? |
| R13 | 113 open space line | Open space line "Allowed in all areas of the region" has no status code. Add it as Allowed, as the service does for other plans? |
| R14 | Tahoe Valley Table 1 | The 2024 table has no Religious Assembly row (the old rows allowed it in 7 districts). Employee housing and personal services are folded into Multiple Family Dwelling, Multi-Person Dwelling, and General Retail and Personal Services by the 2024 definitions. Confirm religious assembly was meant to drop before A05 and A06 are posted. |
| R15 | South Shore Area Plan (SSAP_ districts) | Uses are set by Douglas County Development Code Chapter 20.703, which is not linked. Supply the adopted chapter so the 179 SSAP rows can be checked. |
| R16 | PCAP_REC_HOMEWOOD | Uses are set by the Homewood Mountain Resort Master Plan, which is not linked. The district has no rows. |
| R17 | PCAP_RES_CEDAR_SA1 | Special Area 1 follows Cedar Flat only if the TRPA Ordinance 95-4 findings were made; otherwise Watson Creek applies. Rows were built as Cedar Flat. |
| R18 | 055 and 056 | Washoe Code tables exist for East Shore and Marlette Lake, but both districts extend about 42 percent into Carson City. A04 inserts apply the Washoe list to the whole polygon. |
| R10 | PDF problems | 079 lists single family dwelling and 118 lists transportation routes with no (A) or (S). 089B Stateline/Ski Run has no PDF link. |
