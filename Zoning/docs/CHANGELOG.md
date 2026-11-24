# Changelog

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
- Added `scripts/fix_district_geometry.py` for F26 to F29 and F34, which computes the fixes from current shapes and writes proposed shapes for review. Matches the 2026-11-20 replacement shapes exactly. Dropped F25 because the shapes are valid by Esri rules.
- Ran E04 in `SDE.mtb-edits` (2026-11-24): 36 districts, 1,340 use rows, and 66 special designation rows renamed to WCTAP_.
- Added `scripts/e04_prefix_wctap.py` for the WCTAP_ rename, which renames District and rekeys related rows by GlobalID in one session. Found that changing a District key leaves related rows on the old key.
- Posted E01 in `SDE.mtb-edits` (2026-11-24): use rows for the Carson City halves of 055 and 056, plus special designation copies for the Washoe halves, to 11,034 and 486 rows.
- Built the E01 Carson City package (`packages/e01_carson_pas`) from PAS 055 and 056: 63 use rows with page citations, 2 special designation copies, and 2 PLAN_TYPE updates. `post_table_fixes.py` now accepts partial packages, special designation copies (`sd_inserts.csv`), and `package.yaml` targets. It refuses inserts that already exist and allows existing null keys while refusing new ones. `post_tables.expected_counts` in config is now null by default.
- Posted the table fixes in `SDE.mtb-edits` (95 updates, 687 deletes, and 806 inserts) to 10,971 use rows and 484 special designation rows. Not reconciled yet. District shapes (F25 to F29) still pending. The snapshot afterward matched every expected count. Not reconciled yet. Version matching now handles OS-authenticated owners such as `"TAHOE\ABETTINGER"`.
