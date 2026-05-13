# LTInfo Web Services — Tabular Catalog

Full reference for the tabular REST APIs at `https://www.laketahoeinfo.org/WebServices/`. Authoritative list (login required): `https://www.laketahoeinfo.org/WebServices/List`.

All endpoints use the path pattern:

```
https://www.laketahoeinfo.org/WebServices/<ServiceName>/<CSV|JSON>/<TOKEN>[/<param>]
```

The token is user-scoped, requested from the WebServices List page while signed in. **Treat it as a credential** — never commit it, never embed it in a public-facing HTML page. Store in `.env` as `LTINFO_WEBSERVICES_TOKEN`.

In every example below, `{TOKEN}` is a placeholder. Substitute your own.

---

## Projects

### `GetProject` — single project
Returns detailed information for one project, identified by EIP project number (e.g., `01.01.01.0001`) or Project ID.

```
GET /WebServices/GetProject/JSON/{TOKEN}/01.01.01.0001
GET /WebServices/GetProject/CSV/{TOKEN}/01.01.01.0001
```

### `GetProjects` — all projects
Every project, regardless of stage or year. Useful starting point for a project dashboard.

```
GET /WebServices/GetProjects/JSON/{TOKEN}
GET /WebServices/GetProjects/CSV/{TOKEN}
```

### `GetProjectDescription`
Narrative description for one project.

```
GET /WebServices/GetProjectDescription/JSON/{TOKEN}/01.01.01.0001
```

### `GetProjectKeyPhoto`
URL of the key photo for one project.

```
GET /WebServices/GetProjectKeyPhoto/JSON/{TOKEN}/01.01.01.0001
```

### `GetProjectOrganizations`
Project/organization relationships (funders, implementers) for one project.

```
GET /WebServices/GetProjectOrganizations/JSON/{TOKEN}/01.01.01.0001
```

### `GetProjectExpenditures`
Expenditure data for one project.

```
GET /WebServices/GetProjectExpenditures/JSON/{TOKEN}/01.01.01.0001
```

### `GetReportedProjectAccomplishments`
Performance measure accomplishments for one project — what indicators the project moved, and by how much.

```
GET /WebServices/GetReportedProjectAccomplishments/JSON/{TOKEN}/01.01.01.0001
```

### `GetProjectsByOrganization`
All projects where a given organization is a funder or implementer. Parameter is the OrganizationID (integer).

```
GET /WebServices/GetProjectsByOrganization/JSON/{TOKEN}/18
```

### Project geometries — three flavors

| Endpoint | Output | What you get |
|---|---|---|
| `GetProjectDetailedLocationsAsFeatureCollection` | GeoJSON FC (JSON only) | Projects with detailed polygons / lines |
| `GetProjectSimpleLocationsAsFeatureCollection` | GeoJSON FC (JSON only) | Projects with simple point locations |
| `GetProjectSimpleLocationAndGeospatialAssociations` | JSON / CSV | Lat/lon + geospatial associations as tabular rows |

```
GET /WebServices/GetProjectDetailedLocationsAsFeatureCollection/JSON/{TOKEN}
GET /WebServices/GetProjectSimpleLocationsAsFeatureCollection/JSON/{TOKEN}
GET /WebServices/GetProjectSimpleLocationAndGeospatialAssociations/JSON/{TOKEN}
```

Note: detailed locations are also available spatially via the LTInfo GeoServer layer `vEIPProjectLocationDetail` (no token required).

---

## EIP Indicators (Performance Measures)

### `GetEIPIndicators`
Master list of EIP performance measures, with their subcategories (dimensions) and option counts.

```
GET /WebServices/GetEIPIndicators/JSON/{TOKEN}
```

### `GetReportedEIPIndicatorProjectAccomplishments`
Performance measure accomplishments grouped by a specific Indicator ID.

```
GET /WebServices/GetReportedEIPIndicatorProjectAccomplishments/JSON/{TOKEN}/5
```

---

## Organizations

### `GetOrganizations`
All organizations in the LT Info platform — jurisdictions, agencies, associations, private firms, plus any individual who has requested an account.

```
GET /WebServices/GetOrganizations/JSON/{TOKEN}
```

---

## Parcels & Land Capability

### `GetAllParcels`
All parcels as imported nightly from Accela. The authoritative LTInfo parcel list.

```
GET /WebServices/GetAllParcels/JSON/{TOKEN}
GET /WebServices/GetAllParcels/CSV/{TOKEN}
```

### `GetParcelsByLandCapability`
Parcels with Land Capability records entered, with links to Site Plans and summarized Land Capabilities.

```
GET /WebServices/GetParcelsByLandCapability/JSON/{TOKEN}
```

### `GetParcelIPESScores`
Individual Parcel Evaluation System (IPES) scores.

```
GET /WebServices/GetParcelIPESScores/JSON/{TOKEN}
```

### `GetDeedRestrictedParcels`
Deed-restriction records by parcel. Parcels appear multiple times if covered by multiple deed restrictions or multiple deed-restricted project areas.

```
GET /WebServices/GetDeedRestrictedParcels/JSON/{TOKEN}
```

### Accela-specific variants
For the Accela permit system's use. Same data as the regular endpoints, formatted for Accela ingestion.

```
GET /WebServices/GetParcelLandCapabilitiesForAccela/JSON/{TOKEN}
GET /WebServices/GetParcelDevelopmentRightsForAccela/JSON/{TOKEN}
```

---

## Development Rights

### `GetBankedDevelopmentRights`
All parcels' banked development rights as entered in the Parcel Tracker.

```
GET /WebServices/GetBankedDevelopmentRights/JSON/{TOKEN}
```

### `GetTransactedAndBankedDevelopmentRights`
Combined view — transacted + banked rights per parcel.

```
GET /WebServices/GetTransactedAndBankedDevelopmentRights/JSON/{TOKEN}
```

### `GetDevelopmentRightTransactions`
All development right transactions where data has been entered in the Parcel Tracker.

```
GET /WebServices/GetDevelopmentRightTransactions/JSON/{TOKEN}
```

### `GetDevelopmentRightPoolBalanceReport`
Current pool balances by community / area plan.

```
GET /WebServices/GetDevelopmentRightPoolBalanceReport/JSON/{TOKEN}
```

---

## Moorings

### `GetAssignedMooringTags`
All assigned mooring tags from the LT Info Mooring Registration System.

```
GET /WebServices/GetAssignedMooringTags/JSON/{TOKEN}
```

Spatial complement: `MooringInventoryAndRegistrationStatus` and `vGeoserverMooring` on the LTInfo GeoServer.

---

## Stats & dashboards

### `GetEIPHomepageStats`
Statistics displayed on the EIP homepage. Useful when you want the same numbers your dashboards show without recomputing.

```
GET /WebServices/GetEIPHomepageStats/JSON/{TOKEN}
```

### `GetTransitMonitoringData`
Monthly transit ridership data.

```
GET /WebServices/GetTransitMonitoringData/JSON/{TOKEN}
```

### `GetThresholdEvaluations`
Threshold indicators and their evaluation rollups. Feeds `thresholds.laketahoeinfo.org`.

```
GET /WebServices/GetThresholdEvaluations/JSON/{TOKEN}
```

---

## Notes & gotchas

- **All endpoints are GET.** No body payloads.
- **CSV vs JSON.** Both are usually available, but the FeatureCollection endpoints (`*AsFeatureCollection`) are JSON-only.
- **Pagination.** The LTInfo endpoints generally return the full result set in one call — no `resultOffset` / `resultRecordCount` parameters. If response sizes become a problem, raise it with the LTInfo team (Environmental Science Associates implements the platform).
- **Rate limits.** Not documented publicly. Be considerate in scripts — batch your runs and cache intermediate results.
- **SOAP exists but is unmaintained.** Per the LT Info documentation: stick to REST.
- **Open source.** The EIP Project Tracker (which underlies many of these endpoints) is open source as **ProjectFirma** on GitHub. The Stormwater Tools source is available upon request. Other components are commercially licensed via TRPA.

## Token rotation

If a token is ever exposed (committed, posted publicly, shared with the wrong person), request a new one immediately from the WebServices List page and update `.env`. Tokens are user-scoped, so the rotation only affects you — but old tokens may still work until LT Info revokes them, so don't rely on revocation as a security boundary.
