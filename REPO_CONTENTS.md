# Planning Repo — Contents

A TRPA-owned collection of Python scripts and single-page web apps for land-use planning work in the Lake Tahoe Basin. The HTML apps are designed to be served as static pages (GitHub Pages compatible). The Python scripts run inside TRPA's `arcgispro-py3` environment against ArcGIS Server and SDE.

License: MIT (Tahoe Regional Planning Agency, 2026).

## Top-level layout

| Path | Purpose |
|------|---------|
| `README.md` | One-line project description |
| `LICENSE` | MIT license |
| `.gitignore` | Standard Python ignores |
| `.vscode/` | VS Code workspace settings |
| `.claude/skills/trpa-eip-brand/logos/` | TRPA + EIP program logo assets (PNG) used when building branded outputs |
| `LongRange/` | Public-facing zoning + land-use explorer web apps |
| `Permitting/` | Internal parcel-attributes ETL and parcel/zoning viewers |

---

## `LongRange/` — Public zoning explorer

A multi-page web application that answers two core land-use questions: *"What can I do on my parcel?"* and *"Where can I build X?"* Built as single-file HTML pages (no build tools, CDN-only) using the Calcite Design System 2.13.0, ArcGIS Maps SDK 4.31, and vanilla JavaScript. All spatial data is pulled live from `https://maps.trpa.org/server/rest/services/`.

### HTML apps (`LongRange/html/`)

| File | Purpose |
|------|---------|
| `index.html` | Landing page — two-card entry point to the two main tools (TRPA-branded, Open Sans, navy header) |
| `parcel-lookup.html` | Address or APN → zoning district, tolerance district, jurisdiction, special designations, full permissible-uses table. Two-state UI (search → results with map + sidebar + drag-resizable bottom panel). Lazy MapView init, deep linking via `?q=`. |
| `district-explorer.html` | Category → Use Type → Map. Three-state UI (8-category grid → grouped use-type list with zone counts → map view with `UniqueValueRenderer` highlighting matched districts). Deep links via `?cat=…&use=…`. |
| `deed-restriction-explorer.html` | Deed Restriction Explorer (single-file viewer) |
| `CCCB_EIS_Webmap_8.html` | CCCB EIS Cumulative Projects — Visual Analysis Map (one-off web map supporting the EIS) |

### Plan / reference docs

| File | Purpose |
|------|---------|
| `README.md` | App overview, local serve command (`python -m http.server 8766 --directory LongRange/html`), tech stack, deep-link examples |
| `layers.md` | Reference of every ArcGIS REST layer the apps consume — service, layer index, key fields, and which app uses it. Also documents the Esri World Geocoder bias toward Tahoe (`-120.04, 39.09`). |
| `parcel-lookup-plan.md` | Architecture/spec for `parcel-lookup.html` — user flow, two states, service-call sequence, function inventory, panel layouts, constraints (no AG Grid due to ArcGIS AMD loader conflict, Calcite pinned to 2.13.0). |
| `district-explorer-plan.md` | Architecture/spec for `district-explorer.html` — three-state flow, category color mapping, `UniqueValueRenderer` setup, click handler logic, caching strategy. |
| `skills.md` | Inventory of design-engineering skills installed under `.agents/skills/` (Emil, Impeccable, Stitch, etc.) used during front-end development. |
| `data/`, `scripts/` | Currently empty placeholders |

---

## `Permitting/` — Parcel attributes ETL + viewers

Server-side data engineering plus internal-facing parcel and zoning viewers.

### Python scripts (`Permitting/scripts/`)

| File | Purpose |
|------|---------|
| `Parcel_Attributes_ETL.py` | Updates `SDE.Parcel_Permit_Review_Attributes` by combining (1) direct field copies from Parcel Master, (2) proximity overlays for flood zone, avalanche, HWL buffer, and historic district, (3) scenic-corridor name+type joins for roadway and shoreline, and (4) LCV Yes/No from the Parcel_Joins service. Incremental — compares `last_edited_date` and skips when target is current. Runs in `arcpy`. |
| `utils.py` | ETL helpers — logging setup, timers, scratch GDB management, spatial-join / identity runners, value-map application, type coercion, email notifications. |
| `data_engineering.ipynb` | Notebook for ad-hoc analysis and prototyping ETL logic before promoting to the main script. |

### Configuration

| File | Purpose |
|------|---------|
| `config.py` | All ETL constants — REST service URLs (Parcels, Flood Zone, Avalanche, HWL Buffer, Historic, Scenic Roadway/Shoreline, LCV), target SDE feature class, field mappings, validation thresholds. Loads secrets from `.env`. |
| `.env.template` | Template for required environment variables — GIS paths, SDE/SQL Server credentials, Box API, LTInfo tokens (Accela + Web Services), SMTP/email settings. |

### HTML apps (`Permitting/html/`)

| File | Purpose |
|------|---------|
| `parcel-viewer.html` | 2D Parcel Map Viewer (TRPA) |
| `parcel-viewer-3D.html` | 2D / 3D Parcel Map Viewer with scene toggle |
| `zoning-lookup.html` | Zoning Lookup tool (internal-facing variant) |

---

## Tech stack at a glance

The browser-side apps all share the same shell: Calcite Design System 2.13.0 + ArcGIS Maps SDK 4.31 (pinned together to avoid version drift) + Open Sans + vanilla JS, served as static HTML. The Python side is `arcpy` / `arcgispro-py3` with secrets via `python-dotenv`, writing to enterprise SDE via an `.sde` connection file.

## Data sources

Every app and script pulls from TRPA ArcGIS Server at `https://maps.trpa.org/server/rest/services/`. The key services in use are `Parcels/FeatureServer`, `Parcel_Joins/FeatureServer`, `Zoning/MapServer`, `LocalPlan/MapServer`, `Streams_and_Flood_Zone/MapServer`, `Avalanche_Zones/MapServer`, `Shoreline_Resources/MapServer`, `Historic/MapServer`, and `Scenic_Status/MapServer`. Geocoding uses Esri's World Geocoder biased to the Tahoe Basin.
