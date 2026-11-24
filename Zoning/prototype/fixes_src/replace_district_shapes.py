"""
Method B for EDIT_GUIDE.md steps F26 to F29: replace four District shapes by GlobalID.

Replaces 111_SA2, 030, 114, and TVAP_TC_G with the finished shapes in
F26_F29_District_ReplacementShapes and sets ACRES from the new shape.

How to run
1. Edit config.yaml in the package root: set sde.workspace and sde.district.
2. Save or discard any open edits in ArcGIS Pro. This script opens its own edit session.
3. In the Pro Python window, or the arcgispro-py3 command prompt, run:
       exec(open(r"<package folder>\\scripts\\replace_district_shapes.py").read())
   The first run is a dry run (run.dry_run: true). It prints what would change and edits nothing.
4. Set run.dry_run to false in config.yaml and run again to apply.

Use either this script or the Clip and Merge steps in the guide, not both.
"""
import os
import sys
from datetime import datetime

import arcpy
import yaml

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:  # exec() in the Python window has no __file__
    HERE = os.path.join(os.getcwd(), "scripts")
ROOT = os.path.dirname(HERE)

with open(os.path.join(ROOT, "config.yaml"), "r") as f:
    cfg = yaml.safe_load(f)

workspace = cfg["sde"]["workspace"]
district = cfg["sde"]["district"]
replacement_fc = os.path.join(ROOT, cfg["fixes"]["gdb"], cfg["fixes"]["replacement_shapes"])
dry_run = cfg["run"]["dry_run"]
acres_per_m2 = 1 / 4046.8564224

log_path = os.path.join(ROOT, "logs", f"replace_district_shapes_{datetime.now():%Y-%m-%d_%H%M%S}.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
log_file = open(log_path, "w")


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {msg}"
    print(line)
    log_file.write(line + "\n")


log(f"District: {district}")
log(f"Replacement shapes: {replacement_fc}")
log(f"Dry run: {dry_run}")

target_sr = arcpy.Describe(district).spatialReference
log(f"District spatial reference: {target_sr.name} ({target_sr.factoryCode})")
if target_sr.factoryCode != 26910:
    log("District is not EPSG 26910. Shapes will be projected on read; check results closely.")

# Read the replacement shapes, projected to the District spatial reference
new_shapes = {}
with arcpy.da.SearchCursor(
    replacement_fc, ["TARGET_GLOBALID", "ZONING_ID", "FIX_ID", "SHAPE@"], spatial_reference=target_sr
) as cur:
    for gid, zid, fix, shape in cur:
        new_shapes[gid.upper()] = (zid, fix, shape)
log(f"Read {len(new_shapes)} replacement shapes")
if len(new_shapes) != 4:
    log("Expected 4 replacement shapes. Stopping.")
    sys.exit(1)

where = "GlobalID IN (" + ", ".join(f"'{g}'" for g in new_shapes) + ")"
fields = ["GlobalID", "ZONING_ID", "SHAPE@", "ACRES"]

# Check first: every target exists and its ZONING_ID matches
found = 0
with arcpy.da.SearchCursor(district, fields, where_clause=where) as cur:
    for gid, zid, shape, acres in cur:
        exp_zid, fix, new = new_shapes[gid.upper()]
        if zid != exp_zid:
            log(f"{gid} is {zid} in SDE but {exp_zid} in the fix package. Stopping.")
            sys.exit(1)
        log(f"{fix} {zid}: {shape.area * acres_per_m2:,.4f} ac now, {new.area * acres_per_m2:,.4f} ac after")
        found += 1
if found != 4:
    log(f"Found {found} of 4 target districts by GlobalID. Stopping.")
    sys.exit(1)

if dry_run:
    log("Dry run only. Set run.dry_run to false in config.yaml to apply.")
else:
    versioned = arcpy.Describe(district).isVersioned
    with arcpy.da.Editor(workspace, multiuser_mode=versioned):
        with arcpy.da.UpdateCursor(district, fields, where_clause=where) as cur:
            for row in cur:
                zid, fix, new = new_shapes[row[0].upper()]
                row[2] = new
                row[3] = round(new.area * acres_per_m2, 4)
                cur.updateRow(row)
                log(f"{fix} {zid}: shape replaced, ACRES set to {row[3]:,.4f}")
    log("Done. Continue with guide step F34 (recalculate ACRES for every district).")

log_file.close()
