"""Post the rebuilt table fixes to PermissibleUses and Special_Designation.

Reads a rebuilt package from rebuild_fixes.py (outputs/rebuild_<time>/rebuilt/) and applies
its pending updates, deletes, and inserts to the edit version in one edit session:

1. Updates (pu_updates, area_pu_updates): by GlobalID; the current value must still equal
   OLD_VALUE.
2. Deletes (pu_deletes, area_pu_deletes, sd_deletes): by GlobalID; the key must still match.
3. Inserts (pu_inserts, area_pu_inserts): the ZONING_ID must exist in District.

Every check runs before the edit session (dry run or not): targets exist, old values still
match, no row is both updated and deleted, values fit the field types and lengths, and the
projected row counts equal the computed counts and post_tables.expected_counts. The dry run
also projects null keys and duplicate district and use pairs after posting.

With run.write_to_db true, the edits run in one session and are verified before saving:
final row counts and no null keys in either table. Any failure aborts the session and saves
nothing. District shapes and parcel fixes are not handled here.

Run from any folder:
    python Zoning/scripts/post_table_fixes.py --rebuilt <outputs/rebuild_<time>/rebuilt>
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402
from src.values import norm, same, table_of, use_key  # noqa: E402

UPDATE_FILES = ["pu_updates.csv", "area_pu_updates.csv"]
DELETE_FILES = ["pu_deletes.csv", "area_pu_deletes.csv", "sd_deletes.csv"]
INSERT_FILES = ["pu_inserts.csv", "area_pu_inserts.csv"]
INSERT_FIELDS = ["Zoning_ID", "Category", "Subcategory", "Use_Type", "Use_Status", "Density", "Unit", "Notes"]
TABLES = ("permissible_uses", "special_designation")
CHUNK = 500


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rebuilt", required=True, help="The rebuilt folder written by rebuild_fixes.py.")
    parser.add_argument("--config", default=str(io.ROOT / "config.yaml"))
    return parser.parse_args()


def read(folder: Path, name: str) -> list[dict]:
    path = folder / name
    if not path.exists():
        raise sde.GuardError(f"Rebuilt file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        return [{**r, "_FILE": name} for r in csv.DictReader(handle)]


class Schema:
    """Field names and types for a table, matched case-insensitively."""

    def __init__(self, path: str):
        self.fields = {f.name.casefold(): f for f in arcpy.ListFields(path)}

    def name(self, field: str) -> str:
        f = self.fields.get(field.casefold())
        if f is None:
            raise sde.GuardError(f"Field {field} not found.")
        return f.name

    def convert(self, field: str, value):
        """Convert CSV text to the field's type. Blank becomes None."""
        f = self.fields[field.casefold()]
        if value is None or str(value).strip() == "":
            return None
        text = str(value)
        if f.type in ("Integer", "SmallInteger", "BigInteger"):
            number = float(text)
            if not number.is_integer():
                raise sde.GuardError(f"{f.name} is an integer field; {text!r} has a fraction.")
            return int(number)
        if f.type in ("Double", "Single"):
            return float(text)
        if f.type == "String" and len(text) > f.length:
            raise sde.GuardError(f"{f.name} holds {f.length} characters; value has {len(text)}: {text[:60]!r}")
        return text


def key_field(config: dict, table: str) -> str:
    return config["keys"][table]


def load_rows(path: str, fields: list[str]) -> dict[str, dict]:
    rows = {}
    with arcpy.da.SearchCursor(path, ["GlobalID", *fields]) as cursor:
        for guid, *values in cursor:
            rows[sde.norm_guid(guid)] = dict(zip(fields, values))
    return rows


def plan(config: dict, folder: Path, log) -> dict:
    """Validate the rebuilt package against the version and return the edit plan."""
    paths = {t: sde.dataset_path(config, t) for t in TABLES}
    schemas = {t: Schema(paths[t]) for t in TABLES}
    pu_fields = [schemas["permissible_uses"].name(f) for f in INSERT_FIELDS]
    sd_key = schemas["special_designation"].name(key_field(config, "special_designation"))
    current = {
        "permissible_uses": load_rows(paths["permissible_uses"], pu_fields),
        "special_designation": load_rows(paths["special_designation"], [sd_key]),
    }
    district_ids = {r[0] for r in arcpy.da.SearchCursor(sde.dataset_path(config, "district"), [config["keys"]["district"]])}

    updates = [r for name in UPDATE_FILES for r in read(folder, name)]
    deletes = [r for name in DELETE_FILES for r in read(folder, name)]
    inserts = [r for name in INSERT_FILES for r in read(folder, name)]
    problems = []

    for r in updates:
        table = table_of(r, "permissible_uses")
        schema = schemas[table]
        guid = sde.norm_guid(r["GlobalID"])
        target = current[table].get(guid)
        try:
            field = schema.name(r["FIELD"])
            r["_TABLE"], r["_FIELD"], r["_GUID"] = table, field, guid
            r["_VALUE"] = schema.convert(field, r["NEW_VALUE"])
        except (sde.GuardError, ValueError) as err:
            problems.append(f"{r['FIX_ID']} update {guid}: {err}")
            continue
        if target is None:
            problems.append(f"{r['FIX_ID']} update {guid}: row not found")
        elif not same(target.get(field), r["OLD_VALUE"], field):
            problems.append(f"{r['FIX_ID']} update {guid}: {field} is {target.get(field)!r}, expected {r['OLD_VALUE']!r}")

    for r in deletes:
        table = table_of(r, "special_designation" if r["_FILE"].startswith("sd_") else "permissible_uses")
        guid = sde.norm_guid(r["GlobalID"])
        r["_TABLE"], r["_GUID"] = table, guid
        target = current[table].get(guid)
        key = schemas[table].name(key_field(config, table))
        if target is None:
            problems.append(f"{r['FIX_ID']} delete {guid}: row not found")
        elif not same(target.get(key), r.get("Zoning_ID")):
            problems.append(f"{r['FIX_ID']} delete {guid}: key is {target.get(key)!r}, expected {r.get('Zoning_ID')!r}")

    collide = {r["_GUID"] for r in updates if "_GUID" in r} & {r["_GUID"] for r in deletes}
    if collide:
        problems.append(f"{len(collide)} rows are both updated and deleted: {sorted(collide)[:5]}")

    schema = schemas["permissible_uses"]
    for r in inserts:
        if r["Zoning_ID"] not in district_ids:
            problems.append(f"{r['FIX_ID']} insert {r['Zoning_ID']} {r['Use_Type']}: no District feature")
        try:
            r["_VALUES"] = [schema.convert(f, r.get(f)) for f in pu_fields]
        except (sde.GuardError, ValueError) as err:
            problems.append(f"{r['FIX_ID']} insert {r['Zoning_ID']} {r['Use_Type']}: {err}")

    if problems:
        for p in problems[:50]:
            log.error(p)
        raise sde.GuardError(f"{len(problems)} problems in the rebuilt package; nothing posted.")

    # Projected state after posting.
    counts = {}
    for table in TABLES:
        n_del = sum(1 for r in deletes if r["_TABLE"] == table)
        n_ins = len(inserts) if table == "permissible_uses" else 0
        counts[table] = (len(current[table]), n_del, n_ins, len(current[table]) - n_del + n_ins)
        log.info("%s: %s now, %s deletes, %s inserts, %s after", table, *counts[table])
        expected = (config.get("post_tables", {}).get("expected_counts") or {}).get(table)
        if expected is not None and expected != counts[table][3]:
            raise sde.GuardError(f"{table}: projected {counts[table][3]} rows, config expects {expected}.")

    deleted = {r["_GUID"] for r in deletes}
    final_pu = {g: dict(v) for g, v in current["permissible_uses"].items() if g not in deleted}
    for r in updates:
        if r["_TABLE"] == "permissible_uses":
            final_pu[r["_GUID"]][r["_FIELD"]] = r["_VALUE"]
    pu_key = schema.name(key_field(config, "permissible_uses"))
    pu_use = schema.name("Use_Type")
    projected = list(final_pu.values()) + [dict(zip(pu_fields, r["_VALUES"])) for r in inserts]
    nulls_pu = sum(1 for v in projected if norm(v.get(pu_key)) is None)
    nulls_sd = sum(1 for g, v in current["special_designation"].items() if g not in deleted and norm(v.get(sd_key)) is None)
    pairs = Counter((v.get(pu_key), use_key(v.get(pu_use))) for v in projected)
    dupes = [{"ZONE": z, "Use_Type": u, "rows": n} for (z, u), n in sorted(pairs.items(), key=lambda kv: str(kv[0])) if n > 1]
    log.info("Projected after posting: %s use rows with a null key, %s special designation rows with a null key, "
             "%s district and use pairs on more than one row", nulls_pu, nulls_sd, len(dupes))
    if nulls_pu or nulls_sd:
        raise sde.GuardError("Posting would leave rows with a null key; review the rebuilt package.")

    return {"paths": paths, "schemas": schemas, "pu_fields": pu_fields, "updates": updates,
            "deletes": deletes, "inserts": inserts, "counts": counts, "dupes": dupes,
            "keys": {"permissible_uses": pu_key, "special_designation": sd_key}}


def apply(config: dict, p: dict, log) -> None:
    paths = p["paths"]
    versioned = sde.is_versioned(paths["permissible_uses"])
    log.info("Starting edit session (multiuser_mode=%s)", versioned)
    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        # Updates, grouped by table and field.
        groups = {}
        for r in p["updates"]:
            groups.setdefault((r["_TABLE"], r["_FIELD"]), {})[r["_GUID"]] = r["_VALUE"]
        done = 0
        for (table, field), values in groups.items():
            guids = list(values)
            for start in range(0, len(guids), CHUNK):
                with arcpy.da.UpdateCursor(paths[table], ["GlobalID", field], sde.sql_in("GlobalID", guids[start:start + CHUNK])) as cursor:
                    for guid, _ in cursor:
                        cursor.updateRow([guid, values[sde.norm_guid(guid)]])
                        done += 1
        if done != len(p["updates"]):
            raise sde.GuardError(f"Updated {done} rows, expected {len(p['updates'])}.")
        log.info("Updated %s rows", done)

        for table in TABLES:
            guids = [r["_GUID"] for r in p["deletes"] if r["_TABLE"] == table]
            removed = 0
            for start in range(0, len(guids), CHUNK):
                with arcpy.da.UpdateCursor(paths[table], ["GlobalID"], sde.sql_in("GlobalID", guids[start:start + CHUNK])) as cursor:
                    for _ in cursor:
                        cursor.deleteRow()
                        removed += 1
            if removed != len(guids):
                raise sde.GuardError(f"{table}: deleted {removed} rows, expected {len(guids)}.")
            log.info("%s: deleted %s rows", table, removed)

        with arcpy.da.InsertCursor(paths["permissible_uses"], p["pu_fields"]) as cursor:
            for r in p["inserts"]:
                cursor.insertRow(r["_VALUES"])
        log.info("Inserted %s rows", len(p["inserts"]))

        for table in TABLES:
            expected = p["counts"][table][3]
            actual = sde.count(paths[table])
            if actual != expected:
                raise sde.GuardError(f"{table}: {actual} rows after posting, expected {expected}.")
            key = p["keys"][table]
            nulls = sde.count(paths[table], f"{key} IS NULL OR {key} = '' OR {key} = ' '")
            if nulls:
                raise sde.GuardError(f"{table}: {nulls} rows with a null key after posting.")
            log.info("%s: %s rows, no null keys", table, actual)
        log.info("Verified inside the edit session; saving.")


def main() -> int:
    args = parse_args()
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("post_table_fixes", config, stamp)
    write = bool(config["run"]["write_to_db"])
    folder = Path(args.rebuilt)
    log.info("Config: %s", config["_path"])
    log.info("Rebuilt package: %s", folder)
    log.info("Mode: %s", "WRITE" if write else "dry run")
    try:
        sde.check_version(config, log, for_write=write)
        p = plan(config, folder, log)
        out = io.run_folder(config, "post_tables", stamp)
        sde.write_csv(out / "projected_duplicate_pairs.csv", p["dupes"], ["ZONE", "Use_Type", "rows"])
        actions = (
            [{"ACTION": "update", "FIX_ID": r["FIX_ID"], "TABLE": r["_TABLE"], "GlobalID": r["_GUID"],
              "FIELD": r["_FIELD"], "OLD_VALUE": r["OLD_VALUE"], "NEW_VALUE": r["NEW_VALUE"]} for r in p["updates"]]
            + [{"ACTION": "delete", "FIX_ID": r["FIX_ID"], "TABLE": r["_TABLE"], "GlobalID": r["_GUID"],
                "ZONE": r.get("Zoning_ID")} for r in p["deletes"]]
            + [{"ACTION": "insert", "FIX_ID": r["FIX_ID"], "TABLE": "permissible_uses", "ZONE": r["Zoning_ID"],
                "NEW_VALUE": r["Use_Type"]} for r in p["inserts"]]
        )
        sde.write_csv(out / "actions.csv", actions,
                      ["ACTION", "FIX_ID", "TABLE", "GlobalID", "ZONE", "FIELD", "OLD_VALUE", "NEW_VALUE"])
        log.info("Planned: %s updates, %s deletes, %s inserts. Details: %s",
                 len(p["updates"]), len(p["deletes"]), len(p["inserts"]), out)
        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to post.")
            return 0
        apply(config, p, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1
    log.info("Table fixes posted. Rerun the snapshot and the rebuild to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
