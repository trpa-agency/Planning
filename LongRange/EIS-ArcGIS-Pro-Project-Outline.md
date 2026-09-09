# TRPA EIS — Catch-All ArcGIS Pro Project Outline

Architecture for a single reusable Pro project that produces the full EIS figure set. Companion to
[EIS-Map-List.md](EIS-Map-List.md) (what figures to make); this file is *how the project is built*.

Version 0.1 — 2026-08-17. First application: Housing EIS.

---

## 1. The core idea

**Do not build one layout per figure.** ~75 figures as 75 layouts is what makes an APRX slow,
inconsistent, and unmaintainable, and it guarantees the north-shore inset drifts 200 m between
Figure 3.4-3 and Figure 3.15-2.

Instead:

```
  15 Maps  ×  8 Layouts  ×  a recipe table  →  75+ figures
```

- A **Map** is a category's *entire* symbolized layer stack, grouped, mostly switched off.
- A **Layout** is a *sheet format* — size, frame arrangement, marginalia. Topic-agnostic.
- A **recipe row** names one figure: which map, which layout, which extent, which layer groups on.
- An **arcpy script** walks the recipes and exports. Nothing is positioned by hand twice.

This is what makes "with and without Area-Wide Stormwater Systems" a two-row change in a CSV
instead of two hand-built layouts that will not register with each other.

Revision to my earlier advice: I'd said one APRX per chapter. That's right only under the
layout-per-figure model. Under the recipe model, **one catch-all APRX** is correct and better —
15 maps and 8 layouts is well inside Pro's comfortable range. The one exception is confidential
cultural resources, which stays in a separate project for access-control reasons, not performance.

---

## 2. Disk layout

```
EIS_Housing_2026\
├── TRPA_EIS.aprx                  # the catch-all project
├── TRPA_EIS_Confidential.aprx     # cultural / sensitive species — restricted share
├── data\
│   ├── EIS_Working.gdb            # all analysis outputs, derived layers
│   ├── EIS_Source.gdb             # snapshotted copies of external + REST data
│   └── raster\                    # WHP, hillshade, imagery
├── layers\                        # .lyrx library — one per recurring layer
├── styles\
│   └── TRPA_EIS.stylx             # single shared style
├── layouts\                       # .pagx templates (also live in the APRX)
├── recipes\
│   └── figure_recipes.csv         # the figure manifest
├── scripts\
│   ├── export_figures.py
│   └── snapshot_sources.py        # pull REST layers → EIS_Source.gdb, dated
├── output\
│   ├── admin_draft\
│   ├── public_draft\
│   └── final\
└── docs\
    └── data_sources.csv           # feeds EIS Appendix A
```

**Snapshot everything.** Do not point layouts at live REST services. TRPA services get republished
mid-project and your Draft EIS figure will not match your Final EIS figure with no record of why.
`snapshot_sources.py` copies each service to `EIS_Source.gdb` with a date-stamped name, and that
snapshot date is what goes in the source credit line and in `data_sources.csv`.

---

## 3. Maps (data frames)

All maps: **NAD 1983 UTM Zone 10N (EPSG:26910)**. Each carries the same `_BASE` group at the bottom
so every figure has an identical foundation.

### M00 — shared groups present in every map

| Group | Contents |
|---|---|
| `_BASE_Reference` | TRPA boundary, CA/NV state line, county lines, City of SLT, Lake Tahoe fill, major streams |
| `_BASE_Transport` | US 50, SR 28/89/267/207, arterials, collectors — single neutral gray hierarchy |
| `_BASE_Labels` | Community labels, water body labels, highway shields |
| `_BASE_Terrain` | `Tahoe_Hillshade_Cached` at 30% |

Build once as `.lyrx` files in `layers\_base\`, then drop into each map. Editing the base group
means editing four files, not fifteen maps.

### Category maps

| Map | Serves EIS sections | Primary services (maps.trpa.org unless noted) |
|---|---|---|
| **M01_Location_Jurisdiction** | 1.0-1 … 1.0-5 | `Boundaries/FeatureServer` (0–16), `Ownership/MapServer/0` |
| **M02_LandUse_Zoning** | 3.1, and the PD/alternatives figures | `Zoning/MapServer/{0,1}`, `Boundaries/FeatureServer/1` (Centers), `Planning/FeatureServer/{0,2,3,4,13}`, `LocalPlan/MapServer`, `Special_Designation`, `Existing_Land_Use` |
| **M03_Housing_Demographics** | 3.2, 3.17 | `Housing/MapServer/0–8`, `Deed_Restriction`, `VHR`, `Short_Term_Rental_Density`, `AccessoryDwellingUnit_Density`, `Demographics/MapServer/{1,2,3,19,27,30}`, `Development_Rights_Transacted_and_Banked`, `Existing_Development/MapServer/2` |
| **M04_LandCapability_Soils** | 3.3 | `Soils_and_Land_Capability/MapServer/0–6`, `Slope_Class_Cached`, `Slope_Class_30_50_Cached`, `Impervious_Surface_2019`, `Impervious_Surface_2010`, `Impervious_Surface_Change_2010_to_2019`, `Avalanche_Zones`, `SEZ_Assessment_Unit` |
| **M05_Hydro_WaterQuality** | 3.4, and the Geo/Land impervious figure | `Streams_and_Flood_Zone/MapServer/{0,1,2}`, `Catchments/MapServer/0`, `BMP_Status/MapServer/{2,6}`, `Watershed_Erosion_Prediction_Project_Tahoe_Basin`, `Shoreline_Resources` |
| **M06_Vegetation_Forest** | 3.6 | `Vegetation_Type`, `Vegetation_Seral_Stage`, `Vegetation_Late_Seral`, `Vegetation_Burn_Severity`, `Forest_Health_Stand_Density`, `Forest_Health_Composition_Age`, `Large_Trees_Reference` |
| **M07_Wildlife_Fisheries** | 3.7, 3.8 | `Wildlife_Habitat/MapServer/{0,1,2,3,4,5,45}`, `Wildlife_Activity`, `Fish_Habitat/MapServer/{0,1}`, `eDNA_Samples` |
| **M08_Scenic** | 3.9 | `Scenic_Status/MapServer/{2,3}`, `LTInfo_Monitoring/MapServer/24` |
| **M09_Recreation** | 3.10 | `Recreation/MapServer/0–4`, `ReferenceTrails`, `Trails_Strategy`, `Ownership`, `Parking_Lots` |
| **M10_Transportation** | 3.12 | `Transportation`, `Transportation_Planning`, `Transportation_SMART`, `Housing/MapServer/{3,4}` (transit), `Transportation_Equity_Analysis_Tessellation` |
| **M11_Services_Utilities** | 3.13 | `Boundaries/FeatureServer/{5,6,11}`, `Emergency_Services`, `Demographics/MapServer/7` (school districts) |
| **M12_Hazards_Wildfire** | 3.15 | `Fire/MapServer/{3,6,9,10}`, `Streams_and_Flood_Zone/MapServer/0` + **external**: CAL FIRE FHSZ, WHP raster, CWPP WUI, EnviroStor, GeoTracker, NDEP |
| **M13_AirQuality_Noise** | 3.5, 3.11 | `LTInfo_Monitoring`, modeled contours from consultants, `Boundaries/FeatureServer/1` CNEL field |
| **M14_Cumulative** | Ch. 4 | `vEIPProjectLocationDetail` (LTInfo GeoServer), `LTInfo_Spatial`, pending amendments |
| **M15_Alternatives** | Ch. 2 + PD figures | Single alternatives feature class with an `ALT_ID` field, driven by definition query |
| **M90_Locator** | inset frame in every layout | Basin outline + CA/NV + Sacramento/Reno context. One tiny map, referenced by every layout's second frame. |
| **M99_Confidential** | 3.14 | Separate APRX. Archaeological sensitivity, CNDDB/NNHP occurrences. |

### M15 — how alternatives work

Do **not** make one feature class per alternative. Make one:

```
EIS_Working.gdb\Alternatives_LandUse
  ALT_ID     text   'NP' | 'A1' | 'A2' | 'A3'
  ALT_NAME   text
  ... attributes ...
```

One map, one definition query (`ALT_ID = 'A1'`), swapped by the export script per recipe row.
Identical symbology across alternatives is then structural, not a discipline problem — which is the
whole reason reviewers can actually compare the sheets.

---

## 4. Layouts (sheet formats, not topics)

Eight templates cover the entire document. Every one uses **dynamic text** for figure number,
title, source line, and date so nothing is retyped.

| Layout | Size / orientation | Frames | Used for |
|---|---|---|---|
| **L01_Ltr_Port** | 8.5×11 portrait | 1 main + locator | Default. Most Ch. 3 figures. |
| **L02_Ltr_Land** | 11×8.5 landscape | 1 main + locator | Basin-wide where portrait wastes space |
| **L03_Tab_Land** | 17×11 landscape | 1 main + locator | Basin-wide foldouts: land capability, zoning, alternatives |
| **L04_Tab_NorthSouth** | 17×11 landscape | 2 main (North Shore / South Shore) + locator | **The workhorse for the current ESA request** — one sheet, both shores, shared legend |
| **L05_Ltr_2Panel** | 8.5×11 portrait | 2 stacked + shared legend | With/without overlay comparisons on one sheet |
| **L06_Tab_4Panel** | 17×11 landscape | 4 equal + shared legend | Alternatives small-multiples |
| **L07_Ltr_MapTable** | 8.5×11 portrait | 1 map (upper 60%) + table frame | Threshold status, acreage summaries |
| **L08_Tab_WideLegend** | 17×11 landscape | 1 main + tall right legend column | Long legends: zoning districts, land capability, soils |

**Marginalia block** — build once as a grouped graphic element, paste into all eight:
north arrow · dual scale bar (mi + km) · figure number (dynamic) · title (dynamic) · source line
(dynamic) · date (dynamic) · TRPA logo · sheet n of m.

**Layouts are not bound to maps.** A layout's map frame gets its map reassigned at export time by
the script. That's what lets L01 serve forty different figures.

---

## 5. Bookmarks (extent registry)

Create these once in each map, with **identical names across all maps**. The script sets extent by
bookmark name, so a name mismatch is the one thing that will silently break registration.

| Bookmark | Extent |
|---|---|
| `BASIN` | Full TRPA boundary + 1 mi buffer |
| `NORTH` | North/West shore — Tahoe City through Incline Village |
| `SOUTH` | South shore — Meyers through Zephyr Cove |
| `EAST` | East shore — Glenbrook through Spooner |
| `WEST` | West shore — Emerald Bay through Tahoma |
| `CTR_<name>` | One per Center, for detail insets |

Set these from a fixed scale (e.g. NORTH and SOUTH both at 1:75,000) rather than by eye, so the two
frames on L04 are the same scale and the sheet reads honestly.

---

## 6. The figure recipe table

`recipes\figure_recipes.csv` — the manifest that turns 15 maps into 75 figures. One row per exported
figure.

| Column | Meaning |
|---|---|
| `fig_num` | `3.4-3` |
| `fig_title` | Full title as it appears in the text |
| `map_name` | Which Map in the APRX |
| `layout_name` | Which Layout |
| `frame1_bookmark` | Extent for main frame |
| `frame2_bookmark` | Extent for second frame (L04/L05/L06 only) |
| `layers_on` | Semicolon-delimited group/layer names to switch on |
| `def_query` | Optional, e.g. `ALT_ID = 'A1'` |
| `source_text` | Source credit line for this figure |
| `out_name` | `Fig_3.4-3_Flood-Zones` |
| `dpi` | Default 300 |
| `status` | `todo` / `draft` / `qa` / `final` |

Worked example — the with/without stormwater pairs become two rows that cannot drift apart:

```csv
fig_num,map_name,layout_name,frame1_bookmark,layers_on,def_query,out_name
2.0-1a,M15_Alternatives,L04_Tab_NorthSouth,NORTH,Centers;Zoning;BonusUnitBoundary,ALT_ID = 'NP',Fig_2.0-1a_NoProject
2.0-1b,M15_Alternatives,L04_Tab_NorthSouth,NORTH,Centers;Zoning;BonusUnitBoundary;AreaWideTreatments,ALT_ID = 'NP',Fig_2.0-1b_NoProject_AWT
```

The recipe table is also your production tracker, your figure list for the EIS table of contents,
and — with `source_text` — the raw material for Appendix A. Keep it in git.

---

## 7. Export script

`scripts\export_figures.py`. Run inside `arcgispro-py3`.

```python
"""Export EIS figures from figure_recipes.csv against TRPA_EIS.aprx."""
import csv
import logging
from pathlib import Path

import arcpy

PROJ = Path(r"C:\...\EIS_Housing_2026")
APRX = PROJ / "TRPA_EIS.aprx"
RECIPES = PROJ / "recipes" / "figure_recipes.csv"
OUT = PROJ / "output" / "admin_draft"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def set_layer_visibility(m, on_names):
    """Switch on only the named groups/layers; everything non-_BASE off."""
    wanted = {n.strip().lower() for n in on_names if n.strip()}
    for lyr in m.listLayers():
        if lyr.name.startswith("_BASE"):
            continue
        lyr.visible = lyr.name.lower() in wanted


def apply_def_query(m, query):
    for lyr in m.listLayers():
        if lyr.supports("DEFINITIONQUERY") and lyr.visible:
            lyr.definitionQuery = query or ""


def zoom_to_bookmark(frame, m, bookmark_name):
    if not bookmark_name:
        return
    bm = next((b for b in m.listBookmarks() if b.name == bookmark_name), None)
    if bm is None:
        raise ValueError(f"bookmark '{bookmark_name}' not found in map '{m.name}'")
    frame.zoomToBookmark(bm)


def export(row, aprx):
    m = aprx.listMaps(row["map_name"])[0]
    layout = aprx.listLayouts(row["layout_name"])[0]

    set_layer_visibility(m, row["layers_on"].split(";"))
    apply_def_query(m, row.get("def_query"))

    frames = layout.listElements("MAPFRAME_ELEMENT")
    main = next(f for f in frames if f.name == "MainFrame")
    main.map = m
    zoom_to_bookmark(main, m, row["frame1_bookmark"])

    second = next((f for f in frames if f.name == "SecondFrame"), None)
    if second and row.get("frame2_bookmark"):
        second.map = m
        zoom_to_bookmark(second, m, row["frame2_bookmark"])

    for el in layout.listElements("TEXT_ELEMENT"):
        if el.name == "FigNum":
            el.text = f"Figure {row['fig_num']}"
        elif el.name == "FigTitle":
            el.text = row["fig_title"]
        elif el.name == "SourceLine":
            el.text = row["source_text"]

    out_pdf = OUT / f"{row['out_name']}.pdf"
    layout.exportToPDF(
        str(out_pdf),
        resolution=int(row.get("dpi") or 300),
        image_quality="BEST",
        embed_fonts=True,
        georef_info=False,          # public copy: no georeference leakage
        layers_attributes="NONE",   # flatten — no extractable layer structure
        output_as_image=False,      # keep vector
    )
    log.info("exported %s", out_pdf.name)


def main():
    aprx = arcpy.mp.ArcGISProject(str(APRX))
    OUT.mkdir(parents=True, exist_ok=True)
    with open(RECIPES, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["status"] != "hold"]
    for row in rows:
        try:
            export(row, aprx)
        except Exception:
            log.exception("FAILED %s", row["fig_num"])
    log.info("done: %d figures", len(rows))


if __name__ == "__main__":
    main()
```

Requirements this imposes on the layouts — enforce them when you build the eight templates:

- Main map frame named exactly `MainFrame`; second frame `SecondFrame`.
- Text elements named `FigNum`, `FigTitle`, `SourceLine`.
- Legend set to **show only visible layers** (Legend properties → uncheck "Show unpaired layers"),
  so toggling groups updates the legend automatically. Without this, every recipe row needs a
  hand-edited legend and the whole approach collapses.

---

## 8. Symbology library

One `.lyrx` per recurring layer in `layers\`, one shared `TRPA_EIS.stylx`. Non-negotiable rules:

- Land capability (Bailey 1a–7) and zoning get **one** ramp each, defined once, used everywhere.
- Every polygon fill also carries a hatch, pattern, or clearly distinct value — grayscale proof
  every figure.
- Overlays that must let underlying color show through (`Area Wide Treatments`, WUI, flood zones)
  use a **line-fill symbol layer at 45°, 5 pt separation, 0.5 pt stroke, plus a 1 pt solid
  outline** — not a transparent solid fill. Transparent solid fills mud the colors underneath and
  reproduce badly in print; hatch survives photocopying.
- Keep hatch spacing ≥ 4 pt. Finer than that moirés at 300 dpi.

---

## 9. Data gaps to resolve before the build

Confirmed against `maps.trpa.org` today:

| Need | Status |
|---|---|
| TRPA fish habitat in Lake Tahoe | **Have it** — `Fish_Habitat/MapServer/1` |
| Sierra Nevada yellow-legged frog critical habitat | **Have it** — `Wildlife_Habitat/MapServer/4` (plus `/5` suitable habitat). No need to source from ESA. |
| Area-wide stormwater systems | **Have it** — `BMP_Status/MapServer/6` "Area Wide Treatments" |
| Impervious surfaces | **Have it** — `Impervious_Surface_2019/MapServer/0`, plus 2010 and 2010→2019 change |
| Flood zones, 100- and 500-year | **Have it** — `Streams_and_Flood_Zone/MapServer/0`; has `FLOOD_ZONE`, `ZONE_SUBTYPE`, `FLOOD_YEAR` |
| Recreation resources | **Have it** — `Recreation/MapServer/0–4` + `Ownership/MapServer/0` for State Parks |
| Residential Bonus Unit Boundary | **Have it** — `Housing/MapServer/8` |
| Centers | **Have it** — `Boundaries/FeatureServer/1`, `Description` field = `Town Center District` / `Casino Core District` / `Regional Overlay District`. ⚠ Contains a duplicate Stateline/Ski Run polygon (OBJECTID 19 and 418, both District 46) — dedupe before any acreage table. |
| **CAL FIRE Fire Hazard Severity Zones** | **Not on the TRPA server.** External — CAL FIRE FRAP. CA side only; note the 2025 LRA update vs. the older SRA vintage and pick one deliberately. |
| **Wildfire Hazard Potential** | **Not on the TRPA server.** External raster — USFS WHP / WRAP. Bi-state, which is why it matters: FHSZ leaves the entire Nevada third of the basin blank. |
| **WUI (2025 CWPP)** | **Not on the TRPA server.** Request the GIS layer from Tahoe RCD / Tahoe Fire & Fuels Team. Do not digitize from the PDF. |
| **EnviroStor / GeoTracker / NDEP** | External. Filter to open/active cases and clip to basin; positional accuracy is poor, label "approximate." |

The three wildfire layers are the critical path — they're the only items with an external dependency
and a request-and-wait cycle. Start those emails before building anything else.

---

## 10. Build order

1. Snapshot script + `EIS_Source.gdb` — get the data local and dated.
2. `_BASE` layer group (four `.lyrx` files) and `TRPA_EIS.stylx`.
3. `M90_Locator` and `L01_Ltr_Port` — prove the marginalia block and dynamic text end to end.
4. `L04_Tab_NorthSouth` — needed for the live request.
5. Bookmarks in every map, set from fixed scales.
6. `M02`, `M03`, `M15` — the PD/alternatives figures on the critical path.
7. `export_figures.py` against three recipe rows. Do not build the remaining maps until the script
   round-trips cleanly, or you'll build fifteen maps against assumptions the script doesn't hold.
8. Remaining category maps, in EIS chapter order.
9. Fire out the three wildfire data requests **now**, in parallel with all of the above.
