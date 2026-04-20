# ArcGIS Layers

All spatial data is served from TRPA ArcGIS Server at `https://maps.trpa.org/server/rest/services/`.

## Layer Reference

| Layer | Service | Index | Key Fields | Used By |
|-------|---------|-------|------------|---------|
| Zoning Districts | `Zoning/MapServer` | 0 | `ZONING_ID`, `ZONING_DESCRIPTION`, `PLAN_NAME`, `PLAN_TYPE`, `PLAN_ID`, `SPECIAL_AREA_NAME`, `OVERLAY`, `DESIGN_GUIDELINES_HYPERLINK` | parcel-lookup, district-explorer |
| Zoning Parcels (display) | `Zoning/MapServer` | 1 | — | parcel-lookup (map display only) |
| Permissible Use | `Zoning/MapServer` | 6 | `Zoning_ID`, `Category`, `Use_Type`, `Use_Status`, `Density`, `Unit`, `Notes` | parcel-lookup, district-explorer |
| Special Designation | `Zoning/MapServer` | 7 | `ZONING_ID`, `SPECIAL_DESIGNATION`, `NOTES` | parcel-lookup, district-explorer |
| Parcels (geometry) | `Parcels/FeatureServer` | 0 | `APN` | parcel-lookup (spatial query + highlight) |
| Parcel Attributes | `Parcel_Joins/FeatureServer` | 6 | `APN`, `TOLERANCE_ID`, `JURISDICTION` | parcel-lookup |
| Local Plan | `LocalPlan/MapServer` | 1 | `PLAN_ID`, `FILE_URL` | parcel-lookup, district-explorer |

## External Services

| Service | Provider | URL | Purpose |
|---------|----------|-----|---------|
| World Geocoder | Esri | `https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates` | Address-to-coordinate lookup, biased to Tahoe Basin (`location=-120.04,39.09&distance=75000`) |

## Notes

- `Zoning/MapServer/1` (Zoning Parcels) is display-only — geometry queries must use `Parcels/FeatureServer/0`.
- `LocalPlan/MapServer/1` is queried by `PLAN_ID` (obtained from `Zoning/MapServer/0`) to retrieve `FILE_URL`, a hyperlink to the adopted planning document PDF.
- Permissible Use queries are paginated (2,000 records per batch) to handle categories with large record counts.
- All services use `f=json` REST format with `returnGeometry=false` except where geometry is required.
