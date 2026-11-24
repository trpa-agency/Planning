"""F26 to F29 and F34: fix District overlaps, fill the Tahoe Valley hole, recalculate ACRES.

Computes each fix from the edit version's current shapes, so it can't undo a later edit:

- F26 to F28 (geometry.clips): the overlap between two districts is clipped off the one
  that loses it. Polygon parts smaller than geometry.min_part_sq_m are dropped as slivers.
- F29 (geometry.fill): the coverage hole under the named parcel is found by differencing
  the districts around it, and merged into the named district.
- F34 (geometry.recalc_acres): ACRES is set to planar area in EPSG 26910 on every district
  whose stored value is off by more than geometry.acres_threshold.

Checks before anything is written (dry run or not): each named district exists exactly
once; each overlap and the fill are within geometry.tolerance_acres of the expected area;
after the change each pair overlaps by less than 1 square meter; the fill overlaps no
other district; and the parcel is covered. The dry run writes the proposed shapes to
outputs/geometry_<time>/proposed.gdb so they can be checked in Pro.

With run.write_to_db true, the shapes and ACRES are written in one edit session and the
checks run again on what was written before saving. F25 is dropped: Esri Check Geometry
finds nothing wrong with those three shapes.

Run from any folder:
    python Zoning/scripts/fix_district_geometry.py [--config config.yaml]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import arcpy  # noqa: E402

from src import io, sde  # noqa: E402

SR = arcpy.SpatialReference(26910)
SQ_M_PER_ACRE = sde.SQ_METERS_PER_ACRE
MAX_OVERLAP_SQ_M = 1.0
MAX_UNCOVERED_SQ_M = 5.0


def acres(geom) -> float:
    return geom.area / SQ_M_PER_ACRE if geom else 0.0


def parts(poly) -> list:
    """Split a polygon into single-part polygons, keeping each part's holes."""
    if poly is None or poly.area == 0:
        return []
    return [arcpy.Polygon(poly.getPart(i), SR) for i in range(poly.partCount)]


def merge(polys: list):
    out = None
    for p in polys:
        out = p if out is None else out.union(p)
    return out


def drop_slivers(poly, min_sq_m: float):
    kept = [p for p in parts(poly) if p.area >= min_sq_m]
    return merge(kept)


def load_districts(config: dict) -> dict[str, list]:
    path = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    out = {}
    with arcpy.da.SearchCursor(path, ["GlobalID", key, "ACRES", "SHAPE@"], spatial_reference=SR) as cursor:
        for guid, zid, stored, shape in cursor:
            out.setdefault(zid, []).append({"GlobalID": sde.norm_guid(guid), "ZONING_ID": zid, "ACRES": stored, "SHAPE": shape})
    return out


def one(districts: dict, zid: str) -> dict:
    found = districts.get(zid, [])
    if len(found) != 1:
        raise sde.GuardError(f"Expected one District feature for {zid}, found {len(found)}.")
    return found[0]


def plan(config: dict, log) -> dict:
    g = config["geometry"]
    tol = g["tolerance_acres"]
    districts = load_districts(config)
    changes = {}  # GlobalID -> {ZONING_ID, FIX_ID, OLD, NEW}
    clip_polys, problems = [], []

    for c in g["clips"]:
        lose, keep = one(districts, c["lose"]), one(districts, c["keep"])
        overlap = lose["SHAPE"].intersect(keep["SHAPE"], 4)
        if overlap is None or overlap.area < MAX_OVERLAP_SQ_M:
            log.info("%s: %s and %s no longer overlap; already done, skipped.", c["fix"], c["lose"], c["keep"])
            continue
        got = acres(overlap)
        log.info("%s: %s overlaps %s by %.4f acres (expected %.3f)", c["fix"], c["lose"], c["keep"], got, c["expect_acres"])
        if abs(got - c["expect_acres"]) > tol:
            problems.append(f"{c['fix']}: overlap is {got:.4f} acres, expected {c['expect_acres']}")
            continue
        new = drop_slivers(lose["SHAPE"].difference(keep["SHAPE"]), g["min_part_sq_m"])
        left = new.intersect(keep["SHAPE"], 4).area if new else 0
        if new is None or left >= MAX_OVERLAP_SQ_M:
            problems.append(f"{c['fix']}: {left:.2f} square meters of overlap remain after the clip")
            continue
        changes[lose["GlobalID"]] = {"ZONING_ID": c["lose"], "FIX_ID": c["fix"], "OLD": lose["SHAPE"], "NEW": new}
        clip_polys.append((c["fix"], c["lose"], c["keep"], overlap))

    f = g["fill"]
    target = one(districts, f["district"])
    parcel_path = sde.dataset_path(config, "parcel")
    parcel_shapes = [r[0] for r in arcpy.da.SearchCursor(parcel_path, ["SHAPE@"], f"APN = {sde.sql_text(f['apn'])}", spatial_reference=SR)]
    if not parcel_shapes:
        raise sde.GuardError(f"Parcel {f['apn']} not found.")
    parcel = merge(parcel_shapes)
    region = parcel.buffer(30)
    nearby = [d["SHAPE"] for ds in districts.values() for d in ds if not region.disjoint(d["SHAPE"])]
    gap = region.difference(merge(nearby))
    holes = [h for h in parts(gap) if h.area > 100 and not h.disjoint(parcel)]
    fill = merge(holes)
    if fill is not None and fill.area > parcel.area * 1.5:
        fill = fill.intersect(parcel.buffer(0.5), 4)
    got = acres(fill)
    if fill is None or fill.area == 0:
        log.info("%s: no hole under parcel %s; already done, skipped.", f["fix"], f["apn"])
    elif abs(got - f["expect_acres"]) > tol:
        problems.append(f"{f['fix']}: fill is {got:.4f} acres, expected {f['expect_acres']}")
    else:
        others = [d for ds in districts.values() for d in ds if d["GlobalID"] != target["GlobalID"]]
        hit = sum(fill.intersect(d["SHAPE"], 4).area for d in others if not fill.disjoint(d["SHAPE"]))
        if hit >= MAX_OVERLAP_SQ_M:
            problems.append(f"{f['fix']}: fill overlaps other districts by {hit:.2f} square meters")
        new = target["SHAPE"].union(fill)
        changes[target["GlobalID"]] = {"ZONING_ID": f["district"], "FIX_ID": f["fix"], "OLD": target["SHAPE"], "NEW": new}
        after = [new if not new.disjoint(parcel) else None] + [d["SHAPE"] for d in others if not d["SHAPE"].disjoint(parcel)]
        uncovered = parcel.difference(merge([a for a in after if a])).area
        log.info("%s: parcel %s uncovered after the fill: %.2f square meters", f["fix"], f["apn"], uncovered)
        if uncovered >= MAX_UNCOVERED_SQ_M:
            problems.append(f"{f['fix']}: parcel still has {uncovered:.2f} square meters outside any district")

    if problems:
        for p in problems:
            log.error(p)
        raise sde.GuardError(f"{len(problems)} geometry checks failed; nothing written.")

    for guid, ch in changes.items():
        log.info("%s %s: %.4f acres to %.4f acres (change %+.4f)", ch["FIX_ID"], ch["ZONING_ID"],
                 acres(ch["OLD"]), acres(ch["NEW"]), acres(ch["NEW"]) - acres(ch["OLD"]))

    recalc = []
    if g.get("recalc_acres"):
        for ds in districts.values():
            for d in ds:
                shape = changes[d["GlobalID"]]["NEW"] if d["GlobalID"] in changes else d["SHAPE"]
                new_acres = round(acres(shape), 8)
                if d["ACRES"] is None or abs(d["ACRES"] - new_acres) > g.get("acres_threshold", 0.001) or d["GlobalID"] in changes:
                    recalc.append({"GlobalID": d["GlobalID"], "ZONING_ID": d["ZONING_ID"], "OLD": d["ACRES"], "NEW": new_acres})
        big = sorted(recalc, key=lambda r: -abs((r["OLD"] or 0) - r["NEW"]))
        log.info("F34: ACRES changes on %s of %s districts; %s by more than 0.01 acres. Largest: %s",
                 len(recalc), sum(len(v) for v in districts.values()),
                 sum(1 for r in recalc if abs((r["OLD"] or 0) - r["NEW"]) > 0.01),
                 ", ".join(f"{r['ZONING_ID']} {r['OLD'] or 0:.3f} to {r['NEW']:.3f}" for r in big[:6]))
    return {"changes": changes, "clips": clip_polys, "fill": (f["fix"], f["district"], fill), "recalc": recalc}


def write_proposed(p: dict, folder: Path, log) -> None:
    gdb = folder / "proposed.gdb"
    arcpy.management.CreateFileGDB(str(folder), gdb.name)
    layers = {
        "new_shapes": [(ch["FIX_ID"], ch["ZONING_ID"], acres(ch["NEW"]), ch["NEW"]) for ch in p["changes"].values()],
        "removed_overlaps": [(fix, lose, acres(geom), geom) for fix, lose, keep, geom in p["clips"]],
        "hole_fill": [(p["fill"][0], p["fill"][1], acres(p["fill"][2]), p["fill"][2])],
    }
    for name, rows in layers.items():
        arcpy.management.CreateFeatureclass(str(gdb), name, "POLYGON", spatial_reference=SR)
        path = str(gdb / name)
        arcpy.management.AddField(path, "FIX_ID", "TEXT", field_length=8)
        arcpy.management.AddField(path, "ZONING_ID", "TEXT", field_length=50)
        arcpy.management.AddField(path, "ACRES", "DOUBLE")
        with arcpy.da.InsertCursor(path, ["FIX_ID", "ZONING_ID", "ACRES", "SHAPE@"]) as cursor:
            for row in rows:
                if row[-1] is not None:
                    cursor.insertRow(row)
    log.info("Proposed shapes for review in Pro: %s", gdb)


def apply(config: dict, p: dict, log) -> None:
    path = sde.dataset_path(config, "district")
    key = config["keys"]["district"]
    versioned = sde.is_versioned(path)
    log.info("Starting edit session (multiuser_mode=%s)", versioned)
    acres_by_guid = {r["GlobalID"]: r["NEW"] for r in p["recalc"]}
    with arcpy.da.Editor(sde.workspace(config), multiuser_mode=versioned):
        guids = list(p["changes"])
        done = 0
        with arcpy.da.UpdateCursor(path, ["GlobalID", key, "SHAPE@", "ACRES"], sde.sql_in("GlobalID", guids)) as cursor:
            for guid, zid, _, _ in cursor:
                ch = p["changes"][sde.norm_guid(guid)]
                if zid != ch["ZONING_ID"]:
                    raise sde.GuardError(f"{guid} is {zid}, expected {ch['ZONING_ID']}.")
                cursor.updateRow([guid, zid, ch["NEW"], round(acres(ch["NEW"]), 8)])
                done += 1
        if done != len(guids):
            raise sde.GuardError(f"Replaced {done} shapes, expected {len(guids)}.")
        log.info("Replaced %s district shapes", done)

        if acres_by_guid:
            updated = 0
            # ACRES only; shapes outside the four fixes are not rewritten.
            with arcpy.da.UpdateCursor(path, ["GlobalID", "ACRES"]) as cursor:
                for guid, old in cursor:
                    g = sde.norm_guid(guid)
                    if g in acres_by_guid and g not in p["changes"]:
                        cursor.updateRow([guid, acres_by_guid[g]])
                        updated += 1
            log.info("F34: ACRES recalculated on %s districts", updated)

        # Re-check what was written.
        after = load_districts(config)
        g = config["geometry"]
        for c in g["clips"]:
            lose, keep = one(after, c["lose"]), one(after, c["keep"])
            left = lose["SHAPE"].intersect(keep["SHAPE"], 4).area
            if left >= MAX_OVERLAP_SQ_M:
                raise sde.GuardError(f"{c['fix']}: {left:.2f} square meters of overlap after writing.")
        stale = [d["ZONING_ID"] for ds in after.values() for d in ds
                 if g.get("recalc_acres") and abs((d["ACRES"] or 0) - acres(d["SHAPE"])) > g.get("acres_threshold", 0.001)]
        if stale:
            raise sde.GuardError(f"ACRES does not match the shape on: {stale[:10]}")
        log.info("Verified inside the edit session; saving.")


def main() -> int:
    args = io.parse_args(__doc__.splitlines()[0])
    config = io.load_config(args.config)
    stamp = io.timestamp()
    log = io.get_logger("fix_district_geometry", config, stamp)
    write = bool(config["run"]["write_to_db"])
    log.info("Config: %s", config["_path"])
    log.info("Mode: %s", "WRITE" if write else "dry run")
    try:
        sde.check_version(config, log, for_write=write)
        p = plan(config, log)
        if not p["changes"] and not p["recalc"]:
            log.info("Nothing to change: every fix is already in place and ACRES matches every shape.")
            return 0
        out = io.run_folder(config, "geometry", stamp)
        write_proposed(p, out, log)
        sde.write_csv(out / "acres_changes.csv",
                      [{k: r[k] for k in ("ZONING_ID", "GlobalID", "OLD", "NEW")} for r in p["recalc"]],
                      ["ZONING_ID", "GlobalID", "OLD", "NEW"])
        if not write:
            log.info("Dry run complete. Review proposed.gdb in Pro, then set run.write_to_db to true to write.")
            return 0
        apply(config, p, log)
    except sde.GuardError as err:
        log.error("Stopped: %s", err)
        return 1
    log.info("District geometry fixes written. Rerun the snapshot to confirm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
