"""E04: prefix Washoe County district IDs with WCTAP_ across District and its tables.

ZONING_ID is the join key for District, PermissibleUses, and Special_Designation, so the
rename has to land everywhere at once. This script:

1. Checks the connection is the QA edit version (writes only).
2. Picks the districts: PLAN_ID equal to e04.plan_id, ZONING_ID not already prefixed, and
   not in e04.exclude. Stops unless the count equals e04.expected_count.
3. Stops if any new ID already exists in District or either table.
4. Records the GlobalID of every related row keyed to an old ID, and saves the rename map
   and those rows to rename_map.csv and related_rows_before.csv.
5. With run.write_to_db true, in one edit session: renames the District features, then
   sets the new key on every recorded related row by GlobalID. That works whether the
   relationship passes the change down, blanks the related keys, or leaves them alone.
   Datasets listed in e04.also_update are renamed the same way.
6. Verifies inside the session: no old ID remains anywhere, each new ID carries exactly the
   rows its old ID had, totals are unchanged, and null keys did not increase. Any failure
   aborts the session and saves nothing.

Parcel_Master is not touched; the parcel ETL sets its zoning fields from District.

Dry run by default. Run from any folder:
    python Zoning/scripts/e04_prefix_wctap.py [--config config.yaml]
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

RELATED = ("permissible_uses", "special_designation")


def null_where(field: str) -> str:
    return f"{field} IS NULL OR {field} = '' OR {field} = ' '"


def key_counts(path: str, field: str) -> Counter:
    return Counter(r[0] for r in arcpy.da.SearchCursor(path, [field]))


def select_districts(config: dict, log) -> dict[str, str]:
    """Return the rename map {old: new}."""
    e04 = config["e04"]
    district = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    prefix = e04["prefix"]
    exclude = set(e04.get("exclude") or [])
    rows = sde.rows(district, ["OID@", key, "PLAN_ID"], f"PLAN_ID = {sde.sql_text(e04['plan_id'])}")
    mapping, skipped = {}, []
    for r in sorted(rows, key=lambda r: str(r[key])):
        old = r[key]
        if old is None or str(old).startswith(prefix):
            skipped.append(f"{old} (already prefixed)")
        elif old in exclude:
            skipped.append(f"{old} (excluded)")
        elif old in mapping:
            log.info("ZONING_ID %s is on more than one District feature; renamed together.", old)
        else:
            mapping[old] = prefix + old
    log.info("PLAN_ID %s districts: %s features; skipped %s", e04["plan_id"], len(rows), skipped or "none")
    log.info("To rename (%s): %s", len(mapping), ", ".join(f"{o} to {n}" for o, n in mapping.items()))
    if len(mapping) != e04["expected_count"]:
        raise sde.GuardError(f"Found {len(mapping)} districts to rename, expected {e04['expected_count']}. Review before renaming.")
    return mapping


def targets(config: dict) -> list[tuple[str, str, str]]:
    """(dataset key, path, key field) for District, the related tables, and also_update."""
    out = [("district", sde.dataset_path(config, "district"), config["keys"]["district"])]
    for name in [*RELATED, *(config["e04"].get("also_update") or [])]:
        path = sde.dataset_path(config, name)
        if path is None or not arcpy.Exists(path):
            raise sde.GuardError(f"Dataset {name} is not configured or not found.")
        out.append((name, path, config["keys"][name]))
    return out


def check_collisions(mapping: dict, tgts, log) -> None:
    new_ids = set(mapping.values())
    for name, path, key in tgts:
        present = new_ids & set(key_counts(path, key))
        if present:
            raise sde.GuardError(f"{name} already has new IDs: {sorted(present)}")
    log.info("No new ID exists yet in %s", ", ".join(t[0] for t in tgts))


def record(mapping: dict, tgts) -> dict:
    """GlobalIDs per dataset for every row keyed to an old ID, plus before counts."""
    rec = {}
    for name, path, key in tgts:
        rows = sde.rows(path, ["GlobalID", key], sde.sql_in(key, mapping))
        rec[name] = {
            "rows": [{"GlobalID": sde.norm_guid(r["GlobalID"]), "OLD": r[key], "NEW": mapping[r[key]]} for r in rows],
            "total": sde.count(path),
            "nulls": sde.count(path, null_where(key)),
        }
    return rec


def apply(config: dict, mapping: dict, tgts, rec: dict, log) -> None:
    versioned = sde.is_versioned(tgts[0][1])
    log.info("Starting edit session (multiuser_mode=%s)", versioned)
    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        for name, path, key in tgts:
            new_by_guid = {r["GlobalID"]: r["NEW"] for r in rec[name]["rows"]}
            guids = list(new_by_guid)
            changed = 0
            for start in range(0, len(guids), 500):
                chunk = guids[start:start + 500]
                with arcpy.da.UpdateCursor(path, ["GlobalID", key], sde.sql_in("GlobalID", chunk)) as cursor:
                    for guid, value in cursor:
                        cursor.updateRow([guid, new_by_guid[sde.norm_guid(guid)]])
                        changed += 1
            if changed != len(guids):
                raise sde.GuardError(f"{name}: renamed {changed} rows, expected {len(guids)}.")
            log.info("%s: %s rows renamed", name, changed)

        for name, path, key in tgts:
            counts = key_counts(path, key)
            leftover = sorted(set(mapping) & set(counts))
            if leftover:
                raise sde.GuardError(f"{name}: old IDs remain: {leftover}")
            want = Counter(r["NEW"] for r in rec[name]["rows"])
            wrong = {z: (counts.get(z, 0), n) for z, n in want.items() if counts.get(z, 0) != n}
            if wrong:
                raise sde.GuardError(f"{name}: rows per new ID differ (after, expected): {wrong}")
            if sde.count(path) != rec[name]["total"]:
                raise sde.GuardError(f"{name}: total changed from {rec[name]['total']} to {sde.count(path)}.")
            nulls = sde.count(path, null_where(key))
            if nulls > rec[name]["nulls"]:
                raise sde.GuardError(f"{name}: null keys went from {rec[name]['nulls']} to {nulls}.")
        log.info("Verified inside the edit session; saving.")


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("e04_prefix_wctap", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")
    try:
        sde.check_version(config, log, for_write=write)
        mapping = select_districts(config, log)
        tgts = targets(config)
        check_collisions(mapping, tgts, log)
        rec = record(mapping, tgts)
        out = io.run_folder(config, "e04", stamp)
        sde.write_csv(out / "rename_map.csv", [{"OLD": o, "NEW": n} for o, n in mapping.items()], ["OLD", "NEW"])
        sde.write_csv(out / "related_rows_before.csv",
                      [{"DATASET": name, **r} for name in rec for r in rec[name]["rows"]],
                      ["DATASET", "GlobalID", "OLD", "NEW"])
        for name in rec:
            log.info("%s: %s rows to rename (of %s; %s null keys now)",
                     name, len(rec[name]["rows"]), rec[name]["total"], rec[name]["nulls"])
        log.info("Saved: %s", out)
        if not write:
            log.info("Dry run complete. Set run.write_to_db to true to rename.")
            return 0
        apply(config, mapping, tgts, rec, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1
    log.info("E04 complete. Parcel_Master follows on the next parcel ETL run. Rerun the snapshot to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
