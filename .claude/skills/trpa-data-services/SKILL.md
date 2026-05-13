---
name: trpa-data-services
description: "How to access TRPA's spatial and tabular data. Covers five systems: maps.trpa.org (on-prem ArcGIS Server, ~120 public REST services), services5.arcgis.com (ArcGIS Online tenant), laketahoeinfo.org/WebServices (LTInfo tabular REST, token-authed), laketahoeinfo.org/Api (LTInfo Accela bridge for nightly-refreshed parcel/permit data), and mapserver.laketahoeinfo.org/geoserver (WFS/WMS). Use whenever pulling Lake Tahoe Basin data — parcels, zoning, EIP projects, scenic resources, vegetation, transportation, BMP status, development rights, deed restrictions, IPES scores, threshold indicators, transit ridership, Accela permits, or any TRPA-curated dataset — even if the user doesn't name the source. Apply for Python ETL, arcpy, Jupyter analysis, HTML dashboards, ArcGIS Pro, or QGIS. Trigger phrases: 'where does this data come from?', 'is there a REST endpoint for X?', 'how do I query the parcels FeatureServer?'"
---

# TRPA ArcGIS & Data Services

TRPA data lives in **five** separate systems. They use different base URLs, different authentication models, and different query syntaxes. This skill is the map of where things live and how to talk to each one.

The five systems:

| System | Base URL | Auth | What's there |
|---|---|---|---|
| **On-prem ArcGIS Server** | `https://maps.trpa.org/server/rest/services/` | Public | The big one — ~120 services. Parcels, zoning, planning, transportation, vegetation, forest health, scenic, soils, watersheds, shoreline, housing, imagery (1940/1969/2015/2018/2019), BMP status, deed restrictions, VHR/STR, demographics. ArcGIS Server 11.5. |
| **ArcGIS Online (AGOL) hosted** | `https://services5.arcgis.com/fXXSUzHD5JjcOt1v/arcgis/rest/services/` | Public or AGOL token | TRPA's ArcGIS Online tenant (`trpa.maps.arcgis.com`). Used for hosted feature services that aren't on the on-prem server — often new, externally-shared, or experimental layers (e.g., proposed threshold zones, wildlife studies). |
| **LTInfo Web Services (tabular)** | `https://www.laketahoeinfo.org/WebServices/` | User-specific token in URL path | EIP project data, performance measures, indicators, expenditures, organizations, land capabilities, IPES scores, development rights, deed restrictions, mooring tags, threshold evaluations, transit ridership, EIP homepage stats. CSV or JSON output. |
| **LTInfo Accela API** | `https://www.laketahoeinfo.org/Api/` | Separate Accela token in URL path | Bridge to Accela permit data. LTInfo pulls from Accela nightly and exposes it as CSV. Reports: Accela Parcels, Accela Record Details, Accela Record Documents. Use this instead of hitting Accela directly. |
| **LTInfo GeoServer (spatial)** | `https://mapserver.laketahoeinfo.org/geoserver/` | Public WFS/WMS | Spatial complement to the LTInfo tabular APIs. WFS for vectors, WMS for raster rendering. Layers: AllParcels, AllStormwaterCatchments, MooringInventoryAndRegistrationStatus, ParcelDevelopmentRightTransfers, Project, TrackedParcels, vEIPProjectLocationDetail, vGeoserverMooring. |

When in doubt: most things go to maps.trpa.org first. AGOL is for newer/externally-shared layers. LTInfo is for project, indicator, and development-right data that lives in the LT Info platform.

## Picking the right system

| You want… | Go to… |
|---|---|
| Parcel geometry / APN lookup | `Parcels/FeatureServer/0` on maps.trpa.org |
| Parcel attributes (jurisdiction, tolerance, county) | `Parcel_Joins/FeatureServer/6` on maps.trpa.org |
| Zoning district, permissible uses | `Zoning/MapServer/{0,6,7}` on maps.trpa.org (see `trpa-zoning-services` skill) |
| EIP project records & accomplishments | `GetProject` / `GetProjects` / `GetReportedProjectAccomplishments` on LTInfo |
| EIP project geometries | `vEIPProjectLocationDetail` (LTInfo GeoServer) **or** `GetProjectDetailedLocationsAsFeatureCollection` (LTInfo tabular, GeoJSON) |
| Development right transactions, banking, pool balances | `GetDevelopmentRightTransactions` / `GetBankedDevelopmentRights` / `GetDevelopmentRightPoolBalanceReport` on LTInfo |
| IPES scores, Land Capability | `GetParcelIPESScores` / `GetParcelsByLandCapability` on LTInfo |
| Threshold evaluations | `GetThresholdEvaluations` on LTInfo |
| Transit monthly ridership | `GetTransitMonitoringData` on LTInfo |
| Forest health, vegetation, scenic, transportation layers | Named services on maps.trpa.org |
| A brand-new feature service published from ArcGIS Pro | The AGOL hosted tenant on services5.arcgis.com |
| Accela permit records, document attachments, parcel-permit roll-up | LTInfo Accela API (`/Api/GetAccela*Csv/`) — refreshed nightly from Accela |

Many questions touch both — e.g., a "deed restriction explorer" wants parcel geometry from maps.trpa.org **and** deed-restriction details from `GetDeedRestrictedParcels` on LTInfo. Knowing both systems exist is the whole point of this skill.

---

## 1. maps.trpa.org — On-prem ArcGIS Server

The main one. Public, no auth required for the vast majority of services. ArcGIS REST API. Browse the full catalog at `https://maps.trpa.org/server/rest/services/`.

### Service & layer URL shape

```
https://maps.trpa.org/server/rest/services/<ServiceName>/<ServiceType>/<LayerID>
```

- `<ServiceType>` is `MapServer` (raster/dynamic image rendering, often the only option) or `FeatureServer` (queryable feature data, supports edits if enabled).
- Many services publish **both** — e.g., `Parcels/MapServer` for dynamic rendering, `Parcels/FeatureServer/0` for queries.

**Rule of thumb:** for any query operation, prefer the `FeatureServer` endpoint. Use `MapServer` only when you want the dynamic tile image (e.g., as a base parcel backdrop in Leaflet/ArcGIS SDK).

### Standard query parameters

The `/query` endpoint accepts these (most common subset):

```
where             SQL-like filter, e.g. APN='034-331-023' or APN IN ('A','B','C')
outFields         Comma-separated field list, * for all
returnGeometry    true | false
outSR             Output spatial reference (e.g., 4326 for WGS84, 26910 for UTM 10N)
f                 Response format: json | geojson | pjson | html
geometry          Geometry to spatial-filter against (point/envelope/polygon as JSON)
geometryType      esriGeometryPoint | esriGeometryEnvelope | esriGeometryPolygon
spatialRel        esriSpatialRelIntersects | esriSpatialRelWithin | …
resultOffset      Skip first N records (pagination)
resultRecordCount Page size (most TRPA services cap at 1000 or 2000)
returnCountOnly   true to get a row count instead of records
```

### Pagination pattern

Almost every query against a TRPA FeatureServer needs pagination — services cap responses at 1,000 or 2,000 records. Both `trpa-data-engineering` and `trpa-dashboard-stack` define this; here's the canonical form.

**JavaScript:**

```javascript
async function queryAll(url, where = '1=1', outFields = '*', returnGeometry = false) {
  const all = [];
  const batchSize = 2000;
  let offset = 0;
  while (true) {
    const params = new URLSearchParams({
      where, outFields,
      returnGeometry: String(returnGeometry),
      f: 'json',
      resultOffset: String(offset),
      resultRecordCount: String(batchSize)
    });
    const r = await fetch(`${url}/query?${params}`);
    const j = await r.json();
    if (!j.features?.length) break;
    all.push(...j.features.map(f => returnGeometry ? f : f.attributes));
    if (j.features.length < batchSize) break;
    offset += batchSize;
  }
  return all;
}
```

**Python:**

```python
import requests

def query_all(url, where="1=1", out_fields="*", return_geometry=False):
    all_rows = []
    offset, batch = 0, 2000
    while True:
        params = {
            "where": where, "outFields": out_fields,
            "returnGeometry": str(return_geometry).lower(),
            "f": "json",
            "resultOffset": offset, "resultRecordCount": batch,
        }
        r = requests.get(f"{url}/query", params=params, timeout=60)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            break
        all_rows.extend(feats if return_geometry else [f["attributes"] for f in feats])
        if len(feats) < batch:
            break
        offset += batch
    return all_rows
```

Skip pagination only when you've already checked `returnCountOnly=true` and confirmed the result is small.

### Spatial query (point-in-polygon)

```javascript
// e.g., find the zoning district at a clicked location
const params = new URLSearchParams({
  geometry: JSON.stringify({ x: lon, y: lat, spatialReference: { wkid: 4326 } }),
  geometryType: 'esriGeometryPoint',
  inSR: '4326',
  spatialRel: 'esriSpatialRelIntersects',
  outFields: 'ZONING_ID,ZONING_DESCRIPTION,PLAN_NAME',
  returnGeometry: 'false',
  f: 'json'
});
const r = await fetch(`https://maps.trpa.org/server/rest/services/Zoning/MapServer/0/query?${params}`);
```

### Key services worth memorizing

For the full catalog, see `references/arcgis-server-catalog.md`. The handful that come up over and over:

| Service / layer | Purpose |
|---|---|
| `Parcels/FeatureServer/0` | Parcel geometry + APN, APO_ADDRESS, JURISDICTION, EXISTING_LANDUSE, OWNERSHIP_TYPE |
| `Parcel_Joins/FeatureServer/6` | Parcel attributes — TOLERANCE_ID, JURISDICTION, etc. (the canonical attributes table) |
| `Zoning/MapServer/0` | Zoning district polygons |
| `Zoning/MapServer/6` | Permissible Use table (joins by ZONING_ID) |
| `Zoning/MapServer/7` | Special Designation table |
| `LocalPlan/MapServer/1` | Adopted plan documents — joins by PLAN_ID, returns FILE_URL |
| `Boundaries/FeatureServer/1` | Town Centers |
| `LTInfo_Monitoring/MapServer/24` | Scenic Viewpoints (display copy of the LTInfo set) |
| `Streams_and_Flood_Zone/MapServer/0` | Flood zone for proximity overlays |
| `Avalanche_Zones/MapServer/0` | Avalanche zones |
| `Shoreline_Resources/MapServer/7` | High Water Line buffer |
| `Historic/MapServer/0` | Historic districts |
| `Scenic_Status/MapServer/{2,3}` | Scenic roadway / scenic shoreline |
| `Housing/MapServer` | Housing-related layers (Tahoe Living) |
| `Deed_Restriction/MapServer` | Deed-restricted parcel geometries |
| `Development_Rights_Transacted_and_Banked/MapServer` | Spatial view of development rights data |
| `Forest_Health_Stand_Density/MapServer` | Forest stand density |
| `Vegetation/*` | Multiple services — burn severity, seral stage, late seral, etc. |
| `Transportation_*` | Transportation planning, SMART, equity tessellation |

For zoning-specific schema and join logic, the `trpa-zoning-services` skill is more detailed.

---

## 2. services5.arcgis.com — ArcGIS Online hosted

TRPA's AGOL tenant lives at `https://trpa.maps.arcgis.com/`. Hosted feature services published from ArcGIS Pro or ArcGIS Online live on Esri's `services5.arcgis.com/fXXSUzHD5JjcOt1v/` infrastructure (the `fXXSUzHD5JjcOt1v` is TRPA's tenant ID; treat it as fixed).

### URL shape

```
https://services5.arcgis.com/fXXSUzHD5JjcOt1v/arcgis/rest/services/<ServiceName>/FeatureServer/<LayerID>
```

Example: `…/Proposed_TRPA_Goshawk_Threshold_Zone/FeatureServer/0`

### Why this exists alongside maps.trpa.org

- New layers can be published without GIS staff provisioning a service on the on-prem server.
- Layers shared with external partners often live here so external auth (AGOL accounts) works cleanly.
- Some experimental, time-limited, or rapidly-iterated layers stay on AGOL.

### Auth

Most are public (anonymous). When a service requires a token, it uses standard ArcGIS Online OAuth/token auth — distinct from the on-prem server. Don't reuse tokens between systems.

### Query syntax

Identical to the on-prem server (same ArcGIS REST API). The pagination and spatial-query patterns from §1 apply unchanged — only the base URL differs.

---

## 3. LTInfo Web Services — tabular REST APIs

Lake Tahoe Info's tabular endpoints. EIP project records, performance measures, organizations, development rights, threshold evaluations, transit ridership — anything that lives in the LT Info platform's database rather than a GIS layer.

### Endpoint pattern

```
https://www.laketahoeinfo.org/WebServices/<ServiceName>/<CSV|JSON>/<token>[/<param>]
```

- The **service name** is a verb-style name like `GetProject`, `GetEIPIndicators`.
- The **return type** is the literal string `CSV` or `JSON` (not a query parameter — it's a path segment).
- The **token** is your personal authorization token, requested from `https://www.laketahoeinfo.org/WebServices/List` while logged in. Tokens are user-scoped so LT Info can notify you about breaking changes.
- Some endpoints take a trailing parameter — a project ID, EIP project number, organization ID, or indicator ID.

**Example (project lookup by EIP project number):**

```
https://www.laketahoeinfo.org/WebServices/GetProject/JSON/{TOKEN}/01.01.01.0001
```

### Token handling — important

The token is a credential. Never commit it to git, never paste it into shared notebooks, never include it in a published HTML page (the URL is visible to the user's browser, and if the page is on GitHub Pages anyone who views source can grab it).

**Store the token in `.env`:**

```
LTINFO_WEBSERVICES_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

(Matches the existing `Permitting/.env.template` convention.)

**Read it in Python:**

```python
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.environ["LTINFO_WEBSERVICES_TOKEN"]

url = f"https://www.laketahoeinfo.org/WebServices/GetProjects/JSON/{TOKEN}"
```

**For browser-side apps**, the token has to be either (a) injected at build time and the resulting page kept private, or (b) proxied through a backend you control. Never embed it in a public GitHub Pages site.

### Catalog of services

The full list, grouped by purpose. All require a token; most have both CSV and JSON outputs. See `references/ltinfo-tabular-catalog.md` for an expanded reference with example URLs.

**Projects**
- `GetProject` — single project by EIP project # or Project ID
- `GetProjects` — all projects
- `GetProjectDescription` — narrative description for a project
- `GetProjectKeyPhoto` — URL to the project's key photo
- `GetProjectOrganizations` — funder / implementer relationships
- `GetProjectExpenditures` — expenditure data
- `GetReportedProjectAccomplishments` — performance measure accomplishments for a project
- `GetProjectsByOrganization` — projects where a given org is funder or implementer
- `GetProjectDetailedLocationsAsFeatureCollection` — GeoJSON FC of detailed project geometries (JSON only)
- `GetProjectSimpleLocationsAsFeatureCollection` — GeoJSON FC of simple point locations (JSON only)
- `GetProjectSimpleLocationAndGeospatialAssociations` — lat/lon + geospatial associations

**Indicators**
- `GetEIPIndicators` — all EIP performance measures, with subcategories
- `GetReportedEIPIndicatorProjectAccomplishments` — accomplishments grouped by a specific indicator ID

**Organizations**
- `GetOrganizations` — all orgs in the LT Info platform

**Parcels & development rights**
- `GetAllParcels` — all parcels, refreshed nightly from Accela
- `GetParcelsByLandCapability` — parcels with Land Capability records
- `GetParcelIPESScores` — IPES scores
- `GetBankedDevelopmentRights`
- `GetTransactedAndBankedDevelopmentRights`
- `GetDevelopmentRightTransactions`
- `GetDevelopmentRightPoolBalanceReport` — pool balances by community/area plan
- `GetDeedRestrictedParcels`
- `GetParcelLandCapabilitiesForAccela` / `GetParcelDevelopmentRightsForAccela` — Accela-system specific variants

**Other**
- `GetAssignedMooringTags`
- `GetEIPHomepageStats`
- `GetTransitMonitoringData`
- `GetThresholdEvaluations`

### CSV vs JSON

- **CSV** is great for one-shot exports into Excel or pandas (`pd.read_csv(url)` works directly).
- **JSON** preserves data types and is required for the FeatureCollection endpoints.

For pandas:

```python
import pandas as pd
df = pd.read_csv(f"https://www.laketahoeinfo.org/WebServices/GetProjects/CSV/{TOKEN}")
```

### SOAP

LTInfo also exposes a SOAP interface, but **per the LT Info documentation it is no longer maintained**. Use REST.

---

## 4. LTInfo Accela API — nightly permit data bridge

TRPA's permit system is **Accela**. The authoritative permit data lives there, but the LTInfo platform pulls a snapshot every night and re-publishes it through a separate API at `laketahoeinfo.org/Api/`. Use the LTInfo bridge — not Accela directly — for most workflows. The bridge is faster, doesn't require Accela auth, and is the source LTInfo uses for its own dashboards.

### Endpoint pattern

```
https://www.laketahoeinfo.org/Api/<ReportName>Csv/<ACCELA_TOKEN>
```

CSV-only (note the `Csv` suffix in the path). Returns the full report; no pagination parameters. (A QA host at `qa.laketahoeinfo.org/Api/` mirrors the same routes if you need a non-production environment, but default to production.)

### The three reports

| Report | Endpoint suffix | What you get |
|---|---|---|
| **Accela Parcel Report** | `GetAccelaParcelsCsv/{TOKEN}` | One row per parcel — APN, owner, address, jurisdiction, plus Accela-side attributes (status, last permit date, etc.) |
| **Accela Record Detail Report** | `GetAccelaRecordDetailsCsv/{TOKEN}` | One row per Accela record (permit, application, inspection, etc.) — IDs, type, status, dates, parcel linkage |
| **Accela Record Document Report** | `GetAccelaRecordDocumentsCsv/{TOKEN}` | One row per document attached to an Accela record — file name, type, upload date, link |

### Token

This is a **separate** credential from the WebServices token. Stored in `.env` as `LTINFO_ACCELA_TOKEN`. Same precautions apply — never commit, never embed in public pages, never log.

```python
import os, pandas as pd
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.environ["LTINFO_ACCELA_TOKEN"]

parcels = pd.read_csv(
    f"https://www.laketahoeinfo.org/Api/GetAccelaParcelsCsv/{TOKEN}",
    dtype={"APN": str}  # always string — Accela parcels include NV APNs with leading zeros
)
```

### When to use Accela API vs WebServices

- **Need permit records, application status, or document links?** → Accela API.
- **Need Land Capability, IPES, or development right records that LT Info has entered manually into Parcel Tracker?** → WebServices (`GetParcelsByLandCapability`, `GetParcelIPESScores`, etc.).
- **Need parcel geometry?** → Neither — go to `Parcels/FeatureServer/0` on maps.trpa.org. The Accela parcel report has APNs and attributes but no geometry.

### Freshness

LTInfo refreshes the Accela snapshot **nightly**. If a permit was issued this morning, it won't appear in the Accela API responses until tomorrow. For real-time needs, hit Accela directly — but that's a different auth path and a much bigger maintenance burden.

---

## 5. LTInfo GeoServer — WFS/WMS spatial

The spatial complement to the LTInfo tabular APIs. Served from GeoServer at `https://mapserver.laketahoeinfo.org/geoserver/`. Public.

### Connecting from desktop GIS

Open the WFS or WMS URL in ArcGIS Pro (Insert → Connections → Server → New WFS / WMS) or QGIS (Add Layer → Add WFS Layer / Add WMS Layer). The browseable preview is at:

```
https://mapserver.laketahoeinfo.org/geoserver/web/wicket/bookmarkable/org.geoserver.web.demo.MapPreviewPage
```

### Layers

| Layer | What it is |
|---|---|
| `AllParcels` | Every parcel in the basin parcel tracker |
| `AllStormwaterCatchments` | All urban catchments in the Stormwater Tools |
| `MooringInventoryAndRegistrationStatus` | Mooring locations with registration status |
| `ParcelDevelopmentRightTransfers` | Parcels involved in development right transfers |
| `Project` | All EIP projects |
| `TrackedParcels` | Tracked parcels |
| `vEIPProjectLocationDetail` | Project location boundaries (detailed geometries) |
| `vGeoserverMooring` | Mooring points associated with Mooring Registration |

### Fetching WFS programmatically

GeoServer WFS returns GeoJSON when asked:

```
https://mapserver.laketahoeinfo.org/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=<layer>&outputFormat=application/json
```

Useful when you want EIP project geometries server-side without the LTInfo token. (The tabular `GetProjectDetailedLocationsAsFeatureCollection` endpoint is the alternative — same data, different access path, requires a token.)

---

## Cross-system patterns

### Tokens & secrets

The LTInfo endpoints (both WebServices and Accela API) are token-protected. The Permitting ETL already establishes the convention — `.env` at the repo root, gitignored, with one variable per token:

```
LTINFO_WEBSERVICES_TOKEN=     # for /WebServices/ tabular endpoints
LTINFO_ACCELA_TOKEN=          # for /Api/GetAccela*Csv/ endpoints
```

These a