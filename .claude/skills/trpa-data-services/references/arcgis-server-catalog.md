# maps.trpa.org Service Catalog

Complete inventory of services on TRPA's on-prem ArcGIS Server (`https://maps.trpa.org/server/rest/services/`). ArcGIS Server 11.5. Grouped by domain for navigability.

To get the current live list at any time:

```bash
curl 'https://maps.trpa.org/server/rest/services/?f=pjson' | jq -r '.services[] | "\(.name) (\(.type))"'
```

---

## Parcels & ownership

| Service | Type | Notes |
|---|---|---|
| `Parcels` | MapServer + FeatureServer | The canonical parcel layer. `FeatureServer/0` for queries. |
| `Parcel_Joins` | MapServer + FeatureServer | Parcel attributes (TOLERANCE_ID, JURISDICTION, etc.) — `FeatureServer/6` is the primary join table |
| `AllParcels` | MapServer | All-parcel display layer |
| `APN_Labels` | MapServer | APN label graphics |
| `Ownership` / `Ownership_cached` | MapServer | Ownership polygons |
| `parcel_projection_lines` | MapServer | Parcel projection lines |
| `Burton_Santini_Parcels` | MapServer | Burton-Santini program parcels |
| `AssessedValues` | MapServer | Assessed parcel values |

## Zoning & planning

| Service | Type | Notes |
|---|---|---|
| `Zoning` | MapServer | `/0` districts, `/6` permissible use, `/7` special designation. See `trpa-zoning-services` skill |
| `Planning` | MapServer + FeatureServer | General planning layers |
| `Planning_Buffers` | MapServer | Planning-related buffers |
| `LocalPlan` | MapServer | Adopted local plans — `/1` returns FILE_URL by PLAN_ID |
| `Special_Designation` | MapServer | Special designations layer |
| `Boundaries` | MapServer + FeatureServer | Town centers (`/1`), jurisdictional boundaries |
| `Washoe_County_Area_Plan_*` | MapServer | Washoe County Area Plan base, existing zones, new zones |
| `SR89_Management_Plan` | MapServer | SR-89 corridor management plan |

## Development rights & housing

| Service | Type | Notes |
|---|---|---|
| `Development_Potential` | MapServer | Development potential index |
| `Development_Rights_Transacted_and_Banked` | MapServer | DR transaction + banking spatial view |
| `AccessoryDwellingUnit_Density` | MapServer | ADU density layer |
| `Housing` | MapServer | Housing data layers |
| `Deed_Restriction` | MapServer | Deed-restricted parcels |
| `Short_Term_Rental_Density` | MapServer | STR density |
| `VHR` | MapServer | Vacation Home Rental locations |
| `Securities` | MapServer | Securities held by TRPA |

## Land use & development

| Service | Type | Notes |
|---|---|---|
| `Existing_Land_Use` | MapServer | Existing land-use polygons |
| `Existing_Development` | MapServer | Existing development |
| `Permit_Records` | MapServer | Permit records |
| `AGIS_ACA` / `AGIS_Inspector` / `AGIS_TRPA` | MapServer | Accela GIS services |
| `BMP_Status` | MapServer | Best Management Practice status |

## Environmental — vegetation & forest health

| Service | Type | Notes |
|---|---|---|
| `Vegetation` | MapServer + FeatureServer | Composite vegetation service |
| `Vegetation_Type` / `Vegetation_Type_Cached` | MapServer | Vegetation type |
| `Vegetation_Seral_Stage` | MapServer | Seral stage |
| `Vegetation_Late_Seral` | MapServer + FeatureServer | Late seral vegetation |
| `Vegetation_Burn_Severity` | MapServer | Burn severity layer |
| `Vegetation_Horizontal_Heterogeneity` | MapServer | Horizontal heterogeneity |
| `Caldor_Vegetation_Moderate_and_High_Burn_Severity` | MapServer | Caldor Fire burn severity |
| `Forest_Health_Composition_Age` | MapServer | Forest composition + age |
| `Forest_Health_Stand_Density` | MapServer | Stand density |
| `Trees_in_Meadow` | MapServer | Trees in meadow |
| `Large_Trees_Reference` | MapServer + FeatureServer | Large tree reference points |
| `Fire` | MapServer | Fire history / risk |

## Environmental — water & shoreline

| Service | Type | Notes |
|---|---|---|
| `Streams_and_Flood_Zone` | MapServer | Streams + flood zones |
| `Shoreline_Contours` | MapServer | Shoreline contour lines |
| `Shoreline_Resources` | MapServer | Shoreline resource layers, `/7` for HWL buffer |
| `Fish_Habitat` | MapServer | Fish habitat |
| `BoaterVisits` | MapServer | Boater visit data |
| `BoatTahoe` | MapServer | Boat Tahoe layers |
| `eDNA_Samples` | MapServer | Environmental DNA sample sites |
| `Calcium_Sites` / `Calcium_Survey` | MapServer + FeatureServer | Calcium monitoring |
| `Catchments` | MapServer | Stormwater catchments |
| `Watershed_Erosion_Prediction_Project_Tahoe_Basin` | MapServer + FeatureServer | WEPP analysis |
| `SteamBio_Survey` | MapServer + FeatureServer | Stream biological surveys |
| `SEZ_Assessment_Unit` / `SEZ_Survey` / `SEZ_Viewer_Base_Data` | MapServer + FeatureServer | Stream Environment Zone assessment + survey |
| `TYC_Watering` | MapServer + FeatureServer | TYC watering |

## Environmental — terrain & impervious

| Service | Type | Notes |
|---|---|---|
| `Tahoe_Elevation` | MapServer | Elevation |
| `Tahoe_Hillshade_Cached` | MapServer | Hillshade |
| `Tahoe_Canopy_Hillshade_Cached` | MapServer | Canopy + hillshade composite |
| `Slope_Class_Cached` / `Slope_Class_30_50_Cached` | MapServer | Slope class layers |
| `Soils_and_Land_Capability` | MapServer | Soils + land capability |
| `Land_Capability_Verification_Digitized` | MapServer + FeatureServer | LCV digitized records |
| `Impervious_Surface_2010` / `Impervious_Surface_2019` | MapServer | Impervious surface |
| `Impervious_Surface_Change_2010_to_2019` | MapServer | Impervious change |
| `OverlayAnalysis_Parcel_NRCSSoils_Impervious2018__BonusUnitBoundary` | MapServer + FeatureServer | Overlay analysis for bonus units |

## Wildlife & habitat

| Service | Type | Notes |
|---|---|---|
| `Wildlife_Activity` | MapServer | Wildlife activity |
| `Wildlife_Habitat` | MapServer | Wildlife habitat |
| `Osprey_Nest_Survey` | MapServer + FeatureServer | Osprey nest survey |

## Scenic

| Service | Type | Notes |
|---|---|---|
| `Scenic_Status` | MapServer + FeatureServer | `/2` scenic roadway, `/3` scenic shoreline |

## Historic & cultural

| Service | Type | Notes |
|---|---|---|
| `Historic` | MapServer | Historic districts |
| `Avalanche_Zones` | MapServer | Avalanche hazard zones |
| `Emergency_Services` | MapServer | Emergency services |

## Transportation & recreation

| Service | Type | Notes |
|---|---|---|
| `Transportation` | MapServer | General transportation |
| `Transportation_Planning` | MapServer | Transportation planning layers |
| `Transportation_SMART` | MapServer + FeatureServer | SMART transportation data |
| `Transportation_Equity_Analysis_Tessellation` | MapServer + FeatureServer | Equity analysis tessellation |
| `Recreation` | MapServer | Recreation sites |
| `ReferenceTrails` | MapServer | Trail reference layer |
| `Trails_Strategy` | MapServer | Trails strategy |
| `Trails_Online_Survey_2021` | MapServer | Trails survey 2021 |
| `Parking_Lots` | MapServer | Parking lots |
| `RTP2020_MegaRegion` / `RTP2020_StoryMap` | MapServer | Regional Transportation Plan 2020 |
| `Mountain_to_Marina_Story_Map` | MapServer | Mountain-to-Marina story map |

## LTInfo-related (on-prem)

| Service | Type | Notes |
|---|---|---|
| `LTInfo_Monitoring` | MapServer | Monitoring layers — e.g., `/24` scenic viewpoints |
| `LTInfo_Spatial` | MapServer | LTInfo spatial layers |
| `LTInfo_Tabular` | MapServer | LTInfo tabular layers |
| `LTinfo_Climate_Resilience_Dashboard` | MapServer | Climate dashboard layers |

## Imagery

| Service | Type | Notes |
|---|---|---|
| `1940_Imagery` | MapServer | Historic 1940 imagery |
| `1969_Imagery` | MapServer | Historic 1969 imagery |
| `2015_Imagery` | MapServer | 2015 imagery |
| `2018_Imagery` / `2018_Imagery_Color_Infrared` | MapServer | 2018 imagery (RGB + CIR) |
| `2019_Imagery_Nearshore` | MapServer | 2019 nearshore imagery |

## Demographics

| Service | Type | Notes |
|---|---|---|
| `Demographics` | MapServer | Demographic data |

## Data Downloader services

These power the public Data Downloader on trpa.gov. Generally meant for human download, not programmatic use, but the underlying layers are queryable.

| Service | Type | Domain |
|---|---|---|
| `DataDownloader_Contours` | MapServer | Contours |
| `DataDownloader_Impervious` | MapServer | Impervious surface |
| `DataDownloader_Parcels` | MapServer | Parcels |
| `Datadownloader_PlanningandJurisdictions` | MapServer | Planning + jurisdictions |
| `DataDownloader_Recreation` | MapServer | Recreation |
| `DataDownloader_Shorezone` | MapServer | Shorezone |
| `DataDownloader_SoilsandHydro` | MapServer | Soils + hydro |
| `DataDownloader_Transportation` | MapServer | Transportation |
| `DataDownloader_Wildlife` | MapServer | Wildlife |

## Misc / tools

| Service | Type | Notes |
|---|---|---|
| `MapMaker` | MapServer | MapMaker tool service |
| `Mesh_DOUGLAS` | SceneServer | 3D mesh for Douglas County |
| `Trails_Online_Survey_2021` | MapServer | Public trail survey |
| `Hosted` / `Routing` / `Utilities` | folders | Esri-provided utility folders |

---

## Looking up a layer schema

For any service, append `?f=json` to see metadata, or `/<layer-id>?f=json` for a single layer's schema and field definitions:

```
https://maps.trpa.org/server/rest/services/Parcels/FeatureServer/0?f=json
```

Look for `fields[]` for the schema and `extent` for the spatial extent. This is the authoritative source for field names and types — anything in this document is just a summary.
