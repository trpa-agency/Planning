"""CNEL: export District joined to the CNEL reference CSV as a GeoPackage.

Writes cnel.gpkg (default data/cnel/district_cnel.gpkg, committed) with two layers in
EPSG 26910:

- district_cnel: every District polygon with its CNEL row from
  data/reference/cnel_by_district.csv, plus the district name, plan, and the ID it is
  published under.
- legacy_noise_levels: the legacy AGIS_TRPA/MapServer/82 Noise Levels polygons, for
  comparison.

District comes from one of two sources:

- service (default): the public Zoning/MapServer/0. It still carries the pre-E04 IDs, so
  every district with PLAN_ID e04.plan_id that lacks the e04.prefix is given it, and the
  published ID is kept in PUBLISHED_ZONING_ID. The service has no Carson City halves of
  055 and 056; their CSV rows are listed and skipped, and the whole published 055 and 056
  shapes carry the Washoe rows (both halves are 50 CNEL).
- version: District in the connected SDE version (post-E04 IDs, the 055 and 056 split).
  Read only.

Stops if any District has no CSV row. Run from any folder:
    python Zoning/scripts/cnel_export_gpkg.py [--config config.yaml] [--source service|version]
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import corridors, io, rest, sde  # noqa: E402
from src.cnel import FIELDS, NAMES, load_csv  # noqa: E402

DISTRICT_FIELDS = ["ZONING_ID", "ZONING_DESCRIPTION", "PLAN_ID", "PLAN_NAME", "PLAN_TYPE"]
EXTRA = [("PUBLISHED_ZONING_ID", "TEXT", 50), ("ZONING_DESCRIPTION", "TEXT", 255), ("PLAN_ID", "TEXT", 50),
         ("PLAN_NAME", "TEXT", 100), ("PLAN_TYPE", "TEXT", 50), ("LEGACY_SHARE", "DOUBLE", None),
         ("CHANGE", "TEXT", 20)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=str(io.ROOT / "config.yaml"))
    parser.add_argument("--source", choices=["service", "version"], default="service")
    return parser.parse_args()


def read_districts(config: dict, source: str, scratch: str, log) -> list[dict]:
    """Return District rows with SHAPE@ and a target ZONING_ID."""
    if source == "version":
        sde.check_version(config, log, for_write=False)
        path = sde.dataset_path(config, "district")
        key = config["keys"]["district"]
        rows = sde.rows(path, ["SHAPE@", key] + DISTRICT_FIELDS[1:])
        for r in rows:
            r["ZONING_ID"] = r.pop(key)
            r["PUBLISHED_ZONING_ID"] = r["ZONING_ID"]
        return rows

    url = config["cnel"]["district_url"]
    fc = os.path.join(scratch, "district")
    rest.to_feature_class(url, fc, ",".join(DISTRICT_FIELDS))
    prefix, plan_id = config["e04"]["prefix"], config["e04"]["plan_id"]
    rows = sde.rows(fc, ["SHAPE@"] + DISTRICT_FIELDS)
    renamed = 0
    for r in rows:
        r["PUBLISHED_ZONING_ID"] = r["ZONING_ID"]
        if r["PLAN_ID"] == plan_id and not str(r["ZONING_ID"]).startswith(prefix):
            r["ZONING_ID"] = prefix + r["ZONING_ID"]
            renamed += 1
    log.info("Service districts: %s; given the %s prefix: %s", len(rows), prefix, renamed)
    return rows


def create_gpkg(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if arcpy.Exists(str(path)):
        arcpy.management.Delete(str(path))
    arcpy.management.CreateSQLiteDatabase(str(path), "GEOPACKAGE_1.3")
    return str(path)


def write_districts(gpkg: str, districts: list[dict], rows: dict[str, dict], log) -> None:
    target = os.path.join(gpkg, "district_cnel")
    sr = districts[0]["SHAPE@"].spatialReference
    arcpy.management.CreateFeatureclass(gpkg, "district_cnel", "POLYGON", spatial_reference=sr)
    for name, ftype, length in FIELDS + EXTRA:
        arcpy.management.AddField(target, name, ftype, field_length=length)
    out_fields = ["SHAPE@"] + NAMES + [e[0] for e in EXTRA]
    with arcpy.da.InsertCursor(target, out_fields) as cursor:
        for d in sorted(districts, key=lambda d: d["ZONING_ID"]):
            row = rows[d["ZONING_ID"]]
            share = row["_csv"].get("LEGACY_SHARE") or None
            cursor.insertRow([d["SHAPE@"]] + [row[n] for n in NAMES] + [
                d["PUBLISHED_ZONING_ID"], d["ZONING_DESCRIPTION"], d["PLAN_ID"], d["PLAN_NAME"], d["PLAN_TYPE"],
                float(share) if share else None, row["_csv"].get("CHANGE", "")])
    log.info("district_cnel: %s features", sde.count(target))


def scratch_districts(scratch: str, districts: list[dict]) -> str:
    """District shapes with ZONING_ID only, for the corridor overlay."""
    fc = os.path.join(scratch, "district_ids")
    sr = districts[0]["SHAPE@"].spatialReference
    arcpy.management.CreateFeatureclass(scratch, "district_ids", "POLYGON", spatial_reference=sr)
    arcpy.management.AddField(fc, "ZONING_ID", "TEXT", field_length=50)
    with arcpy.da.InsertCursor(fc, ["SHAPE@", "ZONING_ID"]) as cursor:
        for d in districts:
            cursor.insertRow([d["SHAPE@"], d["ZONING_ID"]])
    return fc


def write_corridors(config: dict, gpkg: str, scratch: str, districts: list[dict], rows: dict, log) -> None:
    cfg = config["corridor"]
    lines = corridors.centerlines(cfg, scratch)
    out_lines = os.path.join(gpkg, "highway_centerlines")
    arcpy.management.CopyFeatures(lines, out_lines)

    pieces = corridors.corridor_pieces(cfg, scratch, lines, scratch_districts(scratch, districts), rows)
    sr = districts[0]["SHAPE@"].spatialReference
    target = os.path.join(gpkg, "noise_corridors")
    arcpy.management.CreateFeatureclass(gpkg, "noise_corridors", "POLYGON", spatial_reference=sr)
    for name, ftype, length in corridors.CORRIDOR_FIELDS:
        arcpy.management.AddField(target, name, ftype, field_length=length)
    names = [f[0] for f in corridors.CORRIDOR_FIELDS]
    with arcpy.da.InsertCursor(target, ["SHAPE@"] + names) as cursor:
        for p in sorted(pieces, key=lambda p: (p["ROUTE"], p["ZONING_ID"])):
            cursor.insertRow([p["SHAPE@"]] + [p[n] for n in names])
    acres = Counter()
    for p in pieces:
        acres[p["CORRIDOR_BASIS"]] += p["ACRES"]
    log.info("noise_corridors: %s pieces; acres by basis: %s", len(pieces),
             {k: round(v) for k, v in acres.items()})
    unstated = Counter((p["ROUTE"], p["ZONING_ID"]) for p in pieces
                       if p["CORRIDOR_BASIS"] == "no corridor standard in document" and p["ACRES"] >= 1)
    if unstated:
        log.info("Routes crossing districts with no corridor standard (1 acre or more): %s",
                 sorted(f"{r} in {z}" for r, z in unstated))


def main() -> int:
    args = parse_args()
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("cnel_export_gpkg", config, stamp)
    log.info("Config: %s; source: %s", config["_path"], args.source)

    try:
        rows = load_csv(config)
        with tempfile.TemporaryDirectory() as tmp:
            arcpy.management.CreateFileGDB(tmp, "scratch.gdb")
            scratch = os.path.join(tmp, "scratch.gdb")
            districts = read_districts(config, args.source, scratch, log)

            ids = Counter(d["ZONING_ID"] for d in districts)
            missing = sorted(set(ids) - set(rows))
            if missing:
                raise sde.GuardError(f"{len(missing)} District IDs have no CNEL row: {missing}")
            extra = sorted(set(rows) - set(ids))
            if extra:
                log.warning("CSV rows with no District shape (skipped): %s", extra)
            multi = sorted(z for z, n in ids.items() if n > 1)
            if multi:
                log.warning("ZONING_IDs on more than one District feature: %s", multi)

            gpkg = create_gpkg(io.resolve(config["cnel"]["gpkg"]))
            write_districts(gpkg, districts, rows, log)
            write_corridors(config, gpkg, scratch, districts, rows, log)
            legacy = os.path.join(gpkg, "legacy_noise_levels")
            rest.to_feature_class(config["cnel"]["legacy_url"], legacy,
                                  "PAS,PAS_NAME,SPEC_AREA,CP,COUNTY,LAND_USE,CNL")
            arcpy.management.ClearWorkspaceCache()
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1

    path = io.resolve(config["cnel"]["gpkg"])
    log.info("Wrote %s (%.1f MB)", path, path.stat().st_size / 1e6)
    log.info("CNEL values: %s", dict(sorted(Counter(rows[d["ZONING_ID"]]["CNEL"] for d in districts).items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
