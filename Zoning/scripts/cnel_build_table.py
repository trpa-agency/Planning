"""CNEL: build the District CNEL table from data/reference/cnel_by_district.csv.

Replaces the legacy AGIS_TRPA/MapServer/82 Noise Levels layer (Plan Area Statement and
Community Plan shapes from before the area plans) with a table keyed on ZONING_ID, like
PermissibleUses and Special_Designation. District keeps the geometry; the published noise
layer becomes District joined to this table. This script:

1. Checks the connection is the QA edit version (writes only).
2. Reads the reference CSV and stops on a duplicate ZONING_ID, a CNEL outside
   cnel.valid_values, or a text value longer than its field.
3. Compares the CSV with District in the version. Stops if any District has no CSV row.
   CSV rows with no District are listed and skipped.
4. Writes review files to outputs/cnel_<time>/: compare.csv, changes.csv (rows whose CNEL
   differs from the legacy layer), decisions.csv (rows waiting on a planner), and
   cnel_review.gdb with District shapes joined to the CSV for a map check.
5. With run.write_to_db true: creates the table if it does not exist and cnel.create_table
   is true (GlobalIDs on, registered as versioned when District is), then in one edit
   session updates changed rows, inserts new rows, and deletes rows whose ZONING_ID is no
   longer in the CSV. Verifies the table matches the CSV before saving; any failure aborts
   the session and saves nothing.

Dry run by default. Run from any folder:
    python Zoning/scripts/cnel_build_table.py [--config config.yaml]
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402
from src.cnel import FIELDS, NAMES, load_csv  # noqa: E402


def compare(config: dict, rows: dict[str, dict], log) -> tuple[list[str], list[str]]:
    """Return (districts to write, CSV rows with no district). Stops on uncovered districts."""
    district = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    ids = {r[0] for r in arcpy.da.SearchCursor(district, [key]) if r[0]}
    missing = sorted(ids - set(rows))
    extra = sorted(set(rows) - ids)
    log.info("District IDs: %s; CSV rows: %s; matched: %s", len(ids), len(rows), len(ids & set(rows)))
    if extra:
        log.warning("CSV rows with no District (skipped): %s", extra)
    if missing:
        raise sde.GuardError(f"{len(missing)} District IDs have no CNEL row: {missing}")
    return sorted(ids), extra


def write_review(config: dict, rows: dict[str, dict], ids: list[str], extra: list[str], out: Path, log) -> None:
    records = [rows[z]["_csv"] for z in ids]
    fields = list(records[0].keys())
    sde.write_csv(out / "compare.csv",
                  [{**rows[z]["_csv"], "IN_DISTRICT": "yes"} for z in ids]
                  + [{**rows[z]["_csv"], "IN_DISTRICT": "no"} for z in extra],
                  fields + ["IN_DISTRICT"])
    sde.write_csv(out / "changes.csv", [r for r in records if " to " in (r.get("CHANGE") or "")], fields)
    sde.write_csv(out / "decisions.csv", [r for r in records if r.get("DECISION")], fields)
    log.info("CNEL values: %s", dict(sorted(Counter(rows[z]["CNEL"] for z in ids).items())))
    log.info("Basis: %s", dict(Counter(rows[z]["BASIS"] for z in ids)))
    log.info("Changed from the legacy layer: %s; waiting on a decision: %s",
             sum(1 for r in records if " to " in (r.get("CHANGE") or "")),
             sum(1 for r in records if r.get("DECISION")))

    # District shapes joined to the CSV, for a map check against the legacy layer.
    gdb = out / "cnel_review.gdb"
    arcpy.management.CreateFileGDB(str(out), gdb.name)
    district = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    target = os.path.join(str(gdb), "District_CNEL")
    sr = arcpy.Describe(district).spatialReference
    arcpy.management.CreateFeatureclass(str(gdb), "District_CNEL", "POLYGON", spatial_reference=sr)
    extras = [("ZONING_DESCRIPTION", "TEXT", 255), ("PLAN_ID", "TEXT", 50), ("PLAN_TYPE", "TEXT", 50),
              ("CHANGE", "TEXT", 20)]
    for name, ftype, length in FIELDS + extras:
        arcpy.management.AddField(target, name, ftype, field_length=length)
    out_fields = ["SHAPE@"] + NAMES + [e[0] for e in extras]
    with arcpy.da.SearchCursor(district, ["SHAPE@", key, "ZONING_DESCRIPTION", "PLAN_ID", "PLAN_TYPE"]) as src, \
            arcpy.da.InsertCursor(target, out_fields) as dst:
        for shape, zid, desc, plan_id, plan_type in src:
            row = rows.get(zid)
            if row is None:
                continue
            dst.insertRow([shape] + [row[n] for n in NAMES]
                          + [desc, plan_id, plan_type, row["_csv"].get("CHANGE", "")])
    log.info("Review geodatabase: %s", target)


def ensure_table(config: dict, log) -> str:
    path = sde.dataset_path(config, "cnel")
    if arcpy.Exists(path):
        have = {f.name.upper() for f in arcpy.ListFields(path)}
        lacking = [n for n in NAMES if n.upper() not in have]
        if lacking:
            raise sde.GuardError(f"{path} exists but lacks fields {lacking}.")
        return path
    if not config["cnel"].get("create_table"):
        raise sde.GuardError(f"{path} does not exist. Set cnel.create_table to true to create it.")
    ws = sde.workspace(config)
    name = path.replace("\\", "/").rsplit("/", 1)[-1].split(".")[-1]
    log.info("Creating table %s in %s", name, ws)
    arcpy.management.CreateTable(ws, name)
    path = os.path.join(ws, name) if not arcpy.Exists(path) else path
    for fname, ftype, length in FIELDS:
        arcpy.management.AddField(path, fname, ftype, field_length=length)
    arcpy.management.AddGlobalIDs(path)
    district = sde.dataset_path(config, "district")
    if sde.is_versioned(district):
        arcpy.management.RegisterAsVersioned(path, "NO_EDITS_TO_BASE")
        log.info("Registered %s as versioned to match District.", path)
    return path


def apply(config: dict, rows: dict[str, dict], ids: list[str], log) -> None:
    table = ensure_table(config, log)
    wanted = {z: rows[z] for z in ids}
    versioned = sde.is_versioned(table)
    log.info("Starting edit session on %s (multiuser_mode=%s)", table, versioned)
    counts = Counter()
    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        seen = set()
        with arcpy.da.UpdateCursor(table, NAMES) as cursor:
            for current in cursor:
                zid = current[0]
                if zid not in wanted or zid in seen:
                    cursor.deleteRow()
                    counts["deleted"] += 1
                    continue
                seen.add(zid)
                new = [wanted[zid][n] for n in NAMES]
                if [None if v == "" else v for v in current] != [None if v == "" else v for v in new]:
                    cursor.updateRow(new)
                    counts["updated"] += 1
                else:
                    counts["unchanged"] += 1
        with arcpy.da.InsertCursor(table, NAMES) as cursor:
            for zid in ids:
                if zid not in seen:
                    cursor.insertRow([wanted[zid][n] for n in NAMES])
                    counts["inserted"] += 1

        after = {r[0]: r for r in arcpy.da.SearchCursor(table, NAMES)}
        total = sde.count(table)
        if total != len(ids) or set(after) != set(ids):
            raise sde.GuardError(f"Table has {total} rows after the edit, expected {len(ids)}.")
        bad = [z for z in ids if after[z][1] != wanted[z]["CNEL"]]
        if bad:
            raise sde.GuardError(f"CNEL differs from the CSV after the edit: {bad[:10]}")
        log.info("Rows %s; table now holds %s. Saving.", dict(counts), total)


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("cnel_build_table", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")

    try:
        sde.check_version(config, log, for_write=write)
        rows = load_csv(config)
        ids, extra = compare(config, rows, log)
        out = io.run_folder(config, "cnel", stamp)
        write_review(config, rows, ids, extra, out, log)
        log.info("Review files: %s", out)
        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to write the table.")
            return 0
        apply(config, rows, ids, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1

    log.info("CNEL table complete. Rerun the snapshot to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
