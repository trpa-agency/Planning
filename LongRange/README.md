# LongRange — TRPA Zoning Explorer

A public-facing, multi-page web application that answers two core questions about land use in the Lake Tahoe Basin. Built as single-file HTML pages (no build tools, CDN only) using Calcite Design System, ArcGIS Maps SDK 4.31, and vanilla JavaScript.

## Apps

| App | Local URL | Description |
|-----|-----------|-------------|
| Landing Page | http://localhost:8766/index.html | Two-card entry point linking to both tools |
| Parcel Lookup | http://localhost:8766/parcel-lookup.html | Enter an address or APN to see zoning district, permissible uses, and special designations for any parcel |
| District Explorer | http://localhost:8766/district-explorer.html | Select a use category and type to see every zoning district in the Basin where that use is permitted |

## Serving locally

```bash
python -m http.server 8766 --directory LongRange/html
```

Or use the launch configuration in `.claude/launch.json` (server name: `longrange`, port 8766).

## Tech stack

- **Calcite Design System 2.13.0** — UI shell, panels, loaders, notices
- **ArcGIS Maps SDK 4.31** — MapView, FeatureLayer, UniqueValueRenderer, widgets
- **Open Sans** — Typography (Google Fonts)
- All data from TRPA ArcGIS REST services at `https://maps.trpa.org/server/rest/services/`

## Deep links

Both tools support URL parameters for sharing specific results:

- Parcel Lookup: `parcel-lookup.html?q=031-102-09` or `parcel-lookup.html?q=128+Market+St`
- District Explorer: `district-explorer.html?cat=Commercial&use=Hotel%20%2F%20Motel`
