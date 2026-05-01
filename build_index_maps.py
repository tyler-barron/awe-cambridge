"""
build_index_maps.py
Patches index.html to add:
  1. Overview map panel (all points + pulsing hotspots)
  2. Interactive Leaflet maps replacing PNGs in archetype map panels
  3. "To answer these questions" bridge panel after the question panel
  4. Background: story panels more white, map panels grey
Run: py build_index_maps.py
"""
import csv, json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── Load data ────────────────────────────────────────────────────────────────
with open('awe_with_clusters.csv', encoding='utf-8-sig') as f:
    awe_rows = list(csv.DictReader(f))
with open('hotspot_points.csv', encoding='utf-8-sig') as f:
    hot_rows = list(csv.DictReader(f))
with open('cambridge_boundary.geojson', encoding='utf-8') as f:
    boundary_geojson = json.load(f)

COLORS = {'1':'#4a7a8a','2':'#5a7d3d','3':'#8c4518','4':'#6b5b8a'}

# All points: [lat, lon, cluster_int]
all_pts = [[round(float(r['lat']),5), round(float(r['lon']),5), int(r['cluster'])] for r in awe_rows]

# Per-cluster points: [lat, lon]
cluster_pts = {}
for c in ['1','2','3','4']:
    cluster_pts[c] = [[round(float(r['lat']),5), round(float(r['lon']),5)]
                      for r in awe_rows if r['cluster']==c]

# All hotspots: [lat, lon]
all_hot = [[round(float(r['lat']),5), round(float(r['lon']),5)] for r in hot_rows]

# Per-cluster hotspots
cluster_hot = {}
for c in ['1','2','3','4']:
    cluster_hot[c] = [[round(float(r['lat']),5), round(float(r['lon']),5)]
                      for r in hot_rows if r['cluster'].startswith(f'Cluster {c}')]

# Compact boundary GeoJSON
boundary_js = json.dumps(boundary_geojson, separators=(',',':'))

# ── Build JS data block ──────────────────────────────────────────────────────
data_block = f"""<script>
/* ── Index map data ── */
const CAMB_BOUNDARY = {boundary_js};
const AWE_ALL_PTS = {json.dumps(all_pts, separators=(',',':'))};
const AWE_CLUSTER_PTS = {{
  '1':{json.dumps(cluster_pts['1'],separators=(',',':'))},
  '2':{json.dumps(cluster_pts['2'],separators=(',',':'))},
  '3':{json.dumps(cluster_pts['3'],separators=(',',':'))},
  '4':{json.dumps(cluster_pts['4'],separators=(',',':'))}
}};
const HOT_ALL = {json.dumps(all_hot,separators=(',',':'))};
const HOT_CLUSTER = {{
  '1':{json.dumps(cluster_hot['1'],separators=(',',':'))},
  '2':{json.dumps(cluster_hot['2'],separators=(',',':'))},
  '3':{json.dumps(cluster_hot['3'],separators=(',',':'))},
  '4':{json.dumps(cluster_hot['4'],separators=(',',':'))}
}};
const CLUSTER_COLORS = {{'1':'{COLORS['1']}','2':'{COLORS['2']}','3':'{COLORS['3']}','4':'{COLORS['4']}'}};
</script>"""

# ── Map init JS ──────────────────────────────────────────────────────────────
map_js = """<script>
/* ── Shared map helpers ── */
function buildCambMap(id, bg) {
  var m = L.map(id, {
    zoomControl: false, attributionControl: false,
    scrollWheelZoom: false, dragging: false,
    doubleClickZoom: false, boxZoom: false,
    keyboard: false, touchZoom: false
  }).setView([42.375, -71.115], 13);
  // Pale grey base
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
    maxZoom:18, subdomains:'abcd', opacity:0.35
  }).addTo(m);
  // Cambridge boundary
  L.geoJSON(CAMB_BOUNDARY, {
    style:{color:'#6b6259',weight:1.5,fillColor: bg||'transparent',fillOpacity:0}
  }).addTo(m);
  return m;
}

function addAwePoints(map, pts, color) {
  pts.forEach(function(p) {
    L.circleMarker([p[0],p[1]], {
      radius:4, color:color, fillColor:color,
      fillOpacity:0.75, weight:0.5, opacity:0.9
    }).addTo(map);
  });
}

function addAllColoredPoints(map, pts) {
  pts.forEach(function(p) {
    var col = CLUSTER_COLORS[String(p[2])];
    L.circleMarker([p[0],p[1]], {
      radius:3.5, color:col, fillColor:col,
      fillOpacity:0.7, weight:0.5, opacity:0.85
    }).addTo(map);
  });
}

function addHotspots(map, pts, color) {
  pts.forEach(function(p) {
    var icon = L.divIcon({
      className:'',
      html:'<div class="hs-ring" style="border-color:'+color+'"></div><div class="hs-dot" style="background:'+color+'"></div>',
      iconSize:[20,20], iconAnchor:[10,10]
    });
    L.marker([p[0],p[1]], {icon:icon}).addTo(map);
  });
}

/* ── Lazy init via IntersectionObserver ── */
var _mapInited = {};
function lazyMap(containerId, initFn) {
  var el = document.getElementById(containerId);
  if (!el) return;
  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      if (e.isIntersecting && !_mapInited[containerId]) {
        _mapInited[containerId] = true;
        obs.disconnect();
        initFn();
      }
    });
  }, {threshold:0.1});
  obs.observe(el);
}

/* ── Overview map (all points) ── */
lazyMap('map-overview', function() {
  var m = buildCambMap('map-overview', '#e8e8e6');
  addAllColoredPoints(m, AWE_ALL_PTS);
  addHotspots(m, HOT_ALL, '#1c1914');
});

/* ── Archetype map 1: Expansive Nature ── */
lazyMap('map-arch1', function() {
  var m = buildCambMap('map-arch1', '#e8e8e6');
  addAwePoints(m, AWE_CLUSTER_PTS['1'], CLUSTER_COLORS['1']);
  addHotspots(m, HOT_CLUSTER['1'], CLUSTER_COLORS['1']);
});

/* ── Archetype map 2: Wild Nature ── */
lazyMap('map-arch2', function() {
  var m = buildCambMap('map-arch2', '#e8e8e6');
  addAwePoints(m, AWE_CLUSTER_PTS['2'], CLUSTER_COLORS['2']);
  addHotspots(m, HOT_CLUSTER['2'], CLUSTER_COLORS['2']);
});

/* ── Archetype map 3: Built Beauty ── */
lazyMap('map-arch3', function() {
  var m = buildCambMap('map-arch3', '#e8e8e6');
  addAwePoints(m, AWE_CLUSTER_PTS['3'], CLUSTER_COLORS['3']);
  addHotspots(m, HOT_CLUSTER['3'], CLUSTER_COLORS['3']);
});

/* ── Archetype map 4: Inclusive Interaction ── */
lazyMap('map-arch4', function() {
  var m = buildCambMap('map-arch4', '#e8e8e6');
  addAwePoints(m, AWE_CLUSTER_PTS['4'], CLUSTER_COLORS['4']);
  addHotspots(m, HOT_CLUSTER['4'], CLUSTER_COLORS['4']);
});
</script>"""

# ── Overview map panel HTML ──────────────────────────────────────────────────
overview_panel = """
<!-- ═══════════════════════════════════════════════════════════════════════
     PANEL 4 — OVERVIEW MAP
     ═══════════════════════════════════════════════════════════════════════ -->
<section class="panel p-map p-map-overview" style="--m-color: var(--ink)">
  <div class="map-left map-left-overview">
    <p class="map-overview-text reveal">
      Most archetypes are spatially clustered within the city, gravitating toward hotspots shaped by where moments of awe were recorded.
    </p>
    <div class="map-overview-legend reveal reveal-delay-1">
      <span class="ov-leg-item" style="color:var(--a1)">● Expansive Nature</span>
      <span class="ov-leg-item" style="color:var(--a2)">● Wild Nature</span>
      <span class="ov-leg-item" style="color:var(--a3)">● Built Beauty</span>
      <span class="ov-leg-item" style="color:var(--a4)">● Inclusive Interaction</span>
      <span class="ov-leg-item" style="color:var(--ink)">◎ Hotspot</span>
    </div>
  </div>
  <div class="map-right">
    <div class="story-map" id="map-overview"></div>
  </div>
  <div class="scroll-cue">
    <div class="scroll-cue-line"></div>
    <div class="scroll-cue-label">Scroll</div>
  </div>
</section>

"""

# ── Bridge text panel HTML ───────────────────────────────────────────────────
bridge_panel = """
<!-- ═══════════════════════════════════════════════════════════════════════
     PANEL — ATLAS BRIDGE
     ═══════════════════════════════════════════════════════════════════════ -->
<section class="panel p-atlas-bridge">
  <div class="bridge-inner">
    <p class="bridge-text reveal">
      To answer these questions, the Awe Atlas offers a set of tools to
      <em>encounter</em>, <em>explore</em> and <em>share</em>
      awe in Cambridge.
    </p>
  </div>
  <div class="scroll-cue">
    <div class="scroll-cue-line"></div>
    <div class="scroll-cue-label">Scroll</div>
  </div>
</section>

"""

# ── Extra CSS to inject ──────────────────────────────────────────────────────
extra_css = """
/* ── Leaflet ── */
.story-map { width:100%; height:100%; position:absolute; inset:0; }
.map-right { position:relative; }

/* ── Pulsing hotspot markers ── */
.hs-ring {
  position:absolute; width:20px; height:20px; border-radius:50%;
  border:2px solid; top:0; left:0;
  animation:hsPulse 2s ease-out infinite;
}
.hs-dot {
  position:absolute; width:6px; height:6px; border-radius:50%;
  top:7px; left:7px;
}
@keyframes hsPulse {
  0%   { transform:scale(0.5); opacity:1; }
  80%  { transform:scale(2.2); opacity:0; }
  100% { transform:scale(0.5); opacity:0; }
}

/* ── Overview map panel ── */
.p-map-overview { background:#e8e8e6; }
.map-left-overview {
  display:flex; flex-direction:column; justify-content:center; gap:20px;
}
.map-overview-text {
  font-size:clamp(17px,2vw,22px); font-style:italic; font-weight:300;
  line-height:1.55; color:var(--ink);
}
.map-overview-legend {
  display:flex; flex-direction:column; gap:6px;
}
.ov-leg-item {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:.08em;
}

/* ── Map panel grey background ── */
.p-map { background:#e8e8e6; }

/* ── Atlas bridge panel ── */
.p-atlas-bridge {
  background:#e8e8e6;
  color:var(--ink);
}
.bridge-inner { max-width:680px; padding:0 48px; text-align:center; }
.bridge-text {
  font-size:clamp(24px,3.2vw,38px); font-weight:300; line-height:1.45;
  color:var(--ink);
}
.bridge-text em { font-style:italic; color:var(--accent); }

/* ── Story panels more white ── */
.p-definition, .p-landscape, .p-archetypes, .p-question, .p-tools {
  background:#fafaf8;
}
.p-definition { background:#1c1914; } /* keep dark */
.p-question   { background:#1c1914; } /* keep dark */
"""

# ── Patch index.html ─────────────────────────────────────────────────────────
with open('index.html', encoding='utf-8') as f:
    html = f.read()

orig_len = len(html)

# 1. Add Leaflet CSS/JS in <head>
LEAFLET_TAG = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>\n<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
if 'leaflet@1.9.4/dist/leaflet.css' not in html:
    html = html.replace(
        '</style>\n</head>',
        extra_css + '\n</style>\n' + LEAFLET_TAG + '\n</head>'
    )
else:
    # Still inject extra CSS
    html = html.replace('</style>\n</head>', extra_css + '\n</style>\n</head>')

# 2. Insert data block right after <body>
if 'CAMB_BOUNDARY' not in html:
    html = html.replace('<body>\n', '<body>\n' + data_block + '\n')

# 3. Insert overview map panel between panel 3 and (old) panel 4
#    Find the comment for PANEL 4 — MAP: EXPANSIVE NATURE
PANEL4_MARKER = '<!-- ═══════════════════════════════════════════════════════════════════════\n     PANEL 4 — MAP: EXPANSIVE NATURE'
if 'map-overview' not in html:
    html = html.replace(PANEL4_MARKER, overview_panel + PANEL4_MARKER)

# 4. Replace PNG images in archetype map panels with Leaflet map divs
ARCH_MAPS = [
    ('cluster_map_cluster_1_expansive_nature.png', 'map-arch1'),
    ('cluster_map_cluster_2_wild_nature.png',       'map-arch2'),
    ('cluster_map_cluster_3_built_beauty.png',      'map-arch3'),
    ('cluster_map_cluster_4_inclusive_interaction.png', 'map-arch4'),
]
for img_src, map_id in ARCH_MAPS:
    # Match the <img> tag for this archetype
    old = f'<img src="{img_src}"'
    new = f'<div class="story-map" id="{map_id}"></div><!--'
    # Remove the rest of the img tag up to >
    pattern = f'<img src="{re.escape(img_src)}"[^>]*>'
    replacement = f'<div class="story-map" id="{map_id}"></div>'
    html = re.sub(pattern, replacement, html)

# 5. Move overview intro text out of panel 4 (it's now in overview panel)
#    The map-cluster-intro paragraph in panel 4 is now redundant
OLD_INTRO = """    <p class="map-cluster-intro reveal">
      Most archetypes are spatially clustered within the city, gravitating toward
      hotspots shaped by where moments of awe were recorded.
    </p>
    <div class="map-cluster-label reveal reveal-delay-1">Archetype 01"""
NEW_INTRO = """    <div class="map-cluster-label reveal">Archetype 01"""
html = html.replace(OLD_INTRO, NEW_INTRO)

# 6. Insert bridge panel after question panel (before the tool grid section)
TOOL_GRID_MARKER = "<!-- ═══════════════════════════════════════════════════════════════════════\n     PANEL 9 — TOOL GRID"
if 'p-atlas-bridge' not in html:
    html = html.replace(TOOL_GRID_MARKER, bridge_panel + TOOL_GRID_MARKER)

# 7. Inject map JS before </body>
REVEAL_SCRIPT = '<script>\nvar observer = new IntersectionObserver'
if 'lazyMap' not in html:
    html = html.replace(REVEAL_SCRIPT, map_js + '\n' + REVEAL_SCRIPT)

# 8. Change parchment to more-white in CSS variable (story panels)
html = html.replace('--parchment: #f7f7f5;', '--parchment: #fafaf8;')
html = html.replace('--linen:     #e8e5e0;', '--linen:     #e0ddd8;')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"OK: index.html patched [{orig_len:,} -> {len(html):,} bytes]")
print(f"  + Overview map panel")
print(f"  + 4 Leaflet archetype maps (replacing PNGs)")
print(f"  + Atlas bridge text panel")
print(f"  + Grey map panel backgrounds")
print(f"  + More-white story panel backgrounds")
