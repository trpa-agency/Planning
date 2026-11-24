"""F36: delete Permissible Use rows where every field is blank.

The mtb-edits version has 58 use rows added on 2026-11-20 with nothing in them, not even a
zoning ID, plus one such row from DEFAULT (OBJECTID 12762, fix F22). They carry no content
to recover. This script:

1. Checks the connection is the QA edit version (writes only).
2. Finds rows where every field in f36.fields is null or blank.
3. Stops unless the count equals f36.expected_count.
4. Saves their OBJECTIDs, GlobalIDs, and editor tracking to empty_rows_before.csv.
5. With run.write_to_db true: deletes them by GlobalID in one edit session and verifies
   that no empty rows remain and the table shrank by exactly that count.

Dry run by default. Run from any folder:
    python Zoning/scripts/f36_delete_empty_use_rows.py [--config config.yaml]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

TRACKING = ["created_user", "created_date", "last_edited_user", "last_edited_date"]


def blank(value) -> bool:
    return value is None or str(value).strip() == ""


def find_empty(config: dict) -> list[dict]:
    f36 = config["f36"]
    path = sde.dataset_path(config, f36["table"])
    present = {f.name.lower(): f.name for f in arcpy.ListFields(path)}
    missing = [f for f in f36["fields"] if f.lower() not in present]
    if missing:
        raise sde.GuardError(f"Fields not found in {path}: {missing}")
    fields = [present[f.lower()] for f in f36["fields"]]
    tracking = [present[t] for t in TRACKING if t in present]
    empty = []
    for row in sde.rows(path, ["OID@", "GlobalID", *fields, *tracking]):
        if all(blank(row[f]) for f in fields):
            empty.append({
                "OBJECTID": row["OID@"],
                "GlobalID": sde.norm_guid(row["GlobalID"]),
                **{t: row[t] for t in tracking},
            })
    return empty


def apply(config: dict, empty: list[dict], log) -> None:
    f36 = config["f36"]
    path = sde.dataset_path(config, f36["table"])
    guids = [r["GlobalID"] for r in empty]
    total_before = sde.count(path)
    versioned = sde.is_versioned(path)
    log.info("Starting edit session (multiuser_mode=%s)", versioned)

    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        deleted = 0
        for start in range(0, len(guids), 500):
            chunk = guids[start:start + 500]
            with arcpy.da.UpdateCursor(path, ["GlobalID"], sde.sql_in("GlobalID", chunk)) as cursor:
                for _ in cursor:
                    cursor.deleteRow()
                    deleted += 1
        if deleted != len(guids):
            raise sde.GuardError(f"Deleted {deleted} rows, expected {len(guids)}.")
        remaining = find_empty(config)
        if remaining:
            raise sde.GuardError(f"{len(remaining)} empty rows remain after the delete.")
        total_after = sde.count(path)
        if total_after != total_before - deleted:
            raise sde.GuardError(f"Row count went from {total_before} to {total_after}, expected {total_before - deleted}.")
        log.info("Deleted %s empty rows; %s rows to %s. Saving.", deleted, total_before, total_after)


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("f36_delete_empty_use_rows", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")

    try:
        sde.check_version(config, log, for_write=write)
        empty = find_empty(config)
        out = io.run_folder(config, "f36", stamp)
        sde.write_csv(out / "empty_rows_before.csv", empty, ["OBJECTID", "GlobalID", *TRACKING])
        log.info("Empty rows found: %s (expected %s)", len(empty), config["f36"]["expected_count"])
        log.info("Saved rows: %s", out / "empty_rows_before.csv")
        if len(empty) != config["f36"]["expected_count"]:
            raise sde.GuardError(f"Found {len(empty)} empty rows, expected {config['f36']['expected_count']}. Review before deleting.")
        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to delete them.")
            return 0
        apply(config, empty, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1

    log.info("F36 complete. Rerun the snapshot to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
