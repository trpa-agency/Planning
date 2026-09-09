# TRPA EIS — Standard Print Map (Figure) Set

A reusable figure list for any TRPA Environmental Impact Statement, built to satisfy the union of
TRPA Compact Article VII / Rules of Procedure Ch. 5 (IEC + EIS), CEQA Appendix G, and NEPA
40 CFR 1502. First application: **Housing EIS**.

Status: draft template. Version 0.1 — 2026-08-17.

---

## 0. Scope note before you build anything

TRPA's EIS is a **Compact Article VII** document, not a NEPA document. NEPA only attaches if a
federal agency (realistically LTBMU, FHWA, or HUD) is lead or cooperating. CEQA only attaches if a
California state or local agency is a lead or responsible agency for a component of the action. For
a Housing EIS driven by TRPA Code and Regional Plan amendments, TRPA is almost certainly the sole
lead, and strictly you owe the IEC topic list plus the nine threshold categories.

Building the full union set anyway is cheap insurance — it costs maybe 8–10 extra figures, and it
means the same APRX and layout templates carry forward if a federal or CEQA nexus shows up later
(or when El Dorado County / City of South Lake Tahoe tier off the document). That is the assumption
this list is built on. If you want to trim, the **Tier** column tells you what to cut first.

**Tier key**

| Tier | Meaning |
|---|---|
| **C** | Core — build for every EIS regardless of topic |
| **H** | Housing-specific — build for this EIS, may not recur |
| **T** | Trigger-based — build only if the action affects that resource |
| **X** | Confidential / not for publication in the public document |

---

## 1. Production standards (set once, reuse forever)

### Sheet and layout

| Item | Standard |
|---|---|
| Primary sheet | 8.5 × 11 in **portrait**, 0.75 in margins, figure occupies ~6.5 × 7.5 in |
| Basin-wide sheet | 11 × 17 in **landscape** foldout — use for anything that must show the whole basin at readable detail |
| Basin-wide scale | ~1:250,000 on letter, ~1:150,000 on tabloid |
| Corridor / community inset | 1:24,000 or 1:12,000 |
| Locator inset | Required on every map that is not basin-wide |
| Figure numbering | `Figure <chapter>.<section>-<n>` — e.g. `Figure 3.4-2` |
| File naming | `Fig_3.4-2_Land-Capability.pdf` (chapter-sorted in Explorer) |

### Coordinate system

Project everything to **NAD 1983 UTM Zone 10N (EPSG:26910)**. The basin spans CA and NV, so
StatePlane forces a zone choice and a seam. Web services from `maps.trpa.org` and AGOL arrive in
Web Mercator (3857) — set the Map's coordinate system to 26910 and let Pro reproject on the fly for
display, but **export any analysis feature class to 26910 before measuring area or distance**.
Acreage tables in an EIS get audited; Web Mercator acreage will not survive that.

### Symbology and color

- Use the TRPA palette as the base: blue `#0072CE`, navy `#003B71`, orange `#E87722`,
  forest `#4A6118`, earth `#B47E00`, brick `#9C3E27`, ice `#B4CBE8`.
- **Every fill must also carry a hatch, pattern, or distinct value.** A large share of EIS copies
  are printed or photocopied in grayscale, and the administrative record copy usually is. Run a
  grayscale proof on every figure before sign-off.
- Check every categorical ramp for deuteranopia/protanopia legibility. Land capability (7 classes)
  and zoning (many classes) are the two that fail most often.
- Consistent across all figures: lake fill one blue, TRPA boundary one heavy dashed line,
  hillshade at 25–35% under everything, roads a single neutral gray hierarchy.
- Minimum type size **8 pt**, target 10 pt. Labels below 8 pt do not survive PDF downsampling by
  a print shop.

### Every figure must carry

North arrow · scale bar (with both miles and kilometers) · legend · figure number and title ·
source and date credit line · TRPA logo · sheet number if part of a series.

Source line format:
`Source: TRPA GIS, 2026; USDA NRCS SSURGO, 2024; FEMA NFHL, 2024. Map prepared <Month Year>.`

Use **dynamic text** for figure number, title, and date so a chapter renumber does not become a
manual edit across 55 layouts.

### Export

- PDF, **300 dpi**, vector output where possible, **embed all fonts**.
- Turn **off** "Export map georeference information" and "Export layers as PDF layers" for the
  public document — reviewers should not be able to pull confidential geometry out of a figure.
  Keep a separate layered export for internal use.
- RGB for the digital/web posting; ask the print vendor whether they want CMYK before the offset run.
- If NEPA applies, the PDF must be **Section 508 accessible** — tagged, with alt text on each figure.
  Write the alt text as you build each map, not at the end.

### ArcGIS Pro organization

- **One APRX per chapter**, not one for the whole document. A 55-layout APRX gets slow and
  corrupts more readily.
- One shared `.stylx` with all EIS symbology; one shared layout template (`.pagx`) per sheet size.
- Keep all analysis outputs in a single project file geodatabase with a fixed naming convention;
  the EIS appendix has to describe methods, and a clean GDB is the fastest way to write that.
- Use **Map Series** (spatial) for anything that repeats by Area Plan or by alternative — do not
  hand-build 12 near-identical layouts.
- Layer files (`.lyrx`) for every recurring layer so land capability looks identical in Ch. 3.3
  and Ch. 4.

---

## 2. Chapter 1 — Introduction and Project Description

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 1.0-1 | Regional Location / Vicinity | C | Lake Tahoe Basin, CA/NV state line, US 50 / SR 28 / SR 89 / I-80, Sacramento–Reno context | TRPA `Boundaries` |
| 1.0-2 | TRPA Planning Area Boundary | C | TRPA regional boundary, basin hydrologic boundary, county lines, City of South Lake Tahoe | TRPA `Boundaries` |
| 1.0-3 | Jurisdictions | C | El Dorado, Placer, Washoe, Douglas, Carson City, City of SLT | TRPA `Boundaries` |
| 1.0-4 | Land Ownership | C | USFS LTBMU, CA State Parks, NV State Parks, CTC, NDSL, local government, private | TRPA + LTBMU |
| 1.0-5 | Project Area / Area of Analysis | C | Whatever the action geographically covers; for a program-level Housing EIS this is basin-wide with centers highlighted | derived |

---

## 3. Chapter 2 — Alternatives

| # | Figure | Tier | Key layers | Notes |
|---|---|---|---|---|
| 2.0-1 | Existing Conditions / No Project | C | Current zoning + adopted development right allocations | The baseline every other alternative is read against |
| 2.0-2..n | **One map per action alternative** | C | Where growth/density/height is directed under that alternative | Use a Map Series driven by an `ALT_ID` field so all alternatives share identical symbology and extent — reviewers compare these side by side |
| 2.0-x | Alternatives Comparison (small multiples) | C | 3–4 panels on one tabloid sheet | Highest-value single figure in the document for a hearing |
| 2.0-y | Alternatives Considered but Eliminated | T | Only if a spatially distinct alternative was dropped | |

---

## 4. Chapter 3 — Affected Environment / Environmental Consequences

Chapter numbering below follows a combined TRPA-threshold + CEQA Appendix G order. Adjust to match
whatever outline the EIS consultant lands on, but keep the *set* intact.

### 3.1 Land Use and Planning

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.1-1 | Existing Land Use | C | `EXISTING_LANDUSE` by parcel | `Parcels/FeatureServer/0` |
| 3.1-2 | TRPA Zoning Districts | C | Zoning district polygons | `Zoning/MapServer/0` |
| 3.1-3 | Plan Areas and Area Plans | C | Adopted Area Plans, remaining Plan Area Statements, Community Plans | `LocalPlan/MapServer` |
| 3.1-4 | Town Centers and Regional Centers | C | Center boundaries, High Density Tourist Districts | `Boundaries/FeatureServer/1` |
| 3.1-5 | Parcel Ownership Pattern / Subdivision | H | Parcel size classes, public vs. private | `Parcels/FeatureServer/0` |
| 3.1-6 | Special Designations Overlay | T | Special Designation table joined to zoning | `Zoning/MapServer/7` |

### 3.2 Population, Employment, and Housing *(the analytical heart of a Housing EIS)*

| # | Figure | Tier | Key layers | Source / notes |
|---|---|---|---|---|
| 3.2-1 | Existing Residential Units by Parcel | H | Residential unit count / density | TRPA residential units dataset |
| 3.2-2 | Housing Density (units/acre) | H | Dot density or graduated by block group | Census + parcel |
| 3.2-3 | Deed-Restricted Affordable & Moderate Housing | H | Deed-restricted parcels by restriction type | `Deed_Restriction/MapServer`; `GetDeedRestrictedParcels` (LTInfo) |
| 3.2-4 | Vacation Home Rentals / STRs | H | VHR permits by parcel, concentration by neighborhood | TRPA VHR service — **verify current layer name** |
| 3.2-5 | Vacant and Underutilized Residential Parcels | H | Vacant residentially-zoned, improvement-to-land value ratio | derived; parcel + assessor |
| 3.2-6 | Candidate / Opportunity Sites | H | The sites the action actually enables | derived — this is the figure the public will look at hardest |
| 3.2-7 | Development Right Pools by Area Plan | H | RUUs, Bonus Units, TAUs, CFA remaining | `GetDevelopmentRightPoolBalanceReport`, `Development_Rights_Transacted_and_Banked/MapServer` |
| 3.2-8 | Development Rights Transacted and Banked | H | Transfer origin/destination | `GetDevelopmentRightTransactions` |
| 3.2-9 | Population Distribution | C | Census block group population | Census ACS |
| 3.2-10 | Employment Centers / Jobs Distribution | H | LEHD WAC by block | LEHD LODES |
| 3.2-11 | Jobs–Housing Relationship / In-Commute | H | LEHD origin-destination, workers commuting in over Spooner / Kingsbury / Echo | LEHD LODES — strong VMT and equity figure |
| 3.2-12 | Housing Cost Burden / Tenure | H | ACS cost-burdened households by tract | Census ACS |

### 3.3 Land Capability, Soils, and Geology *(Soil Conservation threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.3-1 | **Bailey Land Capability** | C | Classes 1a–7 | TRPA Land Capability — the single most-cited TRPA figure |
| 3.3-2 | Stream Environment Zones (SEZ) | C | Class 1b / SEZ delineation | TRPA |
| 3.3-3 | IPES Scores | H | Nevada parcels only (CA uses Bailey) | `GetParcelIPESScores` (LTInfo) |
| 3.3-4 | Soils (SSURGO) | C | Map units, erosion hazard, hydrologic group | NRCS SSURGO |
| 3.3-5 | Slope Classes | C | 0–5, 5–16, 16–30, >30% | 1 m LiDAR DEM |
| 3.3-6 | Geology and Faults | T | West Tahoe–Dollar Point, Incline Village, Stateline faults; alquist-priolo zones on CA side | USGS / CGS / NBMG |
| 3.3-7 | Land Coverage / Impervious Surface | C | Existing coverage vs. allowable by land capability | TRPA — coverage is the TRPA-specific hook CEQA reviewers miss |
| 3.3-8 | Avalanche Zones | T | | `Avalanche_Zones/MapServer/0` |

### 3.4 Hydrology and Water Quality *(Water Quality threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.4-1 | Watersheds and Sub-watersheds | C | Basin hydrologic units, tributary watersheds | TRPA / USGS WBD |
| 3.4-2 | Streams, Lakes, and Wetlands | C | Perennial/intermittent streams, marshes, NWI wetlands | TRPA + USFWS NWI |
| 3.4-3 | FEMA Flood Hazard Zones | C | 100-yr / 500-yr floodplain | `Streams_and_Flood_Zone/MapServer/0`; FEMA NFHL |
| 3.4-4 | Urban Stormwater Catchments | C | TMDL urban catchments, load reduction status | `AllStormwaterCatchments` (LTInfo GeoServer) |
| 3.4-5 | BMP Retrofit / Compliance Status | C | Parcel BMP certification status | TRPA BMP service |
| 3.4-6 | Groundwater Basins and Wells | T | DWR / NDWR basins, public supply wells | DWR, NDWR |
| 3.4-7 | Shorezone and High Water Line | T | HWL, backshore, shorezone tolerance districts | `Shoreline_Resources/MapServer/7` |

### 3.5 Air Quality and Greenhouse Gas *(Air Quality threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.5-1 | Air Basin and Attainment Status | C | Basin boundary, CO maintenance area, applicable nonattainment designations | EPA Green Book, CARB, NDEP — **verify current designations, they change** |
| 3.5-2 | Air Quality Monitoring Stations | C | TRPA/CARB/NDEP monitors | TRPA `LTInfo_Monitoring` |
| 3.5-3 | Sensitive Receptors | C | Schools, childcare, hospitals, senior housing within 1,000 ft of major roadways | derived — required for CEQA health-risk screening |
| 3.5-4 | VMT / Trip Generation by Analysis Zone | H | Modeled VMT per capita | TRPA travel demand model |

### 3.6 Vegetation and Forest Health *(Vegetation threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.6-1 | Existing Vegetation / Cover Types | C | Seral stage, cover type | `Vegetation/*` |
| 3.6-2 | Late Seral / Old Growth | C | | `Vegetation/*` |
| 3.6-3 | Forest Stand Density / SDI | T | | `Forest_Health_Stand_Density/MapServer` |
| 3.6-4 | Fuel Treatments and Burn Severity | T | Completed treatments, recent fire perimeters, burn severity | `Vegetation/*`, EIP projects |
| 3.6-5 | Sensitive Plants and Special-Interest Areas | T | Tahoe yellow cress, uncommon plant communities | CNDDB / NNHP — see confidentiality note |
| 3.6-6 | Wetlands and Riparian Vegetation | C | NWI + SEZ vegetation | USFWS NWI |

### 3.7 Wildlife *(Wildlife threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.7-1 | TRPA Wildlife Disturbance Zones | C | Bald eagle (nesting + winter), osprey, goshawk, peregrine falcon, waterfowl — TRPA Code Ch. 62 | TRPA; AGOL `Proposed_TRPA_Goshawk_Threshold_Zone` |
| 3.7-2 | Deer Winter Range / Migration Corridors | T | | CDFW / NDOW |
| 3.7-3 | Special-Status Wildlife Occurrences | X | CNDDB, NNHP records | **Confidential** — generalize to quarter-quad or omit from the public document |
| 3.7-4 | Habitat Connectivity / Wildlife Crossings | T | Linkage areas, documented crossing hotspots | CDFW ACE, Caltrans |

### 3.8 Fisheries and Aquatic Resources *(Fisheries threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.8-1 | Stream Fish Habitat and Barriers | T | Lahontan cutthroat trout habitat, culvert/dam barriers | CDFW, NDOW, USFS |
| 3.8-2 | Aquatic Invasive Species Occurrence | T | AIS infestation, watercraft inspection stations | TRPA / TRCD |
| 3.8-3 | Nearshore / Littoral Habitat | T | Spawning habitat, substrate | TRPA `Shoreline_Resources` |

### 3.9 Scenic Resources and Community Design *(Scenic threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.9-1 | Scenic Roadway Units and Travel Route Ratings | C | Unit boundaries with attainment status | `Scenic_Status/MapServer/2` |
| 3.9-2 | Scenic Shoreline Units and Ratings | C | | `Scenic_Status/MapServer/3` |
| 3.9-3 | Scenic Viewpoints / Key Observation Points | C | KOPs used for visual simulations | `LTInfo_Monitoring/MapServer/24` |
| 3.9-4 | Viewshed Analysis from KOPs | T | Modeled viewshed from selected KOPs | derived — pair with photo simulations |
| 3.9-5 | Community Design / Height Districts | H | Existing and proposed maximum height by district | TRPA Code Ch. 37 — **critical for a Housing EIS** |
| 3.9-6 | Light and Glare / Existing Night Sky | T | VIIRS nighttime lights | NOAA VIIRS |

### 3.10 Recreation *(Recreation threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.10-1 | Public Recreation Facilities | C | Beaches, campgrounds, boat ramps, day-use areas, parks | TRPA / LTBMU |
| 3.10-2 | Trails and Trailheads | C | Tahoe Rim Trail, Class 1 bike paths, USFS trail system | TRPA / LTBMU |
| 3.10-3 | Ski Areas and Special Use Permits | T | | LTBMU |
| 3.10-4 | Recreation Access Relative to Housing | H | Walk-shed from residential concentrations to public recreation | derived |

### 3.11 Noise *(Noise threshold)*

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.11-1 | CNEL Standards by Plan Area | C | TRPA noise standards by PAS/Area Plan | TRPA Code Ch. 68 |
| 3.11-2 | Modeled Transportation Noise Contours | C | 60/65/70 dBA CNEL along US 50, SR 28, SR 89, SR 267 | modeled — acoustician deliverable, you draft the basemap |
| 3.11-3 | Lake Tahoe Airport Noise Contours | T | CNEL contours, airport influence area | Airport Land Use Compatibility Plan |
| 3.11-4 | Noise-Sensitive Receptors | C | Residences, schools, hospitals, lodging | derived |

### 3.12 Transportation and Circulation

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.12-1 | Roadway Network and Functional Classification | C | | TRPA `Transportation_*` |
| 3.12-2 | Study Intersections and Segments | C | Locations analyzed in the traffic study | traffic consultant |
| 3.12-3 | Existing LOS / VMT by Segment | C | | traffic model |
| 3.12-4 | Transit Routes and Stops | H | TART, TTD, South Shore routes; 1/4- and 1/2-mile stop buffers | TRPA `Transportation_*` |
| 3.12-5 | Bicycle and Pedestrian Network | H | Class 1/2/3 facilities, sidewalk gaps | TRPA |
| 3.12-6 | Mobility Hubs and Parking | T | | TRPA / TTD |
| 3.12-7 | Transit-Proximate Housing Opportunity | H | Candidate sites × transit buffer × center boundaries | derived — the CEQA §15064.3 VMT-reduction argument in one image |

### 3.13 Public Services and Utilities

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.13-1 | Sewer Service Areas | H | STPUD, IVGID, NTPUD, TCPUD, DCSID #1, Kingsbury GID; export lines | district GIS |
| 3.13-2 | Water Purveyor Service Areas | H | Public water systems, service boundaries | CA SWRCB, NDEP |
| 3.13-3 | Fire Protection Districts and Stations | C | Districts, station locations, response-time isochrones | district GIS |
| 3.13-4 | Law Enforcement and Emergency Services | T | | county GIS |
| 3.13-5 | School Districts and School Locations | H | LTUSD, Tahoe Truckee USD, Washoe CSD, Douglas CSD; enrollment capacity | CDE, NDE |
| 3.13-6 | Solid Waste and Recycling Facilities | T | Transfer stations, haul routes | county GIS |
| 3.13-7 | Utility Infrastructure Corridors | T | Electric transmission, gas, broadband | NV Energy, Liberty Utilities |

### 3.14 Cultural, Historic, and Tribal Resources

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.14-1 | Historic Districts and Listed Properties | C | NRHP, CA/NV registers, TRPA historic districts | `Historic/MapServer/0` |
| 3.14-2 | Area of Potential Effects (APE) | T | Only if Section 106 applies | derived |
| 3.14-3 | **Archaeological Sensitivity** | X | Recorded sites, sensitivity model | **NOT FOR PUBLICATION.** Confidential appendix only. Public copy shows a generalized sensitivity surface at best, or nothing. Cal. Gov. Code §6254(r), Pub. Res. Code §21082.3(c), NHPA §304, ARPA §9. Coordinate with the Washoe Tribe THPO before any depiction. |

### 3.15 Hazards, Hazardous Materials, and Wildfire

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.15-1 | Fire Hazard Severity Zones | C | CAL FIRE FHSZ (CA side), NV equivalent | CAL FIRE, NDF |
| 3.15-2 | Wildland-Urban Interface | C | WUI defense/threat zones, CWPP boundaries | CAL FIRE / local CWPPs |
| 3.15-3 | Evacuation Routes and Constraints | H | Designated routes, single-access neighborhoods, capacity chokepoints | county OES — **increasingly the most-commented figure in any Tahoe housing document** |
| 3.15-4 | Hazardous Materials Sites | T | Cortese list, EnviroStor, GeoTracker, NDEP sites | DTSC, SWRCB, NDEP |
| 3.15-5 | Airport Influence / Safety Zones | T | Lake Tahoe Airport ALUCP zones | ALUCP |

### 3.16 Energy

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.16-1 | Electric Service Territories | T | Liberty Utilities (CA), NV Energy (NV) | utility GIS |
| 3.16-2 | Renewable Generation and EV Charging | T | Solar installations, EV charging network | derived |

### 3.17 Environmental Justice and Equity

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 3.17-1 | Disadvantaged / Low-Income Communities | H | CalEnviroScreen 4.0 (CA), EJScreen, ACS low-income block groups | OEHHA, EPA |
| 3.17-2 | Race, Ethnicity, and Language Access | H | ACS; limited-English households — drives the outreach plan too | Census ACS |
| 3.17-3 | TRPA Transportation Equity Tessellation | H | | `Transportation_*` equity tessellation |

Required for NEPA (EO 12898) if a federal nexus exists; strongly advisable regardless for a
Housing EIS, because it is the analysis the public comment period will demand.

---

## 5. Chapter 4 — Cumulative Impacts

| # | Figure | Tier | Key layers | Source |
|---|---|---|---|---|
| 4.0-1 | Cumulative Projects — Location Map | C | Reasonably foreseeable projects with parcel/point locations | derived project list |
| 4.0-2 | EIP Projects (Planned and In Progress) | C | | `vEIPProjectLocationDetail` (LTInfo GeoServer) or `GetProjectDetailedLocationsAsFeatureCollection` |
| 4.0-3 | Pending Area Plan and Code Amendments | T | | TRPA |
| 4.0-4 | Threshold Attainment Status Overview | C | Nine threshold categories, attainment status | `GetThresholdEvaluations` (LTInfo) — usually a map + table combo |

---

## 6. Appendices

| # | Figure | Tier | Notes |
|---|---|---|---|
| A-1 | Data Sources and Methods | C | Table, not a map — layer name, source agency, vintage, scale/accuracy, processing steps. Write it as you go; reconstructing it at the end is miserable. |
| A-2 | Full-size fold-out composites | T | Land capability, zoning, alternatives — the three people actually want at 24 × 36 |
| A-3 | Confidential cultural resources map package | X | Separate bound volume, distribution list, not in the public record |

---

## 7. Counts and effort

| Set | Figures |
|---|---|
| Tier C (core, every EIS) | ~40 |
| Tier H (housing-specific) | ~22 |
| Tier T (trigger-based) | ~25 |
| Tier X (confidential) | 3 |
| **Housing EIS realistic build (C + H + likely T)** | **~70–75** |

Budget roughly 2–4 hours per figure once the template and symbology library exist, and 20–30 hours
up front to build the template, styles, and layer files. Data acquisition and cleanup for the
non-TRPA sources (SSURGO, LEHD, CalEnviroScreen, district boundaries, evacuation routes) will take
longer than the cartography.

---

## 8. Pre-delivery QA checklist

Run this on every figure before it goes into the admin draft.

- [ ] Figure number and title match the text callout exactly
- [ ] Figure is actually referenced in the body text at least once
- [ ] North arrow, scale bar (mi + km), legend, source line, date, logo all present
- [ ] Every legend entry appears on the map; every map symbol appears in the legend
- [ ] Locator inset present (non-basin-wide figures)
- [ ] Grayscale proof is legible — no two categories collapse to the same gray
- [ ] Colorblind check passed
- [ ] Smallest label ≥ 8 pt at final print size
- [ ] Projection is UTM 10N; any acreage/length figures computed in UTM 10N, not Web Mercator
- [ ] Acreage totals in the map match the acreage totals in the text tables
- [ ] Data vintage on the map matches the vintage cited in Section 3.x
- [ ] No confidential cultural or sensitive-species geometry visible at any zoom
- [ ] PDF exported without georeference info and without layer structure (public copy)
- [ ] Fonts embedded
- [ ] Alt text written (if 508 applies)
- [ ] Filename follows `Fig_<num>_<Title>.pdf`

---

## 9. Open items to confirm

1. Is there any federal nexus for the Housing EIS (HUD funding, LTBMU land, FHWA)? Determines
   whether NEPA and 508 accessibility actually apply.
2. Will El Dorado County or the City of South Lake Tahoe tier a CEQA document off this EIS? If so,
   confirm their figure conventions now rather than reformatting later.
3. Confirm current VHR/STR layer name and refresh cadence on `maps.trpa.org`.
4. Confirm current federal attainment designations for the basin (EPA Green Book) — do not carry
   forward the designation language from the last EIS without checking.
5. Confirm the residential-units dataset of record for Figure 3.2-1 — parcel-based count vs.
   the Permitting ETL output.
6. Get the Washoe THPO coordination started early; it gates Figures 3.14-2 and 3.14-3.
