---
name: trpa-climate-dashboard
description: "Climate Resilience Dashboard for Lake Tahoe (climate.laketahoeinfo.org). Use this skill when building, updating, or adding pages to TRPA's Climate Resilience Dashboard. Covers the 4-goal indicator framework, 33 metrics, data sources, visualization types, and page patterns. Trigger on any mention of: climate dashboard, climate resilience, climate indicators, GHG emissions Tahoe, air quality Tahoe, forest health dashboard, resilient systems Tahoe, sustainability dashboard, climate.laketahoeinfo.org, or any request to build a climate-related visualization for TRPA."
---

# TRPA Climate Resilience Dashboard

Reference skill for building and extending the **Climate Resilience Dashboard** at [climate.laketahoeinfo.org](https://climate.laketahoeinfo.org/). The dashboard is hosted via GitHub Pages from the `trpa-agency/ClimateResilienceDashboard` repo.

**Always pair this skill with:**
- `trpa-dashboard-stack` for the tech stack (Plotly, Calcite, ArcGIS, AG Grid)

**Do NOT use** `trpa-brand`, `trpa-eip-brand`, or `tahoe-living-brand` for this dashboard. The Climate Resilience Dashboard lives on the **Lake Tahoe Info (LT Info) platform**, which has its own visual identity described below.

---

## LT Info Platform Identity

The Climate Resilience Dashboard is part of the **laketahoeinfo.org** family of dashboards — a data platform that is related to but visually distinct from trpa.gov. All LT Info dashboards share a common shell: a top nav bar, an "Explore" dropdown linking to sibling dashboards, and a partner-logo footer.

### LT Info color palette

LT Info uses a **dark charcoal/slate** header (not TRPA Blue) with a teal-green accent. The palette is more neutral and data-focused than the TRPA agency brand.

```css
:root {
  /* LT Info platform colors */
  --lti-charcoal:     #2C3E50;   /* Header, nav bar, dark backgrounds */
  --lti-teal:         #1ABC9C;   /* Active nav, accent, links */
  --lti-teal-dark:    #16A085;   /* Hover states */
  --lti-blue:         #3498DB;   /* Secondary accent, info states */
  --lti-text:         #2C3E50;   /* Body text */
  --lti-text-muted:   #7F8C8D;   /* Captions, secondary text */
  --lti-bg:           #ECF0F1;   /* Page background (light gray) */
  --lti-white:        #FFFFFF;   /* Card surfaces */
  --lti-border:       #BDC3C7;   /* Borders, dividers */

  /* Climate dashboard accent — can use TRPA Blue for charts */
  --climate-primary:  #0072CE;   /* TRPA Blue — chart primary series */
  --climate-green:    #27AE60;   /* Positive/nature indicators */
  --climate-amber:    #F39C12;   /* Caution/warning */
  --climate-red:      #E74C3C;   /* Off-track/critical */
}
```

### LT Info header bar

The LT Info nav bar is a **dark charcoal** (`#2C3E50`) bar with white text and the LT Info logo (not the TRPA agency logo). It includes an "Explore" dropdown linking to all sibling dashboards.

```html
<nav class="lti-header" style="background: #2C3E50; color: #fff; padding: 0 1.5rem; display: flex; align-items: center; height: 56px;">
  <a href="https://www.laketahoeinfo.org/">
    <img src="https://www.laketahoeinfo.org/Content/img/LT_INFO_LOGO2025-white.png" alt="Lake Tahoe Info" height="32" />
  </a>
  <a href="https://climate.laketahoeinfo.org/" style="color: #1ABC9C; margin-left: 1.5rem; font-weight: 600; text-decoration: none;">
    Climate Resilience Dashboard
  </a>
  <!-- Explore dropdown linking to sibling dashboards -->
</nav>
```

### LT Info typography

LT Info uses **system fonts / Open Sans** — consistent with the TRPA agency web style but not Lexend Deca (EIP) or Montserrat (Tahoe Living):

```css
body {
  font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--lti-text);
  background: var(--lti-bg);
}
```

### LT Info footer

All LT Info dashboards include a footer with TRPA and partner logos (EPA, SGC, USFS, Caltrans, FHWA, NDEP, TRCD) plus implementation credit to ESA:

```html
<footer style="background: #2C3E50; color: rgba(255,255,255,0.7); padding: 2rem; font-size: 0.8rem; text-align: center;">
  <div>This site brought to you by <a href="https://trpa.gov" style="color: #1ABC9C;">TRPA</a> with funding provided by</div>
  <!-- Partner logo row -->
  <div style="margin-top: 1rem;">
    <img src="https://www.laketahoeinfo.org/Content/img/trpa-logo-footer.png" alt="TRPA" height="30" style="margin: 0 0.5rem;" />
    <!-- EPA, SGC, USFS, Caltrans, FHWA, NDEP, TRCD logos -->
  </div>
  <div style="margin-top: 1rem;">Implementation & Hosting by <a href="https://esassoc.com/services/technology/" style="color: #1ABC9C;">Environmental Science Associates</a></div>
</footer>
```

### Sibling dashboards (Explore dropdown)

The nav includes links to all LT Info dashboards. Include these in the Explore dropdown:

- [Climate Resilience Dashboard](https://climate.laketahoeinfo.org/)
- [EIP Project Tracker](https://eip.laketahoeinfo.org/)
- [Lake Clarity Tracker](https://clarity.laketahoeinfo.org/)
- [Monitoring Dashboard](https://monitoring.laketahoeinfo.org/)
- [Parcel Tracker](https://parcels.laketahoeinfo.org/)
- [Threshold Dashboard](https://thresholds.laketahoeinfo.org/)
- [Transportation Tracker](https://transportation.laketahoeinfo.org/)

### Chart colors for Climate Dashboard

Use TRPA Blue (`#0072CE`) as the primary chart color — this maintains the connection to TRPA while sitting inside the LT Info shell. The full chart colorway:

```javascript
const CLIMATE_COLORS = [
  '#0072CE',  // TRPA Blue (primary series)
  '#27AE60',  // Green (environmental/positive)
  '#F39C12',  // Amber (caution)
  '#E74C3C',  // Red (off-track)
  '#3498DB',  // LT Info blue (secondary)
  '#8E44AD',  // Purple (social/equity data)
  '#1ABC9C',  // Teal (LT Info accent)
  '#95A5A6',  // Muted gray (background category)
];
```

### Plotly.js layout for Climate Dashboard

```javascript
const CLIMATE_LAYOUT = {
  font: {
    family: 'Open Sans, system-ui, sans-serif',
    color: '#2C3E50',
    size: 13
  },
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  margin: { t: 30, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: '#e0e0e0', linecolor: '#BDC3C7' },
  yaxis: { gridcolor: '#e0e0e0', linecolor: '#BDC3C7' },
  colorway: ['#0072CE', '#27AE60', '#F39C12', '#E74C3C', '#3498DB', '#8E44AD', '#1ABC9C'],
  hoverlabel: { font: { family: 'Open Sans, sans-serif' } }
};
```

---

## Dashboard Structure

The dashboard is organized around **4 goals**, each with **outcomes** and **indicators/metrics**. Each indicator typically gets its own subpage (single-file HTML) with charts, maps, and/or data tables.

### Goal 1: Recognize the Changing Climate Conditions

| Outcome | Indicator | Viz Type | Data Source |
|---------|-----------|----------|-------------|
| 1.1 Report GHG emissions | 1.1.a Total GHG emissions by sector | Trendline by sector + total, with 2050 reduction target line | TRPA GHG inventory (base year 2005) |
| 1.2 Track air quality, smoke, heat | 1.2.a Poor air quality days, wildfire smoke days, extreme heat days/year | 3 trendlines (AQI days, smoke days, heat days) over time from ~2000 | AirNow, TRPA Smoke Forecast, National Weather Service |
| 1.3 Monitor lake water | 1.3.a Lake Tahoe water level | Seasonal trendline | UC Davis State of the Lake (annual) |
| 1.3 | 1.3.b Water temperature (volume-averaged + surface) | Trendline, seasonal | UC Davis State of the Lake |
| 1.3 | 1.3.c Lake clarity (Secchi depth) | Scatterplot with trendline | UC Davis TERC; also TRPA Threshold |
| 1.4 Monitor precipitation | 1.4.a Total precip, extreme precip, snow fraction | Trendlines (inches/year) | NOAA / UC Davis long-term daily precip |

### Goal 2: Promote Resilient Natural Systems

| Outcome | Indicator | Viz Type | Data Source |
|---------|-----------|----------|-------------|
| 2.1 Reduce wildfire risk, improve forest | 2.1.a Acres of fuels reduction treated | Bar chart by zone + map of treated areas | EIP Tracker |
| 2.1 | 2.1.b Tree species diversity, old growth | Bar charts vs targets (tree density, large tree density, clump/gap, seral stage) | TRPA Threshold Dashboard |
| 2.1 | 2.1.c Probability of fire by severity & management zone | Map (low/moderate/high severity) | USFS |
| 2.2 Reduce aquatic invasive species | 2.2.a Acres treated for AIS | Bar/trendline from EIP | EIP Tracker |
| 2.3 Watershed resilience & flood | 2.3.a Acres of restored wetlands/meadows | Bar chart + map of restored areas | EIP Tracker |
| 2.3 | 2.3.b Parcels with stormwater BMP improvements | Trendline | EIP Tracker |
| 2.3 | 2.3.c Sq ft of urban area treated by stormwater infrastructure | Bar or trendline (% of total area) | EIP Tracker |

### Goal 3: Support Resilient Built Systems

| Outcome | Indicator | Viz Type | Data Source |
|---------|-----------|----------|-------------|
| 3.1 Housing in Town Centers | 3.1.a Total units in town centers + affordable share | Trendlines over time | TRPA parcel/assessor data (annual) |
| 3.1 | 3.1.b Home energy source (electric/solar vs oil/gas) | Stacked bar by year (% of total) | US Census ACS 5-Year |
| 3.1 | 3.1.c Deed-restricted affordable/moderate/achievable units | Trendline (% of all units, North/South) | TRPA parcel/assessor data |
| 3.2 Renewable energy | 3.2.a % renewable energy of total | Stacked bar (power mix by source, NV/CA sides) | NV Energy, Liberty Utilities |
| 3.3 Transit & active transportation | 3.3.a Transit ridership by system | Stacked bar (TTD + TART, North/South) | TRPA Transportation Dashboard |
| 3.3 | 3.3.b Daily per capita VMT + target | Bar chart | TRPA Threshold Dashboard, RTP |
| 3.3 | 3.3.c EV charging & alt fuel infrastructure | Interactive map (charger locations, electric bus routes, mobility hubs) | PlugShare, US DOE, RTP |
| 3.3 | 3.3.d Mode share (weekday/seasonal) | Bar charts highlighting non-auto modes | TRPA Transportation Dashboard |
| 3.3 | 3.3.e Transportation access in priority communities | Equity map (65+, disabled, poverty) | TRPA Transportation Equity Study |
| 3.3 | 3.3.f Lane miles of low-stress bicycle facilities | Trendline (shared-use paths + LTS analysis) | TRPA Transportation Dashboard |

### Goal 4: Support Resilient Social Systems

| Outcome | Indicator | Viz Type | Data Source |
|---------|-----------|----------|-------------|
| 4.1 Community demographics | 4.1.a Population by race/ethnicity, age | Stacked/clustered bar (North/South) | ACS 5-Year Estimates |
| 4.1 | 4.1.b Median household income (remote vs non-remote workers) | Bar chart over decade (North/South option) | ACS 5-Year, PUMS |
| 4.1 | 4.1.c Housing costs (median home price + rental rates) | Trendline, inflation-adjusted (North/South) | ZORI / Property Radar |
| 4.1 | 4.1.d Housing tenure (owner/renter/second home) by race/ethnicity/age | Stacked bar (North/South) | ACS 5-Year Estimates |
| 4.1 | 4.1.e Commuter patterns (% commuting in, distance, mode) | Trendline + origin/destination map | LEHD/LODES Census On the Map |
| 4.2 Economic diversity | 4.2.a Transient Occupancy Tax revenue over time | Trendline | County TOT data |
| 4.2 | 4.2.b Percent of vacation/second homes | Bar chart over time | ACS 5-Year Estimates |
| 4.3 Emergency preparedness | 4.3.a Evacuation route capacity & constraints | Map | TRPA/local emergency plans |
| 4.3 | 4.3.b Community wildfire preparedness (Firewise communities) | Map + count | NFPA Firewise USA |

---

## Architecture: CMS + Embedded Charts

**Important:** The Climate Resilience Dashboard is NOT a set of standalone HTML pages. It is a **CMS-driven platform** hosted on LT Info (built on ProjectFirma/Keystone by ESA) with individual **chart/map visualizations hosted as separate HTML files on GitHub Pages** that get embedded into the CMS outcome pages.

### Two layers to understand

1. **CMS layer** (LT Info admin at `qa-climate.laketahoeinfo.org`): Manages goals, outcomes, indicators, narrative text, pull quotes, images, related outcomes, and metadata. Staff edit this through admin forms — no code required.

2. **Visualization layer** (GitHub Pages at `trpa-agency.github.io/ClimateResilienceDashboard/`): The actual charts, maps, and interactive visualizations are standalone HTML files hosted on GitHub Pages. These are referenced by URL in the CMS and embedded into the outcome pages.

**When building new visualizations for the climate dashboard, you are building files for layer 2** — standalone HTML chart/map pages that will be linked from the CMS.

### CMS content structure per outcome

Each outcome page in the CMS contains these editable sections (from the How-To Guide):

| Section | What it contains |
|---------|------------------|
| **Outcome Name** | Full name (e.g., "Track Poor Air Quality, Wildfire Smoke, and Extreme Heat Days") |
| **Short Name** | Abbreviated (e.g., "Air Quality and Extreme Heat") |
| **Goal** | Parent goal (dropdown: Goals 1–4) |
| **Pull Quote** | Italicized callout displayed prominently on the page |
| **Picture URL** | Hero image URL (hosted on GitHub Pages in `html/images/`) |
| **Intro** | 1–2 paragraph introduction text |
| **What does the science say?** | Background and context narrative |
| **Additional Information** | Links to resources, studies, reports |
| **What are others doing?** | Partner activities (e.g., "University of Nevada, Reno is researching...") |
| **What can you do?** | Public action items (e.g., "Learn about cooling centers near you") |
| **Related Outcomes** | Multi-select linking to other outcomes |

### CMS content structure per indicator (chart/map)

Each indicator is configured through the LT Info Indicators admin with two tabs:

**Overview tab (green box fields):**
- Display Name, Indicator Type, Data Source Type, Measurement Unit
- Definition (what is being measured and why)
- Sources (data attribution with links)

**Climate Resilience Dashboard tab (blue box fields):**
- Goal, Outcome, Indicator Number (e.g., "1.2.a")
- Indicator Map URL (link to a map HTML on GitHub Pages)
- Additional Charts (nested numbered list format — see below)
- Resilience Dashboard Description
- Resilience Dashboard Interpretation

### How charts are registered in the CMS

The "Additional Charts" field uses a **nested numbered list** format:

```
1. Temperature: Extreme Heat Days
   1. https://trpa-agency.github.io/ClimateResilienceDashboard/html/1.2.a_ExtremeHeatDays.html
   2. Meteostat Developers. (2022, February 18). Python Library.
   3. Description of the chart
2. Air Quality: O3 Concentration
   1. https://trpa-agency.github.io/ClimateResilienceDashboard/html/1.2.a_Air_Quality_O3.html
   2. Source citation
   3. Description
```

Format: Top level = **Title**, Nested-1 = **URL**, Nested-2 = **Source**, Nested-3 = **Description**

### What you build (visualization HTML files)

Each chart or map is a **standalone single-file HTML page** hosted at:
```
https://trpa-agency.github.io/ClimateResilienceDashboard/html/{filename}.html
```

These files follow the `trpa-dashboard-stack` patterns (Plotly.js, AG Grid, ArcGIS Maps SDK) but are **lightweight, embeddable chart pages** — not full dashboard pages with headers and footers. They may be displayed in iframes or linked directly from the CMS.

**Keep chart pages minimal:** No LT Info header/footer chrome. Just the visualization itself with a clean white/transparent background so it embeds cleanly into the CMS page.

Maps go in a separate subfolder:
```
https://trpa-agency.github.io/ClimateResilienceDashboard/html/Maps/{filename}.html
```

### File naming convention

Chart files follow the pattern: `{indicator_number}_{short_description}.html`

Examples from the existing dashboard:
- `1.2.a_ExtremeHeatDays.html`
- `1.2.a_Air_Quality_O3.html`
- `1.2.a_Air_Quality_PM2.5.html`
- `1.2.a_Air_Quality_PM10.html`
- `1.2.a_Purple_Air.html`
- `Maps/1.2.a_SmokeForecast.html`
- `4.1.d_commuter_patterns.html`

### Images

Hero images and other static assets are stored in:
```
https://trpa-agency.github.io/ClimateResilienceDashboard/html/images/
```

Image URLs are entered in the CMS "Picture URL" field.

---

## Goal Colors

Each of the 4 goals has a distinct color configured in the CMS (via the "Other 2" hex code field):

| Goal | Name | Color |
|------|------|-------|
| Goal 1 | Track Changing Climate Conditions | `#A9BCB0` (sage/muted green) |
| Goal 2 | Support a Resilient Environment | Configured per goal in CMS |
| Goal 3 | Promote a Resilient Built Environment | Configured per goal in CMS |
| Goal 4 | Increase Community Resilience | Configured per goal in CMS |

These colors appear as the goal card backgrounds on the main dashboard page. The hex codes are entered in the CMS admin — not hardcoded in the chart HTML files.

---

## Outcome List (14 outcomes across 4 goals)

The CMS currently has 14 outcomes:

| # | Short Name | Full Name |
|---|-----------|-----------|
| 1.1 | Greenhouse Gases and Carbon Sequestration | Reduce Greenhouse Gas (GHG) Emissions and Track... |
| 1.2 | Air Quality and Extreme Heat | Track Poor Air Quality, Wildfire Smoke, and Extreme... |
| 1.3 | Lake Conditions | Monitor Water Level, Temperature, and Clarity |
| 1.4 | Precipitation and Extreme Storms | Track Precipitation and Extreme Storm Trends |
| 2.1 | Forest Resilience and Wildfire Risk | Improve Forest Resilience and Reduce Wildfire Risk |
| 2.2 | Aquatic Invasive Species | Reduce and Control Aquatic Invasive Species |
| 2.3 | Watershed Resilience | Increase Watershed Resilience and Water Quality |
| 3.1 | Access to Housing | Expand Inclusive Access to Energy Efficient, Resilient... |
| 3.2 | Renewable Energy | Increase the Share of Renewable Energy Used |
| 3.3 | Transportation | Equitably Increase Access to Transit, Bicycle and... |
| 4.1 | Demographics and Workforce | Monitor Community Demographic, Housing Access... |
| 4.2 | Economic Resilience | Increase Tahoe's Economic Diversity and Resilience |
| 4.3 | Wildfire Resilience | Increase Community Resiliency to Wildfire... |
| 4.4 | Equitable Protection | *(additional outcome)* |

---

## Key Geographic Splits

Many indicators are displayed with a **North Shore / South Shore** split to align with transit systems (TART = North, TTD = South) and housing planning geographies. When building indicators with this split:

- Use Calcite `calcite-select` or `calcite-segmented-control` to toggle between "Basin Total", "North Shore", "South Shore"
- Default to Basin Total view
- Census tract aggregations define the North/South boundary
- Charts should use consistent colors: primary brand color for total, two tints for North/South

---

## Data Source Integration Patterns

### Linked to EIP Tracker
Indicators 2.1.a, 2.2.a, 2.3.a–c link to `eip.laketahoeinfo.org`. Fetch data from EIP REST APIs or embed existing EIP charts with narrative context.

### Linked to TRPA Threshold Dashboard
Indicators 1.3.a, 1.3.c, 2.1.b, 3.3.b link to `thresholds.laketahoeinfo.org`. Include target/standard lines on charts to show status relative to threshold.

### Linked to TRPA Transportation Dashboard
Indicators 3.3.a, 3.3.b, 3.3.d–f link to `transportation.laketahoeinfo.org`. Maintain consistency with Transportation Dashboard chart styles.

### US Census ACS 5-Year Estimates
Indicators 3.1.b, 4.1.a–d use Census data. These update annually. Use tract-level aggregations for North/South splits. Fetch via Census API or pre-processed CSV.

### UC Davis / TERC
Indicators 1.3.a–c, 1.4.a come from UC Davis State of the Lake reports. Typically annual data published each summer.

### ArcGIS Map-based indicators
Indicators 2.1.a (treated areas), 2.1.c (fire probability), 2.3.a (restored wetlands), 3.3.c (EV charging), 3.3.e (equity), 4.1.e (commuter origins), 4.3.a (evacuation) all include map views. Use ArcGIS Maps SDK with TRPA service layers and the standard Lake Tahoe center/zoom from `trpa-dashboard-stack`.

---

## Status Indicators

Some metrics have targets or thresholds. Display status using the Climate Dashboard status colors:

| Status | Meaning | Color | Token |
|--------|---------|-------|-------|
| On track | Meeting or exceeding target | `#27AE60` | `--climate-green` |
| Caution | Within range but trending wrong | `#F39C12` | `--climate-amber` |
| Off track | Below target | `#E74C3C` | `--climate-red` |
| No target | Informational only | `#0072CE` | `--climate-primary` |

Include target lines on Plotly charts where applicable:

```javascript
// Add a target line to a Plotly chart
const targetLine = {
  type: 'line',
  x0: xMin, x1: xMax,
  y0: targetValue, y1: targetValue,
  line: { color: '#27AE60', width: 2, dash: 'dash' }
};
layout.shapes = [targetLine];
layout.annotations = [{
  x: xMax, y: targetValue,
  text: 'Target',
  showarrow: false,
  font: { size: 11, color: '#27AE60' },
  xanchor: 'left'
}];
```

---

## Narrative Requirements

Each indicator subpage must include a short narrative section (2–4 sentences) above the charts that explains:

1. **What** is being measured and why it matters for climate resilience
2. **How** it connects to Tahoe specifically (not generic climate info)
3. **What actions** are being taken (link to programs, plans, or partners)

Follow TRPA style guide conventions: factual, neutral, no jargon, spell out acronyms on first use, Oxford comma, no symbols in prose.

Example for 1.2.a:
> "Poor air quality, wildfire smoke, and extreme heat are increasing in the Lake Tahoe Region due to climate change. These conditions threaten public health, recreation, and the visitor economy. TRPA and partners monitor air quality through the AirNow network and the TRPA Smoke Forecast tool to help residents and visitors plan around poor air days."

---

## Relationship to Other Dashboards

The Climate Resilience Dashboard intentionally links to and draws from other TRPA dashboards rather than duplicating data:

| Dashboard | Indicators that link to it |
|-----------|---------------------------|
| EIP Tracker | 2.1.a, 2.2.a, 2.3.a, 2.3.b, 2.3.c |
| Threshold Dashboard | 1.3.a, 1.3.c, 2.1.b, 3.3.b |
| Transportation Dashboard | 3.3.a, 3.3.b, 3.3.d, 3.3.e, 3.3.f |
| Parcel Tracker | 3.1.a, 3.1.c |

When an indicator's primary data lives in another dashboard, the climate subpage should provide climate-specific narrative context and link to the source dashboard for full details.
