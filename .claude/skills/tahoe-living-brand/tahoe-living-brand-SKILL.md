---
name: tahoe-living-brand
description: "Tahoe Living / Cultivating Community, Conserving the Basin brand guidelines. Use this skill when building any web page, dashboard, tool, or visualization for the Tahoe Living housing initiative, the Cultivating Community project, or any TRPA housing-related work. Tahoe Living has its own logo and palette (lake blue, mauve, green, purple) distinct from the institutional TRPA blue. Trigger on any mention of: Tahoe Living, Cultivating Community, Conserving the Basin, tahoeliving.org, TRPA housing, housing assessment, growth management, workforce housing, affordable housing at Tahoe, community engagement housing, or housing equity Tahoe."
---

# Tahoe Living — Cultivating Community, Conserving the Basin

Brand guidelines for **Tahoe Living**, TRPA's community-facing housing and growth management initiative. The site lives at [tahoeliving.org](https://www.tahoeliving.org/) and is a more approachable identity than the institutional TRPA brand — designed to welcome community members, renters, workers, and historically underrepresented groups into the planning conversation.

This brand is used for housing dashboards, community engagement tools, survey results, housing needs data, growth management visualizations, and the Environmental Impact Statement materials.

**Source of truth:** the palette, logo colors, and fonts below were taken from the logo master files (in `logos/`) and the live tahoeliving.org stylesheet on 2026-09-09. An earlier version of this skill described a sage/terracotta palette with Montserrat; that was wrong and has been replaced. If tahoeliving.org changes, re-sample the site before trusting this file.

---

## Brand Personality

Tahoe Living's visual identity is **bright, friendly, and inclusive**. Where the TRPA agency brand says "government authority," this brand says "your neighbor who cares about your housing situation." The logo panels — people, trees, and a house inside the outline of the lake — carry the whole message: community, environment, and homes belong together.

Key qualities:
- **Welcoming** — not institutional; designed for community audiences, not regulators
- **Equity-centered** — visuals and language are inclusive of BIPOC communities, renters, and low-income households
- **Environmental** — the lake and forest are always part of the picture, never a backdrop
- **Hopeful** — this is about solutions, not just problems

---

## Color Palette

The four hues come straight from the logo: lake **blue** (outline and wordmark), **purple** (people panel), **green** (trees panel), and **mauve** (house panel). tahoeliving.org publishes a five-step ramp for each hue; the middle step is the logo color.

### Core colors (logo values)

| Token           | Hex       | RGB           | Usage                                              |
|-----------------|-----------|---------------|----------------------------------------------------|
| `--tl-blue`     | `#0A7EC2` | 10, 126, 194  | Primary. Links, buttons, overlines, primary series |
| `--tl-mauve`    | `#A766AA` | 167, 102, 170 | Accent / CTA, highlights, second series            |
| `--tl-green`    | `#93A959` | 147, 169, 89  | Environment, ADUs, positive indicators             |
| `--tl-purple`   | `#5F57A5` | 95, 87, 165   | People, deed-restricted / affordability            |

### Ramps (from tahoeliving.org)

| Hue    | Pale      | Light     | **Base**    | Dark      | Deepest   |
|--------|-----------|-----------|-------------|-----------|-----------|
| Blue   | `#A0CFEB` | `#71B1D6` | **`#0A7EC2`** | `#075481` | `#032A41` |
| Mauve  | `#E1C4E3` | `#C59FC6` | **`#A766AA`** | `#6F4471` | `#382239` |
| Green  | `#D9E2BF` | `#B9C697` | **`#93A959`** | `#62713B` | `#31381E` |
| Purple | `#C1BEE1` | `#9A95C3` | **`#5F57A5`** | `#3F3A6E` | `#201D37` |

Use the dark step for hover states, footers, and large numbers (`--tl-blue-dark` is the workhorse). Use pale and light steps for fills behind text, sequential chart scales, and map fills.

### Neutrals

The site uses plain neutral grays on a white background — there is no cream tint.

| Token                  | Hex       | Usage                                  |
|------------------------|-----------|----------------------------------------|
| `--tl-white`           | `#FFFFFF` | Page and card background               |
| `--tl-bg-section`      | `#F3F5F7` | Alternating section background         |
| `--tl-border`          | `#E2E2E2` | Borders, dividers, chart gridlines     |
| `--tl-text-muted`      | `#757575` | Placeholder text, captions, disabled   |
| `--tl-text-secondary`  | `#404040` | Secondary copy, labels                 |
| `--tl-text-primary`    | `#202020` | Body text, headings                    |

### CSS variables

```css
:root {
  /* Core (logo) */
  --tl-blue:            #0A7EC2;
  --tl-blue-dark:       #075481;
  --tl-blue-light:      #71B1D6;
  --tl-blue-pale:       #A0CFEB;
  --tl-mauve:           #A766AA;
  --tl-mauve-dark:      #6F4471;
  --tl-mauve-light:     #C59FC6;
  --tl-green:           #93A959;
  --tl-green-dark:      #62713B;
  --tl-green-light:     #B9C697;
  --tl-purple:          #5F57A5;
  --tl-purple-dark:     #3F3A6E;
  --tl-purple-light:    #9A95C3;

  /* Neutrals */
  --tl-white:           #FFFFFF;
  --tl-bg:              #FFFFFF;
  --tl-bg-section:      #F3F5F7;
  --tl-border:          #E2E2E2;
  --tl-text-muted:      #757575;
  --tl-text-secondary:  #404040;
  --tl-text-primary:    #202020;
}
```

### Contrast notes

- `#0A7EC2` on white passes WCAG AA for normal text (4.6:1). `#93A959` and `#71B1D6` do **not** — use them for fills, bars, and large display text only, never for body copy or small labels on white.
- `#A766AA` on white is borderline (4.1:1). Fine for bars and headings 18px+; use `#6F4471` for small text.
- White text on `#075481` or `#5F57A5` is safe; white on `#93A959` is not.

---

## Typography

tahoeliving.org pairs a geometric sans for headings and UI with a serif for reading copy.

- **Poppins** — headings, navigation, labels, buttons, KPI numbers, chart and table text. This is also the closest Google Font to the rounded sans in the logo wordmark.
- **EB Garamond** — long-form paragraphs on content pages (about text, stories, explanations). Optional on data dashboards; use it for the intro lede and featured-project blurbs if you want the site's editorial feel.

```html
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet" />
```

```css
body {
  font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 400;
  font-size: 16px;
  line-height: 1.6;
  color: var(--tl-text-primary);
  background: var(--tl-bg);
}
.prose { font-family: 'EB Garamond', Georgia, serif; font-size: 1.125rem; line-height: 1.7; }
```

### Type scale

| Element         | Weight | Size      | Notes                                    |
|-----------------|--------|-----------|------------------------------------------|
| Hero heading    | 700    | 2.5rem    | Large section openers, page titles       |
| Section h2      | 600    | 1.75rem   | Section headings                         |
| Card h3         | 600    | 1.2rem    | Card titles, chart titles                |
| Overline/label  | 500    | 0.75rem   | Section labels ("WHO WE ARE"), uppercase, blue |
| Body            | 400    | 1rem      | Default prose (Poppins or EB Garamond)   |
| Caption         | 400    | 0.85rem   | Source notes, footnotes                  |
| KPI value       | 700    | 2.25rem   | Large metric numbers, `--tl-blue-dark`   |
| KPI label       | 400    | 0.85rem   | Descriptor below KPI values              |

### Overline pattern

Small uppercase labels above section headings are a signature pattern:

```css
.overline {
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--tl-blue);
  margin-bottom: 0.5rem;
}
```

```html
<p class="overline">Who we are</p>
<h2>What is "Cultivating Community, Conserving the Basin?"</h2>
```

---

## Logo

The Tahoe Living logo is a bold outline of Lake Tahoe in blue, filled with three colored panels that each carry a white icon: **purple** (a family, top), **green** (pine trees, middle), and **mauve** (a house, bottom). The "Tahoe Living" wordmark sits to the right in the same blue. It is a filled, multi-color mark — not a line drawing — and it is not the TRPA institutional logo.

**Asset files** (in this skill's `logos/` folder; do not redraw the logo in SVG or CSS):

| File | Use |
|------|-----|
| `TahoeLiving_Logo_COLOR.png` | Full-color master, 3000 x 3001 px with a wide transparent margin |
| `TahoeLiving_Logo_WHITE.png` | All-white master for dark backgrounds, same dimensions |
| `TahoeLiving_Logo_COLOR_trimmed.png` | Color, margin trimmed (1800 x 1542) — use for web |
| `TahoeLiving_Logo_WHITE_trimmed.png` | White, margin trimmed — use for web on dark backgrounds |

For a web page, copy the trimmed version into the page's `assets/` folder and scale it down (about 800 px wide is plenty). The `LongRange/html/assets/` folder in the Planning repo already has `tahoe-living-logo-color.png`, `tahoe-living-logo-white.png`, and `trpa-logo-white.png` ready to use.

**Logo colors** (sampled from the master file; they are the same hues as the palette above, within a few RGB points of the site values):

| Element | Logo file | Palette token |
|---------|-----------|---------------|
| Lake outline and wordmark | `#107CC0` | `--tl-blue` `#0A7EC2` |
| Purple panel (people) | `#5C54A4` | `--tl-purple` `#5F57A5` |
| Green panel (trees) | `#90A858` | `--tl-green` `#93A959` |
| Mauve panel (house) | `#A464A8` | `--tl-mauve` `#A766AA` |

**Logo placement:**
- Top-left of the header, linking to tahoeliving.org. Render it 40–48 px tall on desktop so the wordmark stays legible; the wordmark is part of the image, so do not repeat "Tahoe Living" as text beside it.
- On white or light backgrounds use the color version. On `--tl-blue-dark`, `--tl-purple-dark`, or any dark background use the white version.
- Keep clear space around the mark of at least the height of the wordmark's capital "T". Do not stretch, recolor, crop the lake outline, or put the color version on a busy photo.

```html
<a class="brand-mark" href="https://www.tahoeliving.org/" aria-label="Tahoe Living">
  <img src="assets/tahoe-living-logo-color.png" alt="Tahoe Living" height="40" />
</a>
```

**TRPA co-branding:**
- The TRPA logo appears in the **footer only**, not in the header. Use the white TRPA logo (`trpa-brand/logos/TRPALogo_WHITE.png`) on the dark-blue footer, next to the white Tahoe Living logo.
- Tahoe Living is the lead brand in the header; TRPA is the authority in the footer.
- This deliberate separation keeps the community-facing feel in the navigation while maintaining institutional credibility at the page bottom.

---

## Page Layout Patterns

### Header / Navigation

Clean, minimal sticky nav on white with the logo on the left and horizontal nav links.

```css
.tl-nav {
  background: var(--tl-white);
  border-bottom: 1px solid var(--tl-border);
  padding: 0.5rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.tl-nav a { color: var(--tl-text-primary); text-decoration: none; font-weight: 500; font-size: 0.9rem; }
.tl-nav a:hover { color: var(--tl-blue); }
```

### Hero sections

Full-width photography with overlaid text, using a dark-blue gradient for legibility:

```css
.tl-hero {
  position: relative;
  background-size: cover;
  background-position: center;
  min-height: 400px;
  display: flex;
  align-items: flex-end;
  padding: 3rem 2rem;
}
.tl-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(3,42,65,0.8) 0%, transparent 60%);
}
.tl-hero h1 { position: relative; z-index: 1; color: #fff; font-size: 2.5rem; font-weight: 700; max-width: 700px; }
```

### Content sections with alternating backgrounds

```css
.section { padding: 4rem 2rem; }
.section--white { background: var(--tl-white); }
.section--gray  { background: var(--tl-bg-section); }
```

### Cards

```css
.tl-card {
  background: var(--tl-white);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(32,32,32,0.06);
  border: 1px solid var(--tl-border);
}
```

Border radius is `12px` (rounder than TRPA's `6px`) to keep the friendly feel.

### KPI cards

Left border color-codes the metric (blue default; mauve, purple, green for the logo's other panels).

```css
.tl-kpi {
  background: var(--tl-white);
  border-radius: 12px;
  padding: 1.5rem;
  border-left: 4px solid var(--tl-blue);
  box-shadow: 0 2px 8px rgba(32,32,32,0.06);
}
.tl-kpi .value { font-size: 2.25rem; font-weight: 700; color: var(--tl-blue-dark); }
.tl-kpi .label { font-size: 0.85rem; color: var(--tl-text-secondary); margin-top: 0.25rem; }
```

### Buttons

```css
/* Primary — blue */
.tl-btn-primary {
  background: var(--tl-blue);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-family: 'Poppins', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.tl-btn-primary:hover { background: var(--tl-blue-dark); }

/* Accent — mauve, for the one call to action on a page */
.tl-btn-accent { background: var(--tl-mauve); color: #fff; }
.tl-btn-accent:hover { background: var(--tl-mauve-dark); }

/* Secondary — outlined blue */
.tl-btn-secondary {
  background: transparent;
  color: var(--tl-blue);
  border: 2px solid var(--tl-blue);
  border-radius: 8px;
  padding: 0.65rem 1.5rem;
  font-family: 'Poppins', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}
.tl-btn-secondary:hover { background: var(--tl-blue); color: #fff; }
```

### Footer

```css
.tl-footer {
  background: var(--tl-blue-dark);
  color: rgba(255,255,255,0.85);
  padding: 2.5rem 2rem;
  font-size: 0.85rem;
}
.tl-footer a { color: rgba(255,255,255,0.9); }
.tl-footer a:hover { color: var(--tl-green-light); }
```

The footer carries the white Tahoe Living logo, the white TRPA logo, mailing address, social links, and partner attribution.

---

## Chart & Data Visualization Colors

### Default chart color sequence

```javascript
const TL_COLORS = [
  '#0A7EC2',  // Blue (primary series)
  '#A766AA',  // Mauve
  '#93A959',  // Green
  '#5F57A5',  // Purple
  '#075481',  // Blue dark
  '#C59FC6',  // Mauve light
  '#62713B',  // Green dark
  '#9A95C3',  // Purple light
];
```

### Plotly.js layout for Tahoe Living

```javascript
const TL_LAYOUT = {
  font: { family: 'Poppins, system-ui, sans-serif', color: '#202020', size: 13 },
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  margin: { t: 30, r: 20, b: 40, l: 50 },
  xaxis: { gridcolor: '#E2E2E2', linecolor: '#E2E2E2' },
  yaxis: { gridcolor: '#E2E2E2', linecolor: '#E2E2E2' },
  colorway: ['#0A7EC2', '#A766AA', '#93A959', '#5F57A5', '#075481', '#C59FC6', '#62713B', '#9A95C3'],
  hovermode: 'x unified',   // 'y unified' for horizontal bars
  hoverlabel: { bgcolor: '#FFFFFF', bordercolor: '#E2E2E2', font: { family: 'Poppins, sans-serif', color: '#202020' } }
};
```

Always use unified hover (`x unified`, or `y unified` for horizontal bar charts) with a white hover label so stacked series read as one row.

### Housing-specific data patterns

Locked category colors — use the same color everywhere the category appears:

| Category                    | Color        | Hex       |
|-----------------------------|--------------|-----------|
| Market rate / non-restricted | Blue        | `#0A7EC2` |
| Affordable & workforce      | Mauve        | `#A766AA` |
| Deed-restricted             | Purple       | `#5F57A5` |
| ADU                         | Green        | `#93A959` |
| Pipeline / proposed         | Green (map) or light blue `#71B1D6` (charts) | |
| Tourist / seasonal          | Gray         | `#757575` |

Income levels (sequential, purple-to-blue):

| Category                     | Hex       |
|------------------------------|-----------|
| Very low income (≤30% AMI)   | `#3F3A6E` |
| Low income (30–50% AMI)      | `#5F57A5` |
| Moderate income (50–80% AMI) | `#A766AA` |
| Above moderate (80–120% AMI) | `#0A7EC2` |
| Market rate (>120% AMI)      | `#757575` |

### Maps

- Basemap `gray-vector`; switch to `hybrid` via BasemapToggle for parcel context.
- Point and polygon fills use the locked category colors above at 85 percent opacity with a thin white outline.
- Map labels (including cluster labels) must use an Esri-hosted font such as `Noto Sans` — Poppins is not available to the ArcGIS label engine and will stall the layer.

---

## Photography & Imagery

Warm, people-centered photography showing:

- Diverse community members (families, workers, neighbors)
- Tahoe neighborhoods and streetscapes (not pristine wilderness — this is about *living* in Tahoe)
- Construction and housing (new builds, ADUs, multi-family)
- Community meetings and engagement events

Photography is displayed full-bleed or in large rounded containers, with the dark-blue gradient overlay for text readability.

**Avoid:** stock-photo-looking imagery, exclusively lakefront/tourism shots (this is a housing project, not a tourism site), images that only show affluent settings.

---

## Bilingual / Accessibility Notes

Tahoe Living content is produced in **English and Spanish**. When building tools:

- Include language toggle or bilingual labels where appropriate
- Ensure all chart labels and data table headers can accommodate Spanish translations (which tend to be ~20% longer than English)
- Use ARIA labels on interactive elements
- Check contrast: green and light blue fail AA for small text on white (see Contrast notes above)

---

## Tone & Voice

- **Conversational and direct** — not bureaucratic; "we" and "you" language
- **Community-oriented** — speak to people as neighbors, not as permit applicants
- **Equity-aware** — acknowledge housing disparities without being clinical about them
- **Action-oriented** — emphasize participation: "Get involved," "Sign up," "Share your experience"
- **Bilingual-friendly** — keep sentences clear and translatable; avoid idioms

Example labels:
- ✓ "Housing units needed" (clear, direct)
- ✗ "Projected residential unit demand allocation" (too institutional)
- ✓ "People who rent" (human)
- ✗ "Renter-occupied households" (census-speak)

---

## Relationship to Other TRPA Brands

| Context                          | Brand to use          |
|----------------------------------|-----------------------|
| General TRPA agency tools        | `trpa-brand`          |
| EIP environmental projects       | `trpa-eip-brand`      |
| Housing / Tahoe Living / community engagement | **`tahoe-living-brand`** (this skill) |
| Dashboard tech stack (always)    | `trpa-dashboard-stack` |

Tahoe Living is a **sub-brand** of TRPA. The TRPA logo appears in the footer for credibility, but the header, colors, and feel are entirely Tahoe Living. When building dashboards for housing data that will live on tahoeliving.org or be embedded in Tahoe Living materials, use this brand. When building the same housing data for an internal TRPA report or trpa.gov page, use `trpa-brand` instead.

Reference implementation: `LongRange/html/multifamily-housing.html` in the Planning repo (header, KPIs, filters, Plotly charts, clustered ArcGIS map, AG Grid table, footer).
