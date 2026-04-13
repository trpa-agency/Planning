"""
utils.py

Reusable helper functions for the Parcel Attributes ETL.
All functions here are generic — no ETL-specific business logic.
"""

import arcpy
import json
import logging
import os
import smtplib
import time
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from config import (
    LOG_PATH, SCRATCH_GDB,
    EMAIL_SUBJECT, EMAIL_SENDER, EMAIL_RECEIVER, EMAIL_SMTP_HOST, EMAIL_SMTP_PORT,
    JOIN_KEY, FIELD_MAP, SKIP_INSERT_FIELDS,
)

log = logging.getLogger(__name__)


# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(fmt)
    # Console handler: replace any non-encodable characters rather than crashing
    con_handler = logging.StreamHandler()
    con_handler.setFormatter(fmt)
    con_handler.stream = open(
        con_handler.stream.fileno(), mode="w",
        encoding="utf-8", errors="replace", closefd=False,
    )
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, con_handler])


# ── Decorators ────────────────────────────────────────────────────────────────

def timer(fn):
    """Decorator — logs elapsed wall-clock time for any function."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start   = time.perf_counter()
        result  = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        log.info(f"{fn.__name__} completed in {elapsed:.1f}s")
        return result
    return wrapper


# ── Scratch GDB ───────────────────────────────────────────────────────────────

def ensure_scratch_gdb():
    """Create the scratch file GDB if it does not already exist."""
    gdb_dir  = os.path.dirname(SCRATCH_GDB)
    gdb_name = os.path.basename(SCRATCH_GDB)
    if not arcpy.Exists(SCRATCH_GDB):
        arcpy.management.CreateFileGDB(gdb_dir, gdb_name)
        log.info(f"Created scratch GDB: {SCRATCH_GDB}")
    else:
        log.info(f"Using existing scratch GDB: {SCRATCH_GDB}")


def scratch(name):
    """Return a path inside the scratch GDB, deleting any prior version."""
    path = os.path.join(SCRATCH_GDB, name)
    if arcpy.Exists(path):
        arcpy.management.Delete(path)
    return path


# ── Email ─────────────────────────────────────────────────────────────────────

def send_mail(body):
    """Send an HTML notification email with the log file attached."""
    msg = MIMEMultipart()
    msg['Subject'] = EMAIL_SUBJECT
    msg['From']    = EMAIL_SENDER
    msg['To']      = EMAIL_RECEIVER

    msg.attach(MIMEText(f'{body}<br><br>Cheers,<br>GIS Team', 'html'))

    attachment = MIMEText(open(LOG_PATH, encoding='utf-8', errors='replace').read())
    attachment.add_header("Content-Disposition", "attachment",
                          filename=os.path.basename(LOG_PATH))
    msg.attach(attachment)

    try:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            # Only upgrade to TLS if the server advertises STARTTLS support
            if smtp.has_extn("STARTTLS"):
                smtp.starttls()
                smtp.ehlo()
            smtp.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        log.info("Notification email sent")
    except Exception:
        log.exception("Failed to send notification email — ETL result was: %s", body)


# ── REST service helpers ──────────────────────────────────────────────────────

def query_service(service_url, fields, where="1=1"):
    """
    Query an ArcGIS REST FeatureServer / MapServer layer directly via HTTP.

    Use this when arcpy.da.SearchCursor cannot read a field due to a reserved
    SQL keyword name (e.g. TYPE, DATE, NAME).

    Returns: list of attribute dicts, one per feature.
    Raises:  RuntimeError if the service returns an error response.
    """
    params = urllib.parse.urlencode({
        "where":          where,
        "outFields":      ",".join(fields),
        "returnGeometry": "false",
        "f":              "json",
    })
    url = f"{service_url}/query?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    if "error" in data:
        raise RuntimeError(f"Service query error: {data['error']}")
    return [f["attributes"] for f in data.get("features", [])]


# ── ArcPy helpers ─────────────────────────────────────────────────────────────

def get_last_edited_date(fc, field="last_edited_date"):
    """
    Return the most-recent value of *field* across all rows in *fc*.
    Returns None if the layer is empty or the field is not present.
    """
    try:
        fields = [f.name for f in arcpy.ListFields(fc)]
        if field not in fields:
            log.warning(f"  Field '{field}' not found in {fc} — cannot determine edit date")
            return None
        with arcpy.da.SearchCursor(fc, [field],
                                   sql_clause=(None, f"ORDER BY {field} DESC")) as cur:
            for row in cur:
                return row[0]
    except Exception:
        log.exception(f"  Error reading {field} from {fc}")
    return None


def get_insert_fields(fc):
    """
    Return the ordered list of writable field names for *fc*, excluding
    system-managed fields (OID, GlobalID, editor-tracking, geometry).
    """
    return [
        f.name for f in arcpy.ListFields(fc)
        if f.name not in SKIP_INSERT_FIELDS
        and f.type not in ("OID", "Geometry", "GlobalID")
        and not f.name.startswith("Shape")
    ]


def build_type_coercers(fc, field_names):
    """
    Return a list of coercion callables, one per field in *field_names*,
    that cast values to match the target field type.

    Handles common source/target type mismatches (e.g. String → Integer,
    SmallInteger → String, Double → Integer) without raising on null/empty.
    """
    type_map = {f.name: f.type for f in arcpy.ListFields(fc)}

    def make_coercer(field_type):
        if field_type in ("Integer", "SmallInteger"):
            def coerce(v):
                if v is None or (isinstance(v, str) and not v.strip()):
                    return None
                try:
                    return int(float(v))
                except (ValueError, TypeError):
                    return None
        elif field_type in ("Double", "Single"):
            def coerce(v):
                if v is None or (isinstance(v, str) and not v.strip()):
                    return None
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None
        elif field_type == "String":
            def coerce(v):
                if v is None:
                    return None
                s = str(v).strip()
                return s if s else None
        else:
            def coerce(v):
                return v
        return coerce

    return [make_coercer(type_map.get(f, "String")) for f in field_names]


# ── Value translation ─────────────────────────────────────────────────────────

def apply_value_map(raw_val, value_map):
    """
    Translate *raw_val* using *value_map*.

    Lookup order:
      1. Exact key match
      2. None key  — covers null / empty raw values
      3. "*" key   — wildcard for any non-null, non-empty raw value
      4. Return raw_val unchanged if no rule matches
    """
    if value_map is None:
        return raw_val

    is_empty = raw_val is None or str(raw_val).strip() == ""

    if not is_empty and raw_val in value_map:
        return value_map[raw_val]
    if is_empty and None in value_map:
        return value_map[None]
    if not is_empty and "*" in value_map:
        return value_map["*"]
    return raw_val


# ── Spatial join helpers ──────────────────────────────────────────────────────

@timer
def run_spatial_join(parcel_fc, overlay_fc, output_name, match_option="LARGEST_OVERLAP"):
    """
    Spatial join giving each parcel the attribute of its largest-overlap
    overlay polygon.  Returns the path of the output feature class.
    """
    out_fc = scratch(output_name)
    log.info(f"SpatialJoin: {os.path.basename(str(parcel_fc))} <- {os.path.basename(str(overlay_fc))}")
    arcpy.analysis.SpatialJoin(
        target_features   = parcel_fc,
        join_features     = overlay_fc,
        out_feature_class = out_fc,
        join_operation    = "JOIN_ONE_TO_ONE",
        join_type         = "KEEP_ALL",
        match_option      = match_option,
    )
    count = int(arcpy.management.GetCount(out_fc)[0])
    log.info(f"  -> {count:,} features in join output")
    return out_fc


@timer
def run_identity(parcel_fc, overlay_fc, output_name):
    """
    Identity overlay: parcels straddling multiple polygons are split and
    the dominant-area piece is kept, so each parcel maps to one overlay value.
    Returns the path of the output feature class.
    """
    identity_tmp = scratch(f"{output_name}_identity_tmp")
    out_fc       = scratch(output_name)

    log.info(f"Identity: {os.path.basename(str(parcel_fc))} <- {os.path.basename(str(overlay_fc))}")
    arcpy.analysis.Identity(
        in_features       = parcel_fc,
        identity_features = overlay_fc,
        out_feature_class = identity_tmp,
        join_attributes   = "ALL",
    )

    arcpy.management.AddGeometryAttributes(identity_tmp, "AREA", Area_Unit="SQUARE_METERS")
    sorted_tmp = scratch(f"{output_name}_sorted")
    arcpy.management.Sort(
        identity_tmp, sorted_tmp,
        [[JOIN_KEY, "ASCENDING"], ["POLY_AREA", "DESCENDING"]],
    )
    arcpy.management.DeleteIdentical(sorted_tmp, JOIN_KEY)
    arcpy.management.Rename(sorted_tmp, out_fc)

    count = int(arcpy.management.GetCount(out_fc)[0])
    log.info(f"  → {count:,} unique parcels after identity + dissolve")
    return out_fc


def collect_join_results(join_fc, overlay_key):
    """
    Read an attribute-value join output into { apn: {target_field: value} }
    using the field mapping defined in FIELD_MAP[overlay_key].
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
            attrs = {field_mapping[src]: row[i + 1] for i, src in enumerate(source_fields)}
            results[apn] = attrs

    log.info(f"  Collected {len(results):,} APN records from '{overlay_key}' join")
    return results


# ── Proximity spatial relationships ──────────────────────────────────────────

@timer
def get_spatial_relationships(parcel_fc, overlay_fc, attr_field=None):
    """
    Classify each parcel as "Within", "Intersects", or "Outside" relative to
    an overlay polygon layer.

    Strategy:
      Pass 1 — COMPLETELY_WITHIN spatial join → parcels fully inside overlay
      Pass 2 — INTERSECT spatial join         → parcels with any overlap
      Result  — Within > Intersects > Outside

    If *attr_field* is supplied the label is prefixed with the overlay
    attribute value: "<attr_value> - Within|Intersects"

    Returns: { apn: label_string }
    """
    overlay_name = os.path.basename(str(overlay_fc))

    # Pass 1: COMPLETELY_WITHIN
    within_fc   = run_spatial_join(parcel_fc, overlay_fc,
                                   f"prox_{overlay_name}_within",
                                   match_option="COMPLETELY_WITHIN")
    within_apns = set()
    with arcpy.da.SearchCursor(within_fc, [JOIN_KEY, "Join_Count"]) as cur:
        for row in cur:
            if row[0] and row[1] and row[1] > 0:
                within_apns.add(row[0])
    log.info(f"  Within '{overlay_name}': {len(within_apns):,} parcels")

    # Pass 2: INTERSECT (also captures the attribute value when attr_field is set)
    intersect_fc   = run_spatial_join(parcel_fc, overlay_fc,
                                      f"prox_{overlay_name}_intersect",
                                      match_option="INTERSECT")
    intersect_apns = {}   # apn -> attr_value_or_None
    read_i = [JOIN_KEY, "Join_Count"] + ([attr_field] if attr_field else [])
    with arcpy.da.SearchCursor(intersect_fc, read_i) as cur:
        for row in cur:
            apn, join_count = row[0], row[1]
            if apn and join_count and join_count > 0:
                intersect_apns[apn] = row[2] if attr_field else None
    log.info(f"  Intersects '{overlay_name}': {len(intersect_apns):,} parcels")

    # Combine
    results = {}
    with arcpy.da.SearchCursor(parcel_fc, [JOIN_KEY]) as cur:
        for row in cur:
            apn = row[0]
            if apn is None:
                continue

            if apn in within_apns:
                label = "Within"
            elif apn in intersect_apns:
                label = "Intersects"
            else:
                label = "Outside"

            if attr_field and apn in intersect_apns:
                attr_val = intersect_apns[apn]
                if attr_val and str(attr_val).strip():
                    label = f"{str(attr_val).strip()} - {label}"

            results[apn] = label

    log.info(
        f"  Proximity summary for '{overlay_name}': "
        f"Within={sum(1 for v in results.values() if 'Within' in v):,}  "
        f"Intersects={sum(1 for v in results.values() if 'Intersects' in v):,}  "
        f"Outside={sum(1 for v in results.values() if v == 'Outside'):,}"
    )
    return results
