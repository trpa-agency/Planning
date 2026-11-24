"""F35: restore ZONING_ID on Special Designation rows orphaned from TVAP_TC_NP.

Three Special Designation rows have a null ZONING_ID but still carry the description
"Tahoe Valley Area Plan - Town Center Neighborhood Professional". TVAP_TC_NP has no
Special Designation rows. This script:

1. Checks the connection is the QA edit version (writes only).
2. Confirms the TVAP_TC_NP District feature exists with the expected description.
3. Confirms each configured row exists by GlobalID, has the expected OBJECTID, still has
   a null or blank key, and carries the expected description.
4. Confirms TVAP_TC_NP has no existing row with the same designation, so the restore
   cannot create duplicates.
5. Saves the rows to rows_before.csv.
6. With run.write_to_db true: sets ZONING_ID on those rows by GlobalID and verifies inside
   the edit session. Any failed check aborts the edit session and saves nothing.

Dry run by default. Run from any folder:
    python Zoning/scripts/f35_restore_orphaned_designations.py [--config config.yaml]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

FIELDS = ["OID@", "GlobalID", "ZONING_DESCRIPTION", "SPECIAL_DESIGNATION"]


def blank(value) -> bool:
    return value is None or str(value).strip() == ""


def null_key_where(field: str) -> str:
    return f"{field} IS NULL OR {field} = '' OR {field} = ' '"


def check(config: dict, log) -> list[dict]:
    """Run every guard and return the rows to restore."""
    f35 = config["f35"]
    zid = f35["zoning_id"]
    table = sde.dataset_path(config, f35["table"])
    key = config["keys"][f35["table"]]

    district = sde.dataset_path(config, "district")
    dkey = config["keys"]["district"]
    found = sde.rows(district, ["OID@", "ZONING_DESCRIPTION"], f"{dkey} = {sde.sql_text(zid)}")
    if not found:
        raise sde.GuardError(f"No District feature carries ZONING_ID {zid}.")
    descriptions = {r["ZONING_DESCRIPTION"] for r in found}
    if descriptions != {f35["zoning_description"]}:
        raise sde.GuardError(f"District {zid} description is {descriptions}, expected {f35['zoning_description']!r}.")
    log.info("District %s: OBJECTIDs %s", zid, [r["OID@"] for r in found])

    wanted = {sde.norm_guid(r["globalid"]): int(r["objectid"]) for r in f35["rows"]}
    rows = sde.rows(table, FIELDS + [key], sde.sql_in("GlobalID", wanted))
    by_guid = {sde.norm_guid(r["GlobalID"]): r for r in rows}

    problems = []
    for guid, oid in wanted.items():
        row = by_guid.get(guid)
        if row is None:
            problems.append(f"{guid}: not found")
            continue
        if row["OID@"] != oid:
            problems.append(f"{guid}: OBJECTID {row['OID@']}, expected {oid}")
        if not blank(row[key]):
            problems.append(f"{guid}: key is already {row[key]!r}")
        if row["ZONING_DESCRIPTION"] != f35["zoning_description"]:
            problems.append(f"{guid}: description {row['ZONING_DESCRIPTION']!r}")
    if problems:
        raise sde.GuardError("Row checks failed: " + "; ".join(problems))

    existing = {
        r["SPECIAL_DESIGNATION"]
        for r in sde.rows(table, ["SPECIAL_DESIGNATION"], f"{key} = {sde.sql_text(zid)}")
    }
    clashes = [r["SPECIAL_DESIGNATION"] for r in rows if r["SPECIAL_DESIGNATION"] in existing]
    if clashes:
        raise sde.GuardError(f"{zid} already has these designations: {clashes}")

    for r in rows:
        log.info("To restore: OBJECTID %s %s", r["OID@"], r["SPECIAL_DESIGNATION"])
    return rows


def apply(config: dict, rows: list[dict], log) -> None:
    f35 = config["f35"]
    zid = f35["zoning_id"]
    table = sde.dataset_path(config, f35["table"])
    key = config["keys"][f35["table"]]
    guids = [sde.norm_guid(r["GlobalID"]) for r in rows]
    nulls_before = sde.count(table, null_key_where(key))
    keyed_before = sde.count(table, f"{key} = {sde.sql_text(zid)}")
    versioned = sde.is_versioned(table)
    log.info("Starting edit session (multiuser_mode=%s)", versioned)

    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        updated = 0
        with arcpy.da.UpdateCursor(table, ["GlobalID", key], sde.sql_in("GlobalID", guids)) as cursor:
            for guid, value in cursor:
                if not blank(value):
                    raise sde.GuardError(f"{guid} changed to {value!r} before the update.")
                cursor.updateRow([guid, zid])
                updated += 1
        if updated != len(guids):
            raise sde.GuardError(f"Updated {updated} rows, expected {len(guids)}.")

        keyed = {sde.norm_guid(r["GlobalID"]) for r in sde.rows(table, ["GlobalID"], f"{key} = {sde.sql_text(zid)}")}
        if not set(guids) <= keyed or len(keyed) != keyed_before + len(guids):
            raise sde.GuardError(f"Rows keyed {zid} after the update: {len(keyed)}, expected {keyed_before + len(guids)}.")
        nulls_after = sde.count(table, null_key_where(key))
        if nulls_after != nulls_before - len(guids):
            raise sde.GuardError(f"Null keys went from {nulls_before} to {nulls_after}, expected {nulls_before - len(guids)}.")
        log.info("Restored %s rows to %s; null keys %s to %s. Saving.", updated, zid, nulls_before, nulls_after)


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("f35_restore_orphaned_designations", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")

    try:
        sde.check_version(config, log, for_write=write)
        rows = check(config, log)
        out = io.run_folder(config, "f35", stamp)
        sde.write_csv(
            out / "rows_before.csv",
            [{"OBJECTID": r["OID@"], "GlobalID": r["GlobalID"], "SPECIAL_DESIGNATION": r["SPECIAL_DESIGNATION"]} for r in rows],
            ["OBJECTID", "GlobalID", "SPECIAL_DESIGNATION"],
        )
        log.info("Saved rows: %s", out / "rows_before.csv")
        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to restore the keys.")
            return 0
        apply(config, rows, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1

    log.info("F35 complete. Rerun the snapshot to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
