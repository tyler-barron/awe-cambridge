"""
Run this script to regenerate atlas.html from the CSV.
  python build_atlas.py

To add photos: put image files in an images/ folder, then add an 'image'
column to the CSV with the filename (e.g. broad_discovery.jpg).
"""
import csv, json, io

csv_path = 'awe-data.csv'
with open(csv_path, encoding='utf-8-sig') as f:
    raw = f.read()

reader = csv.DictReader(io.StringIO(raw))
rows = [{k.strip(): v.strip() for k, v in r.items()} for r in reader]
data_json = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
print(f'Loaded {len(rows)} records')

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Awe Atlas — Interactive Map</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Space+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{
  --ink:#1c1914;--charcoal:#2c2118;--parchment:#f4f0e7;--linen:#e3d4c5;
  --stone:#b7aea2;--accent:#8c4518;--saffron:#caa74d;--muted:#6b6259;
  --geo:#4a6a8a;--morph:#6b5b8a;--phenom:#b05a3a;--tempo:#7a8a4a;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;background:var(--parchment);color:var(--ink);font-family:"Cormorant Garamond",serif;overflow:hidden;}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:9000;opacity:.35;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23n)' opacity='.04'/%3E%3C/svg%3E");}

.page{display:flex;flex-direction:column;height:100vh;}

/* ── Header ── */
.site-header{flex-shrink:0;padding:11px 20px;border-bottom:1px solid rgba(140,69,24,.2);display:flex;align-items:center;gap:14px;background:var(--parchment);z-index:100;}
.header-back{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted);text-decoration:none;transition:color .2s;}
.header-back:hover{color:var(--accent);}
.header-title{font-size:20px;font-weight:300;}
.header-title em{font-style:italic;color:var(--accent);}
.header-count{font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:var(--stone);margin-left:auto;}
.header-count.filtered{color:var(--accent);}

/* ── Body ── */
.body-wrap{flex:1;display:flex;overflow:hidden;min-height:0;}

/* ── Sidebar ── */
.sidebar{width:280px;flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid rgba(140,69,24,.15);background:var(--parchment);overflow:hidden;}

/* ── Filter accordion ── */
.filter-scroll{flex-shrink:0;overflow-y:auto;border-bottom:1px solid rgba(140,69,24,.1);}
.filter-scroll::-webkit-scrollbar{width:3px;}
.filter-scroll::-webkit-scrollbar-thumb{background:rgba(140,69,24,.15);border-radius:2px;}
.filter-group{border-bottom:1px solid rgba(140,69,24,.08);}
.filter-group:last-child{border-bottom:none;}
.fg-header{display:flex;align-items:center;gap:8px;padding:8px 14px;cursor:pointer;user-select:none;transition:background .15s;}
.fg-header:hover{background:rgba(140,69,24,.04);}
.fg-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.fg-label{font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.3em;text-transform:uppercase;flex:1;}
.fg-arrow{font-size:9px;color:var(--stone);transition:transform .2s;}
.fg-header.open .fg-arrow{transform:rotate(90deg);}
.fg-body{display:none;padding:0 14px 10px;}
.fg-body.open{display:block;}
.fg-dim{margin-bottom:8px;}
.fg-dim:last-child{margin-bottom:0;}
.fg-dim-label{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--stone);margin-bottom:4px;}
.chip-row{display:flex;flex-wrap:wrap;gap:3px;}
.fchip{padding:2px 8px;border:1px solid rgba(140,69,24,.2);border-radius:20px;font-family:"Cormorant Garamond",serif;font-size:11px;font-style:italic;background:transparent;color:var(--muted);cursor:pointer;white-space:nowrap;transition:all .15s;}
.fchip:hover{border-color:var(--accent);color:var(--ink);}
.fchip.active{background:var(--ink);border-color:var(--ink);color:var(--parchment);font-style:normal;}

.filter-footer{flex-shrink:0;padding:7px 14px;border-bottom:1px solid rgba(140,69,24,.08);display:flex;align-items:center;justify-content:space-between;}
.active-count{font-family:"Space Mono",monospace;font-size:8px;color:var(--stone);}
.active-count.has-filters{color:var(--accent);}
.clear-btn{font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);background:none;border:none;cursor:pointer;display:none;transition:color .15s;}
.clear-btn:hover{color:var(--accent);}
.clear-btn.show{display:block;}

/* ── Instance list ── */
.instance-list{flex:1;overflow-y:auto;padding:0;}
.instance-list::-webkit-scrollbar{width:3px;}
.instance-list::-webkit-scrollbar-thumb{background:rgba(140,69,24,.15);border-radius:2px;}
.list-empty{padding:20px 14px;font-size:13px;font-style:italic;color:var(--stone);text-align:center;}
.inst-card{padding:9px 14px;border-bottom:1px solid rgba(140,69,24,.07);cursor:pointer;transition:background .15s;display:flex;gap:9px;align-items:flex-start;}
.inst-card:hover{background:rgba(140,69,24,.04);}
.inst-card.selected{background:rgba(140,69,24,.07);border-left:3px solid var(--accent);padding-left:11px;}
.inst-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:4px;}
.inst-body{flex:1;min-width:0;}
.inst-name{font-size:13px;font-weight:300;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:1px;}
.inst-meta{font-family:"Space Mono",monospace;font-size:7px;color:var(--stone);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

/* ── Map ── */
.map-wrap{flex:1;position:relative;overflow:hidden;}
#atlas-map{width:100%;height:100%;}
.leaflet-popup-content-wrapper{background:var(--parchment);border:1px solid rgba(140,69,24,.22);border-radius:3px;box-shadow:0 6px 20px rgba(28,25,20,.16);padding:0;}
.leaflet-popup-content{margin:0;font-family:"Cormorant Garamond",serif;}
.leaflet-popup-tip-container{display:none;}
.leaflet-popup-close-button{color:var(--muted) !important;font-size:16px !important;padding:5px 7px !important;}
.leaflet-popup-close-button:hover{color:var(--accent) !important;}
.lpop{padding:11px 13px 12px;}
.lpop-type{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.3em;text-transform:uppercase;margin-bottom:3px;}
.lpop-name{font-size:16px;font-weight:300;line-height:1.25;margin-bottom:5px;}
.lpop-tags{display:flex;flex-wrap:wrap;gap:3px;margin-bottom:6px;}
.ltag{font-family:"Space Mono",monospace;font-size:6px;letter-spacing:.1em;text-transform:uppercase;padding:2px 5px;border-radius:1px;color:white;}
.lpop-desc{font-size:11px;line-height:1.65;color:var(--muted);font-style:italic;max-height:72px;overflow:hidden;}
.lpop-img{width:100%;height:110px;object-fit:cover;display:block;border-bottom:1px solid rgba(140,69,24,.1);margin-bottom:0;}
.lpop-btn{margin-top:8px;width:100%;padding:7px;background:var(--ink);color:var(--parchment);border:none;font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.15em;text-transform:uppercase;cursor:pointer;border-radius:1px;transition:background .15s;}
.lpop-btn:hover{background:var(--accent);}
.map-badge{position:absolute;top:10px;right:10px;z-index:500;background:var(--parchment);border:1px solid rgba(140,69,24,.2);border-radius:2px;padding:5px 9px;font-family:"Space Mono",monospace;font-size:9px;color:var(--stone);pointer-events:none;}

/* ── Detail panel ── */
.detail-panel{width:0;overflow:hidden;border-left:1px solid transparent;background:var(--parchment);transition:width .3s,border-color .3s;flex-shrink:0;}
.detail-panel.open{width:300px;border-left-color:rgba(140,69,24,.15);}
.detail-inner{width:300px;overflow-y:auto;height:100%;}
.detail-inner::-webkit-scrollbar{width:3px;}
.detail-inner::-webkit-scrollbar-thumb{background:rgba(140,69,24,.15);border-radius:2px;}
.d-photo{width:100%;height:160px;object-fit:cover;display:block;}
.dhd{padding:13px 16px 11px;border-bottom:1px solid rgba(140,69,24,.1);display:flex;align-items:flex-start;gap:8px;position:sticky;top:0;background:var(--parchment);z-index:1;}
.dhd-color{width:4px;border-radius:2px;flex-shrink:0;align-self:stretch;min-height:36px;}
.dhd-body{flex:1;min-width:0;}
.dey{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.3em;text-transform:uppercase;margin-bottom:3px;}
.dtitl{font-size:18px;font-weight:300;line-height:1.25;}
.dcls{background:none;border:none;font-size:15px;color:var(--stone);cursor:pointer;padding:0;flex-shrink:0;transition:color .15s;line-height:1;}
.dcls:hover{color:var(--accent);}
.detail-body{padding:13px 16px 32px;display:flex;flex-direction:column;gap:13px;}
.d-section-label{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.35em;text-transform:uppercase;color:var(--stone);margin-bottom:5px;}
.d-desc{font-size:14px;line-height:1.75;font-weight:300;font-style:italic;color:var(--charcoal);}
.d-chips{display:flex;flex-wrap:wrap;gap:3px;}
.d-chip{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.1em;text-transform:uppercase;padding:3px 7px;border-radius:1px;color:white;}
.d-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.d-cell-label{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--stone);margin-bottom:2px;}
.d-cell-val{font-size:13px;font-weight:300;}
.d-binary-row{display:flex;flex-wrap:wrap;gap:3px;}
.d-binary{font-family:"Space Mono",monospace;font-size:7px;letter-spacing:.1em;text-transform:uppercase;padding:2px 6px;border-radius:1px;border:1px solid rgba(140,69,24,.18);color:var(--stone);}
.d-binary.yes{background:var(--ink);border-color:var(--ink);color:var(--parchment);}
</style>
</head>
<body>
<div class="page">

<header class="site-header">
  <a href="index.html" class="header-back">← Atlas</a>
  <div class="header-title">Awe <em>Map</em></div>
  <div class="header-count" id="hcount">220 instances</div>
</header>

<div class="body-wrap">

  <!-- ── Sidebar ── -->
  <div class="sidebar">

    <div class="filter-scroll" id="filter-scroll">
      <!-- Groups built by JS -->
    </div>

    <div class="filter-footer">
      <span class="active-count" id="active-count">No filters active</span>
      <button class="clear-btn" id="clear-btn" onclick="clearFilters()">✕ clear all</button>
    </div>

    <div class="instance-list" id="instance-list"></div>
  </div>

  <!-- ── Map ── -->
  <div class="map-wrap">
    <div id="atlas-map"></div>
    <div class="map-badge" id="map-badge">220 shown</div>
  </div>

  <!-- ── Detail panel ── -->
  <div class="detail-panel" id="detail-panel">
    <div class="detail-inner" id="detail-inner">
      <div class="dhd">
        <div class="dhd-color" id="d-color"></div>
        <div class="dhd-body">
          <div class="dey" id="d-ey"></div>
          <div class="dtitl" id="d-titl"></div>
        </div>
        <button class="dcls" onclick="closeDetail()">&#x2715;</button>
      </div>
      <div class="detail-body" id="detail-body"></div>
    </div>
  </div>

</div>
</div>

<script>
/* ============================================================
   DATA — regenerated by build_atlas.py
   ============================================================ */
const AWE_DATA = DATA_PLACEHOLDER;

/* ============================================================
   FILTER CONFIG — mirrors the alluvial explorer's four categories
   ============================================================ */
const FILTER_GROUPS = [
  { id:"geo",    label:"Geography",    color:"#4a6a8a",
    dims:[
      { key:"location",  csvCol:"location",      label:"Location Type",
        labels:{ "civic, community and cultural venues":"Civic & Cultural","corridor":"Corridor","educational":"Educational","industry/office":"Industry / Office","park":"Park","plaza":"Plaza","residences":"Residences","street":"Street","waterfront":"Waterfront" } },
      { key:"mode",      csvCol:"mode",           label:"Transport Mode",
        labels:{ "bike":"Bike","transit":"Transit","walk":"Walk" } },
      { key:"awe_walk",  csvCol:"awe_walk(y/n)",  label:"Awe Walk Route",
        labels:{ "y":"Yes","n":"No" } },
    ]
  },
  { id:"morph",  label:"Morphology",   color:"#6b5b8a",
    dims:[
      { key:"morph1", csvCol:"morphology1", label:"Wonder Category",
        labels:{ "collective_effervescence":"Collective Effervescence","epiphany/knowledge":"Epiphany / Knowledge","life/death":"Life & Death","moral_beauty":"Moral Beauty","music":"Music","nature":"Nature","visual_design":"Visual Design" } },
      { key:"morph2", csvCol:"morphology2", label:"Physical Form",
        labels:{ "animal":"Animal","architecture":"Architecture","art/object":"Art / Object","communities":"Communities","event":"Event","green space":"Green Space","infrastructure":"Infrastructure","light":"Light","people":"People","plant":"Plant","smell":"Smell","sound":"Sound","vista":"Vista","water":"Water","weather":"Weather" } },
    ]
  },
  { id:"phenom", label:"Phenomenology", color:"#b05a3a",
    dims:[
      { key:"phenom1",   csvCol:"phenomenology1",  label:"Characteristic",
        labels:{ "beauty":"Beauty","interconnection":"Interconnection","mystery":"Mystery","vastness":"Vastness","wonder":"Wonder" } },
      { key:"phenom2",   csvCol:"phenomenology2",  label:"Tension Register",
        labels:{ "curated":"Curated","exclusive":"Exclusive","expansive":"Expansive","familiar":"Familiar","functional":"Functional","impressive":"Impressive","inclusive":"Inclusive","intimate":"Intimate","novel":"Novel","ordinary":"Ordinary","ornate":"Ornate","wild":"Wild" } },
      { key:"threshold", csvCol:"binary_threshold", label:"Threshold",
        labels:{ "y":"Yes","n":"No" } },
      { key:"surprise",  csvCol:"binary_surprise",  label:"Surprise",
        labels:{ "y":"Yes","n":"No" } },
      { key:"sanctuary", csvCol:"binary_sanctuary", label:"Sanctuary",
        labels:{ "y":"Yes","n":"No" } },
      { key:"other",     csvCol:"binary_other",     label:"Other Quality",
        labels:{ "y":"Yes","n":"No" } },
    ]
  },
  { id:"tempo",  label:"Temporality",  color:"#7a8a4a",
    dims:[
      { key:"frequency", csvCol:"frequency",    label:"Frequency",
        labels:{ "daily":"Daily","ephemeral":"Ephemeral","periodic":"Periodic","recurring":"Recurring","seasonal":"Seasonal","timeless":"Year-round" } },
      { key:"history",   csvCol:"history(y/n)", label:"History",
        labels:{ "y":"Yes","n":"No" } },
    ]
  },
];

/* Build flat lookup: key → {csvCol, labels} */
const DIM_MAP = {};
FILTER_GROUPS.forEach(g => g.dims.forEach(d => { DIM_MAP[d.key] = d; }));

const MORPH_COLORS = {
  "collective_effervescence":"#4a7a8a","epiphany/knowledge":"#6b5b8a",
  "life/death":"#7a8a4a","moral_beauty":"#c4a882","music":"#b05a3a",
  "nature":"#97ba74","visual_design":"#8c4518",
};

/* ============================================================
   STATE
   ============================================================ */
let activeFilters = {};   // { dimKey: value }
let selectedIdx   = null;
let markers       = [];   // parallel to AWE_DATA

/* ============================================================
   FILTER LOGIC
   ============================================================ */
function getVisibleIndices() {
  const keys = Object.keys(activeFilters);
  return AWE_DATA.reduce((acc, r, i) => {
    for (const k of keys) {
      if ((r[DIM_MAP[k].csvCol] || "") !== activeFilters[k]) return acc;
    }
    acc.push(i);
    return acc;
  }, []);
}

function setFilter(dimKey, value, chipEl) {
  /* toggle off if same value clicked again */
  if (activeFilters[dimKey] === value) {
    delete activeFilters[dimKey];
    chipEl.classList.remove("active");
  } else {
    /* deactivate the old chip for this dim */
    document.querySelectorAll(`.fchip[data-dim="${dimKey}"]`).forEach(c => {
      c.classList.remove("active");
      c.style.background = ""; c.style.borderColor = "";
    });
    activeFilters[dimKey] = value;
    chipEl.classList.add("active");
  }
  updateFilterFooter();
  applyFilter();
}

function clearFilters() {
  activeFilters = {};
  document.querySelectorAll(".fchip").forEach(c => {
    c.classList.remove("active");
    c.style.background = ""; c.style.borderColor = "";
  });
  updateFilterFooter();
  applyFilter();
}

function updateFilterFooter() {
  const n = Object.keys(activeFilters).length;
  const cnt = document.getElementById("active-count");
  const clr = document.getElementById("clear-btn");
  cnt.textContent = n === 0 ? "No filters active" : n + " filter" + (n > 1 ? "s" : "") + " active";
  cnt.classList.toggle("has-filters", n > 0);
  clr.classList.toggle("show", n > 0);
}

function applyFilter() {
  const vis = new Set(getVisibleIndices());
  const count = vis.size;

  const hcount = document.getElementById("hcount");
  const badge  = document.getElementById("map-badge");
  if (count === AWE_DATA.length) {
    hcount.textContent = "220 instances"; hcount.classList.remove("filtered");
    badge.textContent  = "220 shown";
  } else {
    hcount.textContent = count + " / 220 instances"; hcount.classList.add("filtered");
    badge.textContent  = count + " / 220 shown";
  }

  markers.forEach((m, i) => {
    if (!m) return;
    if (vis.has(i)) { if (!map.hasLayer(m)) m.addTo(map); }
    else            { if (map.hasLayer(m))  map.removeLayer(m); }
  });

  renderList(vis);
  if (selectedIdx !== null && !vis.has(selectedIdx)) closeDetail();
}

/* ============================================================
   FILTER UI BUILDER
   ============================================================ */
function buildFilters() {
  const scroll = document.getElementById("filter-scroll");

  FILTER_GROUPS.forEach((grp, gi) => {
    const groupEl = document.createElement("div");
    groupEl.className = "filter-group";

    const hdr = document.createElement("div");
    hdr.className = "fg-header" + (gi === 0 ? " open" : "");
    hdr.innerHTML =
      `<div class="fg-dot" style="background:${grp.color}"></div>` +
      `<span class="fg-label" style="color:${grp.color}">${grp.label}</span>` +
      `<span class="fg-arrow">▶</span>`;
    hdr.addEventListener("click", () => {
      hdr.classList.toggle("open");
      body.classList.toggle("open");
    });

    const body = document.createElement("div");
    body.className = "fg-body" + (gi === 0 ? " open" : "");

    grp.dims.forEach(dim => {
      /* Collect unique non-empty values sorted by frequency */
      const counts = {};
      AWE_DATA.forEach(r => {
        const v = r[dim.csvCol] || "";
        if (v) counts[v] = (counts[v] || 0) + 1;
      });
      const vals = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
      if (!vals.length) return;

      const dimDiv = document.createElement("div");
      dimDiv.className = "fg-dim";
      dimDiv.innerHTML = `<div class="fg-dim-label">${dim.label}</div>`;
      const row = document.createElement("div");
      row.className = "chip-row";

      vals.forEach(v => {
        const chip = document.createElement("button");
        chip.className = "fchip";
        chip.dataset.dim = dim.key;
        chip.dataset.val = v;
        const displayLabel = dim.labels[v] || v.replace(/_/g, " ");
        chip.textContent = displayLabel;
        chip.addEventListener("click", () => {
          setFilter(dim.key, v, chip);
          if (chip.classList.contains("active")) {
            chip.style.background = grp.color;
            chip.style.borderColor = grp.color;
          } else {
            chip.style.background = "";
            chip.style.borderColor = "";
          }
        });
        row.appendChild(chip);
      });

      dimDiv.appendChild(row);
      body.appendChild(dimDiv);
    });

    groupEl.appendChild(hdr);
    groupEl.appendChild(body);
    scroll.appendChild(groupEl);
  });
}

/* ============================================================
   INSTANCE LIST
   ============================================================ */
function renderList(visSet) {
  const list = document.getElementById("instance-list");
  list.innerHTML = "";
  if (!visSet.size) {
    list.innerHTML = "<div class='list-empty'>No instances match.</div>"; return;
  }
  visSet.forEach(i => {
    const r = AWE_DATA[i];
    const color = MORPH_COLORS[r.morphology1] || "#8c4518";
    const morph1Label = (DIM_MAP["morph1"].labels[r.morphology1] || r.morphology1 || "").replace(/_/g," ");
    const locLabel    = (DIM_MAP["location"].labels[r.location] || r.location || "");
    const div = document.createElement("div");
    div.className = "inst-card" + (selectedIdx === i ? " selected" : "");
    div.dataset.idx = i;
    div.innerHTML =
      `<div class="inst-dot" style="background:${color}"></div>` +
      `<div class="inst-body">` +
        `<div class="inst-name">${r.Name || "(unnamed)"}</div>` +
        `<div class="inst-meta">${morph1Label}${locLabel ? " · " + locLabel : ""}</div>` +
      `</div>`;
    div.addEventListener("click", () => selectInstance(i));
    list.appendChild(div);
  });
}

/* ============================================================
   DETAIL PANEL
   ============================================================ */
function selectInstance(idx) {
  selectedIdx = idx;
  const r = AWE_DATA[idx];
  const color = MORPH_COLORS[r.morphology1] || "#8c4518";

  document.querySelectorAll(".inst-card").forEach(c =>
    c.classList.toggle("selected", +c.dataset.idx === idx));
  document.querySelector(`.inst-card[data-idx="${idx}"]`)
    ?.scrollIntoView({ block:"nearest", behavior:"smooth" });

  if (markers[idx]) { map.panTo(markers[idx].getLatLng(), {animate:true}); markers[idx].openPopup(); }

  /* Header */
  const morph1Label = DIM_MAP["morph1"].labels[r.morphology1] || r.morphology1 || "";
  document.getElementById("d-color").style.background = color;
  document.getElementById("d-ey").style.color = color;
  document.getElementById("d-ey").textContent = morph1Label.toUpperCase();
  document.getElementById("d-titl").textContent = r.Name || "(unnamed)";

  const inner = document.getElementById("detail-inner");
  /* Remove old photo if any */
  const oldPhoto = inner.querySelector(".d-photo");
  if (oldPhoto) oldPhoto.remove();

  /* Photo (if image column populated) */
  if (r.image) {
    const img = document.createElement("img");
    img.className = "d-photo";
    img.src = "images/" + r.image;
    img.alt = r.Name || "";
    img.onerror = () => img.remove();
    inner.insertBefore(img, inner.querySelector(".dhd"));
  }

  const desc = (r.description || "").replace(/^"+|"+$/g, "").trim();
  const binaries = [
    {label:"Threshold", val:r.binary_threshold},
    {label:"Surprise",  val:r.binary_surprise},
    {label:"Sanctuary", val:r.binary_sanctuary},
    {label:"Other",     val:r.binary_other},
  ].filter(b => b.val);

  const locLabel   = DIM_MAP["location"].labels[r.location]   || r.location   || "—";
  const modeLabel  = r.mode || "—";
  const phenLabel  = DIM_MAP["phenom1"].labels[r.phenomenology1] || r.phenomenology1 || "—";
  const freqLabel  = r.frequency || "—";
  const histLabel  = r["history(y/n)"] === "y" ? "Yes" : r["history(y/n)"] === "n" ? "No" : (r["history(y/n)"] || "—");
  const walkLabel  = r["awe_walk(y/n)"] === "y" ? "Yes" : r["awe_walk(y/n)"] === "n" ? "No" : (r["awe_walk(y/n)"] || "—");
  const morph2Label = (r.morphology2 || "").replace(/_/g," ");
  const phenom2Label = (r.phenomenology2 || "").replace(/_/g," ");

  document.getElementById("detail-body").innerHTML =
    (desc ? `<div><div class="d-section-label">Description</div><div class="d-desc">${desc}</div></div>` : "") +

    `<div><div class="d-section-label">Geography</div><div class="d-grid">` +
      cell("Location", locLabel) + cell("Mode", modeLabel) +
      cell("Awe Walk Route", walkLabel) + (r.affiliation ? cell("Affiliation", r.affiliation) : "") +
    `</div></div>` +

    `<div><div class="d-section-label">Morphology</div><div class="d-chips">` +
      (r.morphology1 ? `<span class="d-chip" style="background:${color}">${morph1Label}</span>` : "") +
      (morph2Label   ? `<span class="d-chip" style="background:#9a8878">${morph2Label}</span>` : "") +
    `</div></div>` +

    `<div><div class="d-section-label">Phenomenology</div>` +
      (phenLabel || phenom2Label ? `<div class="d-chips" style="margin-bottom:6px">` +
        (r.phenomenology1 ? `<span class="d-chip" style="background:#b05a3a">${phenLabel}</span>` : "") +
        (phenom2Label     ? `<span class="d-chip" style="background:#7a6e5f">${phenom2Label}</span>` : "") +
      `</div>` : "") +
      (binaries.length ? `<div class="d-binary-row">${binaries.map(b =>
        `<span class="d-binary${b.val.toLowerCase()==="y"?" yes":""}">${b.label}: ${b.val}</span>`
      ).join("")}</div>` : "") +
    `</div>` +

    `<div><div class="d-section-label">Temporality</div><div class="d-grid">` +
      cell("Frequency", freqLabel) + cell("History", histLabel) +
    `</div></div>`;

  document.getElementById("detail-panel").classList.add("open");
}

function cell(label, val) {
  if (!val || val === "—") return `<div><div class="d-cell-label">${label}</div><div class="d-cell-val" style="color:var(--stone)">—</div></div>`;
  return `<div><div class="d-cell-label">${label}</div><div class="d-cell-val">${val}</div></div>`;
}

function closeDetail() {
  selectedIdx = null;
  document.getElementById("detail-panel").classList.remove("open");
  document.querySelectorAll(".inst-card").forEach(c => c.classList.remove("selected"));
  const inner = document.getElementById("detail-inner");
  const photo = inner.querySelector(".d-photo");
  if (photo) photo.remove();
}

/* ============================================================
   LEAFLET MAP
   ============================================================ */
const map = L.map("atlas-map", { center:[42.375,-71.115], zoom:14 });
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
  subdomains:"abcd", maxZoom:19,
}).addTo(map);

function makeIcon(color) {
  return L.divIcon({
    className:"",
    html:`<div style="width:11px;height:11px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.28)"></div>`,
    iconSize:[11,11], iconAnchor:[5,5], popupAnchor:[0,-9],
  });
}

function buildMarkers() {
  AWE_DATA.forEach((r, i) => {
    const lat = parseFloat(r.Y), lng = parseFloat(r.X);
    if (isNaN(lat) || isNaN(lng)) { markers.push(null); return; }
    const color     = MORPH_COLORS[r.morphology1] || "#8c4518";
    const morph1Lbl = DIM_MAP["morph1"].labels[r.morphology1] || r.morphology1 || "";
    const locLbl    = DIM_MAP["location"].labels[r.location] || r.location || "";
    const phenLbl   = DIM_MAP["phenom1"].labels[r.phenomenology1] || r.phenomenology1 || "";
    const desc      = (r.description || "").replace(/^"+|"+$/g,"").trim();
    const short     = desc.length > 110 ? desc.slice(0,108)+"…" : desc;
    const imgHTML   = r.image ? `<img class="lpop-img" src="images/${r.image}" alt="" onerror="this.remove()">` : "";

    const popup = L.popup({maxWidth:250, minWidth:210}).setContent(
      `${imgHTML}<div class="lpop">` +
        `<div class="lpop-type" style="color:${color}">${morph1Lbl.toUpperCase()}</div>` +
        `<div class="lpop-name">${r.Name || "(unnamed)"}</div>` +
        `<div class="lpop-tags">` +
          (locLbl  ? `<span class="ltag" style="background:#4a6a8a">${locLbl}</span>` : "") +
          (phenLbl ? `<span class="ltag" style="background:#b05a3a">${phenLbl}</span>` : "") +
        `</div>` +
        (short ? `<div class="lpop-desc">${short}</div>` : "") +
        `<button class="lpop-btn" onclick="selectInstance(${i})">View Details →</button>` +
      `</div>`
    );
    const marker = L.marker([lat,lng], {icon:makeIcon(color)}).bindPopup(popup);
    marker.addTo(map);
    marker.on("click", () => selectInstance(i));
    markers.push(marker);
  });
}

/* ============================================================
   INIT
   ============================================================ */
buildFilters();
buildMarkers();
renderList(new Set(AWE_DATA.map((_,i) => i)));
</script>
</body>
</html>
"""

output = HTML.replace("DATA_PLACEHOLDER", data_json)
with open("atlas.html", "w", encoding="utf-8") as f:
    f.write(output)
print(f"atlas.html written — {len(output):,} chars")
