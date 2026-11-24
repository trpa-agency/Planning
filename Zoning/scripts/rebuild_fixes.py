"""Rebuild the 2026-11-20 fix package against the current edit version.

The package was built from DEFAULT. Alyssa's version, and the edits in ours, have changed
some of the same rows since. This script reads the edit version (read only), checks every
fix row, and writes a status for each plus a rebuilt package holding only what is still
needed.

Statuses:
- pending      still needed; written to the rebuilt package
- done         already applied in the version (value already new, row already gone, or the
               same district and use already present with the same values)
- conflict     the version changed the row or field some other way; review by hand
- missing      the target row of an update no longer exists; review
- no_district  an insert targets a ZONING_ID with no District feature; review
- not_checkable the target dataset or field is not configured
- dropped      left out on purpose (rebuild.drop in config.yaml, with the reason)

Outputs, under outputs/rebuild_<time>/:
- fix_status.csv         every fix row with its status, current value, and note
- review.csv             only the conflict, missing, and no_district rows
- extra_rows_in_replaced_districts.csv  use rows in A05 districts that A05 would not delete
- rebuilt/<file>.csv     the pending rows, in the package's own columns (A04 rekeyed)

Read only. Run from any folder:
    python Zoning/scripts/rebuild_fixes.py [--default <DEFAULT snapshot .gdb>] [--config ...]
--default enables the District geometry check (has the version changed the shape?).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402
from src.values import norm, same, table_of, use_key  # noqa: E402

PU_FIELDS = ["Zoning_ID", "Category", "Subcategory", "Use_Type", "Use_Status", "Density", "Unit", "Notes"]
INSERT_COMPARE = ["Category", "Use_Status", "Density", "Unit"]
UPDATE_FILES = ["pu_updates.csv", "area_pu_updates.csv"]
DELETE_FILES = ["pu_deletes.csv", "area_pu_deletes.csv", "sd_deletes.csv"]
INSERT_FILES = ["pu_inserts.csv", "area_pu_inserts.csv"]
DISTRICT_FILES = ["district_repair_geometry.csv", "district_replacement_shapes.csv"]
PARCEL_FILES = ["parcel_updates.csv"]
REVIEW = {"conflict", "missing", "no_district"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--default", help="DEFAULT snapshot geodatabase, for the District geometry check.")
    parser.add_argument("--config", default=str(io.ROOT / "config.yaml"))
    return parser.parse_args()


# ---------- file helpers ----------

def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def field_map(path: str) -> dict[str, str]:
    return {f.name.casefold(): f.name for f in arcpy.ListFields(path)}


# ---------- version state ----------

def load_table(path: str, wanted: list[str]) -> dict[str, dict]:
    """Rows keyed by GlobalID, with wanted fields under their canonical names."""
    fields = field_map(path)
    present = [(name, fields[name.casefold()]) for name in wanted if name.casefold() in fields]
    rows = {}
    with arcpy.da.SearchCursor(path, ["GlobalID", *[actual for _, actual in present]]) as cursor:
        for guid, *values in cursor:
            rows[sde.norm_guid(guid)] = {name: value for (name, _), value in zip(present, values)}
    return rows


def load_districts(path: str, key: str) -> dict[str, dict]:
    rows = {}
    with arcpy.da.SearchCursor(path, ["GlobalID", "OID@", key, "SHAPE@WKB"]) as cursor:
        for guid, oid, zid, wkb in cursor:
            rows[sde.norm_guid(guid)] = {
                "OBJECTID": oid, "ZONING_ID": zid,
                "SHAPE": hashlib.md5(bytes(wkb)).hexdigest() if wkb else None,
            }
    return rows


# ---------- checks ----------

def check_updates(rows: list[dict], tables: dict, file: str) -> list[dict]:
    results = []
    for row in rows:
        table = table_of(row, "permissible_uses")
        target = tables[table].get(sde.norm_guid(row.get("GlobalID")))
        field = row["FIELD"]
        if target is None:
            status, current, note = "missing", "", "Target row is not in the version."
        elif field not in target:
            status, current, note = "not_checkable", "", f"Field {field} not read."
        else:
            current = target[field]
            if same(current, row["NEW_VALUE"], field):
                status, note = "done", "Already has the new value."
            elif same(current, row["OLD_VALUE"], field):
                status, note = "pending", ""
            else:
                status, note = "conflict", "Version value matches neither the old nor the new value."
        results.append({**row, "FILE": file, "STATUS": status, "CURRENT": current, "NOTE": note})
    return results


def check_deletes(rows: list[dict], tables: dict, file: str) -> list[dict]:
    results = []
    for row in rows:
        table = table_of(row, "special_designation" if file.startswith("sd_") else "permissible_uses")
        target = tables[table].get(sde.norm_guid(row.get("GlobalID")))
        key = "ZONING_ID" if table == "special_designation" else "Zoning_ID"
        if target is None:
            status, current, note = "done", "", "Row already deleted."
        else:
            current = target.get(key)
            changed = []
            if not same(current, row.get("Zoning_ID")):
                changed.append(f"{key} {row.get('Zoning_ID')!r} to {current!r}")
            if table == "permissible_uses" and row.get("Use_Type") and not same(target.get("Use_Type"), row.get("Use_Type")):
                changed.append(f"Use_Type {row.get('Use_Type')!r} to {target.get('Use_Type')!r}")
            status, note = ("conflict", "Row changed since the package: " + "; ".join(changed)) if changed else ("pending", "")
        results.append({**row, "FILE": file, "STATUS": status, "CURRENT": current, "NOTE": note})
    return results


def check_inserts(rows: list[dict], pu: dict, pending_deletes: set[str], districts: set[str],
                  rekey: dict, file: str) -> list[dict]:
    # Existing rows by (district, use), ignoring rows the package still deletes.
    existing = defaultdict(list)
    for guid, row in pu.items():
        if guid not in pending_deletes:
            existing[(norm(row.get("Zoning_ID")), use_key(row.get("Use_Type")))].append(row)

    results = []
    for row in rows:
        row = dict(row)
        original = row["Zoning_ID"]
        new_id = rekey.get(row.get("FIX_ID"), {}).get(original)
        note_parts = []
        if new_id:
            row["Zoning_ID"] = new_id
            note_parts.append(f"Rekeyed from {original}.")
        matches = existing.get((norm(row["Zoning_ID"]), use_key(row["Use_Type"])), [])
        if row["Zoning_ID"] not in districts:
            status = "no_district"
            note_parts.append(f"No District feature carries {row['Zoning_ID']}.")
        elif not matches:
            status = "pending"
        else:
            diffs = [f for f in INSERT_COMPARE if not same(matches[0].get(f), row.get(f), f)]
            if diffs:
                status = "conflict"
                note_parts.append("Already present with different " + ", ".join(
                    f"{f} ({matches[0].get(f)!r} vs {row.get(f)!r})" for f in diffs))
            else:
                status = "done"
                note_parts.append("Already present.")
            if len(matches) > 1:
                note_parts.append(f"{len(matches)} existing rows for this use.")
        results.append({**row, "FILE": file, "STATUS": status, "CURRENT": "", "NOTE": " ".join(note_parts)})
    return results


def check_districts(rows: list[dict], version: dict, default: dict | None, file: str) -> list[dict]:
    results = []
    for row in rows:
        guid = sde.norm_guid(row.get("GlobalID"))
        target = version.get(guid)
        if target is None:
            status, note = "missing", "District feature is not in the version."
        elif default is None:
            status, note = "pending", "Geometry not compared; pass --default to check."
        elif guid not in default:
            status, note = "conflict", "Feature is not in the DEFAULT snapshot."
        elif target["SHAPE"] != default[guid]["SHAPE"]:
            status, note = "conflict", "Shape changed in the version since DEFAULT."
        elif not same(target["ZONING_ID"], row.get("ZONING_ID")):
            status, note = "conflict", f"ZONING_ID is now {target['ZONING_ID']}."
        else:
            status, note = "pending", ""
        results.append({**row, "FILE": file, "STATUS": status, "CURRENT": target["ZONING_ID"] if target else "", "NOTE": note})
    return results


def check_parcels(rows: list[dict], config: dict, file: str, log) -> list[dict]:
    path = sde.dataset_path(config, "parcel")
    if path is None or not arcpy.Exists(path):
        return [{**r, "FILE": file, "STATUS": "not_checkable", "CURRENT": "", "NOTE": "Parcel dataset not configured."} for r in rows]
    fields = field_map(path)
    wanted = sorted({r["FIELD"] for r in rows if r["FIELD"].casefold() in fields})
    if "apn" not in fields:
        return [{**r, "FILE": file, "STATUS": "not_checkable", "CURRENT": "", "NOTE": "Parcel dataset has no APN."} for r in rows]
    apns = sorted({r["APN"] for r in rows})
    current = {}
    cursor_fields = [fields["apn"], *[fields[w.casefold()] for w in wanted]]
    with arcpy.da.SearchCursor(path, cursor_fields, sde.sql_in(fields["apn"], apns)) as cursor:
        for apn, *values in cursor:
            current.setdefault(apn, []).append(dict(zip(wanted, values)))
    results = []
    for row in rows:
        found = current.get(row["APN"], [])
        if row["FIELD"] not in wanted:
            status, value, note = "not_checkable", "", f"Parcel dataset has no {row['FIELD']} field."
        elif not found:
            status, value, note = "missing", "", "APN not found."
        else:
            value = found[0][row["FIELD"]]
            if len(found) > 1:
                note = f"{len(found)} rows for this APN; checked the first."
            else:
                note = ""
            if same(value, row["NEW_VALUE"], row["FIELD"]):
                status = "done"
            elif same(value, row["OLD_VALUE"], row["FIELD"]):
                status = "pending"
            else:
                status = "conflict"
                note = (note + " Value matches neither the old nor the new value.").strip()
        results.append({**row, "FILE": file, "STATUS": status, "CURRENT": value, "NOTE": note})
    log.info("Parcel fields checked: %s", wanted or "none")
    return results


def extra_rows_in_replaced(a05: list[dict], a06: list[dict], pu: dict) -> list[dict]:
    """Use rows in A05's districts that neither A05 deletes nor A06 inserts.

    These would sit beside the replacement table. Rows matching an A06 insert are the
    replacement itself (after posting), so they are not flagged.
    """
    districts = {r["Zoning_ID"] for r in a05 if r.get("Zoning_ID")}
    listed = {sde.norm_guid(r["GlobalID"]) for r in a05}
    replacement = {(r["Zoning_ID"], use_key(r["Use_Type"])) for r in a06}
    return [
        {"GlobalID": guid, **row}
        for guid, row in pu.items()
        if row.get("Zoning_ID") in districts and guid not in listed
        and (row.get("Zoning_ID"), use_key(row.get("Use_Type"))) not in replacement
    ]


# ---------- main ----------

def main() -> int:
    args = parse_args()
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("rebuild_fixes", config, stamp)
    log.info("Config: %s", config["_path"])
    sde.check_version(config, log, for_write=False)

    fix_dir = io.resolve(config["paths"]["fix_package_csv"])
    rebuild_cfg = config.get("rebuild", {})
    rekey = rebuild_cfg.get("rekey", {})

    pu_path = sde.dataset_path(config, "permissible_uses")
    sd_path = sde.dataset_path(config, "special_designation")
    district_path = sde.dataset_path(config, "district")
    tables = {
        "permissible_uses": load_table(pu_path, PU_FIELDS),
        "special_designation": load_table(sd_path, ["ZONING_ID", "SPECIAL_DESIGNATION"]),
    }
    version_districts = load_districts(district_path, config["keys"]["district"])
    district_ids = {d["ZONING_ID"] for d in version_districts.values()}
    default_districts = None
    if args.default:
        default_districts = load_districts(f"{args.default}/district", config["keys"]["district"])
    log.info("Version: %s use rows, %s special designation rows, %s districts",
             len(tables["permissible_uses"]), len(tables["special_designation"]), len(version_districts))

    files = {}
    for path in sorted(fix_dir.glob("*.csv")):
        files[path.name] = read_csv(path)

    results: list[dict] = []
    for name in UPDATE_FILES:
        results += check_updates(files[name][1], tables, name)
    for name in DELETE_FILES:
        results += check_deletes(files[name][1], tables, name)
    pending_deletes = {
        sde.norm_guid(r["GlobalID"]) for r in results
        if r["FILE"] in DELETE_FILES and r["STATUS"] in ("pending", "conflict")
    }
    for name in INSERT_FILES:
        results += check_inserts(files[name][1], tables["permissible_uses"], pending_deletes, district_ids, rekey, name)
    for name in DISTRICT_FILES:
        results += check_districts(files[name][1], version_districts, default_districts, name)

    # Dropped fix IDs: checked and reported, but never written to the rebuilt package.
    dropped = rebuild_cfg.get("drop", {}) or {}
    drop_note = lambda r: f"Dropped: {dropped[r['FIX_ID']]}"  # noqa: E731
    for name in PARCEL_FILES:
        results += check_parcels(files[name][1], config, name, log)
    for r in results:
        if r.get("FIX_ID") in dropped and r["STATUS"] != "done":
            r["NOTE"] = (drop_note(r) + " " + r.get("NOTE", "")).strip()
            r["STATUS"] = "dropped"

    out = io.run_folder(config, "rebuild", stamp)
    rebuilt = out / "rebuilt"
    rebuilt.mkdir()
    # One ZONE column: PowerShell's Import-Csv ignores case and rejects Zoning_ID beside ZONING_ID.
    for r in results:
        r["ZONE"] = r.get("Zoning_ID") or r.get("ZONING_ID") or ""
    status_cols = ["FILE", "FIX_ID", "STATUS", "NOTE", "CURRENT", "OBJECTID", "GlobalID", "APN",
                   "ZONE", "Use_Type", "FIELD", "OLD_VALUE", "NEW_VALUE"]
    write_rows(out / "fix_status.csv", status_cols, results)
    write_rows(out / "review.csv", status_cols, [r for r in results if r["STATUS"] in REVIEW])

    by_file = defaultdict(list)
    for r in results:
        by_file[r["FILE"]].append(r)
    for name, (columns, _) in files.items():
        if name in rebuild_cfg.get("passthrough", []):
            write_rows(rebuilt / name, columns, files[name][1])
        elif name in by_file:
            write_rows(rebuilt / name, columns, [r for r in by_file[name] if r["STATUS"] == "pending"])
        else:
            # Files without a row-level check (clip and fill) depend on the replacement shapes.
            write_rows(rebuilt / name, columns, files[name][1])

    a05 = [r for r in files["area_pu_deletes.csv"][1] if r["FIX_ID"] == "A05"]
    a06 = [r for r in files["area_pu_inserts.csv"][1] if r["FIX_ID"] == "A06"]
    extra = extra_rows_in_replaced(a05, a06, tables["permissible_uses"])
    write_rows(out / "extra_rows_in_replaced_districts.csv", ["GlobalID", *PU_FIELDS], extra)
    if extra:
        log.warning("%s use rows sit in A05 districts but are not in A05; they would remain beside the A06 inserts.", len(extra))

    tally = Counter((r["FIX_ID"], r["STATUS"]) for r in results)
    for fix_id in sorted({k[0] for k in tally}):
        parts = ", ".join(f"{status} {n}" for (fid, status), n in sorted(tally.items()) if fid == fix_id)
        log.info("%s: %s", fix_id, parts)
    totals = Counter(r["STATUS"] for r in results)
    log.info("All fix rows: %s", dict(sorted(totals.items())))

    pu_now = len(tables["permissible_uses"])
    pu_del = sum(1 for r in results if r["FILE"] in ("pu_deletes.csv", "area_pu_deletes.csv") and r["STATUS"] == "pending")
    pu_ins = sum(1 for r in results if r["FILE"] in INSERT_FILES and r["STATUS"] == "pending")
    log.info("PermissibleUses: %s now, minus %s pending deletes, plus %s pending inserts = %s",
             pu_now, pu_del, pu_ins, pu_now - pu_del + pu_ins)
    sd_del = sum(1 for r in results if r["FILE"] == "sd_deletes.csv" and r["STATUS"] == "pending")
    log.info("Special_Designation: %s now, minus %s pending deletes = %s",
             len(tables["special_designation"]), sd_del, len(tables["special_designation"]) - sd_del)
    log.info("Review rows: %s. Output: %s", sum(totals[s] for s in REVIEW), out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
