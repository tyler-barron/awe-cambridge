# Awe in Cambridge — Project Instructions

## Git: Always Push to Main

**Always push changes directly to `main` so they are immediately visible at https://tyler-barron.github.io/awe-cambridge/**

```
git push origin main
# or from a worktree branch:
git push origin HEAD:main
```

Never leave changes only on a feature branch. After every commit, push to `main`.

## Project Overview

This is Tyler Barron's MCP / DUSP 2026 thesis project — an interactive web atlas exploring awe in Cambridge, MA. It is a static site hosted on GitHub Pages at `https://tyler-barron.github.io/awe-cambridge/`.

### Key Pages
- `index.html` — Main Awe Atlas entry point
- `rhythm-flow.html` — Tool 04: Interactive rhythmanalysis & rhythmactivation flow diagram
- `rhythm.html` — Diagram view of rhythms
- `atlas.html` / `awe-atlas-v5_6.html` — Atlas map views
- `alluvial.html` — Alluvial diagram
- `community.html` — Community data view
- `guide.html` — User guide

### Theoretical Framework (Lefebvre Rhythmanalysis)
The project applies Henri Lefebvre's Rhythmanalysis to awe experiences in Cambridge. The four analytical dimensions are:

1. **Geography** — 9 place types (parks, streets, waterfronts, etc.)
2. **Morphology** — 15 physical forms + 8 Wonders of Life, ordered **Stable → Dynamic** (Architecture → Weather)
3. **Phenomenology** — 6 tension pairs (Ornate↔Functional, Collective↔Individual, Wild↔Curated, Familiar↔Novel, Stable↔Dynamic, Enclosed↔Expansive) + 4 binaries
4. **Temporality** — 7 frequencies ordered **Stable → Dynamic** (History/Timeless → Ephemeral)

### Four Awe Archetypes (from thesis data, n=220)
- **Expansive Nature** — Vista + Waterfront + Timeless
- **Wild Nature** — Nature + Plants + Alterity + Seasonal + Parks (most prevalent, n=85)
- **Built Beauty** — Architecture + Visual Design + Timeless + Streets
- **Inclusive Interaction** — Collective Effervescence + People + Events + Recurring + Civic

### Reference PDFs (in project root)
- `barron-tlbarron-mcp-dusp-2026-thesis.pdf` — Full thesis
- `rhythmanalysis.pdf` — Lefebvre rhythmanalysis framework
- `rhythmactivation.pdf` — Rhythmactivation methodology
- `archetypes.pdf` — Awe archetypes analysis
- `citiesofawe.pdf` — Cities of Awe reference

### Data
- `awe-data.csv` / `awe_with_clusters.csv` — 220 georeferenced awe instances
- `cambridge_boundary.geojson` / `cambridge_openspace.geojson` — Spatial boundaries
- `cambridge_shapefiles/` — BOUNDARY_CityBoundary + RECREATION_OpenSpace shapefiles

### Style Conventions
- Fonts: Cormorant Garamond (serif, display) + Space Mono (monospace, labels)
- Color palette: `--ink #1a1a1a`, `--parchment #f6f6f6`, `--accent #8c4518`, `--geo #4a7a8a`, `--morph #8c4518`, `--phen #6b5b8a`, `--tempo #a07c2a`
- Stable→Dynamic spectrum: `--stable #3a6080` (blue-gray) → `--dynamic #c07030` (amber)
- Design language: editorial, archival, glassmorphic — grain texture overlay, Cormorant for headings
