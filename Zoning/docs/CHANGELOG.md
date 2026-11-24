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
- Pointed the config at the `SDE.mtb-edits` edit version. Version matching now handles OS-authenticated owners such as `"TAHOE\ABETTINGER"`.
