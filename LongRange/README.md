# LongRange — TRPA Zoning Explorer

A public-facing, multi-page web application that answers two core questions about land use in the Lake Tahoe Basin. Built as single-file HTML pages (no build tools, CDN only) using Calcite Design System, ArcGIS Maps SDK 4.31, and vanilla JavaScript.

## Apps

| App | Local URL | Description |
|-----|-----------|-------------|
| Landing Page | http://localhost:8766/html/index.html | Card-based entry point linking to every tool |
| Parcel Lookup | http://localhost:8766/html/parcel-lookup.html | Enter an address or APN to see zoning district, permissible uses, and special designations for any parcel |
| District Explorer | http://localhost:8766/html/district-explorer.html | Select a use category and type to see every zoning district in the Basin where that use is permitted |
| Deed Restriction Explorer | http://localhost:8766/html/deed-restriction-explorer.html | Map and grid of deed-restricted parcels with filters and CSV export |
| Housing Progress Since 2012 | http://localhost:8766/html/multifamily-housing.html | Tahoe Living-branded housing dashboard: multifamily, deed-restricted, ADU, and pipeline units by jurisdiction, timeline, featured projects, map, and table. Joins the spreadsheet-derived records in `data/multifamily_parcels.js` live to `Parcels/FeatureServer/0` (address, zoning, centroid) and `VHR/MapServer/0` (VHR Yes/No). |

## Serving locally

Serve from the `LongRange` folder (not `LongRange/html`) so pages can reach `../data/`:

```bash
python -m http.server 8766 --directory LongRange
```

Or use the launch configuration in `.claude/launch.json` (server name: `longrange-html`, port 8766). Pages are then at `http://localhost:8766/html/<page>.html`.

## Reviewing the housing dashboard wording

`docs/housing-dashboard-text.md` lists every piece of text on the housing dashboard with a
stable ID (T01–T116). Share it with reviewers, who fill in a `New:` line under anything they
want reworded and send it back. The IDs map each change to its place in the page.

## Refreshing the housing data

The housing dashboard reads `data/multifamily_parcels.js`, generated from the "Aff and WF parcels" spreadsheet. To refresh after a new spreadsheet arrives (run in `arcgispro-py3`):

```bash
python LongRange/scripts/build_multifamily_data.py "C:/path/to/Aff and WF parcels.xlsx"
```

Expected columns: `APN`, `Jurisdiction`, `Units`, `Year Built`, `COUNTY_LANDUSE_DESCRIPTION`, `Affordable and Workforce`, `Timing`, `Type`, `Project Notes`. Featured project cards are configured in the `FEATURED_PROJECTS` list near the top of the page script (add a photo URL and blurb per APN). If a spreadsheet APN has been retired or renumbered, add it to `APN_REMAP` in the build script rather than editing the spreadsheet.

## Tech stack

- **Calcite Design System 2.13.0** — UI shell, panels, loaders, notices
- **ArcGIS Maps SDK 4.31** — MapView, FeatureLayer, UniqueValueRenderer, widgets
- **Open Sans** — Typography (Google Fonts)
- All data from TRPA ArcGIS REST services at `https://maps.trpa.org/server/rest/services/`

## Deep links

Both tools support URL parameters for sharing specific results:

- Parcel Lookup: `parcel-lookup.html?q=031-102-09` or `parcel-lookup.html?q=128+Market+St`
- District Explorer: `district-explorer.html?cat=Commercial&use=Hotel%20%2F%20Motel`
