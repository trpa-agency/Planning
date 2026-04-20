# Parcel Lookup — App Plan

**File:** `LongRange/html/parcel-lookup.html`
**Purpose:** Answer "What can I do on my parcel?" — look up zoning rules for any parcel in the Lake Tahoe Basin by street address or APN.

---

## User Flow

```
[Search Screen]
  Enter address or APN
      │
      ├─ APN detected (regex) ──→ query Parcels/FeatureServer/0 by APN
      └─ Address ──────────────→ World Geocoder → spatial hit-test on parcel layer
                                        │
                              Parcel found?
                                   │
                    ┌──────────────┴───────────────┐
                   YES                             NO
                    │                               │
           [Results Screen]                  Inline error on search screen
            Map + sidebar + bottom panel
```

---

## Two States

### State 1: Search Screen
- Centered card layout, no map loaded
- Single text input accepts both addresses and APNs
- APN regex: `/^\d{2,3}[-\s]\d{3}[-\s]\d{2}/`
- Address geocoder bias: `location=-120.04,39.09&distance=75000`
- URL param `?q=` pre-fills and auto-runs search on page load

### State 2: Results Screen
- **Header:** "← New Search" button resets to search state
- **Left sidebar (380px):** Calcite panels — Parcel card, Zoning card, Legend, Layer List
- **Map:** ArcGIS MapView with zoning districts, parcel display layer, highlight graphics layer
- **Bottom panel:** Drag-resizable, shows special designations + permissible uses table

---

## Lazy Map Initialization

The ArcGIS MapView is **not created on page load** — only after a successful search completes and the results screen is displayed. The `parcelQueryLayer` (a FeatureLayer pointing to `Parcels/FeatureServer/0`) works without a MapView for query-only operations.

This avoids loading the ArcGIS rendering pipeline during the search screen, improving perceived performance.

---

## Service Calls (per search)

| Step | Service | Operation |
|------|---------|-----------|
| 1 | `Parcels/FeatureServer/0` | Get parcel geometry by APN or spatial hit-test |
| 2 | `Parcel_Joins/FeatureServer/6` | Get APN, TOLERANCE_ID, JURISDICTION |
| 3 | `Zoning/MapServer/0` | Get district attributes including PLAN_ID |
| 4 | `Zoning/MapServer/6` | Get all permissible uses for ZONING_ID |
| 5 | `Zoning/MapServer/7` | Get special designations for ZONING_ID |
| 6 | `LocalPlan/MapServer/1` | Get FILE_URL for planning document PDF (via PLAN_ID) |

Steps 4, 5, and 6 run in parallel via `Promise.all`.

---

## Key Functions

| Function | Purpose |
|----------|---------|
| `handleSearch()` | Entry point — detects APN vs address, runs appropriate lookup |
| `getParcelByAPN(apn)` | Queries `Parcels/FeatureServer/0` WHERE APN = value |
| `getParcelByAddress(address)` | Geocodes address, then spatial intersect on parcel layer |
| `initMap()` | Creates MapView, layers, widgets (called lazily on first search) |
| `fetchParcelAttrs(apn)` | Returns TOLERANCE_ID, JURISDICTION from Parcel_Joins |
| `fetchPermUses(zoningId)` | Returns all permissible uses for a zoning district |
| `fetchSpecDesig(zoningId)` | Returns special designations |
| `fetchPlanDoc(planId)` | Returns FILE_URL from LocalPlan/MapServer/1 |
| `populatePanel(...)` | Populates sidebar cards and bottom panel from all fetched data |
| `buildTable(data)` | Renders permissible uses HTML table with status badges |
| `exportCSV(data)` | Downloads uses table as CSV |
| `highlightParcel(feature)` | Adds orange highlight graphic over selected parcel |

---

## Sidebar Panels

### Parcel Card
- APN
- Jurisdiction
- Tolerance District (badge)

### Zoning Card
- Zone description + Zoning ID
- Plan Name + Plan Type
- Special Area Name + Overlay
- Action links:
  - **Design Guidelines** (if `DESIGN_GUIDELINES_HYPERLINK` non-null)
  - **Planning Document** (if `FILE_URL` from LocalPlan join non-null)
  - **LTInfo Details** (always shown — links to `parcels.laketahoeinfo.org`)

---

## Bottom Panel — Permissible Uses

- Drag handle (5px strip) for resizing
- Status filter pills: All / Allowed / Requires Approval / See Note
- Sortable columns (click header)
- Export CSV button
- Status badge color coding:
  - Allowed → forest green
  - Conditional Use / Administrative Review → amber/earth
  - See Note → purple

---

## Planning Document Link

`Zoning/MapServer/0` returns a `PLAN_ID` field. This is joined to `LocalPlan/MapServer/1`:

```javascript
async function fetchPlanDoc(planId) {
  const params = new URLSearchParams({
    where: `PLAN_ID = '${planId.replace(/'/g, "''")}'`,
    outFields: "PLAN_ID,FILE_URL",
    returnGeometry: "false", f: "json"
  });
  const resp = await fetch(`${SVC.local_plan}/query?${params}`);
  const json = await resp.json();
  return json.features?.[0]?.attributes?.FILE_URL ?? null;
}
```

The "Planning Document ↗" button is hidden when `FILE_URL` is null.

---

## Known Constraints

- **No AG Grid** — ArcGIS AMD loader hijacks UMD bundles; uses vanilla `<table>` for permissible uses
- **Calcite pinned to 2.13.0** — matches the version bundled with ArcGIS SDK 4.31
- **`parcelQueryLayer` stays hidden** — `Zoning/MapServer/1` is display-only; actual geometry queries use `Parcels/FeatureServer/0` as a hidden FeatureLayer
