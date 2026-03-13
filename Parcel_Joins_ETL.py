"""
Parcel_Joins_ETL.py

Updates SDE.Parcel_Permit_Review_Attributes via a series of spatial joins
and identity overlays from parcel geometry to overlay layers.

Overlay groups:
  - Location     : Jurisdiction, County, HRA, Watershed, Catchment
  - Environmental: Flood Zone, Avalanche Zone, Soil (2003), Priority Watershed
  - Planning     : Plan Area, Town Center, Scenic Corridor, Historic District,
                   Conservation/Rec
  - Land Use     : Zoning, Existing Land Use, Regional Land Use

Author : TRPA GIS
"""

import arcpy
import logging
import os
import time
from datetime import datetime
from functools import wraps

# ── Configuration ─────────────────────────────────────────────────────────────

LOG_PATH    = r"C:\GIS\Logs\Parcel_Joins_ETL.log"
SCRATCH_GDB = r"C:\GIS\Scratch.gdb"

# SDE connection files
# These are .sde connection files; update paths for your environment.
# The db behind the collection service is 'sde_collect'.
COLLECTION_SDE = r"\\<server>\<path>\Collection.sde"   # TODO: update
VECTOR_SDE     = r"\\<server>\<path>\Vector.sde"        # TODO: update

# Target feature class / table in the enterprise GDB
TARGET_FC = os.path.join(COLLECTION_SDE, "SDE.Parcel_Permit_Review_Attributes")

# Parcel master — provides the geometry for all spatial join operations.
# This should be the polygon feature class matching the target table rows.
PARCEL_MASTER = os.path.join(COLLECTION_SDE, "SDE.Parcel_Master")  # TODO: confirm

# ── Overlay layers ─────────────────────────────────────────────────────────────
# Each entry maps a logical name to the SDE feature class path.
# TODO: verify each path and field name against your SDE schema.

OVERLAYS = {
    # key:           (fc_path,                                          join_type)
    # join_type: "SPATIAL_JOIN" (largest overlap) or "IDENTITY"
    "jurisdiction":  (os.path.join(VECTOR_SDE, "SDE.Jurisdiction"),         "SPATIAL_JOIN"),
    "county":        (os.path.join(VECTOR_SDE, "SDE.County"),                "SPATIAL_JOIN"),
    "hra":           (os.path.join(VECTOR_SDE, "SDE.HydrologyResponseArea"), "SPATIAL_JOIN"),
    "flood_zone":    (os.path.join(VECTOR_SDE, "SDE.FloodZone_FEMA"),        "IDENTITY"),
    "avalanche":     (os.path.join(VECTOR_SDE, "SDE.AvalancheZone"),         "IDENTITY"),
    "soil":          (os.path.join(VECTOR_SDE, "SDE.Soils_2003"),            "IDENTITY"),
    "priority_ws":   (os.path.join(VECTOR_SDE, "SDE.PriorityWatershed"),     "SPATIAL_JOIN"),
    "plan":          (os.path.join(VECTOR_SDE, "SDE.PlanningArea"),          "SPATIAL_JOIN"),
    "town_center":   (os.path.join(VECTOR_SDE, "SDE.TownCenter"),            "SPATIAL_JOIN"),
    "scenic":        (os.path.join(VECTOR_SDE, "SDE.ScenicCorridor"),        "IDENTITY"),
    "historic":      (os.path.join(VECTOR_SDE, "SDE.HistoricDistrict"),      "SPATIAL_JOIN"),
    "conservation":  (os.path.join(VECTOR_SDE, "SDE.ConservationRec"),       "SPATIAL_JOIN"),
    "zoning":        (os.path.join(VECTOR_SDE, "SDE.Zoning"),                "SPATIAL_JOIN"),
    "landuse_exist": (os.path.join(VECTOR_SDE, "SDE.ExistingLandUse"),       "SPATIAL_JOIN"),
    "landuse_region":(os.path.join(VECTOR_SDE, "SDE.RegionalLandUse"),       "SPATIAL_JOIN"),
    # Scenic Travel Routes — polygon layers; parcels outside get NULL → "N/A"
    # Source: Scenic_Status/FeatureServer layers 2 & 3
    "scenic_roadway":  (os.path.join(VECTOR_SDE, "SDE.Scenic_Roadway_Travel_Route"),   "SPATIAL_JOIN"),
    "scenic_shoreline":(os.path.join(VECTOR_SDE, "SDE.Scenic_Shoreline_Travel_Route"), "SPATIAL_JOIN"),
}

# Field mapping: overlay_key -> {source_field_in_overlay: target_field_in_table}
# TODO: verify the source field names match your actual overlay layer schemas.
FIELD_MAP = {
    "jurisdiction":  {"JURISDICTION": "JURISDICTION"},
    "county":        {"COUNTY":       "COUNTY"},
    "hra":           {
                        "HRA_NAME":       "HRA_NAME",
                        "WATERSHED_NAME": "WATERSHED_NAME",
                        "CATCHMENT":      "CATCHMENT",
                     },
    "flood_zone":    {"FLD_ZONE":     "FLOOD_ZONE"},
    "avalanche":     {"AVLN_ZONE":    "AVALANCHE_ZONE"},
    "soil":          {"SOIL_TYPE":    "SOIL_2003"},
    "priority_ws":   {"PRIORITY_WS":  "PRIORITY_WATERSHED"},
    "plan":          {"PLAN_NAME":    "PLAN_NAME"},
    "town_center":   {
                        "TC_NAME":    "TOWN_CENTER",
                        "TC_LOC":     "LOCATION_TO_TOWNCENTER",
                     },
    "scenic":        {"SCENIC_CORR":  "SCENIC_CORRIDOR"},
    "historic":      {"HIST_DIST":    "HISTORIC_DISTRICT"},
    "conservation":  {"CONS_REC":     "CONSERVATION_REC"},
    "zoning":        {"ZONING_DESC":  "ZONING_DESCRIPTION"},
    "landuse_exist": {"LU_DESC":      "EXISTING_LANDUSE"},
    "landuse_region":{"RLU_DESC":     "REGIONAL_LANDUSE"},
    # UNIT is the named scenic unit (e.g. "US-50", "Lake Tahoe Shoreline")
    "scenic_roadway":  {"UNIT": "SCENIC_ROADWAY_UNIT"},
    "scenic_shoreline":{"UNIT": "SCENIC_SHORELINE_UNIT"},
}

# Fields that should default to "N/A" when the spatial join returns null
# (i.e. the parcel falls outside the overlay coverage entirely)
NULL_DEFAULTS = {
    "SCENIC_ROADWAY_UNIT":  "N/A",
    "SCENIC_SHORELINE_UNIT": "N/A",
}

# Primary join key shared between parcel master and the target table
JOIN_KEY = "APN"

# ── Validation config ──────────────────────────────────────────────────────────

# Expected row count range for the parcel master (update to match your dataset)
PARCEL_COUNT_MIN = 63_000
PARCEL_COUNT_MAX = 65_500

# Fields that must be non-null / non-empty after the update
REQUIRED_FIELDS = ["JURISDICTION", "COUNTY", "HRA_NAME", "FLOOD_ZONE", "ZONING_DESCRIPTION"]

# Valid domain values for spot-check fields (add/adjust as needed)
VALID_JURISDICTIONS = {"El Dorado County", "Placer County", "Douglas County",
                       "Washoe County", "Carson City", "City of South Lake Tahoe"}
VALID_COUNTIES      = {"EL", "PL", "DG", "WA", "CC"}

# Max null rate (0–1) allowed per required field before validation fails
NULL_RATE_THRESHOLD = 0.05   # 5%

# Max issues to log per check (keeps logs readable)
MAX_ISSUES = 5

# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(),
        ],
    )

log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def timer(fn):
    """Decorator that logs elapsed time for any function."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        log.info(f"{fn.__name__} completed in {elapsed:.1f}s")
        return result
    return wrapper


def ensure_scratch_gdb():
    """Create scratch GDB if it doesn't already exist."""
    gdb_dir  = os.path.dirname(SCRATCH_GDB)
    gdb_name = os.path.basename(SCRATCH_GDB)
    if not arcpy.Exists(SCRATCH_GDB):
        arcpy.management.CreateFileGDB(gdb_dir, gdb_name)
        log.info(f"Created scratch GDB: {SCRATCH_GDB}")
    else:
        log.info(f"Using existing scratch GDB: {SCRATCH_GDB}")


def scratch(name):
    """Return a path inside the scratch GDB, deleting it first if it exists."""
    path = os.path.join(SCRATCH_GDB, name)
    if arcpy.Exists(path):
        arcpy.management.Delete(path)
    return path

# ── Validation ────────────────────────────────────────────────────────────────

def validate_inputs():
    """
    Pre-flight checks before any spatial operations run.

    Verifies that all input datasets exist and that the parcel master
    row count is within the expected range.  Raises RuntimeError if any
    critical check fails so the ETL aborts before touching the SDE.

    Returns True on pass.
    """
    log.info("--- Pre-flight validation ---")
    issues = []

    # 1. Target table accessible
    if not arcpy.Exists(TARGET_FC):
        issues.append(f"Target table not found: {TARGET_FC}")

    # 2. Parcel master accessible and within expected count range
    if not arcpy.Exists(PARCEL_MASTER):
        issues.append(f"Parcel master not found: {PARCEL_MASTER}")
    else:
        count = int(arcpy.management.GetCount(PARCEL_MASTER)[0])
        log.info(f"  Parcel master row count: {count:,}")
        if not (PARCEL_COUNT_MIN <= count <= PARCEL_COUNT_MAX):
            issues.append(
                f"Parcel master count {count:,} is outside expected range "
                f"[{PARCEL_COUNT_MIN:,} – {PARCEL_COUNT_MAX:,}]"
            )

    # 3. All overlay layers accessible
    missing_overlays = []
    for key, (fc_path, _) in OVERLAYS.items():
        if not arcpy.Exists(fc_path):
            missing_overlays.append(f"  {key}: {fc_path}")
    if missing_overlays:
        issues.append("Missing overlay layers:\n" + "\n".join(missing_overlays))

    if issues:
        for msg in issues:
            log.error(f"VALIDATION FAIL: {msg}")
        raise RuntimeError(f"Pre-flight validation failed with {len(issues)} issue(s) — see log")

    log.info("  Pre-flight validation PASSED")
    return True


def validate_outputs():
    """
    Post-update quality checks on the target SDE table.

    Checks:
      1. Required fields are not null/empty above the allowed threshold
      2. JURISDICTION values are within the known domain
      3. COUNTY codes are within the known domain
      4. Duplicate APNs in the target table

    Logs warnings for each issue found (does not raise — updates already committed).
    Returns True if all checks pass, False if any warning was issued.
    """
    log.info("--- Post-update validation ---")
    passed = True

    read_fields = [JOIN_KEY] + REQUIRED_FIELDS + ["COUNTY"]
    total       = 0
    null_counts = {f: 0 for f in REQUIRED_FIELDS}
    bad_jurisdictions = []
    bad_counties      = []
    apn_seen          = {}   # apn -> first row index (for duplicate detection)
    duplicate_apns    = []

    with arcpy.da.SearchCursor(TARGET_FC, read_fields) as cur:
        for i, row in enumerate(cur):
            total += 1
            apn          = row[0]
            jurisdiction = row[read_fields.index("JURISDICTION")]
            county       = row[read_fields.index("COUNTY")]

            # Null / empty checks for all required fields
            for j, field in enumerate(REQUIRED_FIELDS):
                val = row[j + 1]
                if val is None or str(val).strip() == "":
                    null_counts[field] += 1

            # Domain check: JURISDICTION
            if jurisdiction and jurisdiction not in VALID_JURISDICTIONS:
                if len(bad_jurisdictions) < MAX_ISSUES:
                    bad_jurisdictions.append(f"APN {apn}: '{jurisdiction}'")

            # Domain check: COUNTY
            if county and county not in VALID_COUNTIES:
                if len(bad_counties) < MAX_ISSUES:
                    bad_counties.append(f"APN {apn}: '{county}'")

            # Duplicate APN detection
            if apn in apn_seen:
                if len(duplicate_apns) < MAX_ISSUES:
                    duplicate_apns.append(apn)
            else:
                apn_seen[apn] = i

    log.info(f"  Target table row count: {total:,}")

    # Report null rates
    for field, null_ct in null_counts.items():
        rate = null_ct / total if total else 0
        status = "WARN" if rate > NULL_RATE_THRESHOLD else "OK"
        log.log(
            logging.WARNING if status == "WARN" else logging.INFO,
            f"  [{status}] {field}: {null_ct:,} nulls ({rate:.1%})"
        )
        if status == "WARN":
            passed = False

    # Report domain violations
    if bad_jurisdictions:
        passed = False
        log.warning(f"  [WARN] Unexpected JURISDICTION values (first {len(bad_jurisdictions)}):")
        for msg in bad_jurisdictions:
            log.warning(f"    {msg}")

    if bad_counties:
        passed = False
        log.warning(f"  [WARN] Unexpected COUNTY codes (first {len(bad_counties)}):")
        for msg in bad_counties:
            log.warning(f"    {msg}")

    # Report duplicates
    if duplicate_apns:
        passed = False
        log.warning(f"  [WARN] Duplicate APNs found (first {len(duplicate_apns)}): {duplicate_apns}")
    else:
        log.info("  [OK] No duplicate APNs")

    if passed:
        log.info("  Post-update validation PASSED")
    else:
        log.warning("  Post-update validation completed WITH WARNINGS — review log")

    return passed


# ── Spatial operations ────────────────────────────────────────────────────────

@timer
def run_spatial_join(parcel_fc, overlay_fc, output_name, match_option="LARGEST_OVERLAP"):
    """
    Join overlay attributes to parcels using SpatialJoin.

    Uses LARGEST_OVERLAP so each parcel gets the attribute of whichever
    overlay polygon covers the most area of that parcel.

    Returns the path to the output feature class.
    """
    out_fc = scratch(output_name)
    log.info(f"SpatialJoin: {os.path.basename(parcel_fc)} ← {os.path.basename(overlay_fc)}")
    arcpy.analysis.SpatialJoin(
        target_features   = parcel_fc,
        join_features     = overlay_fc,
        out_feature_class = out_fc,
        join_operation    = "JOIN_ONE_TO_ONE",
        join_type         = "KEEP_ALL",
        match_option      = match_option,
    )
    count = int(arcpy.management.GetCount(out_fc)[0])
    log.info(f"  → {count:,} features in join output")
    return out_fc


@timer
def run_identity(parcel_fc, overlay_fc, output_name):
    """
    Overlay parcels with an identity layer.

    Use Identity when a parcel may straddle multiple overlay polygons
    and you want the dominant value (largest area portion).  The result
    is dissolved back to one row per parcel using the JOIN_KEY.

    Returns the path to the output feature class.
    """
    identity_tmp = scratch(f"{output_name}_identity_tmp")
    out_fc       = scratch(output_name)

    log.info(f"Identity: {os.path.basename(parcel_fc)} ← {os.path.basename(overlay_fc)}")
    arcpy.analysis.Identity(
        in_features     = parcel_fc,
        identity_features = overlay_fc,
        out_feature_class = identity_tmp,
        join_attributes = "ALL",
    )

    # Dissolve to one record per parcel, keeping the largest-area value.
    # We add a shape area field so we can pick the dominant overlay polygon.
    arcpy.management.AddGeometryAttributes(identity_tmp, "AREA", Area_Unit="SQUARE_METERS")

    # Sort descending by area so the first row per APN is the largest piece,
    # then dissolve (first occurrence wins after the sort).
    sorted_tmp = scratch(f"{output_name}_sorted")
    arcpy.management.Sort(identity_tmp, sorted_tmp, [[JOIN_KEY, "ASCENDING"], ["POLY_AREA", "DESCENDING"]])
    arcpy.management.DeleteIdentical(sorted_tmp, JOIN_KEY)  # keep first (largest) per APN

    arcpy.management.Rename(sorted_tmp, out_fc)
    count = int(arcpy.management.GetCount(out_fc)[0])
    log.info(f"  → {count:,} unique parcels after identity + dissolve")
    return out_fc


def collect_join_results(join_fc, overlay_key):
    """
    Read a join output feature class into a dict keyed by APN.

    Returns:
        { apn: {target_field: value, ...}, ... }
    """
    field_mapping = FIELD_MAP[overlay_key]
    source_fields = list(field_mapping.keys())
    read_fields   = [JOIN_KEY] + source_fields

    results = {}
    with arcpy.da.SearchCursor(join_fc, read_fields) as cur:
        for row in cur:
            apn = row[0]
            if apn is None:
                continue
            attrs = {}
            for i, src in enumerate(source_fields):
                target_field = field_mapping[src]
                val = row[i + 1]
                # Apply N/A (or other) default for fields outside overlay coverage
                if (val is None or str(val).strip() == "") and target_field in NULL_DEFAULTS:
                    val = NULL_DEFAULTS[target_field]
                attrs[target_field] = val
            results[apn] = attrs

    log.info(f"  Collected {len(results):,} APN records from '{overlay_key}' join")
    return results


# ── Update target table ───────────────────────────────────────────────────────

@timer
def update_target_table(all_results):
    """
    Apply collected join results to the target SDE table using an edit session.

    all_results: dict of { apn: {target_field: value, ...} }
    """
    # Determine which target fields are present across all results
    target_fields_set = set()
    for attrs in all_results.values():
        target_fields_set.update(attrs.keys())
    target_fields = sorted(target_fields_set)

    update_fields = [JOIN_KEY] + target_fields
    log.info(f"Updating {len(target_fields)} fields on {len(all_results):,} parcels")

    editor = arcpy.da.Editor(COLLECTION_SDE)
    editor.startEditing(False, True)   # no undo, versioned
    editor.startOperation()

    updated = 0
    skipped = 0
    try:
        with arcpy.da.UpdateCursor(TARGET_FC, update_fields) as cur:
            for row in cur:
                apn = row[0]
                if apn not in all_results:
                    skipped += 1
                    continue
                attrs = all_results[apn]
                changed = False
                for i, field in enumerate(target_fields):
                    new_val = attrs.get(field)
                    if row[i + 1] != new_val:
                        row[i + 1] = new_val
                        changed = True
                if changed:
                    cur.updateRow(row)
                    updated += 1

        editor.stopOperation()
        editor.stopEditing(True)  # save edits
        log.info(f"Updated {updated:,} rows  |  Skipped {skipped:,} rows (no join match)")

    except Exception:
        editor.stopOperation()
        editor.stopEditing(False)  # rollback
        log.exception("Edit session rolled back due to error")
        raise


# ── Main ──────────────────────────────────────────────────────────────────────

@timer
def main():
    setup_logging()
    log.info("=" * 60)
    log.info("Parcel_Joins_ETL  started")
    log.info("=" * 60)

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = SCRATCH_GDB

    ensure_scratch_gdb()

    # Pre-flight — abort early if inputs are missing or counts are wrong
    validate_inputs()

    # Accumulate all join results keyed by APN
    all_results = {}   # { apn: {field: value, ...} }

    for overlay_key, (overlay_fc, join_type) in OVERLAYS.items():
        log.info(f"--- Processing overlay: {overlay_key} ---")
        try:
            output_name = f"join_{overlay_key}"

            if join_type == "IDENTITY":
                join_fc = run_identity(PARCEL_MASTER, overlay_fc, output_name)
            else:
                join_fc = run_spatial_join(PARCEL_MASTER, overlay_fc, output_name)

            overlay_results = collect_join_results(join_fc, overlay_key)

            # Merge into the master results dict (each overlay adds its fields)
            for apn, attrs in overlay_results.items():
                if apn not in all_results:
                    all_results[apn] = {}
                all_results[apn].update(attrs)

        except Exception:
            log.exception(f"Failed on overlay '{overlay_key}' — skipping")

    log.info(f"Total APNs collected across all overlays: {len(all_results):,}")

    # Push results to SDE
    update_target_table(all_results)

    # Post-update quality checks
    validate_outputs()

    log.info("Parcel_Joins_ETL  finished")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
