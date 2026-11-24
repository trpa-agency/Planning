"""E03: delete the duplicate Crystal Bay Condominiums District shape and keep its use table.

District relates to PermissibleUses and Special_Designation through simple relationships
keyed on ZONING_ID. Deleting a District feature nulls the key on related rows, and both
035 shapes share those rows. This script:

1. Checks the connection is the QA edit version (writes only).
2. Confirms exactly two District features carry the ZONING_ID: the one to delete and the
   one to keep, and that the duplicate covers no meaningful area outside the kept shape.
3. Saves the GlobalIDs of every related row to related_rows_before.csv.
4. With run.write_to_db true: deletes the duplicate, writes the ZONING_ID back on the saved
   rows by GlobalID, and verifies counts inside the edit session. Any failed check raises,
   which aborts the edit session and saves nothing.

Dry run by default. Run from the Zoning folder:
    python scripts/e03_delete_duplicate_district.py [--config config.yaml]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

RELATED = ("permissible_uses", "special_designation")


def null_key_where(field: str) -> str:
    return f"{field} IS NULL OR {field} = '' OR {field} = ' '"


def check_districts(config: dict, log) -> None:
    """Confirm the two District features and the geometry overlap."""
    e03 = config["e03"]
    district = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    found = sde.rows(district, ["OID@", key, "SHAPE@"], f"{key} = {sde.sql_text(e03['zoning_id'])}")
    by_oid = {r["OID@"]: r for r in found}
    log.info("District features with ZONING_ID %s: %s", e03["zoning_id"], sorted(by_oid))

    expected = {e03["delete_objectid"], e03["keep_objectid"]}
    if set(by_oid) != expected:
        raise sde.GuardError(
            f"Expected District OBJECTIDs {sorted(expected)} for ZONING_ID {e03['zoning_id']}, "
            f"found {sorted(by_oid)}."
        )

    dup = by_oid[e03["delete_objectid"]]["SHAPE@"]
    keep = by_oid[e03["keep_objectid"]]["SHAPE@"]
    extra = sde.acres(dup.difference(keep))
    log.info(
        "Duplicate %.3f acres, kept %.3f acres, duplicate area outside kept shape %.4f acres",
        sde.acres(dup), sde.acres(keep), extra,
    )
    if extra > e03["max_extra_acres"]:
        raise sde.GuardError(
            f"Duplicate covers {extra:.4f} acres outside the kept shape "
            f"(limit {e03['max_extra_acres']}). Review before deleting."
        )


def related_rows(config: dict) -> list[dict]:
    zid = config["e03"]["zoning_id"]
    records = []
    for table in RELATED:
        field = config["keys"][table]
        for row in sde.rows(sde.dataset_path(config, table), ["OID@", "GlobalID"], f"{field} = {sde.sql_text(zid)}"):
            records.append({"TABLE": table, "OBJECTID": row["OID@"], "GlobalID": sde.norm_guid(row["GlobalID"])})
    return records


def null_counts(config: dict) -> dict[str, int]:
    return {t: sde.count(sde.dataset_path(config, t), null_key_where(config["keys"][t])) for t in RELATED}


def apply(config: dict, saved: list[dict], nulls_before: dict[str, int], log) -> None:
    """Delete the duplicate, restore keys, and verify, all in one edit session."""
    e03 = config["e03"]
    zid = e03["zoning_id"]
    district = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    versioned = sde.is_versioned(district)
    log.info("Starting edit session (multiuser_mode=%s)", versioned)

    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        deleted = 0
        where = f"OBJECTID = {int(e03['delete_objectid'])} AND {key} = {sde.sql_text(zid)}"
        with arcpy.da.UpdateCursor(district, ["OID@"], where) as cursor:
            for _ in cursor:
                cursor.deleteRow()
                deleted += 1
        if deleted != 1:
            raise sde.GuardError(f"Expected to delete 1 District feature, deleted {deleted}.")
        log.info("Deleted District OBJECTID %s", e03["delete_objectid"])

        for table in RELATED:
            field = config["keys"][table]
            guids = [r["GlobalID"] for r in saved if r["TABLE"] == table]
            path = sde.dataset_path(config, table)
            restored = 0
            with arcpy.da.UpdateCursor(path, ["GlobalID", field], sde.sql_in("GlobalID", guids)) as cursor:
                for guid, value in cursor:
                    if value != zid:
                        cursor.updateRow([guid, zid])
                        restored += 1
            log.info("%s: %s rows saved, %s keys written back", table, len(guids), restored)

            after = {sde.norm_guid(r["GlobalID"]) for r in sde.rows(path, ["GlobalID"], f"{field} = {sde.sql_text(zid)}")}
            if after != set(guids):
                raise sde.GuardError(
                    f"{table}: rows keyed {zid} after the edit do not match the saved rows "
                    f"({len(after)} after, {len(guids)} saved)."
                )
            nulls_after = sde.count(path, null_key_where(field))
            if nulls_after != nulls_before[table]:
                raise sde.GuardError(
                    f"{table}: null keys went from {nulls_before[table]} to {nulls_after}."
                )

        remaining = [r["OID@"] for r in sde.rows(district, ["OID@"], f"{key} = {sde.sql_text(zid)}")]
        if remaining != [e03["keep_objectid"]]:
            raise sde.GuardError(f"District features keyed {zid} after the edit: {remaining}.")
        log.info("Verified inside the edit session; saving.")


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("e03_delete_duplicate_district", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")

    try:
        sde.check_version(config, log, for_write=write)
        check_districts(config, log)

        saved = related_rows(config)
        out = io.run_folder(config, "e03", stamp)
        sde.write_csv(out / "related_rows_before.csv", saved, ["TABLE", "OBJECTID", "GlobalID"])
        for table in RELATED:
            log.info("%s rows keyed %s: %s", table, config["e03"]["zoning_id"],
                     sum(1 for r in saved if r["TABLE"] == table))
        nulls_before = null_counts(config)
        log.info("Null keys before: %s", nulls_before)
        log.info("Saved related rows: %s", out / "related_rows_before.csv")

        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to delete and restore.")
            return 0

        apply(config, saved, nulls_before, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1

    log.info("E03 complete. Rerun the snapshot to confirm, then reconcile when ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
