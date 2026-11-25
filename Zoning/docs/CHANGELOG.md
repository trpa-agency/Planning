# Changelog

## 2026-11-24

- Added the District CNEL table to replace the legacy noise layer `AGIS_TRPA/MapServer/82`: `data/reference/cnel_by_district.csv` (283 districts, with page citations), `scripts/cnel_build_table.py` (checks District coverage, writes review files and a review geodatabase, and creates and fills `SDE.District_CNEL`; dry run by default), a `cnel` section and dataset in `config.yaml`, and `docs/CNEL.md`. 33 districts change from the legacy layer; 9 carry legacy values and N01 to N08 are open. Tested on a file geodatabase copy; not run in SDE.
- Added `scripts/cnel_export_gpkg.py` and the committed GeoPackage `data/cnel/district_cnel.gpkg` (281 districts from the public service with post-E04 IDs, plus the legacy layer 82 polygons). Moved the CNEL schema and CSV loader to `src/cnel.py`, and added `src/rest.py` for paged REST pulls.
- Added highway noise corridors to the GeoPackage (`highway_centerlines` and `noise_corridors`, built by `src/corridors.py` from the `corridor` config section): Major Highways with route names corrected from Streets, county roads dropped, 8.2 miles of gaps filled, buffered 300 feet, and split by district with each district's corridor standard. Added `parse_corridors` to `src/cnel.py`.
- Fixed PAS 120 in `cnel_by_district.csv`: the document also sets the Highway 50 corridor at 65 CNEL, which the row had dropped. Rebuilt the GeoPackage; 66 acres of US 50 in PAS 120 move from no corridor standard to 65. A check of every PAS noise sentence against the CSV found no other missed corridor. Logged why the airport corridor is still not drawn (the 1987 CLUP zones are safety zones, and the 2019 ALUCP contours exist only as a figure).

## 2026-11-23

- Added the Zoning folder: handoff bundle from the 2026-11-20 QA pass (prototype code, fixtures, and fix package).
- Logged Alyssa's edit requests as E01 to E04 in `docs/EDIT_REQUESTS.md`, with Mason's answers.
- Added `config.yaml`, `src/io.py`, and `src/sde.py` (config, logging, version guard, and cursor helpers).
- Added `scripts/snapshot_version.py`, a read-only snapshot of the QA edit version with review CSVs and a check of the fix package IDs.
- Added `scripts/e03_delete_duplicate_district.py`, which deletes duplicate District 842 and restores the 035 related keys by GlobalID. Dry run by default.
- Added `tests/build_test_gdb.py`, a local test geodatabase with simple relationship classes and a planted duplicate shape.
- Ran the first DEFAULT snapshot on the server. It matches the 2026-11-20 counts, and all 803 checkable fix package rows match SDE. Fixed two snapshot bugs: OBJECTIDs read from the renumbered copy, and float OBJECTIDs in the fix CSVs.
- Added F35 and `scripts/f35_restore_orphaned_designations.py`, which restores ZONING_ID TVAP_TC_NP on Special Designation rows 145, 164, and 207. Dry run by default.
- Added `scripts/compare_snapshots.py`, which diffs two snapshots by GlobalID. Logged the mtb-edits findings in `docs/EDIT_REQUESTS.md`.
- E03 now also deletes the 28 copied 035 use rows, keeping the originals, and stops unless the copy count matches `e03.expected_duplicates`.
- Added F36 and `scripts/f36_delete_empty_use_rows.py`, which deletes the 59 fully blank use rows (Alyssa's 58 from the Nov. 20 append plus F22's 12762). It stops unless the count matches.
- Pointed the config at the `SDE.mtb-edits` edit version.
- Added `scripts/rebuild_fixes.py`, which checks every fix package row against the version (pending, done, conflict, missing, no_district), rekeys A04 to the WCTAP halves, and writes a rebuilt package of pending rows. Added `tests/build_snapshot_gdb.py`, a test geodatabase from the 2026-11-20 snapshot with real GlobalIDs. The baseline reproduces the package; simulated edits produce every status.
- Dropped F30 to F33 because the parcel ETL sets the Parcel_Master zoning fields. Added `rebuild.drop` and the "dropped" status.
- Added `scripts/post_table_fixes.py`, which posts the rebuilt table fixes in one edit session with count, old value, and null key guards. Moved the shared comparison helpers to `src/values.py`.
- Ran E03, F35, and F36 in `SDE.mtb-edits` on the server.
- Ran `fix_district_geometry.py` in `SDE.mtb-edits` (2026-11-24 11:04): replaced 4 district shapes (F26 -6.4386, F27 -0.5213, F28 -0.0117, F29 +1.0451 acres) and recalculated ACRES on 79 more districts (F34; 83 in all). The largest corrections were the 055 and 056 halves, which both still carried the full pre-split acreage; each pair sums to the original within 0.02 acres. A dry run afterward reported nothing to change. Snapshot at 11:22 matched the 283, 11,034, and 486 counts. Reconciled into `Misc edits Nov 2026` (by attribute, in favor of the target), a dry run after the reconcile again reported nothing to change, and posted the same day.
- Added the district shape fixes to `docs/REVIEW_2026-11-24.md`.
- Added `scripts/fix_district_geometry.py` for F26 to F29 and F34, which computes the fixes from current shapes and writes proposed shapes for review. Matches the 2026-11-20 replacement shapes exactly. Dropped F25 because the shapes are valid by Esri rules.
- Ran E04 in `SDE.mtb-edits` (2026-11-24): 36 districts, 1,340 use rows, and 66 special designation rows renamed to WCTAP_.
- Added `scripts/e04_prefix_wctap.py` for the WCTAP_ rename, which renames District and rekeys related rows by GlobalID in one session. Found that changing a District key leaves related rows on the old key.
- Posted E01 in `SDE.mtb-edits` (2026-11-24): use rows for the Carson City halves of 055 and 056, plus special designation copies for the Washoe halves, to 11,034 and 486 rows.
- Built the E01 Carson City package (`packages/e01_carson_pas`) from PAS 055 and 056: 63 use rows with page citations, 2 special designation copies, and 2 PLAN_TYPE updates. `post_table_fixes.py` now accepts partial packages, special designation copies (`sd_inserts.csv`), and `package.yaml` targets. It refuses inserts that already exist and allows existing null keys while refusing new ones. `post_tables.expected_counts` in config is now null by default.
- Posted the table fixes in `SDE.mtb-edits` (95 updates, 687 deletes, and 806 inserts) to 10,971 use rows and 484 special designation rows. Not reconciled yet. District shapes (F25 to F29) still pending. The snapshot afterward matched every expected count. Not reconciled yet. Version matching now handles OS-authenticated owners such as `"TAHOE\ABETTINGER"`.
