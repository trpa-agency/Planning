# Methods: CCCB EIS Cumulative Projects — Visual Analysis Webmap

**Files:**

- `LongRange/html/CCCB_EIS_Webmap_trpabrand.html` — TRPA agency brand (institutional Navy + TRPA Blue, Open Sans)
- `LongRange/html/CCCB_EIS_Webmap_tahoelivingbrand.html` — Tahoe Living brand (warm cream + sage/terracotta/pine, Montserrat)

Both files share identical data sources, layer logic, and Arcade expressions. Only the visual identity differs — pick the brand variant appropriate to where the map will be embedded.

**Owner:** jstock@trpa.gov
**Last reviewed:** 2026-05-12

## Purpose

A single-file web map supporting the visual analysis section of the CCCB EIS. It overlays the cumulative project parcels (filtered by a hand-curated APN list) and the EIS focal scenic viewpoints against the basin's town centers and full parcel layer so reviewers can see at a glance which parcels are in scope and which viewpoints they relate to.

## Tech stack

Single-file HTML, CDN-only. Built per `trpa-dashboard-stack`:

- **Calcite Design System 5.0** — UI shell, loader
- **ArcGIS Maps SDK for JavaScript 4.31** — map, feature layers, renderers, popups, widgets
- **Open Sans** — TRPA web typography
- **TRPA brand palette** (`trpa-brand`) — Navy header, TRPA Blue town centers, Brick scenic-focal viewpoints, Orange highlighted parcels

No Plotly or AG Grid are loaded — this is a map viewer with no charts or tabular displays.

## Data sources

| Source | Service | Layer | Purpose | Notes |
|---|---|---|---|---|
| Parcel basemap | `Parcels/MapServer` | 0 | Subtle backdrop showing all parcels | MapImageLayer, 40 percent sublayer opacity |
| Town Centers | `Boundaries/FeatureServer` | 1 | Town center polygons | Fields: `Name`, `Jurisdiction`, `District_Number`, `Land_Use`, `Acres` |
| Scenic Viewpoints | `LTInfo_Monitoring/MapServer` | 24 | Scenic viewpoint points | Field `id` (lowercase) keys EIS focal vs. other via Arcade |
| Highlighted parcels | `Parcels/FeatureServer` | 0 | The CCCB EIS cumulative project parcels | Filtered by `definitionExpression: APN IN (...)` |

All services are hosted at `https://maps.trpa.org/server/rest/services/`.

## Processing steps

This is a viewer, not a pipeline — all processing happens client-side at page load:

1. **Map init** — load `topo-vector` basemap, set view to CCCB project area (`[-119.98, 38.96]`, zoom 12).
2. **Layer construction** — build four layers with brand-aligned renderers and popup templates.
3. **APN filter** — assemble the highlighted APN list into a SQL `IN (...)` clause and apply it as a `definitionExpression` on the Parcels FeatureLayer. The server returns only the matching parcels.
4. **Scenic viewpoint classification** — an Arcade expression on `vpLayer.renderer.valueExpression` reads `$feature.id` (falling back to `$feature.ID`) and returns `"EIS focal"` or `"Other"`. This collapses what would otherwise be one legend entry per viewpoint into two clean categories.
5. **Widgets** — Home, ScaleBar (dual units), LayerList in the side panel, Legend in a top-right Expand.

## Key assumptions

- The highlighted APN list is canonical for the CCCB EIS Visual Analysis tab — these are the cumulative project parcels. If the EIS scope changes, the `HIGHLIGHTED_APNS` array in the script must be updated.
- The EIS focal scenic viewpoints (`36.1`, `32.3`, `20.2`, `22.3`, `35.1`, all `-roadway`) are the five viewpoints the EIS visual analysis evaluates from. Other viewpoints are shown for context but not weighted.
- `Parcels/FeatureServer/0` uses uppercase `APN` for the field name. APN values are strings with embedded hyphens (e.g. `034-331-023`) and occasionally a different format (e.g. `1318-27-001-010` for Carson City).
- `LTInfo_Monitoring/MapServer/24` uses lowercase `id`. The Arcade expression also checks uppercase `ID` defensively in case the service is republished with a different case convention.

## Known caveats

- **Mixed APN formats.** El Dorado / Placer / Washoe APNs use the `NNN-NNN-NNN` pattern; Carson City APNs (`1318-27-001-010`) use a longer format. The SQL `IN (...)` clause handles both transparently, but any new APNs must keep their source-system formatting.
- **APN list scale.** The current list is ~30 APNs. If this list grows beyond a few hundred, the `IN (...)` clause will hit the service's SQL length limits. At that point switch to a client-side approach: query a wider extent and filter in JavaScript using a `Set`, or post the APN list to a hosted feature service that supports `relatedQuery`.
- **Scenic viewpoint field naming.** The source service has historically inconsistent casing. The Arcade expression handles both `id` and `ID`. If the service returns a totally different field name in the future (e.g. `VIEWPOINT_ID`), the expression needs updating.
- **No data refresh schedule on the viewer.** The map fetches live on page load. If TRPA staff edits a parcel or a viewpoint, the change appears on the next page load. There is no caching layer.
- **Renderer accessibility.** Brick (#9C3E27) and Purple (#7B6A8A) have ~3:1 contrast against the topo basemap, which is below WCAG AAA for small graphics. Acceptable for a map but flag if accessibility review surfaces it.

## Downstream consumers

- CCCB EIS Visual Analysis project team — internal review of cumulative project parcels and scenic viewpoint overlay.
- May be linked from a public EIS document appendix; if so, also verify the page works without TRPA VPN (the REST services are public, so this should be fine).

## Editing checklist

When updating the highlighted APN list or the EIS focal viewpoints:

1. Edit the `HIGHLIGHTED_APNS` array (parcels) or `EIS_VP_IDS` array (viewpoints) in the `<script>` block.
2. Update the legend wording in the side panel if the focal viewpoint IDs change so the static legend stays in sync.
3. Update this document's "Key assumptions" section if the meaning of "EIS focal" shifts.
4. Open the page locally (`python -m http.server 8766 --directory LongRange/html`) and confirm: highlighted parcels render orange, EIS viewpoints render brick at size 12, others render purple at size 7, and popups populate for each layer.

## Changelog

### 2026-05-12

- Renamed files: `_8.html` → `_trpabrand.html`, `_9.html` → `_tahoelivingbrand.html`. Turned off service-defined labels on the Town Centers layer in both variants (`labelsVisible: false`).
- Added a second brand variant: `CCCB_EIS_Webmap_tahoelivingbrand.html` applies the Tahoe Living brand (sage/forest/terracotta/pine on cream, Montserrat, TRPA logo moved to footer per TL co-branding rules, scenic-focal viewpoints in Pine, cumulative-project parcels in Terracotta). Same data sources and Arcade logic as the agency variant.
- Rewrote the viewer onto the TRPA dashboard stack (ArcGIS Maps SDK 4.31 + Calcite 5.0 + Open Sans), replacing the previous Leaflet + Esri Leaflet implementation. Applied TRPA brand palette: Navy header, Blue town centers, Brick EIS-focal viewpoints, Orange highlighted parcels.

### Initial build

- Leaflet + Esri Leaflet implementation with the same four data sources.
