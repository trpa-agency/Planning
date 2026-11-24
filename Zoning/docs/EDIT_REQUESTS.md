# Zoning edit requests

Edit requests from planning staff, tracked against the 2026-11-20 QA fix package (see `CLAUDE.md` sections 7 and 8). Each request gets an E-series ID. Fix IDs (F, A) and decision IDs (R) keep their meaning from the package.

Live service checks below ran on 2026-11-23 against `Zoning/MapServer`, `Boundaries/MapServer`, and the 2026-11-20 snapshot.

## Requests from Alyssa (Senior Planner), 2026-11-23

| ID | Request | Status |
|---|---|---|
| E01 | Add use lists for 056, WCTAP_056, 055, WCTAP_055, 032B, and 035_SA1 | Ready. Split done in Alyssa's version; A04 covers Washoe; Carson City PAS lists to build |
| E02 | Split 045 Incline Village Commercial into Town Center and non-Town Center districts | On hold for Alyssa: what she meant, given 045 is entirely inside the Town Center |
| E03 | Delete Crystal Bay Condominiums OBJECTID 842 without losing the use table for OBJECTID 405 | Ready. 842 is an accidental duplicate of 035 |
| E04 | Prefix Washoe County zoning IDs with WCTAP | Ready. Run last |

### Answers from Mason, 2026-11-23

- E02: 045 looks entirely inside the Town Center. Left for Mason to raise with Alyssa; no scripts until then.
- E03: OBJECTID 842 carries ZONING_ID 035. It is an accidental duplicate shape of OBJECTID 405.
- E01: Alyssa already split 055 and 056 along the county line in `Misc edits Nov 2026`. Both halves of each district get a copy of its Special Designation row.
- E04: The prefix is `WCTAP_` plus the current ID, and 019 Martis Peak gets it too. Only five things read ZONING_ID: District, PermissibleUses, Special_Designation, the Parcel layer, and the Local Plan layer. The web apps need only a retest.
- Versioning: see the Versioning section.

### E01: Use lists for the empty Washoe and Carson City districts

What exists today:

- The service has no Permissible Use rows for 032B, 035_SA1, 055, or 056. [Certain]
- Fix A04 inserts 158 rows from the Washoe County code: 032B (59), 035_SA1 (36), 055 (39), and 056 (24). [Certain]

What Alyssa's list adds:

- She lists a Carson City and a Washoe County version of both 055 and 056. That means splitting each polygon at the Carson City line, which also settles R18 (each is about 42 percent in Carson City). [Likely]
- The Washoe portions become WCTAP_055 and WCTAP_056 and take the A04 rows, rekeyed.
- The Carson City portions keep 055 and 056 and need use lists from the Plan Area Statements. Carson City has no area plan, so the PAS still governs there. [Likely] The PAS PDFs exist at `.../documents/archive/2/055.pdf` and `.../056.pdf`, but the prototype PAS pass did not parse them, because District folds both into WCTAP. Those are new parser runs.

Open points:

- Which line to split on. `Boundaries/MapServer/10` Jurisdictions Combined looks like generalized Census county lines (section 3). Splitting zoning on a generalized line moves real parcels to the wrong side. Prefer the county line from parcel fabric or the official Carson City and Washoe boundary.
- Special Designation has one row each for 055 and 056. Both halves probably need a copy.

### E02: Split 045 into Town Center and non-Town Center

The current service carries Multiple Family Dwelling at 15 units per acre on 045 (Special Use) and 045_SA1 (Allowed). Alyssa wants 25 inside the Town Center and 15 outside.

The problem: on the published Town Center layer (`Boundaries/MapServer/1`, Incline Village Commercial, 207.86 acres), all of 045 is inside the Town Center. [Certain]

| District | Acres | Inside Town Center | Outside |
|---|---|---|---|
| 045 | 133.43 | 133.37 | 0.06 |
| 045_SA1 | 48.27 | 48.27 | 0 |
| 045_SA2 | 2.06 | 2.06 | 0 |
| 045_SA3 | 23.88 | 23.88 | 0 |

The 0.06 acres is a sliver, not a district. The Parcel layer agrees: all 325 parcels in 045 and its special areas carry the Incline Village Commercial Town Center.

Resolved 2026-11-23: no split. 045 is entirely inside the Town Center.

Open point: if Alyssa's rule is 25 units per acre inside the Town Center, then all of 045 should be at 25, not the 15 the service carries today. Check the Washoe County Development Code Article 220 entry for Incline Village Commercial before changing anything. Area plan densities were never checked in the first QA pass. If the code says 25, the fix is a density update on the 045 Multiple Family Dwelling row, and on 045_SA1 if its own table says the same.

Original question, kept for the record: which boundary defines "outside the Town Center"? Possibilities are an amended Town Center line from the Washoe area plan, a different district (for example 046 or 047), or a Town Center layer that needs its own update. The split can't be drawn until that's settled. Once it is, the edit is a polygon split, a new ZONING_ID, a copy of the 045 use rows to the new ID, and a density change on one Multiple Family Dwelling row. Density is an Integer field, so 25 and 15 store fine.

### E03: Delete OBJECTID 842 and keep the 405 use table

Why it happens:

- Both relationships from District (to `SDE.PermissibleUses` and `SDE.Special_Designation`) are simple, not composite, and keyed on ZONING_ID. [Certain]
- In a simple relationship, deleting an origin feature sets the foreign key to null on every related row. [Certain] Both Crystal Bay Condominiums features share one ZONING_ID, so deleting either one nulls the key on all of them. The rows are still there, but they belong to no district.
- The 33 Permissible Use rows with a null Zoning_ID in the 2026-11-20 snapshot are probably the same symptom from an earlier delete. [Likely]

OBJECTID 842 isn't in the published service. Only OBJECTID 405 (035, 62.18 acres) is. So 842 exists only in Alyssa's version or in an unpublished state. [Certain] Today 035 has 28 Permissible Use rows and 1 Special Designation row.

Method, in Alyssa's version (scriptable, dry run first):

1. Confirm 842's ZONING_ID and that its geometry adds nothing that 405 lacks.
2. Save the GlobalIDs of every Permissible Use and Special Designation row where the ZONING_ID equals that value.
3. Delete OBJECTID 842.
4. Set ZONING_ID back on those rows, matched by GlobalID.
5. Verify: same row counts as step 2, no new null keys, and the relate from 405 returns the full table.

Another route: change 842's ZONING_ID to a throwaway value before deleting it. Don't use it. If the edit session cascades key changes, the 405 rows would move to the throwaway value. [Guessing]

### E04: Prefix Washoe County zoning IDs with WCTAP

Scope: 38 districts carry PLAN_ID WCTAP (019 through 056, including special areas). The format to confirm is `WCTAP_` plus the current ID, for example `WCTAP_045_SA1`.

ZONING_ID is the join key for everything, so the rename touches more than the District layer:

| Target | How it follows the rename |
|---|---|
| SDE.District | The edit itself |
| SDE.PermissibleUses, SDE.Special_Designation | Simple relationship on ZONING_ID. Update the keys explicitly in the same edit, then verify the counts. Don't count on the relationship cascading the change. |
| Parcel ZONING_ID (Zoning layer 1, LocalPlan layer 0) | Not related. Separate update, or rerun whatever populates it. |
| Fix package | Every WCTAP row in A01 to A04, plus F21's "45" to 045 change, uses the old IDs |
| Web apps | LongRange district explorer and parcel lookup, and the Permitting zoning lookup and parcel viewers, read the Zoning service. No hardcoded zoning IDs turned up in a quick scan. Retest them after the rename. |
| 019 Martis Peak | Folded into WCTAP in District, but the Local Plan layer keeps it as its own PAS. Confirm it should get the prefix. |
| 055 and 056 Carson City halves | Keep their current IDs (E01) |

The rename goes last. Do every edit keyed on the old IDs first, then rename in one pass.

## Findings from the DEFAULT snapshot, 2026-11-23

- DEFAULT matches the 2026-11-20 service: 281 districts, 10,812 use rows, 515 special designation rows, and 61,275 parcels. Nothing changed between the QA pass and this snapshot. [Certain]
- All 803 checkable fix package rows match SDE by GlobalID and OBJECTID. The other 8 are inserts and open decisions with no existing row. The fix package OBJECTIDs are safe to use. [Certain]
- Permissible Use has 33 rows with a null key, as the QA pass found. A05 deletes them.
- Special Designation has 3 rows with a null key that the QA pass missed: OBJECTIDs 145, 164, and 207. All three still carry the ZONING_DESCRIPTION "Tahoe Valley Area Plan - Town Center Neighborhood Professional". TVAP_TC_NP has no Special Designation rows, and its sibling districts TVAP_TC_C and TVAP_TC_MUC carry the same three designations (TDR receiving areas for existing development, TDR receiving areas for MFRU, and Town Center). All three rows were last edited on Apr. 4, 2025. These rows were most likely orphaned when a TVAP_TC_NP shape was deleted or replaced, the same simple relationship behavior as E03. [Likely] Proposed fix F35: set ZONING_ID to TVAP_TC_NP on those three rows, matched by GlobalID:
  - 145 `{BEE7739F-C287-42CB-9915-6A06B4E8C029}`
  - 164 `{F0ED7835-9BB0-4646-AF0F-D3BC30EAD9C2}`
  - 207 `{C173A649-23D3-4B22-9F36-C771EB51207B}`

## Findings from the mtb-edits snapshot, 2026-11-23

`compare_snapshots.py` compared DEFAULT (20:54) with `SDE.mtb-edits` (21:50), which inherits Alyssa's `Misc edits Nov 2026`. Every added row was created by the `SDE` login on 2026-11-20 between 23:51 and 23:58 (times as recorded by editor tracking).

District (281 to 284):
- 055 kept its ID and took the Carson City shape; PLAN_ID changed from WCTAP to 055. New WCTAP_055 added.
- 056 was renamed WCTAP_056 and reshaped. New 056 added for the Carson City side.
- 842 added as a copy of 035.

Permissible Use (10,812 to 10,907):
- 28 rows keyed 035 were added at 23:51:47, copies of 405's table made with 842. 035 now has 56 rows. E03 deletes the copies and keeps the originals (lowest OBJECTID in each identical pair), and stops if the count is not exactly 28.
- 58 rows were added with a null key: 56 at 23:57:59 and 1 each at 23:51:04 and 23:51:08. None of their use types appear in the 035 list, so they are not 035 copies. Probably an append where `Zoning_ID` did not map. [Guessing] Open: identify the intended district.
- Other edits by Alyssa: new rows in 045 (2), 048 (6), and 054 (2); one 045 row deleted; field changes on 36 rows (27 Notes in 042; Density in 045 and 045_SA1; Use_Status in 034 and 042; Use_Type, Unit, Density, and Notes in 048).

Special Designation (515 to 516): one row added in each of 034 and 054. OBJECTID 493 deleted, which was the F24 duplicate in 045, so that F24 row is already done.

Effect on the fix package: Alyssa's version touches districts the package also edits: A01 in 034, 042, and 045_SA1, and A03 in 054. Some of these fixes may already be applied. A04's 055 and 056 rows now belong to WCTAP_055 and WCTAP_056. Rebuild the fix rows against the version before posting any of them.

## Recommended order

1. Create the QA edit version as a Protected child of `Misc edits Nov 2026`.
2. Snapshot the edit version to a local file geodatabase. Record how Alyssa keyed the 055 and 056 halves, and check the fix package OBJECTIDs and GlobalIDs against the version.
3. E03: delete 842 with the key restore.
4. Post the 2026-11-20 fix package, or the parts of it staff accept, on the old IDs.
5. E01: rekey the A04 055 and 056 rows to the Washoe halves, insert the Carson City PAS lists, and copy the Special Designation rows to both halves.
6. E02: on hold until Alyssa answers.
7. E04: rename to `WCTAP_` across District, PermissibleUses, Special_Designation, the Parcel layer, and the Local Plan layer. Include 019. Leave the Carson City halves of 055 and 056 unchanged.
8. Rerun the QA against the edit version. Then reconcile into Alyssa's version and retest the LongRange and Permitting apps after she posts.

## Running the scripts on the server

Every script that touches SDE runs on the server, from a clone of this repo. Code is written and tested locally against `data/test/zoning_test.gdb` (built by `tests/build_test_gdb.py`), pushed to `main`, then pulled on the server.

1. Edit version: `SDE.mtb-edits`, Protected, a child of `"TAHOE\ABETTINGER"."Misc edits Nov 2026"` (created 2026-11-23).
2. Connection: copy `F:\GIS\DB_CONNECT\Vector.sde` to `F:\GIS\DB_CONNECT\Vector_mtb-edits.sde`. In Pro, add the copy, right-click it, open **Connection Properties**, and set the transactional version to `mtb-edits`. Leave `Vector.sde` on DEFAULT. `config.yaml` already points at the copy.
3. After each push: `git pull origin main` on the server branch (`mtb-arc11`).
4. Snapshot (read only): `python Zoning/scripts/snapshot_version.py`. The log should say `Connected version: SDE.mtb-edits` with no warnings. Review `Zoning/outputs/snapshot_<time>/`: `watch_districts.csv` for how Alyssa keyed the 055 and 056 halves, `duplicate_zoning_ids.csv` for 035 on 405 and 842, and `fix_id_check.csv`.
5. E03 dry run: `python Zoning/scripts/e03_delete_duplicate_district.py`. It confirms that 842 and 405 are the only 035 features, that 842 adds no area, and saves the related rows to `outputs/e03_<time>/related_rows_before.csv`.
6. F35 dry run: `python Zoning/scripts/f35_restore_orphaned_designations.py`. It confirms the three rows still have a null key and the TVAP_TC_NP description, and that TVAP_TC_NP doesn't already have those designations.
7. Writes: set `run.write_to_db: true`, run E03, then run F35, then set it back to `false`. Both scripts refuse to write unless the connection is `SDE.mtb-edits`. Every check runs inside the edit session, and any failure discards the edit. A rerun after a successful write stops at the guards.
8. Rerun the snapshot to confirm: no duplicate 035, and Special Designation null keys go from 3 to 0.

Use the Pro Python: `"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"`.

Local test results, 2026-11-23: deleting the duplicate in a simple relationship nulled the key on all 28 use rows and the 1 Special Designation row, and the script wrote all 29 back. The guard stopped the script on a wrong OBJECTID and on a rerun after the delete.

## Versioning

Confirmed 2026-11-23: traditional versioning. Alyssa's version is `Misc edits Nov 2026`, a child of DEFAULT, with Public access. Our edit version is a child of hers. Edits reconcile into her version, and she posts to DEFAULT.

Because her version is Public, anyone can edit it directly. Make all QA edits in our child version, never in hers.

- Traditional versioning: a child version under Alyssa's version works. Our edits reconcile into hers, and hers into DEFAULT.
- Branch versioning: every named version must be a direct child of DEFAULT. A version under Alyssa's version isn't possible. Edits also have to go through a feature service with version management, not a direct `.sde` connection. Use two sibling versions under DEFAULT, keep the edits apart by request, and reconcile hers first.
