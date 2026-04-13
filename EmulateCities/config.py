"""
config.py

All configuration constants for Parcel_Attributes_ETL.py.
Edit this file to update service URLs, field mappings, and thresholds.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────

_gis_dir = os.environ.get('GIS_WORKING_DIR', r'C:\GIS')
_sde_dir = os.environ.get('SDE_CONNECT_DIR', r'F:\GIS\DB_CONNECT')

LOG_PATH    = os.path.join(_gis_dir, r'Logs\Parcel_Joins_ETL.log')
SCRATCH_GDB = os.path.join(_gis_dir, 'Scratch.gdb')

# SDE connection file — used ONLY for the write path (truncate + append)
COLLECTION_SDE = os.path.join(_sde_dir, 'Collection.sde')

# Target feature class in the enterprise GDB (write path)
TARGET_FC = os.path.join(COLLECTION_SDE, "SDE.Parcel_Permit_Review_Attributes")

# ── Map Service URLs (read path) ──────────────────────────────────────────────
# All source layers are read from ArcGIS REST FeatureServer / MapServer endpoints.

MAP_SERVICES = {
    "parcel_master": "https://maps.trpa.org/server/rest/services/Parcels/FeatureServer/0",
    "flood_zone":    "https://maps.trpa.org/server/rest/services/Streams_and_Flood_Zone/MapServer/0",
    "avalanche":     "https://maps.trpa.org/server/rest/services/Avalanche_Zones/MapServer/0",
    "hwl_buffer":    "https://maps.trpa.org/server/rest/services/Shoreline_Resources/MapServer/7",
    "historic":      "https://maps.trpa.org/server/rest/services/Historic/MapServer/0",
    "scenic_rdwy":   "https://maps.trpa.org/server/rest/services/Scenic_Status/MapServer/2",
    "scenic_shore":  "https://maps.trpa.org/server/rest/services/Scenic_Status/MapServer/3",
    "lcv":           "https://maps.trpa.org/server/rest/services/Parcel_Joins/FeatureServer/1",
}

PARCEL_MASTER = MAP_SERVICES["parcel_master"]

# Primary join key shared by Parcel Master and the target table
JOIN_KEY = "APN"

# ── Parcel Master direct-copy fields ──────────────────────────────────────────
# Fields read directly from Parcel Master with no spatial operation required.
# Includes attributes that were formerly derived from separate overlay services
# but are now pre-joined into the Parcel Master service.
# Format: (parcel_master_field, target_table_field)

PARCEL_MASTER_FIELDS = [
    ("APN",                        "APN"),
    ("PPNO",                       "PPNO"),
    ("JURISDICTION",               "JURISDICTION"),
    ("COUNTY",                     "COUNTY"),
    ("OWNERSHIP_TYPE",             "OWNERSHIP_TYPE"),
    ("COUNTY_LANDUSE_DESCRIPTION",  "COUNTY_LANDUSE_DESCRIPTION"),
    ("EXISTING_LANDUSE",           "EXISTING_LANDUSE"),
    ("REGIONAL_LANDUSE",           "REGIONAL_LANDUSE"),
    ("IPES_SCORE",                 "IPES_SCORE"),
    ("AS_SUM",                     "AS_SUM"),
    ("TAX_SUM",                    "TAX_SUM"),
    ("YEAR_BUILT",                 "YEAR_BUILT"),
    ("UNITS",                      "UNITS"),
    ("BEDROOMS",                   "BEDROOMS"),
    ("BATHROOMS",                  "BATHROOMS"),
    ("BUILDING_SQFT",              "BUILDING_SQFT"),
    ("PLAN_ID",                    "PLAN_ID"),
    ("PLAN_NAME",                  "PLAN_NAME"),
    ("PLAN_TYPE",                  "PLAN_TYPE"),
    ("TOLERANCE_ID",               "TOLERANCE_ID"),
    ("TAZ",                        "TAZ"),
    ("PARCEL_ACRES",               "PARCEL_ACRES"),
    ("PARCEL_SQFT",                "PARCEL_SQFT"),
    ("IMPERVIOUS_SURFACE_SQFT",    "ESTIMATED_COVERAGE"),
    ("ESTIMATED_COVERAGE_ALLOWED", "ESTIMATED_COVERAGE_ALLOWED"),  # TODO: confirm source field name
    ("ZONING_ID",                  "ZONING_ID"),
    ("ZONING_DESCRIPTION",         "ZONING_DESCRIPTION"),
    ("FIREPD",                     "FIREPD"),
    # ── Pre-joined spatial attributes (already populated in Parcel Master) ──
    # Future: AVALANCHE_ZONE, FLOOD_ZONE, HWL_BUFFER, HISTORIC_DISTRICT,
    #         SCENIC_* will move here once added to the Parcel Master service.
    ("HRA_NAME",                   "HRA_NAME"),
    ("CATCHMENT",                  "CATCHMENT"),
    ("WATERSHED_NAME",             "WATERSHED_NAME"),
    ("PRIORITY_WATERSHED",         "PRIORITY_WATERSHED"),
    ("SOIL_2003",                  "SOIL_2003"),
    ("TOWN_CENTER",                "TOWN_CENTER"),
    ("LOCATION_TO_TOWNCENTER",     "LOCATION_TO_TOWNCENTER"),
]

# ── Parcel Master flag / value-translated fields ──────────────────────────────
# Fields derived from a Parcel Master field with a value translation applied.
# Format: (pm_field, target_field, value_map)
#
# value_map rules (applied in order):
#   • Exact key match → use that value
#   • None key        → fallback for null / empty source values
#   • "*" key         → fallback for any non-null, non-empty source value

PARCEL_MASTER_FLAG_FIELDS = [
    # CONSERVATION_REC: "CON" or "REC" when REGIONAL_LANDUSE matches exactly; null otherwise.
    ("REGIONAL_LANDUSE", "CONSERVATION_REC", {"CON": "CON", "REC": "REC", "*": None, None: None}),
]

# ── Attribute-value overlays ──────────────────────────────────────────────────
# HRA, soils, priority watershed, town center, and zoning are now direct-copy
# fields from Parcel Master (see PARCEL_MASTER_FIELDS above).  OVERLAYS and
# FIELD_MAP are kept as extension points for any future overlay layers that are
# not yet pre-joined into Parcel Master.
# Format: key -> (service_url, join_type)   join_type: "SPATIAL_JOIN" or "IDENTITY"

OVERLAYS: dict = {}

# Field mapping: overlay_key -> {source_field_in_overlay: target_field_in_table}
FIELD_MAP: dict = {}

# ── Proximity overlays ────────────────────────────────────────────────────────
# Produce "Within" / "Intersects" / "Outside" labels for each parcel.
# If attr_field is set the label is prefixed: "<attr_value> - Within|Intersects"
# Format: key -> (service_url, target_field, attr_field_or_None)
#
# Future: once AVALANCHE_ZONE, FLOOD_ZONE, HWL_BUFFER, and HISTORIC_DISTRICT
# are pre-joined into Parcel Master these entries can be removed.

PROXIMITY_OVERLAYS = {
    "flood_zone": (
        MAP_SERVICES["flood_zone"],
        "FLOOD_ZONE",
        "FLOOD_ZONE",  # e.g. "AE - Within" / "AE - Intersects" / "Outside"
    ),
    "avalanche": (
        MAP_SERVICES["avalanche"],
        "AVALANCHE_ZONE",
        None,         # "Within" / "Intersects" / "Outside"
    ),
    "hwl_buffer": (
        MAP_SERVICES["hwl_buffer"],
        "HWL_BUFFER",
        None,         # "Within" / "Intersects" / "Outside"
    ),
    "historic": (
        MAP_SERVICES["historic"],
        "HISTORIC_DISTRICT",
        None,         # "Within" / "Intersects" / "Outside"
    ),
}

# ── Scenic Corridor config ─────────────────────────────────────────────────────
# Roadway and Shoreline corridors are served as separate map service layers.
# SCENIC_CORRIDOR           = "Within" / "Intersects" / "Outside" (most-specific across both)
# SCENIC_CORRIDOR_RDWY      = "<CORRIDOR_NAME> <TYPE>" for Roadway matches, else "N/A"
# SCENIC_CORRIDOR_SHORELINE = "<CORRIDOR_NAME> <TYPE>" for Shoreline matches, else "N/A"

# Format: (label, service_url, target_field, category_filter)
# category_filter is applied as WHERE CATEGORY = '<value>' when building the name join.
# Both services currently point to the same layer, so filtering by CATEGORY is required
# to avoid cross-contaminating RDWY and SHORELINE results.
SCENIC_CORRIDOR_SERVICES = [
    ("roadway",   MAP_SERVICES["scenic_rdwy"],  "SCENIC_CORRIDOR_RDWY",      "Roadway"),
    ("shoreline", MAP_SERVICES["scenic_shore"], "SCENIC_CORRIDOR_SHORELINE", "Shoreline"),
]

# ── Validation config ──────────────────────────────────────────────────────────

PARCEL_COUNT_MIN = 60_000
PARCEL_COUNT_MAX = 65_500

REQUIRED_FIELDS = [
    "JURISDICTION", "COUNTY", "HRA_NAME", "FLOOD_ZONE", "ZONING_DESCRIPTION",
]

VALID_JURISDICTIONS = {
    "El Dorado County", "Placer County", "Douglas County",
    "Washoe County", "Carson City", "City of South Lake Tahoe",
}
VALID_COUNTIES = {"EL", "PL", "DG", "WA", "CC"}

NULL_RATE_THRESHOLD = 0.05   # flag fields with > 5 % nulls in post-update QA
MAX_ISSUES          = 5      # max sample rows reported per QA category

# ── Email ─────────────────────────────────────────────────────────────────────

EMAIL_SUBJECT   = "Parcel Attributes ETL"
EMAIL_SENDER    = os.environ.get('EMAIL_SENDER')
EMAIL_RECEIVER  = os.environ.get('EMAIL_RECEIVER')
EMAIL_SMTP_HOST = os.environ.get('EMAIL_SMTP_HOST')
EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', 25))

# ── Write-path constants ───────────────────────────────────────────────────────

# Fields managed by ArcGIS automatically — never pass these to InsertCursor.
SKIP_INSERT_FIELDS = {
    "OBJECTID", "GlobalID", "GlobalID_1",
    "created_user", "created_date",
    "last_edited_user", "last_edited_date",
    "Shape", "Shape_Length", "Shape_Area",
}
