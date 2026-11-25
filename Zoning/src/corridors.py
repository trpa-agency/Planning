"""Highway noise corridors: centerlines from Major Highways, buffered and split by district.

Steps, all in a scratch file geodatabase in EPSG 26910:

1. Pull Major Highways and the Streets segments whose name is a state route (per
   corridor.streets_names) from the REST services.
2. Give each Major Highways segment a route code. The route comes from the Streets
   segments within corridor.match_m of it, by overlapping length, when they cover at least
   corridor.match_share of the segment. Otherwise it comes from the Major Highways name
   (corridor.major_names). Segments with neither are dropped and logged; that removes
   county roads such as Pioneer Trail and Lakeshore Blvd.
3. Fill gaps: Streets route segments farther than corridor.fill_gap_m from every kept
   Major Highways segment, in pieces at least corridor.fill_min_m long.
4. Buffer each route corridor.buffer_feet each side, dissolved by route, and intersect with
   the districts.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict

import arcpy

from src import rest
from src.cnel import parse_corridors

log = logging.getLogger("sde")
FEET_TO_M = 0.3048
SQ_M_PER_ACRE = 4046.8564224


def _route_for(name, jurisdiction, table: dict[str, list]) -> str | None:
    """Look up a road name in {route: [name or "NAME|JURISDICTION"]}."""
    name = (name or "").strip().upper()
    if not name:
        return None
    for route, names in table.items():
        for entry in names:
            entry_name, _, entry_juris = str(entry).upper().partition("|")
            if name == entry_name and (not entry_juris or entry_juris == (jurisdiction or "").upper()):
                return route
    return None


def centerlines(cfg: dict, ws: str) -> str:
    """Build the route centerlines in ws. Returns the feature class path."""
    arcpy.env.overwriteOutput = True
    major = os.path.join(ws, "major")
    streets = os.path.join(ws, "streets")
    rest.to_feature_class(cfg["major_url"], major, "NAME")
    names = sorted({str(n).split("|")[0] for ns in cfg["streets_names"].values() for n in ns})
    where = "NAME IN (" + ", ".join("'" + n.replace("'", "''") + "'" for n in names) + ")"
    data = rest.query_all(cfg["streets_url"], "NAME,MAINT_JURISDICTION", where=where)
    tmp_json = os.path.join(os.path.dirname(ws), "streets.json")
    with open(tmp_json, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    arcpy.conversion.JSONToFeatures(tmp_json, streets)
    log.info("Streets route segments pulled: %s", len(data["features"]))

    # Route code on every Streets segment; drop names that do not map.
    arcpy.management.AddField(streets, "ROUTE", "TEXT", field_length=10)
    with arcpy.da.UpdateCursor(streets, ["NAME", "MAINT_JURISDICTION", "ROUTE"]) as cursor:
        for name, juris, _ in cursor:
            route = _route_for(name, juris, cfg["streets_names"])
            if route:
                cursor.updateRow([name, juris, route])
            else:
                cursor.deleteRow()

    # Route on each Major Highways segment, by overlap with Streets routes.
    street_buf = os.path.join(ws, "street_buf")
    arcpy.analysis.PairwiseBuffer(streets, street_buf, f"{cfg['match_m']} Meters", "LIST", ["ROUTE"])
    overlap = os.path.join(ws, "major_overlap")
    arcpy.analysis.PairwiseIntersect([major, street_buf], overlap, "ALL")
    oid_field = [f.name for f in arcpy.ListFields(overlap) if f.name.upper().startswith("FID_MAJOR")][0]
    share = defaultdict(Counter)
    for oid, route, length in arcpy.da.SearchCursor(overlap, [oid_field, "ROUTE", "SHAPE@LENGTH"]):
        share[oid][route] += length

    lines = os.path.join(ws, "centerlines")
    sr = arcpy.Describe(major).spatialReference
    arcpy.management.CreateFeatureclass(ws, "centerlines", "POLYLINE", spatial_reference=sr)
    for name, length in (("ROUTE", 10), ("SOURCE", 40), ("SOURCE_NAME", 60), ("ROUTE_FROM", 20)):
        arcpy.management.AddField(lines, name, "TEXT", field_length=length)
    dropped, how = Counter(), Counter()
    with arcpy.da.SearchCursor(major, ["OID@", "NAME", "SHAPE@"]) as src, \
            arcpy.da.InsertCursor(lines, ["SHAPE@", "ROUTE", "SOURCE", "SOURCE_NAME", "ROUTE_FROM"]) as dst:
        for oid, name, shape in src:
            best = share[oid].most_common(1)
            if best and best[0][1] >= cfg["match_share"] * shape.length:
                route, origin = best[0][0], "Streets name"
            else:
                route, origin = _route_for(name, None, cfg["major_names"]), "Major Highways name"
            if not route:
                dropped[(name or "").strip() or "(no name)"] += shape.length / 1609.344
                continue
            how[origin] += 1
            dst.insertRow([shape, route, "Major Highways", (name or "").strip(), origin])
    log.info("Major Highways segments kept by route source: %s", dict(how))
    log.info("Major Highways dropped (miles): %s", {k: round(v, 2) for k, v in dropped.items()})

    # Fill gaps from Streets.
    major_buf = os.path.join(ws, "major_buf")
    arcpy.analysis.PairwiseBuffer(lines, major_buf, f"{cfg['fill_gap_m']} Meters", "ALL")
    gap = os.path.join(ws, "gap")
    arcpy.analysis.PairwiseErase(streets, major_buf, gap)
    gap_parts = os.path.join(ws, "gap_parts")
    arcpy.management.Dissolve(gap, gap_parts, ["ROUTE"], multi_part="SINGLE_PART", unsplit_lines="UNSPLIT_LINES")
    filled = Counter()
    with arcpy.da.SearchCursor(gap_parts, ["ROUTE", "SHAPE@"]) as src, \
            arcpy.da.InsertCursor(lines, ["SHAPE@", "ROUTE", "SOURCE", "SOURCE_NAME", "ROUTE_FROM"]) as dst:
        for route, shape in src:
            if shape.length >= cfg["fill_min_m"]:
                dst.insertRow([shape, route, "Streets (gap fill)", "", "Streets name"])
                filled[route] += shape.length / 1609.344
    log.info("Gap fill from Streets (miles): %s", {k: round(v, 2) for k, v in filled.items()})
    miles = Counter()
    for route, length in arcpy.da.SearchCursor(lines, ["ROUTE", "SHAPE@LENGTH"]):
        miles[route] += length / 1609.344
    log.info("Centerline miles by route: %s", {k: round(v, 1) for k, v in sorted(miles.items())})
    return lines


def corridor_pieces(cfg: dict, ws: str, lines: str, district_fc: str, rows: dict[str, dict]) -> list[dict]:
    """Buffer routes, split by district, and attach the corridor standard of each district."""
    buf = os.path.join(ws, "route_buf")
    width_m = cfg["buffer_feet"] * FEET_TO_M
    arcpy.analysis.PairwiseBuffer(lines, buf, f"{width_m} Meters", "LIST", ["ROUTE"])
    pieces_fc = os.path.join(ws, "route_district")
    arcpy.analysis.PairwiseIntersect([buf, district_fc], pieces_fc, "ALL")
    pieces = []
    for route, zid, shape in arcpy.da.SearchCursor(pieces_fc, ["ROUTE", "ZONING_ID", "SHAPE@"]):
        if shape is None or shape.area / SQ_M_PER_ACRE < cfg["min_piece_acres"]:
            continue
        row = rows[zid]
        stated = parse_corridors(row["CORRIDOR_CNEL"], row["CNEL"]).get(route)
        if stated:
            value, kind = stated
            basis = {"stated": "corridor standard", "permissible": "override permissible where applicable",
                     "included": "corridor included in district value"}[kind]
        else:
            value, basis = None, "no corridor standard in document"
        pieces.append({
            "SHAPE@": shape, "ROUTE": route, "ZONING_ID": zid, "DISTRICT_CNEL": row["CNEL"],
            "CORRIDOR_CNEL": value, "EFFECTIVE_CNEL": value if value is not None else row["CNEL"],
            "CORRIDOR_BASIS": basis, "WIDTH_FT": cfg["buffer_feet"], "SOURCE_DOC": row["SOURCE_DOC"],
            "SOURCE_PAGE": row["SOURCE_PAGE"], "ACRES": round(shape.area / SQ_M_PER_ACRE, 3),
        })
    return pieces


CORRIDOR_FIELDS = [
    ("ROUTE", "TEXT", 10), ("ZONING_ID", "TEXT", 50), ("DISTRICT_CNEL", "SHORT", None),
    ("CORRIDOR_CNEL", "SHORT", None), ("EFFECTIVE_CNEL", "SHORT", None), ("CORRIDOR_BASIS", "TEXT", 60),
    ("WIDTH_FT", "SHORT", None), ("SOURCE_DOC", "TEXT", 150), ("SOURCE_PAGE", "TEXT", 10), ("ACRES", "DOUBLE", None),
]
