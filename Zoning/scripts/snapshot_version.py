"""Snapshot the QA edit version before any edits.

Exports District, PermissibleUses, Special_Designation, and the parcel layers to a
timestamped file geodatabase (GlobalIDs preserved), then writes review CSVs:

- counts.csv               row counts per dataset
- watch_districts.csv      District rows matching snapshot.watch_zoning_ids, with acres
- related_counts.csv       use and special designation rows per watched ZONING_ID
- duplicate_zoning_ids.csv District ZONING_IDs on more than one feature
- null_keys.csv            related rows with a null or blank key
- fix_id_check.csv         every fix package row with an OBJECTID or GlobalID, checked
                           against the snapshot

Read only. Run from the Zoning folder:
    python scripts/snapshot_version.py [--config config.yaml]
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

FIX_TABLES = {
    "pu_updates.csv": "permissible_uses",
    "pu_deletes.csv": "permissible_uses",
    "area_pu_updates.csv": "permissible_uses",
    "area_pu_deletes.csv": "permissible_uses",
    "sd_deletes.csv": "special_designation",
    "pending_rulings.csv": None,        # TABLE column decides
    "area_pending_rulings.csv": None,
    "district_repair_geometry.csv": "district",
    "district_replacement_shapes.csv": "district",
}
TABLE_NAMES = {
    "permissibleuses": "permissible_uses",
    "permissible_uses": "permissible_uses",
    "special_designation": "special_designation",
    "specialdesignation": "special_designation",
    "district": "district",
}


def export(config: dict, gdb: str, log) -> dict[str, str]:
    """Export each configured dataset into the snapshot geodatabase."""
    arcpy.env.preserveGlobalIds = True
    exported = {}
    for key in config["datasets"]:
        source = sde.dataset_path(config, key)
        if source is None:
            log.warning("Dataset %s is not configured; skipped.", key)
            continue
        if not arcpy.Exists(source):
            if key in ("district", "permissible_uses", "special_designation"):
                raise sde.GuardError(f"Required dataset not found: {source}")
            log.warning("Dataset %s not found at %s; skipped.", key, source)
            continue
        target = f"{gdb}/{key}"
        if arcpy.Describe(source).dataType in ("Table", "TableView"):
            arcpy.conversion.ExportTable(source, target)
        else:
            arcpy.conversion.ExportFeatures(source, target)
        exported[key] = target
        log.info("Exported %s: %s rows", key, sde.count(target))
    return exported


def watch_where(config: dict) -> str:
    field = config["keys"]["district"]
    patterns = config["snapshot"]["watch_zoning_ids"]
    return " OR ".join(f"{field} LIKE {sde.sql_text(p)}" for p in patterns)


def watched_districts(config: dict, snap: dict[str, str]) -> list[dict]:
    key = config["keys"]["district"]
    fields = ["OID@", key, "PLAN_ID", "ZONING_DESCRIPTION", "GlobalID", "SHAPE@"]
    records = []
    for row in sde.rows(snap["district"], fields, watch_where(config)):
        records.append({
            "OBJECTID": row["OID@"],
            "ZONING_ID": row[key],
            "PLAN_ID": row["PLAN_ID"],
            "ZONING_DESCRIPTION": row["ZONING_DESCRIPTION"],
            "GlobalID": row["GlobalID"],
            "ACRES": round(sde.acres(row["SHAPE@"]), 3),
        })
    return sorted(records, key=lambda r: (str(r["ZONING_ID"]), r["OBJECTID"]))


def related_counts(config: dict, snap: dict[str, str], zoning_ids: list[str]) -> list[dict]:
    records = []
    for zid in sorted(set(zoning_ids)):
        record = {"ZONING_ID": zid}
        for table in ("permissible_uses", "special_designation"):
            field = config["keys"][table]
            record[table] = sde.count(snap[table], f"{field} = {sde.sql_text(zid)}")
        records.append(record)
    return records


def duplicate_ids(config: dict, snap: dict[str, str]) -> list[dict]:
    key = config["keys"]["district"]
    tally = Counter(r[key] for r in sde.rows(snap["district"], [key]))
    dupes = []
    for zid, n in sorted(tally.items(), key=lambda kv: str(kv[0])):
        if n > 1:
            oids = [r["OID@"] for r in sde.rows(snap["district"], ["OID@"], f"{key} = {sde.sql_text(zid)}")]
            dupes.append({"ZONING_ID": zid, "features": n, "OBJECTIDS": " ".join(map(str, oids))})
    return dupes


def null_keys(config: dict, snap: dict[str, str]) -> list[dict]:
    records = []
    for table in ("permissible_uses", "special_designation"):
        field = config["keys"][table]
        where = f"{field} IS NULL OR {field} = '' OR {field} = ' '"
        for row in sde.rows(snap[table], ["OID@", "GlobalID", field], where):
            records.append({"TABLE": table, "OBJECTID": row["OID@"], "GlobalID": row["GlobalID"]})
    return records


def fix_id_check(config: dict, snap: dict[str, str], log) -> list[dict]:
    """Check each fix package row's OBJECTID and GlobalID against the snapshot."""
    lookup = {}
    for table in ("district", "permissible_uses", "special_designation"):
        by_guid = {}
        for row in sde.rows(snap[table], ["OID@", "GlobalID"]):
            by_guid[sde.norm_guid(row["GlobalID"])] = row["OID@"]
        lookup[table] = by_guid

    fix_dir = io.resolve(config["paths"]["fix_package_csv"])
    records = []
    for name, default_table in FIX_TABLES.items():
        path = fix_dir / name
        if not path.exists():
            log.warning("Fix file not found: %s", path)
            continue
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                table = default_table or TABLE_NAMES.get(str(row.get("TABLE", "")).strip().lower())
                guid = sde.norm_guid(row.get("GlobalID"))
                oid = str(row.get("OBJECTID", "")).strip()
                if table is None or not guid:
                    status, found_oid = "not checkable", ""
                elif guid not in lookup[table]:
                    status, found_oid = "GlobalID not in version", ""
                else:
                    found_oid = lookup[table][guid]
                    status = "match" if str(found_oid) == oid else "OBJECTID differs"
                records.append({
                    "FILE": name,
                    "FIX_ID": row.get("FIX_ID", ""),
                    "TABLE": table or row.get("TABLE", ""),
                    "OBJECTID": oid,
                    "GlobalID": guid,
                    "VERSION_OBJECTID": found_oid,
                    "STATUS": status,
                })
    return records


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("snapshot_version", config, stamp)
    log.info("Config: %s", config["_path"])

    try:
        version = sde.check_version(config, log, for_write=False)
    except sde.GuardError as err:
        log.error(str(err))
        return 1

    snap_dir = io.resolve(config["paths"]["snapshots"])
    snap_dir.mkdir(parents=True, exist_ok=True)
    label = (version or "local").replace(".", "_").replace(" ", "_")
    gdb_name = f"{label}_{stamp}.gdb"
    arcpy.management.CreateFileGDB(str(snap_dir), gdb_name)
    gdb = str(snap_dir / gdb_name)
    log.info("Snapshot geodatabase: %s", gdb)

    try:
        snap = export(config, gdb, log)
    except sde.GuardError as err:
        log.error(str(err))
        return 1

    out = io.run_folder(config, "snapshot", stamp)
    sde.write_csv(out / "counts.csv", [{"dataset": k, "rows": sde.count(v)} for k, v in snap.items()])

    watched = watched_districts(config, snap)
    sde.write_csv(out / "watch_districts.csv", watched)
    sde.write_csv(out / "related_counts.csv", related_counts(config, snap, [w["ZONING_ID"] for w in watched]))

    dupes = duplicate_ids(config, snap)
    sde.write_csv(out / "duplicate_zoning_ids.csv", dupes, ["ZONING_ID", "features", "OBJECTIDS"])
    for d in dupes:
        log.info("Duplicate District ZONING_ID %s on OBJECTIDs %s", d["ZONING_ID"], d["OBJECTIDS"])

    nulls = null_keys(config, snap)
    sde.write_csv(out / "null_keys.csv", nulls, ["TABLE", "OBJECTID", "GlobalID"])
    log.info("Related rows with a null or blank key: %s", len(nulls))

    checks = fix_id_check(config, snap, log)
    sde.write_csv(out / "fix_id_check.csv", checks)
    for status, n in sorted(Counter(c["STATUS"] for c in checks).items()):
        log.info("Fix package rows, %s: %s", status, n)

    log.info("Review CSVs: %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
