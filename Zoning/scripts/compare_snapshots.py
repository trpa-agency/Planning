"""Compare two snapshot geodatabases row by row, matched on GlobalID.

Use it to see exactly what a version changed relative to DEFAULT, or what a script run
changed. For each dataset in both snapshots it writes, under outputs/compare_<time>/:

- <dataset>_added.csv    rows only in --after
- <dataset>_deleted.csv  rows only in --before
- <dataset>_changed.csv  one row per changed field (geometry reported as SHAPE)
- key_changes.csv        every change to the zoning key, with before and after values

The log tallies key changes by before and after value. A key that went from a zoning ID
to blank usually means its District feature was deleted (simple relationship behavior).

Read only. Run from any folder:
    python Zoning/scripts/compare_snapshots.py --before <DEFAULT.gdb> --after <version.gdb>
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

SKIP_NAMES = {"src_objectid", "shape_length", "shape_area", "shape.starea()", "shape.stlength()"}
SKIP_TYPES = {"OID", "Geometry", "GlobalID", "Blob", "Raster"}
EDITOR_FIELDS = {"created_user", "created_date", "last_edited_user", "last_edited_date"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--before", required=True, help="Snapshot geodatabase to compare from, usually DEFAULT.")
    parser.add_argument("--after", required=True, help="Snapshot geodatabase to compare to, usually the edit version.")
    parser.add_argument("--config", default=str(io.ROOT / "config.yaml"))
    return parser.parse_args()


def compare_fields(path: str) -> list[str]:
    return [
        f.name for f in arcpy.ListFields(path)
        if f.type not in SKIP_TYPES and f.name.lower() not in SKIP_NAMES
    ]


def has_globalid(path: str) -> bool:
    return any(f.type == "GlobalID" for f in arcpy.ListFields(path))


def load(path: str, fields: list[str], geometry: bool) -> dict[str, dict]:
    """Read rows keyed by GlobalID. Geometry is reduced to a hash of its WKB."""
    cursor_fields = ["GlobalID", *fields] + (["SHAPE@WKB"] if geometry else [])
    rows = {}
    with arcpy.da.SearchCursor(path, cursor_fields) as cursor:
        for values in cursor:
            record = dict(zip(cursor_fields, values))
            if geometry:
                wkb = record.pop("SHAPE@WKB")
                record["SHAPE"] = hashlib.md5(bytes(wkb)).hexdigest() if wkb else None
            rows[sde.norm_guid(record.pop("GlobalID"))] = record
    return rows


def norm(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def compare_dataset(name: str, before_gdb: str, after_gdb: str, key: str | None, out: Path, log) -> list[dict]:
    before_path, after_path = f"{before_gdb}/{name}", f"{after_gdb}/{name}"
    if not (arcpy.Exists(before_path) and arcpy.Exists(after_path)):
        log.info("%s: not in both snapshots; skipped.", name)
        return []
    if not (has_globalid(before_path) and has_globalid(after_path)):
        log.warning("%s: no GlobalID field; skipped.", name)
        return []

    fields = [f for f in compare_fields(before_path) if f in set(compare_fields(after_path))]
    geometry = arcpy.Describe(before_path).dataType == "FeatureClass"
    before = load(before_path, fields, geometry)
    after = load(after_path, fields, geometry)

    added = [{"GlobalID": g, **after[g]} for g in after.keys() - before.keys()]
    deleted = [{"GlobalID": g, **before[g]} for g in before.keys() - after.keys()]
    columns = ["GlobalID", *fields] + (["SHAPE"] if geometry else [])
    sde.write_csv(out / f"{name}_added.csv", sorted(added, key=lambda r: str(r.get(key))), columns)
    sde.write_csv(out / f"{name}_deleted.csv", sorted(deleted, key=lambda r: str(r.get(key))), columns)

    changes, key_changes = [], []
    context = [f for f in fields if f.lower() in EDITOR_FIELDS]
    for guid in sorted(before.keys() & after.keys()):
        b, a = before[guid], after[guid]
        for field in [f for f in columns if f != "GlobalID" and f.lower() not in EDITOR_FIELDS]:
            if norm(b.get(field)) != norm(a.get(field)):
                change = {
                    "GlobalID": guid, "FIELD": field,
                    "BEFORE": b.get(field), "AFTER": a.get(field),
                    "KEY_BEFORE": b.get(key) if key else None,
                    **{f"AFTER_{c}": a.get(c) for c in context},
                }
                changes.append(change)
                if key and field == key:
                    key_changes.append({"DATASET": name, **change})
    sde.write_csv(
        out / f"{name}_changed.csv", changes,
        ["GlobalID", "FIELD", "BEFORE", "AFTER", "KEY_BEFORE", *[f"AFTER_{c}" for c in context]],
    )
    log.info(
        "%s: %s before, %s after; %s added, %s deleted, %s field changes on %s rows",
        name, len(before), len(after), len(added), len(deleted), len(changes),
        len({c["GlobalID"] for c in changes}),
    )
    if key:
        for label, rows in (("added", added), ("deleted", deleted)):
            tally = Counter(norm(r.get(key)) for r in rows)
            if tally:
                log.info("%s %s by %s: %s", name, label, key, dict(sorted(tally.items(), key=lambda kv: str(kv[0]))))
    return key_changes


def main() -> int:
    args = parse_args()
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("compare_snapshots", config, stamp)
    for label, gdb in (("Before", args.before), ("After", args.after)):
        if not arcpy.Exists(gdb):
            log.error("%s snapshot not found: %s", label, gdb)
            return 1
        log.info("%s: %s", label, gdb)

    out = io.run_folder(config, "compare", stamp)
    key_changes = []
    for name in ("district", "permissible_uses", "special_designation", "parcel", "local_plan_parcels"):
        key_changes += compare_dataset(name, args.before, args.after, config["keys"].get(name), out, log)

    sde.write_csv(
        out / "key_changes.csv", key_changes,
        ["DATASET", "GlobalID", "FIELD", "BEFORE", "AFTER", "KEY_BEFORE"]
        + sorted({k for c in key_changes for k in c if k.startswith("AFTER_")}),
    )
    tally = Counter((c["DATASET"], norm(c["BEFORE"]), norm(c["AFTER"])) for c in key_changes)
    for (dataset, before, after), n in sorted(tally.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        log.info("Key change %s: %s -> %s on %s rows", dataset, before, after, n)
    log.info("Compare CSVs: %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
