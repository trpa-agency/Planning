# Zoning edit requests

Edit requests from planning staff, tracked against the 2026-11-20 QA fix package (see `CLAUDE.md` sections 7 and 8). Each request gets an E-series ID. Fix IDs (F, A) and decision IDs (R) keep their meaning from the package.

Live service checks below ran on 2026-11-23 against `Zoning/MapServer`, `Boundaries/MapServer`, and the 2026-11-20 snapshot.

## Requests from Alyssa (Senior Planner), 2026-11-23

| ID | Request | Status |
|---|---|---|
| E01 | Add use lists for 056, WCTAP_056, 055, WCTAP_055, 032B, and 035_SA1 | Done in `SDE.mtb-edits` 2026-11-24. Washoe lists via A04; Carson City lists via `packages/e01_carson_pas`. Not yet reconciled |
| E02 | Split 045 Incline Village Commercial into Town Center and non-Town Center districts | On hold for Alyssa: what she meant, given 045 is entirely inside the Town Center |
| E03 | Delete Crystal Bay Condominiums OBJECTID 842 without losing the use table for OBJECTID 405 | Done in `SDE.mtb-edits` 2026-11-23. Not yet reconciled |
| E04 | Prefix Washoe County zoning IDs with WCTAP | Done in `SDE.mtb-edits` 2026-11-24: 36 districts, 1,340 use rows, and 66 special designation rows. Parcels follow on the next ETL run. Not yet reconciled |

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

Built 2026-11-24 (`packages/e01_carson_pas`; rows and page citations in `data/reference/e01_carson_pas_rows.csv`):

- 055 Carson City: 39 use rows from PAS 055 East Shore, p. 3, with densities from p. 4. These are single family dwelling and summer homes at 1 unit per parcel, employee housing at 5 (stored as "units per State Park Lands", following 057), developed campgrounds at 8 sites per acre, and group facilities at 25 persons per acre.
- 056 Carson City: 24 use rows from PAS 056 Marlette Lake, p. 2, with summer homes at 1 unit per parcel from p. 3.
- Shorezone uses are left out, as in every other PAS district in the service. Combined phrases are expanded to the service's uses, for example structural and nonstructural fish and wildlife habitat management to four uses.
- Cross-check: the same 63 uses as A04's Washoe code lists for 055 and 056, with matching statuses except 055 Single Family Dwelling. The PAS says Special Use and the Washoe code says Allowed. Each governs its own side of the county line, so both stand. [Certain]
- Special Designation: copies of 461 (055, TDR receiving area for MFRU, limited to employee housing) and 462 (056, None) go to WCTAP_055 and WCTAP_056 as Area Plan. PLAN_TYPE on 461 and 462 changes from Area Plan to Plan Area Statement. That change is inferred from Alyssa's PLAN_ID change on 055 and is easy to drop. [Likely]
- Targets: 10,971 to 11,034 use rows and 484 to 486 special designation rows (`package.yaml`).

Post it with `python Zoning/scripts/post_table_fixes.py --rebuilt Zoning/packages/e01_carson_pas`, dry run first.

Open points, kept for the record:

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

Script (2026-11-24): `python Zoning/scripts/e04_prefix_wctap.py`. It renames every District with PLAN_ID WCTAP that isn't already prefixed, except the Carson City 055 and 056 (`e04.exclude`), and stops unless that's 36 (`e04.expected_count`). The dry run lists every old and new ID. In one session it renames District, then rekeys every related use and special designation row by GlobalID, recorded beforehand. It stops if a new ID already exists, if any old ID remains, if the rows per new ID differ from before, or if totals or null keys change. Parcel_Master is left to the parcel ETL. The Local Plan layer is renamed only if added to `e04.also_update`.

Tested on the test geodatabase with simple relationship classes: 36 districts, 120 use rows, and 9 special designation rows renamed; 055 and 056 unchanged; the wrong count guard and the rerun guard both stopped. Changing a District key there left all 92 related rows on the old key, so a hand rename in Pro orphans the use table.

Open: the Local Plan layer (LocalPlan/MapServer/0) carries ZONING_ID. Is it maintained by the parcel ETL like Parcel_Master? If not, add its dataset to `datasets.local_plan_parcels` and `e04.also_update`.

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
- 58 rows were added with a null key: 56 at 23:57:59 and 1 each at 23:51:04 and 23:51:08. Every field is blank, including Category, Use_Type, Use_Status, Density, and Unit. [Certain] There is nothing to recover. Probably an append that mapped no fields. [Likely] F36 deletes them, together with DEFAULT's one empty row (OBJECTID 12762, already fix F22), so 59 in all.
- Other edits by Alyssa: new rows in 045 (2), 048 (6), and 054 (2); one 045 row deleted; field changes on 36 rows (27 Notes in 042; Density in 045 and 045_SA1; Use_Status in 034 and 042; Use_Type, Unit, Density, and Notes in 048).

Special Designation (515 to 516): one row added in each of 034 and 054. OBJECTID 493 deleted, which was the F24 duplicate in 045, so that F24 row is already done.

Effect on the fix package: Alyssa's version touches districts the package also edits: A01 in 034, 042, and 045_SA1, and A03 in 054. Some of these fixes may already be applied. A04's 055 and 056 rows now belong to WCTAP_055 and WCTAP_056. Rebuild the fix rows against the version before posting any of them.

## Edits made in SDE.mtb-edits, 2026-11-23

Run on the server; logs and before-state CSVs are in the server's `Zoning/outputs/`. Not yet reconciled into Alyssa's version.

| Fix | Result |
|---|---|
| E03 | Deleted District 842. Deleted the 28 copied 035 use rows and wrote 035 back on the 28 originals and the 1 Special Designation row. |
| F35 | Restored TVAP_TC_NP on Special Designation rows 145, 164, and 207. |
| F36 | Deleted 59 fully blank use rows (10,879 to 10,820), including F22's 12762. |
| Table fixes | 23:48. Posted the rebuilt package (rebuild 23:44): 95 updates, 687 deletes (655 use, 32 special designation), and 806 inserts, covering F01 to F24 and A01 to A06 less what was already done. PermissibleUses 10,820 to 10,971 and Special_Designation 516 to 484, with no null keys and no duplicate district and use pairs. Confirmed by a rebuild at 23:52: all 1,592 table fix rows read done; left are the A03 054 conflict (Alyssa's row stands), F25 to F29 pending, and F30 to F33 dropped. |

Snapshot after the edits (23:03): 283 districts, 10,820 use rows, 516 special designation rows, and no duplicate zoning IDs. Use rows with a null key are down from 91 to 32; A05 deletes those. No Special Designation rows have a null key. Fix package: 801 rows match. The 2 not found in the version are F24's 493 (deleted by Alyssa) and F22's 12762 (deleted by F36), so both fixes are done.

E04, run 2026-11-24 00:23: renamed 36 WCTAP districts (019 through 054_SA1) to `WCTAP_<id>`, with 1,340 use rows and 66 special designation rows rekeyed by GlobalID. Totals are unchanged and there are no null keys. WCTAP_055 and WCTAP_056 were already prefixed; the Carson City 055 and 056 carry their own PLAN_IDs and were not candidates. The rebuild script keys on the old IDs, so it no longer applies to the 2026-11-20 package, which is fully posted.

After posting to DEFAULT: run the parcel ETL so `SDE.Parcel_Master` (also published as LocalPlan/MapServer/0) picks up the new IDs. Until then, Washoe parcels carry the old IDs and parcel-based use lookups return nothing for them. Retest the LongRange and Permitting zoning apps after the ETL.

E01 Carson City, posted 2026-11-24 00:09: 2 PLAN_TYPE updates, 63 use rows (055 and 056), and 2 special designation copies (WCTAP_055 and WCTAP_056). PermissibleUses 10,971 to 11,034 and Special_Designation 484 to 486, with no null keys and no duplicate district and use pairs.

## District geometry (F25 to F29, F34), built 2026-11-24

`scripts/fix_district_geometry.py` computes the fixes from the version's current shapes instead of loading the 2026-11-20 replacement shapes. It can't undo a later edit, and it follows the E04 rename (030 and 040 are WCTAP_030 and WCTAP_040).

- F25 dropped. Esri Check Geometry (ESRI method) finds no problem with the three shapes. They fail only the OGC method: they are self-touching rings, which ArcGIS allows. [Certain]
- F26 to F28: each overlap is clipped off the losing district, and parts under 1 square meter are dropped. The expected overlaps are 6.4386, 0.5213, and 0.0117 acres.
- F29: the hole under parcel 032-141-018 (1.0451 acres) is found by differencing nearby districts and merged into TVAP_TC_G.
- F34: stored ACRES is planar area in EPSG 26910; 255 of 281 districts match to 0.01 acres. The rest drifted after shape edits, for example PCAP_RES_CHAMBERS stored at 372.48 but measuring 409.78. The script resets ACRES where it is off by more than 0.001 acres: 81 districts in the DEFAULT state, 28 of them by more than 0.01.
- Guards: each district exists once; each overlap and the fill are within 0.05 acres of expected; after writing, each pair overlaps by less than 1 square meter, the fill overlaps no other district, and the parcel is covered. A fix already in place is skipped, so a rerun changes nothing.
- Tested on a copy of the public districts: the computed shapes match the 2026-11-20 replacement shapes in the delivered zip with 0.000 square meters of difference. Write, verify, and rerun all behaved.

## Fix package rebuilt against SDE.mtb-edits, 2026-11-23 (23:28)

1,641 rows pending, 4 done, 1 conflict, and nothing missing. After posting, PermissibleUses goes from 10,820 to 10,971 and Special_Designation from 516 to 484.

- A01: 2 done. Alyssa set the same Use_Status in 034 and 042. [Likely]
- A03: 1 conflict, resolved in favor of Alyssa's row. 054 Employee Housing already exists in her version with the same status, plus a density of 15 units per acre; the A03 insert carried no density, because area plan densities were not checked in the QA pass. Her row stands, and the rebuilt package leaves the insert out.
- F22 and F24 (493): done, deleted by F36 and by Alyssa.
- A04: all 158 pending, with 055 and 056 rekeyed to WCTAP_055 and WCTAP_056.
- F25 to F29: pending; the targeted district shapes are unchanged from DEFAULT.
- F30 to F33: pending; `SDE.Parcel_Master` has ZONING_ID, ZONING_DESCRIPTION, PLAN_ID, and PLAN_NAME, and every old value still matches.
- No use rows sit in A05 districts outside A05.

Decided 2026-11-23: the parcel ETL sets the Parcel_Master zoning fields from District, so F30 to F33 are dropped (`rebuild.drop` in `config.yaml`). The ETL carries the district fixes through to parcels.

Still open: F25 to F29 need the replacement shapes from the fix geodatabase in the delivered zip, which is not in the repo.

### Posting the table fixes

`scripts/post_table_fixes.py` applies the rebuilt updates, deletes, and inserts to PermissibleUses and Special_Designation in one edit session. Order: updates, then deletes, then inserts. Before anything is written, it checks every target by GlobalID and every old value, and stops unless the projected counts equal `post_tables.expected_counts` (10,971 and 484). It also stops if any row would be left with a null key. It verifies the final counts and null keys inside the session before saving.

1. Rebuild fresh, so the package matches the version as it is now:
   `python Zoning/scripts/rebuild_fixes.py --default Zoning/data/snapshots/sde_DEFAULT_20261123_205432.gdb`
2. Dry run: `python Zoning/scripts/post_table_fixes.py --rebuilt Zoning/outputs/rebuild_<time>/rebuilt`
3. Write: set `run.write_to_db: true`, rerun step 2, then `git checkout -- Zoning/config.yaml`.
4. Confirm: rerun the rebuild. Every table fix should read done, and only F25 to F29 should stay pending.

Tested on the 2026-11-20 state: 97 updates, 689 deletes, and 744 inserts posted. The result was 10,900 and 482 rows with no null keys and no duplicate district and use pairs. A second run stopped without writing, and the rebuild afterward read every table fix as done.

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
7. F36 dry run: `python Zoning/scripts/f36_delete_empty_use_rows.py`. It should find 59 rows where every field is blank.
8. Writes: set `run.write_to_db: true`, run E03, F35, and F36, then set it back to `false`. Both scripts refuse to write unless the connection is `SDE.mtb-edits`. Every check runs inside the edit session, and any failure discards the edit. A rerun after a successful write stops at the guards.
9. Rerun the snapshot to confirm: no duplicate 035, use rows with a null key go from 91 to 32 (DEFAULT's 33 minus F22's empty row; A05 deletes the rest), and Special Designation null keys go from 3 to 0.

Rebuild the fix package against the version before posting any of it (read only):

```
python Zoning/scripts/rebuild_fixes.py --default Zoning/data/snapshots/sde_DEFAULT_20261123_205432.gdb
```

It marks every fix row as pending, done, conflict, missing, or no_district, moves the A04 rows for 055 and 056 to WCTAP_055 and WCTAP_056, and writes `outputs/rebuild_<time>/`: `fix_status.csv`, `review.csv` (rows to settle by hand), `extra_rows_in_replaced_districts.csv`, and `rebuilt/` (only the pending rows, in the package's own columns). `--default` adds the District geometry check. Against the unchanged 2026-11-20 state it reproduces the package exactly: 1,537 pending, and 10,812 use rows to 10,900 (10,963 less the 63 A04 rows whose districts do not exist in DEFAULT).

Use the Pro Python: `"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"`.

Local test results, 2026-11-23: deleting the duplicate in a simple relationship nulled the key on all 28 use rows and the 1 Special Designation row, and the script wrote all 29 back. The guard stopped the script on a wrong OBJECTID and on a rerun after the delete.

## Versioning

Confirmed 2026-11-23: traditional versioning. Alyssa's version is `Misc edits Nov 2026`, a child of DEFAULT, with Public access. Our edit version is a child of hers. Edits reconcile into her version, and she posts to DEFAULT.

Because her version is Public, anyone can edit it directly. Make all QA edits in our child version, never in hers.

- Traditional versioning: a child version under Alyssa's version works. Our edits reconcile into hers, and hers into DEFAULT.
- Branch versioning: every named version must be a direct child of DEFAULT. A version under Alyssa's version isn't possible. Edits also have to go through a feature service with version management, not a direct `.sde` connection. Use two sibling versions under DEFAULT, keep the edits apart by request, and reconcile hers first.
