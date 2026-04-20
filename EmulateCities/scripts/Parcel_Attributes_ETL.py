"""
Parcel_Attributes_ETL.py

Updates SDE.Parcel_Permit_Review_Attributes via:
  1. Direct field copy from Parcel Master — includes pre-joined attributes
     (HRA, soils, priority watershed, town center, zoning, location to town
     center) that are already populated in the Parcel Master service.
  2. Proximity overlays — "Within" / "Intersects" / "Outside" for
     FLOOD_ZONE, AVALANCHE_ZONE, HWL_BUFFER, and HISTORIC_DISTRICT.
     (These will move to Parcel Master in a future iteration.)
  3. Scenic corridor joins — SCENIC_CORRIDOR proximity + name+type for
     Roadway and Shoreline corridors via two separate map services.
  4. LCV status — Yes/No via APN join against the Parcel_Joins service.

The ETL is incremental: it compares the most-recent last_edited_date in
Parcel Master against the same field in the target table and skips the run
if the target is already up to date.

Target layer (web service reference):
  https://maps.trpa.org/server/rest/services/Parcel_Joins/FeatureServer/6

Author : TRPA GIS
"""

import arcpy
import logging

from config import (
    PARCEL_MASTER, TARGET_FC, COLLECTION_SDE, SCRATCH_GDB,
    JOIN_KEY, PARCEL_MASTER_FIELDS, PARCEL_MASTER_FLAG_FIELDS,
    OVERLAYS, FIELD_MAP, PROXIMITY_OVERLAYS, SCENIC_CORRIDOR_SERVICES,
    MAP_SERVICES,
    PARCEL_COUNT_MIN, PARCEL_COUNT_MAX, REQUIRED_FIELDS,
    VALID_JURISDICTIONS, VALID_COUNTIES, NULL_RATE_THRESHOLD, MAX_ISSUES,
)
from utils import (
    setup_logging, timer, ensure_scratch_gdb, scratch, send_mail,
    get_last_edited_date, get_insert_fields, apply_value_map,
    run_spatial_join, run_identity, collect_join_results,
    get_spatial_relationships, query_service, build_type_coercers,
)

log = logging.getLogger(__name__)


# ── Incremental update check ──────────────────────────────────────────────────

def needs_update():
    """
    Return True if the target table is out of date relative to Parcel Master.
    Defaults to True (run the ETL) when either date cannot be determined.
    """
    pm_date     = get_last_edited_date(PARCEL_MASTER)
    target_date = get_last_edited_date(TARGET_FC)

    if pm_date is None or target_date is None:
        log.info("  Could not compare edit dates — proceeding with full update")
        return True

    log.info(f"  Parcel Master last edited : {pm_date}")
    log.info(f"  Target table last edited  : {target_date}")

    if pm_date > target_date:
        log.info("  Parcel Master is newer — update required")
        return True

    log.info("  Target table is already up to date — skipping ETL")
    return False


# ── Validation ────────────────────────────────────────────────────────────────

def validate_inputs():
    """
    Pre-flight checks before any spatial operations run.
    Raises RuntimeError on failure so the ETL aborts before touching the SDE.
    """
    log.info("--- Pre-flight validation ---")
    issues = []

    if not arcpy.Exists(TARGET_FC):
        issues.append(f"Target table not found: {TARGET_FC}")

    if not arcpy.Exists(PARCEL_MASTER):
        issues.append(f"Parcel master not found: {PARCEL_MASTER}")
    else:
        count = int(arcpy.management.GetCount(PARCEL_MASTER)[0])
        log.info(f"  Parcel master row count: {count:,}")
        if not (PARCEL_COUNT_MIN <= count <= PARCEL_COUNT_MAX):
            issues.append(
                f"Parcel master count {count:,} outside expected range "
                f"[{PARCEL_COUNT_MIN:,} – {PARCEL_COUNT_MAX:,}]"
            )

    missing = []
    for key, (fc_path, *_) in OVERLAYS.items():
        if not arcpy.Exists(fc_path):
            missing.append(f"  {key}: {fc_path}")
    for key, (fc_path, *_) in PROXIMITY_OVERLAYS.items():
        if not arcpy.Exists(fc_path):
            missing.append(f"  {key} (proximity): {fc_path}")
    if missing:
        issues.append("Missing overlay layers:\n" + "\n".join(missing))

    if issues:
        for msg in issues:
            log.error(f"VALIDATION FAIL: {msg}")
        raise RuntimeError(
            f"Pre-flight validation failed with {len(issues)} issue(s) — see log"
        )

    log.info("  Pre-flight validation PASSED")
    return True


def validate_outputs():
    """Post-update quality checks on the target SDE table."""
    log.info("--- Post-update validation ---")
    passed = True

    read_fields       = [JOIN_KEY] + REQUIRED_FIELDS + ["COUNTY"]
    total             = 0
    null_counts       = {f: 0 for f in REQUIRED_FIELDS}
    bad_jurisdictions = []
    bad_counties      = []
    apn_seen          = {}
    duplicate_apns    = []

    with arcpy.da.SearchCursor(TARGET_FC, read_fields) as cur:
        for i, row in enumerate(cur):
            total        += 1
            apn           = row[0]
            jurisdiction  = row[read_fields.index("JURISDICTION")]
            county        = row[read_fields.index("COUNTY")]

            for j, field in enumerate(REQUIRED_FIELDS):
                val = row[j + 1]
                if val is None or str(val).strip() == "":
                    null_counts[field] += 1

            if jurisdiction and jurisdiction not in VALID_JURISDICTIONS:
                if len(bad_jurisdictions) < MAX_ISSUES:
                    bad_jurisdictions.append(f"APN {apn}: '{jurisdiction}'")

            if county and county not in VALID_COUNTIES:
                if len(bad_counties) < MAX_ISSUES:
                    bad_counties.append(f"APN {apn}: '{county}'")

            if apn in apn_seen:
                if len(duplicate_apns) < MAX_ISSUES:
                    duplicate_apns.append(apn)
            else:
                apn_seen[apn] = i

    log.info(f"  Target table row count: {total:,}")

    for field, null_ct in null_counts.items():
        rate   = null_ct / total if total else 0
        status = "WARN" if rate > NULL_RATE_THRESHOLD else "OK"
        log.log(
            logging.WARNING if status == "WARN" else logging.INFO,
            f"  [{status}] {field}: {null_ct:,} nulls ({rate:.1%})"
        )
        if status == "WARN":
            passed = False

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

    if duplicate_apns:
        passed = False
        log.warning(f"  [WARN] Duplicate APNs (first {len(duplicate_apns)}): {duplicate_apns}")
    else:
        log.info("  [OK] No duplicate APNs")

    if passed:
        log.info("  Post-update validation PASSED")
    else:
        log.warning("  Post-update validation completed WITH WARNINGS — review log")

    return passed


# ── ETL steps ─────────────────────────────────────────────────────────────────

@timer
def copy_parcel_master_fields():
    """
    Read PARCEL_MASTER_FIELDS and PARCEL_MASTER_FLAG_FIELDS from Parcel Master.
    Direct-copy fields are passed through as-is; flag fields are run through
    their value_map translation before storing.

    Returns: { apn: {target_field: value, ...} }
    """
    log.info("--- Collecting fields from Parcel Master ---")

    direct_pm  = [pm  for pm, _     in PARCEL_MASTER_FIELDS]
    direct_tgt = [tgt for _, tgt    in PARCEL_MASTER_FIELDS]
    flag_pm    = [pm  for pm, _, _  in PARCEL_MASTER_FLAG_FIELDS]
    flag_tgt   = [tgt for _, tgt, _ in PARCEL_MASTER_FLAG_FIELDS]
    flag_maps  = [vm  for _, _, vm  in PARCEL_MASTER_FLAG_FIELDS]

    # Deduplicate field names while keeping APN at index 0
    all_pm_fields = direct_pm + [f for f in flag_pm if f not in direct_pm]
    idx           = {pm: i for i, pm in enumerate(all_pm_fields)}

    results = {}
    with arcpy.da.SearchCursor(PARCEL_MASTER, all_pm_fields) as cur:
        for row in cur:
            apn = row[0]
            if apn is None:
                continue
            attrs = {tgt: row[idx[pm]] for pm, tgt in zip(direct_pm, direct_tgt)}
            for pm, tgt, vmap in zip(flag_pm, flag_tgt, flag_maps):
                attrs[tgt] = apply_value_map(row[idx[pm]], vmap)
            results[apn] = attrs

    log.info(f"  Read {len(results):,} parcels from Parcel Master "
             f"({len(direct_pm)} direct fields, {len(flag_pm)} flag fields)")
    return results


@timer
def run_scenic_corridor_joins(parcel_fc):
    """
    Populate SCENIC_CORRIDOR, SCENIC_CORRIDOR_RDWY, SCENIC_CORRIDOR_SHORELINE.

    Roadway and Shoreline corridors live in separate map services
    (SCENIC_CORRIDOR_SERVICES).  For each service:
      • get_spatial_relationships determines Within / Intersects / Outside
      • a spatial join reads CORRIDOR_NAME + TYPE for matched parcels

    SCENIC_CORRIDOR is promoted to the most-specific relationship seen
    across both corridor types (Within > Intersects > Outside).

    Returns: { apn: {"SCENIC_CORRIDOR": ..., "SCENIC_CORRIDOR_RDWY": ...,
                     "SCENIC_CORRIDOR_SHORELINE": ...} }
    """
    log.info("--- Processing overlay: scenic_corridor ---")
    results = {}
    _RANK   = {"Within": 2, "Intersects": 1, "Outside": 0}

    for label, svc_url, target_field, category in SCENIC_CORRIDOR_SERVICES:
        log.info(f"  Processing {label} corridors (CATEGORY = '{category}')")

        # Overall proximity uses the full (unfiltered) layer
        prox = get_spatial_relationships(parcel_fc, svc_url)

        # Build CORRIDOR_NAME -> TYPE lookup via REST query.
        # "TYPE" is a SQL reserved word — arcpy.da.SearchCursor silently drops
        # it from both direct and * reads, so we bypass arcpy entirely here.
        type_lookup = {}
        for rec in query_service(svc_url, ["CORRIDOR_NAME", "TYPE"],
                                 where=f"CATEGORY = '{category}'"):
            name = rec.get("CORRIDOR_NAME") or ""
            typ  = rec.get("TYPE") or ""
            if name:
                type_lookup[name.strip()] = typ.strip()
        log.info(f"  TYPE lookup built: {len(type_lookup)} {label} corridors")

        # Name join filters to this corridor category so RDWY/SHORELINE don't bleed
        lyr_name = f"scenic_{label}_lyr"
        arcpy.management.MakeFeatureLayer(svc_url, lyr_name, f"CATEGORY = '{category}'")
        join_fc = run_spatial_join(parcel_fc, lyr_name, f"join_scenic_{label}")
        arcpy.management.Delete(lyr_name)

        with arcpy.da.SearchCursor(join_fc, [JOIN_KEY, "CORRIDOR_NAME", "Join_Count"]) as cur:
            for row in cur:
                apn, corridor_name, join_count = row
                if apn is None:
                    continue
                if apn not in results:
                    results[apn] = {
                        "SCENIC_CORRIDOR":           "Outside",
                        "SCENIC_CORRIDOR_RDWY":      "N/A",
                        "SCENIC_CORRIDOR_SHORELINE": "N/A",
                    }

                rel = prox.get(apn, "Outside")
                if _RANK.get(rel, 0) > _RANK.get(results[apn]["SCENIC_CORRIDOR"], 0):
                    results[apn]["SCENIC_CORRIDOR"] = rel

                if join_count and join_count > 0 and corridor_name:
                    name_part = str(corridor_name).strip()
                    type_part = type_lookup.get(name_part, "")
                    # Omit TYPE when it is absent, empty, or the placeholder "N/A"
                    if type_part and type_part.upper() != "N/A":
                        results[apn][target_field] = f"{name_part} {type_part}"
                    else:
                        results[apn][target_field] = name_part or "N/A"

        matched = sum(1 for v in results.values() if v.get(target_field) != "N/A")
        log.info(f"  {label}: {matched:,} parcels matched a scenic corridor")

    # Ensure every parcel from parcel_fc appears in results
    with arcpy.da.SearchCursor(parcel_fc, [JOIN_KEY]) as cur:
        for row in cur:
            apn = row[0]
            if apn and apn not in results:
                results[apn] = {
                    "SCENIC_CORRIDOR":           "Outside",
                    "SCENIC_CORRIDOR_RDWY":      "N/A",
                    "SCENIC_CORRIDOR_SHORELINE": "N/A",
                }

    log.info(
        f"  Scenic corridor: "
        f"{sum(1 for v in results.values() if v['SCENIC_CORRIDOR'] != 'Outside'):,} "
        f"parcels in at least one corridor"
    )
    return results


@timer
def fetch_lcv_from_service():
    """
    Derive LCV (Yes / No) via APN join against MAP_SERVICES['lcv'].

    Reads all APNs present in the LCV service layer and returns "Yes" for
    each one.  APNs absent from the service are set to "No" in main() after
    the merge step.

    Returns: { apn: {"LCV": "Yes"} }
    """
    log.info("--- Fetching LCV status from service ---")
    lcv_url = MAP_SERVICES["lcv"]
    lcv_results = {}
    try:
        with arcpy.da.SearchCursor(lcv_url, [JOIN_KEY]) as cur:
            for row in cur:
                if row[0]:
                    lcv_results[row[0]] = {"LCV": "Yes"}
        log.info(f"  {len(lcv_results):,} LCV APNs read from service")
    except Exception:
        log.exception("  Failed to read LCV service — LCV field will be null")
    return lcv_results


@timer
def truncate_and_append(all_results):
    """
    Replace the contents of TARGET_FC using a staged bulk append.

    TruncateTable is not supported on versioned tables; DeleteRows is used
    instead.  Row-by-row InsertCursor against a versioned SDE table is slow;
    staging to a local FGDB first and then using Append is significantly faster.

    1. Export the target schema to a staging table in SCRATCH_GDB (zero rows).
    2. InsertCursor into the local staging table (fast, no network overhead).
    3. Build a FieldMappings object that covers only insert_fields, explicitly
       omitting editor-tracking fields so the SDE engine populates them.
    4. DeleteRows + Append inside an edit session so both operations are posted
       as versioned edits.

    all_results: { apn: {target_field: value, ...} }
    """
    insert_fields = get_insert_fields(TARGET_FC)
    coercers      = build_type_coercers(TARGET_FC, insert_fields)
    log.info(f"Delete+append: {len(all_results):,} rows into {len(insert_fields)} fields")
    log.debug(f"  Insert fields: {insert_fields}")

    # ── Stage to local FGDB (fast, no network overhead) ──────────────────────
    staging = scratch("staging_parcel_attrs")
    arcpy.conversion.ExportTable(TARGET_FC, staging, where_clause="1=0")

    inserted = 0
    skipped  = 0
    with arcpy.da.InsertCursor(staging, insert_fields) as cur:
        for apn, attrs in all_results.items():
            if apn is None:
                skipped += 1
                continue
            row = [coerce(attrs.get(f)) for coerce, f in zip(coercers, insert_fields)]
            cur.insertRow(row)
            inserted += 1
    log.info(f"  Staged {inserted:,} rows  |  Skipped {skipped:,} (null APN)")

    # Explicit field mapping — only insert_fields, editor-tracking fields omitted
    # so the SDE geodatabase engine auto-populates them on insert.
    fm = arcpy.FieldMappings()
    for f in insert_fields:
        fmap = arcpy.FieldMap()
        fmap.addInputField(staging, f)
        out_field      = fmap.outputField
        out_field.name = f
        fmap.outputField = out_field
        fm.addFieldMap(fmap)

    # ── Bulk load into SDE inside edit session ────────────────────────────────
    editor = arcpy.da.Editor(COLLECTION_SDE)
    editor.startEditing(False, True)   # no undo, versioned
    editor.startOperation()
    try:
        arcpy.management.DeleteRows(TARGET_FC)
        log.info("  Target table rows deleted")
        arcpy.management.Append(staging, TARGET_FC, "NO_TEST", fm)
        log.info(f"  Appended {inserted:,} rows to target table")
        editor.stopOperation()
        editor.stopEditing(True)
    except Exception:
        editor.stopOperation()
        editor.stopEditing(False)
        log.exception("Edit session rolled back — target table may be empty")
        raise


# ── Main ──────────────────────────────────────────────────────────────────────

@timer
def main():
    setup_logging()
    log.info("=" * 60)
    log.info("Parcel_Attributes_ETL  started")
    log.info("=" * 60)

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = SCRATCH_GDB

    ensure_scratch_gdb()

    # ── Incremental check ─────────────────────────────────────────────────────
    log.info("--- Incremental update check ---")
    if not needs_update():
        log.info("Parcel_Attributes_ETL  finished (no update needed)")
        log.info("=" * 60)
        return

    # ── Pre-flight validation ─────────────────────────────────────────────────
    validate_inputs()

    all_results = {}   # { apn: {target_field: value, ...} }

    def merge(source_dict):
        for apn, attrs in source_dict.items():
            if apn not in all_results:
                all_results[apn] = {}
            all_results[apn].update(attrs)

    # ── Step 1: Direct copy from Parcel Master ────────────────────────────────
    merge(copy_parcel_master_fields())

    # ── Step 2: Attribute-value overlays (extension point — currently empty) ──
    for overlay_key, (overlay_fc, join_type) in OVERLAYS.items():
        log.info(f"--- Processing overlay: {overlay_key} ---")
        try:
            output_name = f"join_{overlay_key}"
            join_fc = (
                run_identity(PARCEL_MASTER, overlay_fc, output_name)
                if join_type == "IDENTITY"
                else run_spatial_join(PARCEL_MASTER, overlay_fc, output_name)
            )
            merge(collect_join_results(join_fc, overlay_key))
        except Exception:
            log.exception(f"Failed on overlay '{overlay_key}' — skipping")

    # ── Step 3: Proximity overlays (Within / Intersects / Outside) ────────────
    for prox_key, (overlay_fc, target_field, attr_field) in PROXIMITY_OVERLAYS.items():
        log.info(f"--- Processing proximity overlay: {prox_key} ---")
        try:
            rel_results = get_spatial_relationships(PARCEL_MASTER, overlay_fc, attr_field)
            merge({apn: {target_field: label} for apn, label in rel_results.items()})
        except Exception:
            log.exception(f"Failed on proximity overlay '{prox_key}' — skipping")

    # ── Step 4: Scenic corridor joins ─────────────────────────────────────────
    try:
        merge(run_scenic_corridor_joins(PARCEL_MASTER))
    except Exception:
        log.exception("Failed on scenic corridor joins — skipping")

    # ── Step 5: LCV status (APN join against Parcel_Joins service) ───────────
    try:
        merge(fetch_lcv_from_service())
        for apn in all_results:
            all_results[apn].setdefault("LCV", "No")
    except Exception:
        log.exception("Failed on LCV join — skipping")

    log.info(f"Total APNs collected across all sources: {len(all_results):,}")

    # ── Truncate + append to SDE ──────────────────────────────────────────────
    # NOTE: TruncateTable is non-recoverable without a version rollback.
    # All spatial joins must complete before this step runs.
    truncate_and_append(all_results)

    # ── Post-update quality checks ────────────────────────────────────────────
    validate_outputs()

    log.info("Parcel_Attributes_ETL  finished")
    log.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
        send_mail("SUCCESS - Parcel attribute ETL completed.")
    except arcpy.ExecuteError:
        log.error(arcpy.GetMessages())
        send_mail("ERROR - ArcPy exception — check log")
        raise
    except Exception:
        log.exception("Unhandled error in Parcel_Attributes_ETL")
        send_mail("ERROR - System error — check log")
        raise
