"""
Run this script once to regenerate alluvial.html from the CSV.
  python build_alluvial.py
"""
import csv, json, io, os

csv_path = 'awe-data.csv'
with open(csv_path, encoding='utf-8-sig') as f:
    raw = f.read()

reader = csv.DictReader(io.StringIO(raw))
rows = [{k.strip(): v.strip() for k, v in r.items()} for r in reader]
data_json = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))

print(f'Loaded {len(rows)} records')

# ── HTML template ──────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Awe Atlas — Alluvial Explorer</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Space+Mono&display=swap" rel="stylesheet">
<style>
:root{--ink:#1c1914;--parchment:#f4f0e7;--linen:#e3d4c5;--stone:#b7aea2;--accent:#8c4518;--saffron:#caa74d;--muted:#6b6259;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;background:var(--parchment);color:var(--ink);font-family:"Cormorant Garamond",serif;}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:9000;opacity:.4;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E");}
.page{display:flex;flex-direction:column;height:100vh;overflow:hidden;}

/* ── Header ── */
.site-header{flex-shrink:0;padding:12px 24px;border-bottom:1px solid rgba(140,69,24,.2);display:flex;align-items:center;gap:16px;background:var(--parchment);z-index:100;}
.header-back{font-family:"Space Mono",monospace;font-size:10px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .2s;}
.header-back:hover{color:var(--accent);}
.header-title{font-size:20px;font-weight:300;}
.header-title em{font-style:italic;color:var(--accent);}
.header-count{font-family:"Space Mono",monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--stone);margin-left:auto;}
.header-count.filtered{color:var(--accent);}

/* ── Controls bar ── */
.controls-bar{flex-shrink:0;background:rgba(255,255,255,.5);border-bottom:2px solid rgba(140,69,24,.12);padding:10px 24px 8px;}
.ctrl-top{display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap;margin-bottom:8px;}
.ctrl-bottom{display:flex;align-items:center;gap:6px;flex-wrap:wrap;min-height:30px;}
.chips-label{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:var(--stone);flex-shrink:0;}

/* ── Category dropdown buttons ── */
.cat-btn-wrap{position:relative;}
.cat-btn{display:flex;align-items:center;gap:6px;padding:6px 13px;border-radius:2px;border:none;cursor:pointer;font-family:"Space Mono",monospace;font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:white;transition:opacity .15s;}
.cat-btn:hover{opacity:.85;}
.cat-arrow{font-size:8px;transition:transform .2s;display:inline-block;}
.cat-btn.open .cat-arrow{transform:rotate(180deg);}
.cat-dropdown{display:none;position:absolute;top:calc(100% + 4px);left:0;z-index:600;background:var(--parchment);border:1px solid rgba(140,69,24,.22);border-radius:3px;box-shadow:0 8px 24px rgba(28,25,20,.14);padding:8px;min-width:185px;}
.cat-dropdown.open{display:block;}
.cat-dd-title{font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.3em;text-transform:uppercase;color:var(--stone);padding:2px 6px 6px;border-bottom:1px solid rgba(140,69,24,.1);margin-bottom:4px;}
.cat-option{display:flex;align-items:center;gap:8px;padding:6px 7px;border-radius:2px;cursor:pointer;user-select:none;transition:background .15s;}
.cat-option:hover{background:rgba(140,69,24,.06);}
.cat-option input{accent-color:var(--accent);cursor:pointer;width:13px;height:13px;flex-shrink:0;}
.cat-opt-label{font-family:"Space Mono",monospace;font-size:10px;letter-spacing:.06em;color:var(--ink);}

/* ── Active chips ── */
.active-chips{display:flex;align-items:center;gap:5px;flex-wrap:wrap;}
.no-chips-hint{font-family:"Space Mono",monospace;font-size:9px;color:var(--stone);font-style:italic;}
.dim-chip{display:flex;align-items:center;gap:4px;padding:4px 8px 4px 9px;border-radius:2px;font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:white;cursor:grab;user-select:none;transition:opacity .15s;}
.dim-chip.dragging{opacity:.4;cursor:grabbing;}
.dim-chip.drag-over{outline:2px dashed rgba(255,255,255,.6);}
.dca{background:none;border:none;color:rgba(255,255,255,.55);font-size:10px;line-height:1;cursor:pointer;padding:0;transition:color .15s;}
.dca:hover{color:white;}
.dca:disabled{opacity:.2;cursor:default;}
.dcx{background:none;border:none;color:rgba(255,255,255,.5);font-size:11px;line-height:1;cursor:pointer;padding:0 0 0 3px;transition:color .15s;}
.dcx:hover{color:white;}

/* ── Filter bar ── */
.filter-bar{flex-shrink:0;display:none;align-items:center;gap:6px;padding:6px 24px 7px;background:rgba(140,69,24,.05);border-bottom:1px solid rgba(140,69,24,.14);flex-wrap:wrap;}
.filter-bar.show{display:flex;}
.filter-label{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:var(--accent);flex-shrink:0;margin-right:2px;}
.filter-tags{display:flex;flex-wrap:wrap;gap:4px;align-items:center;}
.ftag{display:inline-flex;align-items:center;gap:4px;padding:3px 7px;border-radius:2px;font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:white;}
.ftag-x{background:none;border:none;color:rgba(255,255,255,.55);font-size:10px;line-height:1;cursor:pointer;padding:0;transition:color .15s;}
.ftag-x:hover{color:white;}
.filter-clear{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);background:none;border:1px solid rgba(140,69,24,.22);padding:3px 9px;border-radius:1px;cursor:pointer;margin-left:6px;transition:color .15s,border-color .15s;}
.filter-clear:hover{border-color:var(--accent);color:var(--accent);}
.filter-hint{font-family:"Space Mono",monospace;font-size:8px;color:var(--stone);font-style:italic;margin-left:auto;}

/* ── Main body ── */
.main-body{flex:1;display:flex;overflow:hidden;min-height:0;}
.diagram-area{flex:1;position:relative;overflow:hidden;min-width:0;}
#alluvial-svg{width:100%;height:100%;display:block;}

/* SVG */
.sankey-link{fill:none;stroke-opacity:.3;transition:stroke-opacity .18s;cursor:pointer;}
.sankey-link:hover{stroke-opacity:.75;}
.sankey-link.dim{stroke-opacity:.04;}
.sankey-node rect{cursor:pointer;transition:stroke .15s;}
.sankey-node.dim rect{opacity:.18;}
.sankey-node.sel rect{stroke:rgba(255,255,255,.9);stroke-width:2.5;}
.slabel{font-family:"Space Mono",monospace;font-size:10px;fill:var(--ink);pointer-events:none;}
.scol{font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.22em;text-transform:uppercase;}

/* ── Empty state ── */
.diagram-msg{position:absolute;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;gap:10px;font-style:italic;color:var(--stone);font-size:17px;pointer-events:none;}
.diagram-msg.show{display:flex;}
.diagram-msg span{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--linen);}

/* ── Detail panel ── */
.detail-panel{width:0;overflow:hidden;border-left:1px solid transparent;background:var(--parchment);transition:width .3s,border-color .3s;flex-shrink:0;}
.detail-panel.open{width:310px;border-left-color:rgba(140,69,24,.18);}
.detail-inner{width:310px;overflow-y:auto;height:100%;}
.dhd{padding:15px 18px 12px;border-bottom:1px solid rgba(140,69,24,.12);display:flex;align-items:flex-start;gap:8px;}
.dhd-text{flex:1;}
.dey{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.3em;text-transform:uppercase;color:var(--accent);margin-bottom:3px;}
.dtitl{font-size:18px;font-weight:300;line-height:1.25;}
.dcnt{font-family:"Space Mono",monospace;font-size:9px;color:var(--muted);margin-top:2px;}
.dcls{background:none;border:none;font-size:15px;color:var(--stone);cursor:pointer;padding:0;flex-shrink:0;transition:color .15s;}
.dcls:hover{color:var(--accent);}
.dlist{padding:8px 18px 28px;}
.ditem{padding:10px 0;border-bottom:1px solid rgba(140,69,24,.08);}
.ditem:last-child{border-bottom:none;}
.dname{font-size:14px;line-height:1.3;margin-bottom:3px;}
.dtags{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px;}
.dtag{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.12em;text-transform:uppercase;padding:2px 6px;border-radius:1px;color:white;}
.ddesc{font-size:11px;line-height:1.65;color:var(--muted);font-style:italic;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}

/* ── Tooltip ── */
#tt{position:fixed;z-index:8000;background:var(--ink);color:var(--parchment);padding:7px 11px;border-radius:2px;font-family:"Space Mono",monospace;font-size:9px;line-height:1.6;pointer-events:none;opacity:0;transition:opacity .15s;max-width:210px;}
#tt.on{opacity:1;}
#tt strong{color:var(--saffron);}

/* ── Guide panel ── */
.guide-backdrop{display:none;position:fixed;inset:0;z-index:6000;background:rgba(28,25,20,.3);}
.guide-backdrop.open{display:block;}
.guide-panel{position:fixed;top:0;right:-420px;bottom:0;width:420px;z-index:6001;background:var(--parchment);border-left:1px solid rgba(140,69,24,.2);box-shadow:-8px 0 32px rgba(28,25,20,.18);overflow-y:auto;transition:right .3s cubic-bezier(.22,.61,.36,1);display:flex;flex-direction:column;}
.guide-panel.open{right:0;}
.guide-panel-header{position:sticky;top:0;background:var(--parchment);padding:14px 18px 12px;border-bottom:1px solid rgba(140,69,24,.14);display:flex;align-items:center;gap:10px;z-index:2;flex-shrink:0;}
.guide-panel-title{font-size:18px;font-weight:300;flex:1;}
.guide-panel-title em{font-style:italic;color:var(--accent);}
.guide-panel-close{background:none;border:none;font-size:16px;color:var(--stone);cursor:pointer;padding:0;transition:color .15s;}
.guide-panel-close:hover{color:var(--accent);}
.guide-panel-hint{font-family:"Space Mono",monospace;font-size:8px;color:var(--stone);padding:8px 18px 0;font-style:italic;flex-shrink:0;}
.guide-full-link{display:block;margin:10px 18px 0;padding:7px 12px;background:rgba(140,69,24,.07);border:1px solid rgba(140,69,24,.18);border-radius:2px;font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent);text-decoration:none;text-align:center;transition:background .15s;}
.guide-full-link:hover{background:rgba(140,69,24,.13);}
.guide-dim-section{border-bottom:1px solid rgba(140,69,24,.1);flex-shrink:0;}
.guide-dim-toggle{width:100%;padding:12px 18px;background:none;border:none;cursor:pointer;display:flex;align-items:center;gap:10px;text-align:left;transition:background .15s;}
.guide-dim-toggle:hover{background:rgba(140,69,24,.04);}
.guide-dim-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0;}
.guide-dim-name{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;flex:1;}
.guide-dim-num{font-family:"Space Mono",monospace;font-size:8px;color:var(--stone);}
.guide-dim-arrow{font-size:9px;color:var(--stone);transition:transform .2s;}
.guide-dim-toggle.open .guide-dim-arrow{transform:rotate(180deg);}
.guide-dim-body{display:none;padding:0 18px 14px;}
.guide-dim-body.open{display:block;}
.guide-col-block{margin-bottom:12px;}
.guide-col-label{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.3em;text-transform:uppercase;color:var(--stone);margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid rgba(140,69,24,.08);}
.guide-val-row{display:flex;gap:8px;padding:4px 0;border-bottom:1px solid rgba(140,69,24,.05);}
.guide-val-row:last-child{border-bottom:none;}
.guide-val-name{font-size:12px;font-weight:400;min-width:110px;flex-shrink:0;color:var(--ink);}
.guide-val-def{font-size:11px;color:var(--muted);font-style:italic;line-height:1.45;flex:1;}
.guide-heuristic{font-family:"Space Mono",monospace;font-size:7px;color:var(--accent);line-height:1.4;margin-top:2px;display:block;}
.guide-tension-row{padding:6px 0;border-bottom:1px solid rgba(140,69,24,.05);}
.guide-tension-row:last-child{border-bottom:none;}
.guide-tension-poles{font-size:13px;color:var(--ink);margin-bottom:2px;}
.guide-tension-poles em{font-style:italic;color:#b05a3a;}
.guide-tension-def{font-size:11px;color:var(--muted);font-style:italic;line-height:1.45;}
</style>
</head>
<body>
<div class="page">

<header class="site-header">
  <a href="index.html" class="header-back">← Threshold</a>
  <div class="header-title">Awe <em>Alluvial</em></div>
  <div class="header-count" id="hcount">220 instances</div>
  <button class="header-guide-btn" id="guide-toggle-btn" onclick="toggleGuide()" title="Understanding Awe — dimension reference">
    <span>?</span> Guide
  </button>
</header>
<style>
.header-guide-btn{margin-left:12px;padding:5px 11px;background:none;border:1px solid rgba(140,69,24,.28);border-radius:2px;font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:5px;transition:color .15s,border-color .15s;}
.header-guide-btn:hover,.header-guide-btn.active{border-color:var(--accent);color:var(--accent);}
.header-guide-btn span{font-size:10px;font-weight:bold;}
</style>

<div class="controls-bar">
  <div class="ctrl-top" id="cat-btns">
    <div class="usage-hint">
      <span class="usage-step"><span class="usage-num">1</span> Pick columns from the dropdowns to build the diagram.</span>
      <span class="usage-step"><span class="usage-num">2</span> Click any node to filter by that value.</span>
      <span class="usage-step"><span class="usage-num">3</span> Drag chips to reorder columns.</span>
      <span class="usage-step"><span class="usage-num">4</span> Click <strong>? Guide</strong> for definitions of every category.</span>
    </div>
  </div>
  <div class="ctrl-bottom">
    <span class="chips-label">Active:</span>
    <div class="active-chips" id="active-chips">
      <div class="no-chips-hint">Select columns from the dropdowns above</div>
    </div>
  </div>
</div>
<style>
.usage-hint{display:flex;flex-wrap:wrap;align-items:center;gap:6px 18px;margin-left:auto;padding:2px 0;}
.usage-step{font-family:"Space Mono",monospace;font-size:9px;color:var(--muted);letter-spacing:.04em;display:flex;align-items:center;gap:5px;}
.usage-step strong{color:var(--ink);}
.usage-num{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border-radius:50%;background:var(--linen);border:1px solid rgba(140,69,24,.18);font-size:8px;color:var(--muted);flex-shrink:0;}
</style>

<div class="filter-bar" id="filter-bar">
  <span class="filter-label">Filtering:</span>
  <div class="filter-tags" id="filter-tags"></div>
  <button class="filter-clear" id="filter-clear">✕ clear all</button>
  <span class="filter-hint">click a node to add · click again to remove</span>
</div>

<div class="main-body">
  <div class="diagram-area" id="diagram-area">
    <svg id="alluvial-svg"></svg>
    <div class="diagram-msg show" id="diagram-msg">
      Select at least two columns above
      <span>Use the category dropdowns to get started</span>
    </div>
  </div>
  <div class="detail-panel" id="detail-panel">
    <div class="detail-inner">
      <div class="dhd">
        <div class="dhd-text">
          <div class="dey" id="d-ey"></div>
          <div class="dtitl" id="d-titl"></div>
          <div class="dcnt" id="d-cnt"></div>
        </div>
        <button class="dcls" id="d-cls">&#x2715;</button>
      </div>
      <div class="dlist" id="d-list"></div>
    </div>
  </div>
</div>

</div>
</div>

<!-- ===== GUIDE PANEL ===== -->
<div class="guide-backdrop" id="guide-backdrop" onclick="closeGuide()"></div>
<div class="guide-panel" id="guide-panel">
  <div class="guide-panel-header">
    <div class="guide-panel-title"><em>Understanding</em> Awe</div>
    <button class="guide-panel-close" onclick="closeGuide()">&#x2715;</button>
  </div>
  <p class="guide-panel-hint">A reference for every column in the explorer. Click a dimension to expand its values.</p>
  <a href="guide.html" target="_blank" class="guide-full-link">Open full guide ↗</a>

  <!-- Geography -->
  <div class="guide-dim-section" id="gdim-geography">
    <button class="guide-dim-toggle" onclick="toggleDim(this)">
      <div class="guide-dim-dot" style="background:#4a6a8a"></div>
      <span class="guide-dim-name" style="color:#4a6a8a">Geography</span>
      <span class="guide-dim-num">01</span>
      <span class="guide-dim-arrow">▾</span>
    </button>
    <div class="guide-dim-body">
      <p style="font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.6;margin-bottom:12px">Where awe happens in the city and how you were moving through it.</p>
      <div class="guide-col-block">
        <div class="guide-col-label">Location type</div>
        <div class="guide-val-row"><span class="guide-val-name">Civic &amp; Cultural</span><span class="guide-val-def">Libraries, cafés, concert halls, markets, places of worship, museums</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Corridors</span><span class="guide-val-def">Train tracks and transportation right-of-ways</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Educational</span><span class="guide-val-def">Universities and schools</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Industry &amp; Office</span><span class="guide-val-def">Research labs, factories, offices</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Parks</span><span class="guide-val-def">Open spaces, cemeteries, community gardens, courtyards</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Plazas</span><span class="guide-val-def">Urban squares and public spaces designed for gathering</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Residences</span><span class="guide-val-def">Personal dwellings</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Streets</span><span class="guide-val-def">Sidewalks, bike lanes, and roads</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Waterfronts</span><span class="guide-val-def">Beaches, canals, bridges, and paths along bodies of water</span></div>
      </div>
      <div class="guide-col-block">
        <div class="guide-col-label">Transport mode</div>
        <div class="guide-val-row"><span class="guide-val-name">Walking</span><span class="guide-val-def">The most prevalent mode — allows for slowness and spontaneous encounter</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Biking</span><span class="guide-val-def">Combines pace with exposure — bodily attunement to the street</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Public Transit</span><span class="guide-val-def">Collective presence, transition, and unexpected views</span></div>
      </div>
    </div>
  </div>

  <!-- Morphology -->
  <div class="guide-dim-section" id="gdim-morphology">
    <button class="guide-dim-toggle" onclick="toggleDim(this)">
      <div class="guide-dim-dot" style="background:#6b5b8a"></div>
      <span class="guide-dim-name" style="color:#6b5b8a">Morphology</span>
      <span class="guide-dim-num">02</span>
      <span class="guide-dim-arrow">▾</span>
    </button>
    <div class="guide-dim-body">
      <p style="font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.6;margin-bottom:12px">The external forms and stimuli that give rise to awe — what triggered the feeling.</p>
      <div class="guide-col-block">
        <div class="guide-col-label">Wonder category (8 wonders of life)</div>
        <div class="guide-val-row"><span class="guide-val-name">Nature</span><span class="guide-val-def">Awe in the face of the living, non-human world</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Visual Design</span><span class="guide-val-def">Awe in the presence of beauty made by human hands</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Collective Effervescence</span><span class="guide-val-def">Awe in shared energy — being swept up in something larger than yourself</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Moral Beauty</span><span class="guide-val-def">Awe at extraordinary goodness, virtue, or kindness</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Music</span><span class="guide-val-def">Awe through sound organized in time — moves through and beyond the body</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Epiphany / Knowledge</span><span class="guide-val-def">Awe in a flash of understanding — expansion of one's frame of reference</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Life &amp; Death</span><span class="guide-val-def">Awe at the fragility and magnitude of existence</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Spirituality</span><span class="guide-val-def">Awe encountered in sacred spaces, rituals, and the transcendent</span></div>
      </div>
      <div class="guide-col-block">
        <div class="guide-col-label">Physical form (15 types)</div>
        <div class="guide-val-row"><span class="guide-val-name">Animals</span><span class="guide-val-def">Birds and mammals interrupting the built environment</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Architecture</span><span class="guide-val-def">Building forms, enclosure, color, materiality, ornament</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Art &amp; Objects</span><span class="guide-val-def">Murals, sculptures, installations, found items, museum exhibits</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Communities</span><span class="guide-val-def">Social bodies with shared purpose — awe in collective belonging</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Events</span><span class="guide-val-def">Gatherings, performances, festivals — awe that exists only in the moment</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Green Space</span><span class="guide-val-def">Designed or semi-designed outdoor spaces</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Infrastructure</span><span class="guide-val-def">Bridges, alleyways, boathouses, transit spaces</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Light</span><span class="guide-val-def">Sunsets, reflections, shade, seasonal lighting — the city's most ephemeral material</span></div>
        <div class="guide-val-row"><span class="guide-val-name">People</span><span class="guide-val-def">Strangers, individuals, historic figures — awe at human presence</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Plants</span><span class="guide-val-def">Trees, lawns, flowers, shrubs, gardens, mushrooms</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Smells</span><span class="guide-val-def">Olfactory encounters with food and natural elements</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Sounds</span><span class="guide-val-def">Auditory encounters through movement or nature</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Vistas</span><span class="guide-val-def">Expansive views of sky, cityscapes, bodies of water</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Water</span><span class="guide-val-def">Rivers, canals, and ponds moving through the city</span></div>
        <div class="guide-val-row"><span class="guide-val-name">Weather</span><span class="guide-val-def">Rain, snow, ice, frost, and seasonal transitions</span></div>
      </div>
    </div>
  </div>

  <!-- Phenomenology -->
  <div class="guide-dim-section" id="gdim-phenomenology">
    <button class="guide-dim-toggle" onclick="toggleDim(this)">
      <div class="guide-dim-dot" style="background:#b05a3a"></div>
      <span class="guide-dim-name" style="color:#b05a3a">Phenomenology</span>
      <span class="guide-dim-num">03</span>
      <span class="guide-dim-arrow">▾</span>
    </button>
    <div class="guide-dim-body">
      <p style="font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.6;margin-bottom:12px">The inner qualities of the experience — how it felt to be there.</p>
      <div class="guide-col-block">
        <div class="guide-col-label">Characteristic (5 types)</div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Beauty</span><span class="guide-val-def">Perception of aesthetic harmony or sensory pleasure in the environment</span><span class="guide-heuristic">Does this place feel beautiful in some way?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Mystery</span><span class="guide-val-def">An encounter with something that cannot easily be explained or understood</span><span class="guide-heuristic">Does this place escape easy understanding?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Wonder</span><span class="guide-val-def">A state of curiosity, openness, and receptivity</span><span class="guide-heuristic">Does this place invite fresh eyes?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Vastness</span><span class="guide-val-def">Something physically, temporally, or conceptually large that transcends ordinary experience</span><span class="guide-heuristic">Does this feel larger than your current frame of reference?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Interconnection</span><span class="guide-val-def">A sense of being part of a larger whole or embedded system</span><span class="guide-heuristic">Does this make you feel part of something bigger?</span></div></div>
      </div>
      <div class="guide-col-block">
        <div class="guide-col-label">Tension register (6 spectrums)</div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Ornate</em> ←→ <em>Utilitarian</em></div><div class="guide-tension-def">Does this thing do more than it needs to, or exactly what it needs to?</div></div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Inclusive</em> ←→ <em>Exclusive</em></div><div class="guide-tension-def">Does this space invite you in, or hold you at a boundary?</div></div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Wild</em> ←→ <em>Curated</em></div><div class="guide-tension-def">Is this place managing nature, or is nature managing itself?</div></div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Impressive</em> ←→ <em>Ordinary</em></div><div class="guide-tension-def">Does this exceed a normal range for its category, or stand quietly outside comparison?</div></div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Novel</em> ←→ <em>Familiar</em></div><div class="guide-tension-def">Is something new being noticed, or is something known being seen more deeply?</div></div>
        <div class="guide-tension-row"><div class="guide-tension-poles"><em>Expansive</em> ←→ <em>Intimate</em></div><div class="guide-tension-def">Does this space open outwardly beyond you, or does it draw you in?</div></div>
      </div>
      <div class="guide-col-block">
        <div class="guide-col-label">Phenomenological binaries</div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Threshold</span><span class="guide-val-def">A felt sense of transition — passage across a spatial, sensory, or perceptual register</span><span class="guide-heuristic">Did this denote a passage from one quality to another?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Surprise</span><span class="guide-val-def">The experience was unanticipated or interrupted the moment</span><span class="guide-heuristic">Was this moment unexpected?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Sanctuary</span><span class="guide-val-def">A felt sense of enclosure and refuge — solitude, shelter, intimacy</span><span class="guide-heuristic">Did this feel like being held rather than drawn outward?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Alterity</span><span class="guide-val-def">An encounter with irreducible otherness — recognizing presence beyond the self</span><span class="guide-heuristic">Did this help you recognize something entirely beyond you?</span></div></div>
      </div>
    </div>
  </div>

  <!-- Temporality -->
  <div class="guide-dim-section" id="gdim-temporality">
    <button class="guide-dim-toggle" onclick="toggleDim(this)">
      <div class="guide-dim-dot" style="background:#7a8a4a"></div>
      <span class="guide-dim-name" style="color:#7a8a4a">Temporality</span>
      <span class="guide-dim-num">04</span>
      <span class="guide-dim-arrow">▾</span>
    </button>
    <div class="guide-dim-body">
      <p style="font-size:11.5px;color:var(--muted);font-style:italic;line-height:1.6;margin-bottom:12px">When awe is available — the temporal nature and potential for repetition.</p>
      <div class="guide-col-block">
        <div class="guide-col-label">Frequency (6 types)</div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Timeless</span><span class="guide-val-def">Continuously available — persistent regardless of season or schedule</span><span class="guide-heuristic">Is this awe available in any given moment?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Daily</span><span class="guide-val-def">Marked by everyday rhythms — diurnal cycles, regular hours</span><span class="guide-heuristic">Is this available within the rhythm of an ordinary day?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Recurring</span><span class="guide-val-def">Based on human schedule — weekly, monthly, or annual programming</span><span class="guide-heuristic">Does this recur based on a calendar or human activity?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Seasonal</span><span class="guide-val-def">Dependent on natural cycles — migration, flowering, weather</span><span class="guide-heuristic">Does this return with the seasons?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Periodic</span><span class="guide-val-def">Part of an unpredictable cycle — irregular or sporadic recurrence</span><span class="guide-heuristic">Does this return on a cycle that can't quite be predicted?</span></div></div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">Ephemeral</span><span class="guide-val-def">Occurred once — unlikely to reliably recur. Rarity and singularity</span><span class="guide-heuristic">Is this likely to occur just once?</span></div></div>
      </div>
      <div class="guide-col-block">
        <div class="guide-col-label">Temporal binary</div>
        <div class="guide-val-row"><div><span class="guide-val-name" style="display:block">History</span><span class="guide-val-def">A felt sense of the past or awareness of accumulated time — longevity and the presence of history as active and alive</span><span class="guide-heuristic">Was this informed by the past, or connected to something old?</span></div></div>
      </div>
    </div>
  </div>

</div>

<div id="tt"></div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
<script>
/* ============================================================
   DATA  (220 records from CSV — auto-generated by build_alluvial.py)
   ============================================================ */
const AWE_DATA = DATA_PLACEHOLDER;

/* ============================================================
   CATEGORY CONFIG
   ============================================================ */
const CATEGORIES = [
  { id:"geography",    label:"Geography",     color:"#4a6a8a",
    dims:[
      { key:"awe_walk", csvCol:"awe_walk(y/n)", label:"Awe Walk Route" },
      { key:"mode",     csvCol:"mode",          label:"Transport Mode" },
      { key:"location", csvCol:"location",      label:"Location Type"  },
    ]
  },
  { id:"morphology",   label:"Morphology",    color:"#6b5b8a",
    dims:[
      { key:"morph1", csvCol:"morphology1", label:"Wonder Category" },
      { key:"morph2", csvCol:"morphology2", label:"Physical Form"   },
    ]
  },
  { id:"phenomenology",label:"Phenomenology", color:"#b05a3a",
    dims:[
      { key:"phenom1",    csvCol:"phenomenology1",  label:"Characteristic"   },
      { key:"phenom2",    csvCol:"phenomenology2",  label:"Tension Register" },
      { key:"threshold",  csvCol:"binary_threshold", label:"Threshold" },
      { key:"surprise",   csvCol:"binary_surprise",  label:"Surprise"  },
      { key:"sanctuary",  csvCol:"binary_sanctuary", label:"Sanctuary" },
      { key:"other",      csvCol:"binary_other",     label:"Other"     },
    ]
  },
  { id:"temporality",  label:"Temporality",   color:"#7a8a4a",
    dims:[
      { key:"frequency", csvCol:"frequency",    label:"Frequency"   },
      { key:"history",   csvCol:"history(y/n)", label:"History" },
    ]
  },
];

// Flat key->info lookup
const DIM = {};
CATEGORIES.forEach(cat => cat.dims.forEach(d => {
  DIM[d.key] = { csvCol:d.csvCol, label:d.label, color:cat.color };
}));

/* Display-name map: raw CSV value → human label */
const LABEL_MAP = {
  // morphology1
  "collective_effervescence":"Collective Effervescence",
  "epiphany/knowledge":"Epiphany / Knowledge",
  "life/death":"Life & Death",
  "moral_beauty":"Moral Beauty",
  "music":"Music","nature":"Nature",
  "visual_design":"Visual Design",
  // morphology2
  "animal":"Animal","architecture":"Architecture","art/object":"Art / Object",
  "communities":"Communities","event":"Event","green space":"Green Space",
  "infrastructure":"Infrastructure","light":"Light","people":"People",
  "plant":"Plant","smell":"Smell","sound":"Sound","vista":"Vista",
  "water":"Water","weather":"Weather",
  // phenomenology1
  "beauty":"Beauty","interconnection":"Interconnection","mystery":"Mystery",
  "vastness":"Vastness","wonder":"Wonder",
  // phenomenology2
  "curated":"Curated","exclusive":"Exclusive","expansive":"Expansive",
  "familiar":"Familiar","functional":"Functional","impressive":"Impressive",
  "inclusive":"Inclusive","intimate":"Intimate","novel":"Novel",
  "ordinary":"Ordinary","ornate":"Ornate","wild":"Wild",
  // location
  "civic, community and cultural venues":"Civic & Cultural","corridor":"Corridor",
  "educational":"Educational","industry/office":"Industry / Office",
  "park":"Park","plaza":"Plaza","residences":"Residences",
  "street":"Street","waterfront":"Waterfront",
  // mode / frequency / binary
  "bike":"Bike","transit":"Transit","walk":"Walk",
  "daily":"Daily","ephemeral":"Ephemeral","periodic":"Periodic",
  "recurring":"Recurring","seasonal":"Seasonal","timeless":"Year-round",
  "y":"Yes","n":"No"
};
function dLabel(v) {
  if (!v || v==="(blank)") return "(blank)";
  return LABEL_MAP[v] || v.replace(/_/g," ").replace(/\b\w/g, c=>c.toUpperCase());
}

/* ============================================================
   STATE
   ============================================================ */
let activeKeys   = [];
let selectedNodes = []; // [{dimKey, value}] — additive path filter

/* ============================================================
   FILTER HELPERS
   ============================================================ */
function getFilteredData() {
  if (!selectedNodes.length) return AWE_DATA;
  return AWE_DATA.filter(row =>
    selectedNodes.every(sel => (row[DIM[sel.dimKey].csvCol] || "") === sel.value)
  );
}

function isNodeSelected(dimKey, value) {
  return selectedNodes.some(s => s.dimKey === dimKey && s.value === value);
}

function toggleNodeFilter(dimKey, value) {
  const idx = selectedNodes.findIndex(s => s.dimKey === dimKey && s.value === value);
  if (idx !== -1) selectedNodes.splice(idx, 1);
  else            selectedNodes.push({ dimKey, value });
  renderFilterBar();
  render();
}

function renderFilterBar() {
  const bar  = document.getElementById("filter-bar");
  const tags = document.getElementById("filter-tags");
  tags.innerHTML = "";
  if (!selectedNodes.length) { bar.classList.remove("show"); return; }
  bar.classList.add("show");
  selectedNodes.forEach(sel => {
    const cat = CATEGORIES.find(c => c.dims.some(d => d.key === sel.dimKey));
    const tag = document.createElement("span");
    tag.className = "ftag";
    tag.style.background = cat ? cat.color : "#8c4518";
    const dimLabel = DIM[sel.dimKey]?.label || sel.dimKey;
    tag.innerHTML =
      dimLabel + ": <strong style='margin-left:3px'>" + dLabel(sel.value) + "</strong>" +
      " <button class='ftag-x' data-key='" + sel.dimKey + "' data-val='" + sel.value + "'>✕</button>";
    tag.querySelector(".ftag-x").addEventListener("click", ev => {
      ev.stopPropagation();
      const k = ev.currentTarget.dataset.key, v = ev.currentTarget.dataset.val;
      selectedNodes = selectedNodes.filter(s => !(s.dimKey === k && s.value === v));
      renderFilterBar(); render();
    });
    tags.appendChild(tag);
  });
}

document.getElementById("filter-clear").addEventListener("click", () => {
  selectedNodes = [];
  renderFilterBar(); render();
  document.getElementById("detail-panel").classList.remove("open");
});

/* ============================================================
   COLOUR HELPERS
   ============================================================ */
const colCache = new Map();
function dimColMap(key) {
  if (!colCache.has(key)) {
    const base  = DIM[key].color;
    const col   = DIM[key].csvCol;
    const vals  = [...new Set(AWE_DATA.map(r => r[col]||"").filter(Boolean))].sort();
    const interp = d3.interpolateHsl(
      d3.interpolateRgb(base,"#f4f0e7")(0.5),
      d3.interpolateRgb(base,"#1c1914")(0.35)
    );
    const sc = d3.scaleSequential([0, Math.max(vals.length-1,1)]).interpolator(interp);
    colCache.set(key, new Map(vals.map((v,i) => [v, sc(i)])));
  }
  return colCache.get(key);
}
function nCol(node) { return dimColMap(node.dimKey).get(node.name) || DIM[node.dimKey]?.color || "#8c4518"; }

/* ============================================================
   SANKEY BUILDER  (uses filtered data)
   ============================================================ */
function buildGraph(keys) {
  const data = getFilteredData();
  const nMap = new Map(), nodes = [], lMap = new Map();

  function nid(col,val) { return col+"::"+(val||"(blank)"); }
  function ensure(col,val,key) {
    const sid = nid(col,val);
    if (!nMap.has(sid)) {
      const idx = nodes.length;
      nMap.set(sid, idx);
      nodes.push({id: idx, name:val||"(blank)", colIdx:col, dimKey:key, instances:[]});
    }
    return nMap.get(sid);
  }

  data.forEach(row => {
    const vals = keys.map(k => row[DIM[k].csvCol]||"");
    keys.forEach((k,c) => { const ni = ensure(c,vals[c],k); nodes[ni].instances.push(row); });
    for (let c=0; c<keys.length-1; c++) {
      const si = ensure(c,  vals[c],  keys[c]);
      const ti = ensure(c+1,vals[c+1],keys[c+1]);
      const lk = si+"-"+ti;
      if (!lMap.has(lk)) lMap.set(lk, {source:si, target:ti, value:0, instances:[]});
      lMap.get(lk).value++;
      lMap.get(lk).instances.push(row);
    }
  });

  nodes.forEach(n => {
    const seen = new Set();
    n.instances = n.instances.filter(r => { const k=r.Name+r.X; return seen.has(k)?false:(seen.add(k),true); });
  });

  return { nodes, links:[...lMap.values()] };
}

/* ============================================================
   RENDER
   ============================================================ */
function render() {
  const svgEl  = document.getElementById("alluvial-svg");
  const msgEl  = document.getElementById("diagram-msg");
  const hcount = document.getElementById("hcount");
  d3.select(svgEl).selectAll("*").remove();

  // Update instance count in header
  const filteredCount = getFilteredData().length;
  if (filteredCount === AWE_DATA.length) {
    hcount.textContent = "220 instances";
    hcount.classList.remove("filtered");
  } else {
    hcount.textContent = filteredCount + " / 220 instances";
    hcount.classList.add("filtered");
  }

  if (activeKeys.length < 2) { msgEl.classList.add("show"); return; }
  msgEl.classList.remove("show");

  if (filteredCount === 0) {
    msgEl.classList.add("show");
    msgEl.innerHTML = "No instances match the current filter<span>Click a filter tag above to remove it</span>";
    return;
  }
  msgEl.innerHTML = "Select at least two columns above<span>Use the category dropdowns to get started</span>";

  const area = document.getElementById("diagram-area");
  const W = area.clientWidth, H = area.clientHeight;
  const pad = {top:44, right:165, bottom:16, left:20};
  const svg = d3.select(svgEl).attr("width",W).attr("height",H);

  const gd = buildGraph(activeKeys);
  if (!gd.nodes.length) return;

  const sankey = d3.sankey()
    .nodeId(d=>d.id).nodeAlign(d3.sankeyLeft)
    .nodeWidth(14).nodePadding(10)
    .extent([[pad.left,pad.top],[W-pad.right,H-pad.bottom]]);

  let g;
  try { g = sankey({nodes:gd.nodes.map(d=>({...d})), links:gd.links.map(d=>({...d}))}); }
  catch(e) { console.error("Sankey error:",e); return; }
  const {nodes,links} = g;

  // Column headers
  const hx = new Map();
  nodes.forEach(n => { if(!hx.has(n.colIdx)||n.x0<hx.get(n.colIdx)) hx.set(n.colIdx,n.x0); });
  activeKeys.forEach((k,i) => {
    svg.append("text").attr("class","scol")
      .attr("x",(hx.get(i)??0)+7).attr("y",pad.top-12)
      .attr("text-anchor","start").attr("fill",DIM[k].color)
      .text(DIM[k].label.toUpperCase());
  });

  // Links
  const lsel = svg.append("g").selectAll(".sankey-link").data(links).join("path")
    .attr("class","sankey-link")
    .attr("d", d3.sankeyLinkHorizontal())
    .attr("stroke-width", d => Math.max(1, d.width))
    .attr("stroke", d => nCol(d.source))
    .on("mouseenter", (ev,d) => {
      lsel.classed("dim", l => l!==d);
      showTT(ev, "<strong>"+dLabel(d.source.name)+"</strong> → <strong>"+dLabel(d.target.name)+"</strong><br>"+d.value+" instance"+(d.value!==1?"s":""));
    })
    .on("mousemove", mvTT)
    .on("mouseleave", () => { lsel.classed("dim",false); hideTT(); })
    .on("click", (_,d) => openDetail(dLabel(d.source.name)+" → "+dLabel(d.target.name), d.source.dimKey+" → "+d.target.dimKey, d.instances, d.value));

  // Nodes
  svg.append("g").selectAll(".sankey-node").data(nodes).join("g")
    .attr("class", d => "sankey-node" + (isNodeSelected(d.dimKey, d.name) ? " sel" : ""))
    .attr("transform", d => "translate("+d.x0+","+d.y0+")")
    .call(sel => {
      sel.append("rect")
        .attr("height", d => Math.max(1,d.y1-d.y0))
        .attr("width",  d => d.x1-d.x0)
        .attr("fill",   d => nCol(d)).attr("rx",1);
      sel.append("text").attr("class","slabel")
        .attr("x", d => (d.x1-d.x0)+6).attr("y", d => (d.y1-d.y0)/2)
        .attr("dy",".35em").attr("text-anchor","start")
        .text(d => { const l=dLabel(d.name); return (l.length>24?l.slice(0,22)+"…":l)+" ("+d.value+")"; });
    })
    .on("mouseenter", (ev,d) => {
      lsel.classed("dim", l => l.source!==d && l.target!==d);
      const selTip = isNodeSelected(d.dimKey, d.name) ? "<br><em>click to remove filter</em>" : "<br><em>click to filter by this</em>";
      showTT(ev, "<strong>"+dLabel(d.name)+"</strong><br>"+d.value+" instance"+(d.value!==1?"s":"")+selTip);
    })
    .on("mousemove", mvTT)
    .on("mouseleave", () => { lsel.classed("dim",false); hideTT(); })
    .on("click", (_,d) => {
      hideTT();
      toggleNodeFilter(d.dimKey, d.name);
      // After re-render, open detail panel showing filtered instances
      const filtered = getFilteredData();
      if (filtered.length) openDetail(dLabel(d.name), d.dimKey, filtered, filtered.length);
    });
}

/* ============================================================
   TOOLTIP
   ============================================================ */
const ttEl = document.getElementById("tt");
function showTT(ev,html) { ttEl.innerHTML=html; ttEl.classList.add("on"); mvTT(ev); }
function mvTT(ev) { ttEl.style.left=Math.min(ev.clientX+14,window.innerWidth-225)+"px"; ttEl.style.top=(ev.clientY-10)+"px"; }
function hideTT() { ttEl.classList.remove("on"); }

/* ============================================================
   DETAIL PANEL
   ============================================================ */
function openDetail(title, ctx, instances, count) {
  const eyebrow = ctx.includes("→")
    ? ctx.split("→").map(s=>DIM[s.trim()]?.label||s.trim()).join(" → ")
    : (DIM[ctx]?.label||ctx);
  document.getElementById("d-ey").textContent   = eyebrow.toUpperCase();
  document.getElementById("d-titl").textContent = title;
  document.getElementById("d-cnt").textContent  = count+" instance"+(count!==1?"s":"");
  const list = document.getElementById("d-list");
  list.innerHTML = "";
  instances.forEach(r => {
    const div = document.createElement("div"); div.className="ditem";
    const desc = (r.description||"").replace(/^"+|"+$/g,"").trim();
    const ds   = desc.length>200?desc.slice(0,197)+"…":desc;
    div.innerHTML =
      "<div class='dname'>"+(r.Name||"(unnamed)")+"</div>"+
      "<div class='dtags'>"+
        (r.affiliation?"<span class='dtag' style='background:#8c4518'>"+r.affiliation+"</span>":"")+
        (r.morphology1?"<span class='dtag' style='background:#6b5b8a'>"+dLabel(r.morphology1)+"</span>":"")+
        (r.location   ?"<span class='dtag' style='background:#4a6a8a'>"+dLabel(r.location)+"</span>":"")+
      "</div>"+
      (ds?"<div class='ddesc'>"+ds+"</div>":"");
    list.appendChild(div);
  });
  document.getElementById("detail-panel").classList.add("open");
}
document.getElementById("d-cls").addEventListener("click", () => {
  document.getElementById("detail-panel").classList.remove("open");
});

/* ============================================================
   CONTROLS — category dropdowns
   ============================================================ */
function buildCatButtons() {
  const wrap = document.getElementById("cat-btns");
  CATEGORIES.forEach(cat => {
    const bw  = document.createElement("div"); bw.className = "cat-btn-wrap";
    const btn = document.createElement("button");
    btn.className = "cat-btn"; btn.style.background = cat.color;
    btn.id = "cb-"+cat.id;
    btn.innerHTML = cat.label + " <span class='cat-arrow'>&#9662;</span>";

    const menu = document.createElement("div");
    menu.className = "cat-dropdown"; menu.id = "cm-"+cat.id;
    menu.innerHTML = "<div class='cat-dd-title'>"+cat.label.toUpperCase()+"</div>";

    cat.dims.forEach(d => {
      const lbl = document.createElement("label"); lbl.className = "cat-option";
      lbl.innerHTML =
        "<input type='checkbox' value='"+d.key+"'> "+
        "<span class='cat-opt-label'>"+d.label+"</span>";
      lbl.querySelector("input").addEventListener("change", e => {
        if (e.target.checked) {
          if (!activeKeys.includes(d.key)) activeKeys.push(d.key);
          // Auto-open the matching guide dimension section
          if (typeof openGuideDim === "function") openGuideDim(cat.id);
        } else {
          activeKeys = activeKeys.filter(k=>k!==d.key);
        }
        // Clear any selected-node filters that reference a now-inactive key
        selectedNodes = selectedNodes.filter(s => activeKeys.includes(s.dimKey));
        renderFilterBar();
        renderChips(); render();
      });
      menu.appendChild(lbl);
    });

    btn.addEventListener("click", ev => {
      ev.stopPropagation();
      const isOpen = menu.classList.contains("open");
      document.querySelectorAll(".cat-dropdown.open").forEach(m => {
        m.classList.remove("open");
        const b = document.getElementById("cb-"+m.id.replace("cm-",""));
        if(b) b.classList.remove("open");
      });
      if (!isOpen) { menu.classList.add("open"); btn.classList.add("open"); }
    });

    bw.appendChild(btn); bw.appendChild(menu); wrap.appendChild(bw);
  });

  document.addEventListener("click", () => {
    document.querySelectorAll(".cat-dropdown.open").forEach(m => {
      m.classList.remove("open");
      const b = document.getElementById("cb-"+m.id.replace("cm-",""));
      if(b) b.classList.remove("open");
    });
  });
}

function syncCheckboxes() {
  document.querySelectorAll(".cat-option input").forEach(cb => {
    cb.checked = activeKeys.includes(cb.value);
  });
}

function renderChips() {
  const wrap = document.getElementById("active-chips");
  wrap.innerHTML = "";
  syncCheckboxes();
  if (!activeKeys.length) {
    wrap.innerHTML = "<div class='no-chips-hint'>Select columns from the dropdowns above</div>";
    return;
  }
  activeKeys.forEach((key, i) => {
    const d   = DIM[key];
    const cat = CATEGORIES.find(c => c.dims.some(dd => dd.key===key));
    const chip = document.createElement("div");
    chip.className="dim-chip"; chip.draggable=true; chip.dataset.key=key;
    chip.style.background = cat.color;
    chip.innerHTML =
      "<button class='dca' data-dir='left'"+(i===0?" disabled":"")+">◀</button> "+
      d.label+
      " <button class='dca' data-dir='right'"+(i===activeKeys.length-1?" disabled":"")+">▶</button>"+
      "<button class='dcx'>✕</button>";

    chip.querySelectorAll(".dca").forEach(b => {
      b.addEventListener("click", ev => {
        ev.stopPropagation();
        const idx=activeKeys.indexOf(key), dir=b.dataset.dir;
        if (dir==="left"  && idx>0)                       [activeKeys[idx-1],activeKeys[idx]]=[activeKeys[idx],activeKeys[idx-1]];
        if (dir==="right" && idx<activeKeys.length-1)     [activeKeys[idx],activeKeys[idx+1]]=[activeKeys[idx+1],activeKeys[idx]];
        renderChips(); render();
      });
    });
    chip.querySelector(".dcx").addEventListener("click", ev => {
      ev.stopPropagation();
      activeKeys = activeKeys.filter(k=>k!==key);
      selectedNodes = selectedNodes.filter(s => activeKeys.includes(s.dimKey));
      renderFilterBar();
      renderChips(); render();
    });
    chip.addEventListener("dragstart", ev => { ev.dataTransfer.setData("text/plain",key); setTimeout(()=>chip.classList.add("dragging"),0); });
    chip.addEventListener("dragend",   () => chip.classList.remove("dragging"));
    chip.addEventListener("dragover",  ev => { ev.preventDefault(); chip.classList.add("drag-over"); });
    chip.addEventListener("dragleave", () => chip.classList.remove("drag-over"));
    chip.addEventListener("drop", ev => {
      ev.preventDefault(); chip.classList.remove("drag-over");
      const from=ev.dataTransfer.getData("text/plain"), fi=activeKeys.indexOf(from), ti=activeKeys.indexOf(key);
      if(fi!==-1&&ti!==-1&&fi!==ti){activeKeys.splice(fi,1);activeKeys.splice(ti,0,from);}
      renderChips(); render();
    });
    wrap.appendChild(chip);
  });
}

/* ============================================================
   RESIZE
   ============================================================ */
new ResizeObserver(() => { if(activeKeys.length>=2) render(); })
  .observe(document.getElementById("diagram-area"));

/* ============================================================
   INIT
   ============================================================ */
buildCatButtons();
renderChips();

/* ============================================================
   GUIDE PANEL
   ============================================================ */
function toggleGuide() {
  var panel = document.getElementById("guide-panel");
  var backdrop = document.getElementById("guide-backdrop");
  var btn = document.getElementById("guide-toggle-btn");
  var isOpen = panel.classList.contains("open");
  panel.classList.toggle("open", !isOpen);
  backdrop.classList.toggle("open", !isOpen);
  btn.classList.toggle("active", !isOpen);
}
function closeGuide() {
  document.getElementById("guide-panel").classList.remove("open");
  document.getElementById("guide-backdrop").classList.remove("open");
  document.getElementById("guide-toggle-btn").classList.remove("active");
}
function toggleDim(btn) {
  var body = btn.nextElementSibling;
  var isOpen = body.classList.contains("open");
  body.classList.toggle("open", !isOpen);
  btn.classList.toggle("open", !isOpen);
}

// Auto-open the relevant dimension when a category button is clicked
// by patching renderChips to also hint the guide
function openGuideDim(catId) {
  var sectionMap = {
    geography: "gdim-geography",
    morphology: "gdim-morphology",
    phenomenology: "gdim-phenomenology",
    temporality: "gdim-temporality"
  };
  var secId = sectionMap[catId];
  if (!secId) return;
  var sec = document.getElementById(secId);
  if (!sec) return;
  // Open that section
  var toggle = sec.querySelector(".guide-dim-toggle");
  var body   = sec.querySelector(".guide-dim-body");
  if (toggle && body && !body.classList.contains("open")) {
    body.classList.add("open");
    toggle.classList.add("open");
  }
}

// openGuideDim is called directly from buildCatButtons' checkbox handler above
</script>
</body>
</html>
"""

# Inject the data
output = HTML.replace("DATA_PLACEHOLDER", data_json)

with open('alluvial.html', 'w', encoding='utf-8') as f:
    f.write(output)

print(f'alluvial.html written — {len(output):,} chars')
