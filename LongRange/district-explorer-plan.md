# District Explorer — App Plan

**File:** `LongRange/html/district-explorer.html`
**Purpose:** Answer "Where can I build X?" — explore every zoning district in the Lake Tahoe Basin that permits a given use type.

---

## User Flow

```
[State 1: Category Grid]
  Select a use category (8 options)
        │
        ▼
[State 2: Use Type List]
  Fetch uses for category (paginated)
  Group by Use_Type, count distinct ZONING_IDs
  Sorted by zone count descending
        │
        ▼
[State 3: Map + Sidebar]
  Apply UniqueValueRenderer on districtLayer
  Zoom to extent of matched districts
  Click district → populate detail card
```

Back navigation: ← Use Type list → ← Category grid

---

## Three States

### State 1: Category Grid
- 8 category cards in a responsive grid (auto-fill, 210px min)
- Each card has a brand color (left border + icon background tint)
- No ArcGIS SDK loaded at this stage
- Emil hover lift + scale active on cards

### State 2: Use Type List
- Breadcrumb "← [Category Name]" returns to State 1
- Fetches all uses for the category from `Zoning/MapServer/6` (paginated, 2000/batch)
- Groups rows by `Use_Type`, counts distinct `Zoning_ID` values per use type
- List sorted by zone count (most permissive first)
- Each row shows: use type name, zone count pill, arrow
- Clicking a row transitions to State 3

### State 3: Map + Sidebar
- Layout: 340px sidebar + flex-1 MapView
- ArcGIS MapView initialized lazily (first time State 3 is entered)
- UniqueValueRenderer applied to `districtLayer` with matched districts colored
- Map zooms to extent of all matched districts via `districtLayer.queryExtent()`
- Click a district → sidebar populates with detail card

---

## Category → Color Mapping

| Category | Primary Color | Text Color | Icon |
|----------|--------------|------------|------|
| Residential | `#4A6118` | `#fff` | 🏘 |
| Tourist Accommodation | `#9C3E27` | `#fff` | 🏨 |
| Commercial | `#E87722` | `#fff` | 🏬 |
| Public Services | `#0072CE` | `#fff` | 🏛 |
| Recreation | `#007878` | `#fff` | 🌲 |
| Resource Management | `#B5A64C` | `#003B71` | 🌿 |
| Open Space | `#4a7fa5` | `#fff` | 🏔 |
| General | `#7B6A8A` | `#fff` | 📋 |

---

## UniqueValueRenderer

Matched districts (ZONING_IDs in the selected use type's set) are colored at 55% opacity with a 90% opacity outline. Unmatched districts are grayed to 8% opacity.

```javascript
districtLayer.renderer = {
  type: "unique-value",
  field: "ZONING_ID",
  defaultSymbol: {
    type: "simple-fill",
    color: [200, 200, 200, 0.08],
    outline: { color: [180, 180, 180, 0.2], width: 0.4 }
  },
  uniqueValueInfos: [...zoningIds].map(id => ({
    value: id,
    symbol: {
      type: "simple-fill",
      color: [...rgb, 0.55],
      outline: { color: [...rgb, 0.9], width: 1.4 }
    }
  }))
};
```

---

## District Click Handler

On map click, the district layer is queried at the clicked point (spatial intersect). The returned `ZONING_ID` is checked against the current use type's `zoningIds` set:

- **In set** → show full detail card (name, plan, status badge, density, notes, special designations, action links)
- **Not in set** → show "not permitted" message with district name

Special designations are fetched asynchronously after the card renders (shows "Loading…" then populates).

---

## Caching Strategy

`usesCache` is an object keyed by category name. Each entry is a `Map<useType, { uses[], zoningIds: Set, allowed: number, conditional: number }>`. Navigating back to a previously visited category or use type does not re-fetch from the API.

---

## Key Functions

| Function | Purpose |
|----------|---------|
| `selectCategory(catName)` | Fetch + cache uses for category, render use type list |
| `selectUseType(useType)` | Show map screen, apply renderer, zoom to matched districts |
| `fetchUsesForCategory(cat)` | Paginated query to Zoning/MapServer/6 for the category |
| `groupByUseType(uses)` | Groups raw use rows by Use_Type, counts distinct ZONING_IDs |
| `applyRenderer(catObj, zoningIds)` | Sets UniqueValueRenderer on districtLayer |
| `populateDistrictDetail(attrs, uses, hasUse)` | Renders district detail card in sidebar |
| `fetchSpecDesig(zoningId)` | Returns special designations (called on district click) |
| `fetchPlanDoc(planId)` | Returns FILE_URL from LocalPlan/MapServer/1 |
| `showScreen(name)` | Switches between cat/use/map screens |
| `updateURL(cat, use)` | Updates URL params for deep linking |

---

## Sidebar Detail Card

When a highlighted district is clicked:
1. **District header** — ZONING_DESCRIPTION + ZONING_ID (monospace)
2. **Plan section** — PLAN_NAME, PLAN_TYPE
3. **Use section** (one per row in usesCache for this district) — status badge, density, unit, notes (italic)
4. **Special designations** — chips, fetched async after render
5. **Action links:**
   - Design Guidelines ↗ (if `DESIGN_GUIDELINES_HYPERLINK` non-null)
   - Planning Document ↗ (if `FILE_URL` from LocalPlan join non-null)

When a non-highlighted district is clicked:
- Shows district name + "[Use type] is **not permitted** in this district."

---

## Planning Document Link

Same pattern as parcel-lookup — `PLAN_ID` from `Zoning/MapServer/0` joined to `LocalPlan/MapServer/1` to retrieve `FILE_URL`. The "Planning Document ↗" button is added to the action links div and revealed asynchronously once the URL is confirmed non-null.

---

## URL Deep Linking

`?cat=Commercial&use=Hotel%20%2F%20Motel` restores full state on page load — runs `selectCategory()` then `selectUseType()` on the cached data. Enables bookmarking and sharing specific use type searches.

---

## Known Constraints

- **No AG Grid** — same AMD loader conflict as parcel-lookup; uses no tabular data component
- **Calcite pinned to 2.13.0** — matches ArcGIS SDK 4.31 bundle
- **Paginated fetch required** — `Zoning/MapServer/6` has many records per category; uses 2,000-record batches
- **`districtLayer.queryExtent()`** — used to zoom the map to the matched districts; requires providing the WHERE clause with all matched ZONING_IDs, which can be a long SQL string for categories with many zones
