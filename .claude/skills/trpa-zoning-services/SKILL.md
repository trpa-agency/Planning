---
name: trpa-zoning-services
description: "TRPA zoning and permissible use data services. Use this skill whenever querying zoning districts, permitted uses, tolerance districts, special designations, or parcel attributes for any Lake Tahoe Basin parcel. Covers REST endpoints, field schemas, join logic, and query patterns for Zoning/MapServer, Planning/FeatureServer, Parcels/FeatureServer, and Parcel_Joins/FeatureServer."
---

# TRPA Zoning Services

All zoning and permissible use data for the Lake Tahoe Basin is served from `https://maps.trpa.org/server/rest/services/`. This skill documents the key services, their layer schemas, and how to join them together.

---

## Core Services for Zoning Lookup

### Join Key

**`ZONING_ID`** (string, e.g. `"MAP_1"`, `"TP_1"`) is the primary join key across all zoning-related layers and tables.

```
Zoning District (geometry) ──ZONING_ID──► Permissible Use (table)
                            ──ZONING_ID──► Special Designation (table)
Parcels (geometry) ──APN──► Parcel Attributes (table) → TOLERANCE_ID, JURISDICTION
```

---

### 1. Zoning District — Polygon layer

**Endpoint:** `https://maps.trpa.org/server/rest/services/Zoning/MapServer/0`

Use for: spatial lookup (point-in-polygon) to find a parcel's zoning district.

| Field | Type | Notes |
|-------|------|-------|
| ZONING_ID | String | Join key — e.g. `"MAP_1"`, `"TP_1"` |
| ZONING_DESCRIPTION | String | Human-readable zone name — e.g. `"Multi-Use Area Plan"` |
| PLAN_ID | String | Plan identifier |
| PLAN_NAME | String | e.g. `"Meyers Area Plan"` |
| PLAN_TYPE | String | e.g. `"Area Plan"`, `"Community Plan"` |
| SPECIAL_AREA_NAME | String | Special area within the plan, if applicable |
| SPECIAL_AREA_NUMBER | String | Number for special area |
| OVERLAY | String | Overlay designation, if applicable |
| ACRES | Double | District polygon area in acres |
| DESIGN_GUIDELINES_HYPERLINK | String | URL to design guidelines PDF — render as a link when populated |

**Sample spatial query (point-in-polygon):**
```javascript
const q = zoningLayer.createQuery();
q.geometry           = clickPoint;            // esri/geometry/Point from map click
q.spatialRelationship = "intersects";
q.outFields          = ["ZONING_ID","ZONING_DESCRIPTION","PLAN_NAME","PLAN_TYPE",
                        "SPECIAL_AREA_NAME","OVERLAY","DESIGN_GUIDELINES_HYPERLINK"];
q.returnGeometry     = false;
const result = await zoningLayer.queryFeatures(q);
const district = result.features[0]?.attributes;
```

---

### 2. Permissible Use — Table (no geometry)

**Endpoint:** `https://maps.trpa.org/server/rest/services/Zoning/MapServer/6`

Use for: listing all land uses allowed (or not) in a given zoning district.

| Field | Type | Notes |
|-------|------|-------|
| Zoning_ID | String | Foreign key → matches `ZONING_ID` in District layer |
| Category | String | Use category — e.g. `"Residential"`, `"Commercial"`, `"Tourist Accommodation"` |
| Subcategory | String | Sub-grouping within category |
| Use_Type | String | Specific use — e.g. `"Multiple Family Dwelling"`, `"Hotel/Motel"` |
| Use_Status | String | `"Allowed"`, `"Conditional Use"`, or `"Not Permitted"` |
| Density | Integer | Density value (numeric) |
| Unit | String | Density unit — e.g. `"units/acre"`, `"persons/acre"` |
| Notes | String | Additional conditions or notes |
| Zoning_Description | String | Denormalized from District (for standalone queries) |
| Plan_Name | String | Denormalized from District |
| Plan_Type | String | Denormalized from District |

**Sample query:**
```javascript
const params = new URLSearchParams({
  where: `Zoning_ID = '${zoningId.replace(/'/g, "''")}'`,
  outFields: 'Category,Subcategory,Use_Type,Use_Status,Density,Unit,Notes',
  f: 'json'
});
const resp = await fetch(
  `https://maps.trpa.org/server/rest/services/Zoning/MapServer/6/query?${params}`
);
const json = await resp.json();
const uses = json.features.map(f => f.attributes);
```

**Use_Status values and display colors:**
- `"Allowed"` → green (`#4A6118`)
- `"Conditional Use"` → amber (`#B47E00`)
- `"Not Permitted"` → red (`#9C3E27`)

---

### 3. Special Designation — Table (no geometry)

**Endpoint:** `https://maps.trpa.org/server/rest/services/Zoning/MapServer/7`

Use for: overlay restrictions or special designations applied to a zoning district.

| Field | Type | Notes |
|-------|------|-------|
| ZONING_ID | String | Foreign key |
| ZONING_DESCRIPTION | String | Denormalized zone name |
| PLAN_TYPE | String | Denormalized plan type |
| SPECIAL_DESIGNATION | String | e.g. `"Town Center"`, `"Scenic Restoration Area"` |
| NOTES | String | Additional notes |

**Sample query:**
```javascript
const params = new URLSearchParams({
  where: `ZONING_ID = '${zoningId.replace(/'/g, "''")}'`,
  outFields: 'SPECIAL_DESIGNATION,NOTES',
  f: 'json'
});
const resp = await fetch(
  `https://maps.trpa.org/server/rest/services/Zoning/MapServer/7/query?${params}`
);
const json = await resp.json();
const designations = json.features.map(f => f.attributes);
```

---

### 4. Parcels — Polygon layer (within Zoning service)

**Endpoint:** `https://maps.trpa.org/server/rest/services/Zoning/MapServer/1`

Use for: map display, spatial highlight, and APN lookup by click point. This parcel layer is co-served with the zoning service and should be used (not `Parcels/FeatureServer/0`) in zoning-related apps.

Key fields: `APN` (plus any additional parcel attributes published in the service)

**Sample spatial query:**
```javascript
const q = parcelLayer.createQuery();
q.geometry            = clickPoint;
q.spatialRelationship = "intersects";
q.outFields           = ["APN"];
q.returnGeometry      = true;
q.outSpatialReference = view.spatialReference;
q.num                 = 1;
const result = await parcelLayer.queryFeatures(q);
const parcel = result.features[0];
```

---

### 5. Parcel Permit Review Attributes — Table

**Endpoint:** `https://maps.trpa.org/server/rest/services/Parcel_Joins/FeatureServer/6`

Use for: retrieving TOLERANCE_ID, JURISDICTION, and other permit-relevant attributes by APN.

Key fields: `APN`, `TOLERANCE_ID`, `JURISDICTION`, `ZONING_ID`, `ZONING_DESCRIPTION`

**Sample query:**
```javascript
const params = new URLSearchParams({
  where: `APN = '${apn.replace(/'/g, "''")}'`,
  outFields: 'APN,TOLERANCE_ID,JURISDICTION,ZONING_ID,ZONING_DESCRIPTION',
  returnGeometry: false,
  f: 'json'
});
const resp = await fetch(
  `https://maps.trpa.org/server/rest/services/Parcel_Joins/FeatureServer/6/query?${params}`
);
const json = await resp.json();
const attrs = json.features[0]?.attributes;
```

---

## Additional Useful Services

| Service | Endpoint | Key Layers |
|---------|----------|-----------|
| Planning Districts | `Planning/FeatureServer/1` | Same schema as Zoning/MapServer/0 |
| Planning Permissible Use | `Planning/FeatureServer/7` | Same schema as Zoning/MapServer/6 |
| Development Potential | `Development_Potential/MapServer` | Layers 0–14: residential/commercial allowed |
| Special Designations (polygons) | `Special_Designation/MapServer` | 10 layers by designation type |
| All Parcels (historical) | `AllParcels/MapServer` | Layers by year back to 2006 |
| Land Capability | `Soils_and_Land_Capability/MapServer` | Layers 3–6: LC by methodology |

---

## Complete Zoning Lookup Query Flow

```javascript
async function lookupZoning(clickPoint, apn) {
  // Run all queries in parallel
  const [districtResult, parcelAttrResult] = await Promise.all([
    // 1. Zoning district by location
    zoningLayer.queryFeatures({
      geometry: clickPoint,
      spatialRelationship: "intersects",
      outFields: ["ZONING_ID","ZONING_DESCRIPTION","PLAN_NAME","PLAN_TYPE",
                  "SPECIAL_AREA_NAME","OVERLAY","DESIGN_GUIDELINES_HYPERLINK"],
      returnGeometry: false
    }),
    // 2. Parcel attributes by APN
    fetch(`${PARCEL_JOINS_URL}/query?${new URLSearchParams({
      where: `APN = '${apn}'`,
      outFields: 'APN,TOLERANCE_ID,JURISDICTION',
      returnGeometry: false, f: 'json'
    })}`).then(r => r.json())
  ]);

  const district = districtResult.features[0]?.attributes;
  if (!district) return null;

  const zoningId = district.ZONING_ID;

  // Run uses + designations lookups in parallel
  const [usesResp, desigResp] = await Promise.all([
    fetch(`${PERM_USE_URL}/query?${new URLSearchParams({
      where: `Zoning_ID = '${zoningId}'`,
      outFields: 'Category,Subcategory,Use_Type,Use_Status,Density,Unit,Notes',
      f: 'json'
    })}`).then(r => r.json()),
    fetch(`${SPEC_DESIG_URL}/query?${new URLSearchParams({
      where: `ZONING_ID = '${zoningId}'`,
      outFields: 'SPECIAL_DESIGNATION,NOTES',
      f: 'json'
    })}`).then(r => r.json())
  ]);

  return {
    district,
    parcelAttrs: parcelAttrResult.features[0]?.attributes ?? {},
    permissibleUses: usesResp.features.map(f => f.attributes),
    specialDesignations: desigResp.features.map(f => f.attributes)
  };
}
```

---

## Notes

- **MapServer vs FeatureServer:** MapServer/6 and MapServer/7 are tables (no geometry) — query them with `fetch()` directly rather than creating a FeatureLayer. FeatureServer layers support `FeatureLayer.queryFeatures()`.
- **ZONING_ID case:** The field is `ZONING_ID` (uppercase) in District and Special Designation; it is `Zoning_ID` (mixed case) in the Permissible Use table. Use the correct casing in WHERE clauses.
- **No domain constraints:** All string fields in these services are free-form — no coded value domains are defined. Filter and display values as returned.
- **Authentication:** Most of these services are publicly accessible without a token. Some services (e.g. ZoningDistrict edit endpoints) require authentication.
