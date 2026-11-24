# Changelog

## 2026-11-23

- Added the Zoning folder: handoff bundle from the 2026-11-20 QA pass (prototype code, fixtures, and fix package).
- Logged Alyssa's edit requests as E01 to E04 in `docs/EDIT_REQUESTS.md`, with Mason's answers.
- Added `config.yaml`, `src/io.py`, and `src/sde.py` (config, logging, version guard, and cursor helpers).
- Added `scripts/snapshot_version.py`, a read-only snapshot of the QA edit version with review CSVs and a check of the fix package IDs.
- Added `scripts/e03_delete_duplicate_district.py`, which deletes duplicate District 842 and restores the 035 related keys by GlobalID. Dry run by default.
- Added `tests/build_test_gdb.py`, a local test geodatabase with simple relationship classes and a planted duplicate shape.
