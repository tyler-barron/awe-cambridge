"""
build_community.py — Generates community.html (Awe Atlas, Tool 01)
by taking awe-atlas-v5_6.html as the base template and making
surgical replacements: title, header text, and all data arrays.
Everything else (CSS, HTML, JS) is preserved byte-for-byte.

Usage:
  py build_community.py
"""

import csv, math, re

# ── Config ──────────────────────────────────────────────────────────────────
CSV_PATH    = "awe-data.csv"
SOURCE_HTML = "awe-atlas-v5_6.html"
OUTPUT_HTML = "community.html"

# Harvard Square as the reference origin for distances / bearings
ORIGIN_LAT = 42.3736
ORIGIN_LNG = -71.1190

# ── Display-name mappings ────────────────────────────────────────────────────
MORPH1_TYPE = {
    'collective_effervescence': 'Collective Effervescence',
    'epiphany/knowledge':       'Epiphany / Knowledge',
    'life/death':               'Life & Death',
    'moral_beauty':             'Moral Beauty',
    'music':                    'Music',
    'nature':                   'Nature',
    'visual_design':            'Visual Design',
}

MORPH1_EMOJI = {
    'collective_effervescence': '🌊',
    'epiphany/knowledge':       '✨',
    'life/death':               '🕯️',
    'moral_beauty':             '🧡',
    'music':                    '🎵',
    'nature':                   '🌿',
    'visual_design':            '🏛️',
}

FREQ_SEASON = {
    'daily':     'Daily',
    'ephemeral': 'Ephemeral',
    'periodic':  'Periodic',
    'recurring': 'Recurring',
    'seasonal':  'Seasonal',
    'timeless':  'Always',
}

# Compass-step templates indexed by 8-point bearing
COMPASS_STEPS = {
    'N':  ["Head <em>north</em>. Let the familiar streets become unfamiliar.",
           "Look for a change in scale — something larger than its neighbours.",
           "Slow down as you approach. <em>Arrive without hurrying.</em>",
           "Stay as long as you need to. <em>There is no schedule here.</em>"],
    'NE': ["Head <em>northeast</em>. Let yourself be pulled by whatever looks interesting.",
           "You are looking for a change in texture — a shift in the street's feeling.",
           "The place will reveal itself. <em>You will know when you are close.</em>",
           "If you wander off course, <em>good.</em> Notice what you find."],
    'E':  ["Head <em>east</em>. The character of the streets changes gradually.",
           "Look for the thing that seems slightly out of place. <em>That is your landmark.</em>",
           "Resist the urge to check your phone. <em>Navigate by feel.</em>",
           "Arrive and take a breath before you start noticing."],
    'SE': ["Head <em>southeast</em>. The neighbourhood shifts as you walk.",
           "Follow the longest straight stretch of street you can find.",
           "The destination is quieter than you expect. <em>Give it room.</em>",
           "<em>Linger.</em> The experience compounds with time."],
    'S':  ["Head <em>south</em>. The city opens up as you go.",
           "Follow what draws your eye rather than the shortest route.",
           "You are looking for a threshold — a doorway, a gap, a change in light.",
           "<em>Come to a complete stop.</em> Let everything arrive."],
    'SW': ["Head <em>southwest</em>. The streets become quieter.",
           "Let yourself get slightly lost. <em>That is part of it.</em>",
           "When you arrive, stand still for a moment before approaching.",
           "Notice the quality of the light here versus where you started."],
    'W':  ["Head <em>west</em>. Follow streets that slope downhill.",
           "You will sense it before you see it. <em>Trust that.</em>",
           "Look for what does not quite fit — that is usually the thing.",
           "<em>No introduction necessary.</em> Just show up and be present."],
    'NW': ["Head <em>northwest</em>. Look for something old among the new.",
           "The main entrance may not be the right one. <em>Try the side.</em>",
           "Walk slowly as you arrive. Rush and you will miss the whole thing.",
           "<em>Sit. Wait. Let the place find you.</em>"],
}

# ── Geometry helpers ─────────────────────────────────────────────────────────
def haversine_miles(lat1, lng1, lat2, lng2):
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlmbd = math.radians(lng2 - lng1)
    a = (math.sin(dphi/2)**2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlmbd/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing_deg(lat1, lng1, lat2, lng2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlmbd = math.radians(lng2 - lng1)
    x = math.sin(dlmbd) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2)
         - math.sin(phi1) * math.cos(phi2) * math.cos(dlmbd))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def bearing_octant(deg):
    octants = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    return octants[round(deg / 45) % 8]

def dist_label(miles):
    mins = max(1, round(miles / 3.0 * 60))   # ~3 mph walking
    return f"{miles:.1f} mi · {mins} min"

# ── Escape for a JS single-quoted string ─────────────────────────────────────
def js_esc(s):
    return (s.replace('\\', '\\\\')
             .replace("'", "\\'")
             .replace('\n', ' ')
             .replace('\r', ''))

# ── Read CSV ─────────────────────────────────────────────────────────────────
with open(CSV_PATH, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f"Read {len(rows)} rows from {CSV_PATH}")

# ── Build JS arrays ──────────────────────────────────────────────────────────
places_parts  = []
coords_parts  = []

for r in rows:
    try:
        lat = float(r['Y'])
        lng = float(r['X'])
    except (ValueError, KeyError):
        continue

    m1      = r.get('morphology1', '').strip()
    freq    = r.get('frequency', '').strip()
    name    = r.get('Name', '').strip()
    raw_desc = r.get('description', '').strip().strip('"')
    is_walk  = r.get('awe_walk(y/n)', 'n').strip().lower() == 'y'

    # Change 3: binary fields
    freq_raw  = r.get('frequency', '').strip()
    threshold = r.get('binary_threshold', 'n').strip().lower() == 'y'
    sanctuary = r.get('binary_sanctuary', 'n').strip().lower() == 'y'
    history_f = r.get('history(y/n)', 'n').strip().lower() == 'y'
    alterity  = r.get('binary_other', 'n').strip().lower() == 'y'

    atype  = MORPH1_TYPE.get(m1, 'Nature')
    emoji  = MORPH1_EMOJI.get(m1, '🌿')
    season = FREQ_SEASON.get(freq, freq.title() if freq else 'Year-round')

    miles   = haversine_miles(ORIGIN_LAT, ORIGIN_LNG, lat, lng)
    bdeg    = bearing_deg(ORIGIN_LAT, ORIGIN_LNG, lat, lng)
    boct    = bearing_octant(bdeg)
    dist_s  = dist_label(miles)

    # Trim description for desc (250 chars) and hint (120 chars)
    desc_s = raw_desc[:250].rstrip(',. ') + ('…' if len(raw_desc) > 250 else '')
    hint_s = raw_desc[:120].rstrip(',. ') + ('…' if len(raw_desc) > 120 else '')
    if not desc_s:
        desc_s = 'A place worth finding.'
        hint_s = ''

    note_text = raw_desc[:200].rstrip(',. ') + ('…' if len(raw_desc) > 200 else '') if raw_desc else 'A place worth finding.'
    notes_js  = "[{author:'Field notes',text:'" + js_esc(note_text) + "'}]"
    steps_js  = "[" + ",".join("'" + js_esc(s) + "'" for s in COMPASS_STEPS[boct]) + "]"
    walk_meta = 'Schedule an awe walk →' if is_walk else ''

    obj = (
        "  {"
        f"emoji:'{emoji}',"
        f"type:'{atype}',"
        f"season:'{js_esc(season)}',"
        f"dist:'{dist_s}',"
        f"name:'{js_esc(name)}',"
        f"desc:'{js_esc(desc_s)}',"
        f"bearing:'{boct}',"
        f"bearingDeg:{round(bdeg)},"
        f"hasWalk:{'true' if is_walk else 'false'},"
        f"frequency:'{js_esc(freq_raw)}',"
        f"threshold:{'true' if threshold else 'false'},"
        f"sanctuary:{'true' if sanctuary else 'false'},"
        f"historyPlace:{'true' if history_f else 'false'},"
        f"alterity:{'true' if alterity else 'false'},"
        f"walkMeta:'{js_esc(walk_meta)}',"
        f"notes:{notes_js},"
        f"compassSteps:{steps_js},"
        f"hint:'{js_esc(hint_s)}'"
        "}"
    )
    places_parts.append(obj)
    coords_parts.append(f"  [{lat}, {lng}]")

places_js     = "var places = [\n" + ",\n".join(places_parts) + "\n];"
placecoords_js = "var placeCoords = [\n" + ",\n".join(coords_parts) + "\n];"

# Change 7: Build walkPlaces JS array
walk_rows = [r for r in rows if r.get('awe_walk(y/n)', 'n').strip().lower() == 'y']
walk_places_parts = []
for r in walk_rows:
    try:
        lat = float(r['Y']); lng = float(r['X'])
    except: continue
    name = r.get('Name', '').strip()
    m1   = r.get('morphology1', '').strip()
    atype = MORPH1_TYPE.get(m1, 'Nature')
    emoji = MORPH1_EMOJI.get(m1, '🌿')
    miles = haversine_miles(ORIGIN_LAT, ORIGIN_LNG, lat, lng)
    dist_s = dist_label(miles)
    raw_desc = r.get('description', '').strip().strip('"')
    desc_s = raw_desc[:180].rstrip(',. ') + ('…' if len(raw_desc) > 180 else '') if raw_desc else ''
    walk_places_parts.append(
        "{name:'" + js_esc(name) + "',type:'" + atype + "',emoji:'" + emoji +
        "',dist:'" + dist_s + "',desc:'" + js_esc(desc_s) + "'}"
    )
walk_places_js = "var walkPlaces = [\n  " + ",\n  ".join(walk_places_parts) + "\n];"

# ── Read source HTML ─────────────────────────────────────────────────────────
with open(SOURCE_HTML, encoding='utf-8') as f:
    html = f.read()

# ── Surgical text replacements ───────────────────────────────────────────────

# Change 2: Page title — keep as "Awe Atlas — Research Tool 01"
html = html.replace(
    '<title>Awe Atlas</title>',
    '<title>Awe Atlas — Research Tool 01</title>',
    1
)

# Change 1: Welcome lines — revert to near-original feel
html = html.replace(
    '<div class="welcome-lines" id="welcome-lines">\n'
    '      <div class="wl wl-sm" id="wl-0">There are places in every city</div>\n'
    '      <div class="wl wl-sm" id="wl-1">that stop people in their tracks.</div>\n'
    '      <div class="wl wl-md" style="margin-top:20px" id="wl-2">A staircase no one notices.</div>\n'
    '      <div class="wl wl-md" id="wl-3">Light through an old window at noon.</div>\n'
    '      <div class="wl wl-md" id="wl-4">Strangers who swim together at dawn.</div>\n'
    '      <div class="wl wl-lg" style="margin-top:24px" id="wl-5">Most of us walk past them every day.</div>\n'
    '    </div>',
    '<div class="welcome-lines" id="welcome-lines">\n'
    '      <div class="wl wl-sm" id="wl-0">There are places in this city</div>\n'
    '      <div class="wl wl-sm" id="wl-1">that stop people in their tracks.</div>\n'
    '      <div class="wl wl-md" style="margin-top:20px" id="wl-2">A garden hidden behind a building.</div>\n'
    '      <div class="wl wl-md" id="wl-3">Light through a window at exactly noon.</div>\n'
    '      <div class="wl wl-md" id="wl-4">A stranger\'s kindness that changes your afternoon.</div>\n'
    '      <div class="wl wl-lg" style="margin-top:24px" id="wl-5">Most of us walk past them every day.</div>\n'
    '    </div>',
    1
)

# Replace the JS animation sequence with a reliable CSS-first version.
# Old code uses per-line setTimeout hide (fragile). New: each line fades in
# via CSS animation (guaranteed order), JS only handles the final
# block→wordmark→button transition.
ANIM_OLD = r"""// JS-driven animation sequence using opacity transitions
(function() {
  // All lines start invisible
  var lineIds = ['wl-0','wl-1','wl-2','wl-3','wl-4','wl-5'];
  lineIds.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) { el.style.opacity = '0'; el.style.transition = 'opacity 1.2s ease'; }
  });

  var wm = document.getElementById('welcome-wordmark');
  var btn = document.getElementById('welcome-enter-btn');
  var skip = document.getElementById('welcome-skip-btn');
  var lines = document.getElementById('welcome-lines');

  if (wm) wm.style.opacity = '0';
  if (btn) btn.style.opacity = '0';

  // Make skip always visible so user can always escape
  if (skip) { skip.style.opacity = '0.7'; skip.style.fontSize = '13px'; skip.style.transition = 'opacity .3s'; }

  function showLine(id, delay, hideAfter) {
    setTimeout(function() {
      var el = document.getElementById(id);
      if (el) {
        el.style.opacity = '1';
        if (hideAfter) {
          setTimeout(function() { el.style.opacity = '0'; }, hideAfter);
        }
      }
    }, delay);
  }

  // Line 0+1 together
  showLine('wl-0', 600,  3200);
  showLine('wl-1', 1000, 3200);
  // Line 2+3+4 staggered
  showLine('wl-2', 4800, 3200);
  showLine('wl-3', 5700, 3200);
  showLine('wl-4', 6600, 3200);
  // Line 5 alone
  showLine('wl-5', 9200, 3400);

  // Fade out lines block, fade in wordmark
  setTimeout(function() {
    if (lines) { lines.style.transition = 'opacity .9s ease'; lines.style.opacity = '0'; }
  }, 13200);
  setTimeout(function() {
    if (wm) { wm.style.transition = 'opacity 1.4s ease'; wm.style.opacity = '1'; }
  }, 13800);
  // Show button
  setTimeout(function() {
    if (btn) { btn.style.transition = 'opacity 1.2s ease'; btn.style.opacity = '1'; }
  }, 15200);
})();"""

ANIM_NEW = r"""// CSS-first welcome animation — each line fades in sequentially via
// animation-delay, stays visible, then the whole block fades out together.
(function() {
  var delays = [0.5, 1.6, 3.2, 4.5, 5.8, 7.4]; // seconds, one per line
  var lineIds = ['wl-0','wl-1','wl-2','wl-3','wl-4','wl-5'];

  lineIds.forEach(function(id, i) {
    var el = document.getElementById(id);
    if (!el) return;
    el.style.opacity = '0';
    el.style.animation = 'wlFadeIn 1.1s ease ' + delays[i] + 's forwards';
  });

  var wm   = document.getElementById('welcome-wordmark');
  var btn  = document.getElementById('welcome-enter-btn');
  var skip = document.getElementById('welcome-skip-btn');
  var lines = document.getElementById('welcome-lines');

  if (wm)   wm.style.opacity  = '0';
  if (btn)  btn.style.opacity = '0';
  if (skip) { skip.style.opacity = '0.7'; skip.style.transition = 'opacity .3s'; }

  // After all lines have settled (~9.8s), fade out block, then show wordmark + button
  setTimeout(function() {
    if (lines) { lines.style.transition = 'opacity 1s ease'; lines.style.opacity = '0'; }
  }, 10200);
  setTimeout(function() {
    if (wm) { wm.style.transition = 'opacity 1.4s ease'; wm.style.opacity = '1'; }
  }, 11000);
  setTimeout(function() {
    if (btn) { btn.style.transition = 'opacity 1.2s ease'; btn.style.opacity = '1'; }
  }, 12200);
})();"""

html = html.replace(ANIM_OLD, ANIM_NEW, 1)

# Add the @keyframes wlFadeIn rule to the CSS (inject before first </style>)
html = html.replace(
    '.wl-sm { font-size: 15px; letter-spacing: .04em; }',
    '@keyframes wlFadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }\n'
    '.wl-sm { font-size: 15px; letter-spacing: .04em; }',
    1
)

# Welcome screen — label: Change 2 — updated label
html = html.replace(
    '<div class="welcome-wordmark-label">A field guide to wonder</div>',
    '<div class="welcome-wordmark-label">Awe in Cambridge</div>',
    1
)

# Change 2: Keep welcome-wordmark-title as "Awe Atlas" (no replacement needed,
# just don't change it). Remove the old rename replacement.

# Change 2: Welcome sub — revert to original
html = html.replace(
    '<div class="welcome-wordmark-sub">Find the places that will move you.</div>',
    '<div class="welcome-wordmark-sub">Find the places that will move you.</div>',
    1
)

# Change 2: Header wordmark — change to "← Threshold · Awe Atlas"
html = html.replace(
    '<div class="wordmark">A field guide to wonder</div>',
    '<div class="wordmark"><a href="index.html" style="color:inherit;text-decoration:none;">← Threshold</a> · Awe Atlas</div>',
    1
)

# Change 2: Keep h1 as "Awe Atlas" (no replacement — don't rename to Everyday Awe)
# The original h1 is: <h1 class="title">Awe <em>Atlas</em></h1> — keep as-is.

# Header subtitle
html = html.replace(
    '<p class="subtitle">Wander toward something that will move you.</p>',
    '<p class="subtitle">Find and create everyday moments of wonder.</p>',
    1
)

# Discord community card title
html = html.replace(
    '<div class="discord-card-title">Awe Atlas Community</div>',
    '<div class="discord-card-title">Everyday Awe Community</div>',
    1
)

# Replace typeColors to match updated type names
html = html.replace(
    "var typeColors = {\n"
    "  'Nature':       'var(--nature)',\n"
    "  'Art & Design': 'var(--art)',\n"
    "  'Collective':   'var(--collective)',\n"
    "  'Spiritual':    'var(--spiritual)',\n"
    "  'Moral Beauty': 'var(--moral)',\n"
    "  'Epiphany':     'var(--epiphany)',\n"
    "  'Music':        'var(--saffron)',\n"
    "  'Life & Death': 'var(--charcoal)'\n"
    "};",
    "var typeColors = {\n"
    "  'Nature':                  'var(--nature)',\n"
    "  'Visual Design':           'var(--art)',\n"
    "  'Collective Effervescence':'var(--collective)',\n"
    "  'Moral Beauty':            'var(--moral)',\n"
    "  'Epiphany / Knowledge':    'var(--epiphany)',\n"
    "  'Music':                   'var(--saffron)',\n"
    "  'Life & Death':            'var(--charcoal)'\n"
    "};",
    1
)

# ── Submission system ────────────────────────────────────────────────────────
# Replace the alert() submit handler with localStorage accumulation + success screen

SUBMIT_HANDLER_OLD = r"""document.getElementById('submit-place-btn').addEventListener('click', function() {
  var name = document.getElementById('sub-name').value.trim();
  if (!name) { alert('Give the place a name first.'); return; }
  var coords = document.getElementById('map-coords').textContent;
  var coordMsg = coords !== 'no pin yet' ? ' Pinned at ' + coords + '.' : ' No map pin — you can add later.';
  alert('Thank you for submitting "' + name + '".' + coordMsg + ' It will be reviewed and added to the atlas soon.');
  showScreen('screen-share'); setActiveTab('share');
});"""

SUBMIT_HANDLER_NEW = r"""
/* ============================================================
   SUBMISSION — localStorage accumulation + CSV export
   ============================================================ */
var AWE_SUBMISSIONS_KEY = 'awe_submissions_v1';

function getSubmissions() {
  try { return JSON.parse(localStorage.getItem(AWE_SUBMISSIONS_KEY) || '[]'); }
  catch(e) { return []; }
}

function saveSubmission(sub) {
  var all = getSubmissions();
  sub.id = Date.now();
  sub.submitted_at = new Date().toISOString();
  all.push(sub);
  localStorage.setItem(AWE_SUBMISSIONS_KEY, JSON.stringify(all));
  return sub;
}

var CSV_COLS = ['X','Y','Name','affiliation','awe_walk(y/n)','mode','location',
  'history(y/n)','frequency','morphology1','morphology2','phenomenology1',
  'phenomenology2','binary_threshold','binary_surprise','binary_sanctuary',
  'binary_other','description','wayfinding','senses','submitted_at'];

function subToRow(s) {
  var v = function(x) { return '"' + (x||'').toString().replace(/"/g,'""') + '"'; };
  return [
    v(s.lng), v(s.lat), v(s.name), v(s.affiliation), v(''),
    v(s.mode), v(''), v(''), v(s.frequency), v(''), v(''), v(''), v(''),
    v(''), v(''), v(''), v(''), v(s.description), v(s.wayfinding),
    v(s.senses), v(s.submitted_at)
  ].join(',');
}

function downloadSubmissionsCSV() {
  var all = getSubmissions();
  if (!all.length) { alert('No submissions yet.'); return; }
  var lines = [CSV_COLS.join(',')].concat(all.map(subToRow));
  var blob = new Blob([lines.join('\n')], { type:'text/csv;charset=utf-8;' });
  var url  = URL.createObjectURL(blob);
  var a = document.createElement('a'); a.href = url;
  a.download = 'awe_submissions_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click(); URL.revokeObjectURL(url);
}

document.getElementById('submit-place-btn').addEventListener('click', function() {
  var name = document.getElementById('sub-name').value.trim();
  if (!name) { document.getElementById('sub-name').focus(); return; }

  // Collect map coords
  var coordsRaw = document.getElementById('map-coords').textContent;
  var lat = '', lng = '';
  if (coordsRaw && coordsRaw !== 'no pin yet') {
    var parts = coordsRaw.split(',');
    if (parts.length === 2) { lat = parts[0].trim(); lng = parts[1].trim(); }
  }

  // Collect chips
  function getChips(groupId) {
    var sel = [];
    (document.getElementById(groupId)||{querySelectorAll:function(){return[];}})
      .querySelectorAll('.chip.selected').forEach(function(c){ sel.push(c.textContent.trim()); });
    return sel.join('; ');
  }
  function getSingleChip(attr) {
    var el = document.querySelector('[data-single="'+attr+'"].selected');
    return el ? el.textContent.trim() : '';
  }

  var sub = {
    name:        name,
    address:     document.getElementById('sub-address').value.trim(),
    lat:         lat,
    lng:         lng,
    awe_types:   getChips('sub-awe-type'),
    description: document.getElementById('sub-desc').value.trim(),
    season:      getSingleChip('avail-season'),
    frequency:   getSingleChip('avail-freq'),
    wayfinding:  document.getElementById('sub-wayfind').value.trim(),
    affiliation: document.getElementById('sub-author').value.trim(),
    mode:        getChips('sub-how-found-group'),
    senses:      getChips('sub-senses-group'),
  };

  saveSubmission(sub);

  // Populate success screen
  document.getElementById('ss-name').textContent    = sub.name;
  document.getElementById('ss-address').textContent = sub.address || '—';
  document.getElementById('ss-coords').textContent  = (lat && lng) ? lat + ', ' + lng : 'no pin placed';
  document.getElementById('ss-type').textContent    = sub.awe_types || '—';
  document.getElementById('ss-desc').textContent    = sub.description ? (sub.description.length > 150 ? sub.description.slice(0,148)+'…' : sub.description) : '—';
  document.getElementById('ss-season').textContent  = [sub.season, sub.frequency].filter(Boolean).join(' · ') || '—';
  document.getElementById('ss-count').textContent   = getSubmissions().length;

  // Build clipboard row
  var row = CSV_COLS.join(',') + '\n' + subToRow(sub);
  document.getElementById('ss-copy-btn').onclick = function() {
    navigator.clipboard.writeText(row).then(function() {
      document.getElementById('ss-copy-btn').textContent = 'Copied!';
      setTimeout(function(){ document.getElementById('ss-copy-btn').textContent = 'Copy CSV row'; }, 2500);
    });
  };

  // Clear form
  ['sub-name','sub-address','sub-desc','sub-wayfind','sub-author'].forEach(function(id){
    var el = document.getElementById(id); if (el) el.value = '';
  });
  document.querySelectorAll('.submit-place-form .chip.selected').forEach(function(c){ c.classList.remove('selected'); });

  showScreen('screen-submit-success');
});"""

html = html.replace(SUBMIT_HANDLER_OLD, SUBMIT_HANDLER_NEW, 1)

# Inject success screen and download button before </body>
SUCCESS_SCREEN = r"""
<div class="screen" id="screen-submit-success">
  <div class="submit-success-wrap">
    <div class="ss-icon">✦</div>
    <div class="ss-headline">Thank you for submitting.</div>
    <p class="ss-sub">Your moment of awe has been saved to this device. The research team reviews submissions regularly and adds them to the atlas.</p>
    <div class="ss-card">
      <div class="ss-row"><span class="ss-label">Place</span><span class="ss-val" id="ss-name">—</span></div>
      <div class="ss-row"><span class="ss-label">Address</span><span class="ss-val" id="ss-address">—</span></div>
      <div class="ss-row"><span class="ss-label">Coordinates</span><span class="ss-val" id="ss-coords">—</span></div>
      <div class="ss-row"><span class="ss-label">Awe type</span><span class="ss-val" id="ss-type">—</span></div>
      <div class="ss-row"><span class="ss-label">Season</span><span class="ss-val" id="ss-season">—</span></div>
      <div class="ss-row ss-row-desc"><span class="ss-label">Description</span><span class="ss-val" id="ss-desc">—</span></div>
    </div>
    <p class="ss-hint">You have <strong id="ss-count">1</strong> submission saved on this device.</p>
    <div class="ss-actions">
      <button class="btn-primary" id="ss-copy-btn">Copy CSV row</button>
      <button class="btn-ghost" onclick="downloadSubmissionsCSV()">Download all as CSV</button>
    </div>
    <button class="ss-back" onclick="showScreen('screen-share');setActiveTab('share');document.getElementById('smode-submit').click();">+ Submit another place</button>
    <button class="ss-back" onclick="showScreen('screen-home');setActiveTab('discover');" style="margin-top:6px">← Back to Discover</button>
  </div>
</div>

<style>
.submit-success-wrap{padding:40px 28px 80px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:0;}
.ss-icon{font-size:36px;margin-bottom:14px;color:var(--saffron);}
.ss-headline{font-size:30px;font-weight:300;line-height:1.1;margin-bottom:10px;}
.ss-headline em{font-style:italic;color:var(--accent);}
.ss-sub{font-size:14px;line-height:1.7;color:var(--muted);font-style:italic;max-width:320px;margin-bottom:24px;}
.ss-card{width:100%;background:rgba(255,255,255,.35);border:1px solid rgba(140,69,24,.18);border-radius:3px;padding:14px 16px;text-align:left;margin-bottom:16px;}
.ss-row{display:flex;gap:8px;padding:5px 0;border-bottom:1px solid rgba(140,69,24,.07);}
.ss-row:last-child{border-bottom:none;}
.ss-row-desc{flex-direction:column;gap:3px;}
.ss-label{font-family:"Space Mono",monospace;font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:var(--stone);flex-shrink:0;min-width:80px;padding-top:2px;}
.ss-val{font-size:13px;color:var(--ink);line-height:1.4;}
.ss-hint{font-size:13px;color:var(--muted);font-style:italic;margin-bottom:18px;}
.ss-actions{display:flex;flex-direction:column;gap:8px;width:100%;margin-bottom:16px;}
.ss-back{background:none;border:none;font-family:"Space Mono",monospace;font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);cursor:pointer;text-decoration:underline;text-underline-offset:3px;transition:color .2s;}
.ss-back:hover{color:var(--accent);}
</style>
"""

# Also add chip group IDs for mode and senses in the form so JS can collect them
html = html.replace(
    '<div class="chip-group">\n            <button class="chip" data-multi="true">\U0001f6b6 Walking</button>',
    '<div class="chip-group" id="sub-how-found-group">\n            <button class="chip" data-multi="true">\U0001f6b6 Walking</button>',
    1
)
html = html.replace(
    '<div class="chip-group">\n            <button class="chip" data-multi="true">\U0001f441 Sight</button>',
    '<div class="chip-group" id="sub-senses-group">\n            <button class="chip" data-multi="true">\U0001f441 Sight</button>',
    1
)

html = html.replace('</body>', SUCCESS_SCREEN + '\n</body>', 1)

# ── Download button in Field Notes header ────────────────────────────────────
EXPORT_BTN_JS = r"""
// Export submissions CSV button
var exportBtn = document.getElementById('export-submissions-btn');
if (exportBtn) {
  exportBtn.addEventListener('click', downloadSubmissionsCSV);
  // Show count badge
  function updateExportBadge() {
    var n = getSubmissions().length;
    var badge = document.getElementById('export-badge');
    if (badge) { badge.textContent = n; badge.style.display = n ? 'inline' : 'none'; }
  }
  updateExportBadge();
}
"""

# Inject the export button after the share-mode toggle buttons
html = html.replace(
    '<button class="share-mode-btn" id="smode-submit">Submit a place</button>',
    '<button class="share-mode-btn" id="smode-submit">Submit a place</button>'
    + '<button class="share-mode-btn" id="export-submissions-btn" style="margin-left:auto;font-size:8px;opacity:.7">'
    + 'Export CSV <span id="export-badge" style="display:none;background:var(--saffron);color:var(--ink);border-radius:8px;padding:1px 5px;font-size:7px;margin-left:3px"></span>'
    + '</button>',
    1
)

# ── Update atlas map filter buttons to use new type names ────────────────────
html = html.replace(
    '<button class="map-filter-btn" data-mapfilter="Collective">Collective</button>',
    '<button class="map-filter-btn" data-mapfilter="Collective Effervescence">Collective Effervescence</button>',
    1
)
html = html.replace(
    '<button class="map-filter-btn" data-mapfilter="Art &amp; Design">Art &amp; Design</button>',
    '<button class="map-filter-btn" data-mapfilter="Visual Design">Visual Design</button>',
    1
)
html = html.replace(
    '<button class="map-filter-btn" data-mapfilter="Epiphany">Epiphany</button>',
    '<button class="map-filter-btn" data-mapfilter="Epiphany / Knowledge">Epiphany / Knowledge</button>',
    1
)
# Remove "Spiritual" filter button — no longer a category in our data
html = html.replace(
    '\n        <button class="map-filter-btn" data-mapfilter="Spiritual">Spiritual</button>',
    '',
    1
)

# Change 4: Inject temporality chips + binary toggles into home screen HTML
html = html.replace(
    '      <div style="padding-top:16px">\n'
    '        <div class="section-label">How do you want to navigate?</div>',
    '      <div style="padding-top:16px">\n'
    '        <div class="section-label">When do you want to find it?</div>\n'
    '        <div class="tempo-chips" id="tempo-chips">\n'
    '          <button class="chip all-chip" data-tempo="all">All</button>\n'
    '          <button class="chip selected" data-tempo="timeless">Always</button>\n'
    '          <button class="chip" data-tempo="daily">Daily</button>\n'
    '          <button class="chip" data-tempo="recurring">Recurring</button>\n'
    '          <button class="chip" data-tempo="seasonal">Seasonal</button>\n'
    '        </div>\n'
    '        <p class="nav-desc" id="tempo-note" style="font-size:11px;margin-top:6px;margin-bottom:0">Always — these places are there whenever you arrive. No timing required.</p>\n'
    '      </div>\n'
    '      <div style="padding-top:14px">\n'
    '        <div class="section-label">Only show places that are... <span style="font-style:italic;font-family:\'Cormorant Garamond\',serif;text-transform:none;letter-spacing:0;font-size:12px;color:var(--muted)">(optional)</span></div>\n'
    '        <div class="binary-toggles" id="binary-toggles">\n'
    '          <button class="binary-toggle" data-binary="threshold">Threshold Crossing</button>\n'
    '          <button class="binary-toggle" data-binary="sanctuary">Sanctuary</button>\n'
    '          <button class="binary-toggle" data-binary="historyPlace">Historical</button>\n'
    '          <button class="binary-toggle" data-binary="alterity">Alterity</button>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div style="padding-top:16px">\n'
    '        <div class="section-label">How do you want to navigate?</div>',
    1
)

# Change 8: Add id="walk-cards-container" to the walks section
html = html.replace(
    '      <div class="walk-card" data-walk="0">',
    '      <div id="walk-cards-container">\n      <div class="walk-card" data-walk="0">',
    1
)

# ── Leaflet map overrides ─────────────────────────────────────────────────────
LEAFLET_OVERRIDES = r"""
/* ── Leaflet map overrides ────────────────────────────────────────────── */
/* Tooltip styling to match app design */
.leaf-tip {
  background: var(--parchment) !important;
  border: 1px solid rgba(140,69,24,.22) !important;
  border-radius: 2px !important;
  box-shadow: 0 3px 10px rgba(28,25,20,.14) !important;
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 13px !important;
  font-style: italic !important;
  color: var(--ink) !important;
  padding: 4px 8px !important;
}
.leaf-tip::before { display: none !important; }

/* Change 6: Hide place description */
#place-desc { display: none; }
"""

LEAFLET_JS = r"""
/* ============================================================
   LEAFLET MAP OVERRIDES
   Replaces the SVG-based atlas map and submit-form pin map
   with real Leaflet maps matching the Interactive Map tool.
   ============================================================ */
var _leafAtlas = null;
var _leafAtlasMarkers = [];

var TYPE_HEX = {
  'Nature':                   '#97ba74',
  'Visual Design':            '#b05a3a',
  'Collective Effervescence': '#4a7a8a',
  'Moral Beauty':             '#c4a882',
  'Epiphany / Knowledge':     '#6b5b8a',
  'Music':                    '#caa74d',
  'Life & Death':             '#2c2118'
};

function initAtlasMap() {
  if (_leafAtlas) { renderAtlasPins(currentMapFilter); return; }
  atlasMapInited = true;
  var el = document.getElementById('atlas-map');
  if (!el) return;

  _leafAtlas = L.map('atlas-map', { center:[42.3736,-71.1190], zoom:14 });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution:'\u00a9 OpenStreetMap contributors \u00a9 CARTO', maxZoom:19
  }).addTo(_leafAtlas);
  _leafAtlas.on('click', function() { closeMapPopup(); });
  renderAtlasPins('all');
}

function renderAtlasPins(filter) {
  currentMapFilter = filter;
  if (!_leafAtlas) return;

  _leafAtlasMarkers.forEach(function(m){ _leafAtlas.removeLayer(m); });
  _leafAtlasMarkers = [];

  var visible = 0;
  places.forEach(function(p, i) {
    if (filter !== 'all' && p.type !== filter) return;
    var coord = placeCoords[i];
    if (!coord || !coord[0] || !coord[1]) return;

    var hex = TYPE_HEX[p.type] || '#8c4518';
    var icon = L.divIcon({
      className: '',
      html: '<div style="width:11px;height:11px;border-radius:50%;background:' + hex +
            ';border:2px solid rgba(255,255,255,.9);box-shadow:0 1px 5px rgba(0,0,0,.32);cursor:pointer;transition:transform .15s"></div>',
      iconSize: [11,11], iconAnchor:[5,5]
    });

    var marker = L.marker([coord[0],coord[1]], {icon:icon});
    (function(idx){ marker.on('click', function(e){ L.DomEvent.stopPropagation(e); showMapPopup(idx); }); })(i);
    marker.bindTooltip(p.name.replace(/<[^>]+>/g,''), {
      direction:'top', offset:[0,-8], className:'leaf-tip'
    });
    marker.addTo(_leafAtlas);
    _leafAtlasMarkers.push(marker);
    visible++;
  });

  var badge = document.getElementById('map-count-badge');
  if (badge) badge.textContent = visible + ' place' + (visible !== 1 ? 's' : '');
}

/* Submit-form pin map */
var _leafSub = null, _leafSubPin = null;

function initMap() {
  if (_leafSub) return;
  var el = document.getElementById('sub-map');
  if (!el) return;

  _leafSub = L.map('sub-map', { center:[42.3736,-71.1190], zoom:14 });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution:'\u00a9 OpenStreetMap contributors \u00a9 CARTO', maxZoom:19
  }).addTo(_leafSub);

  _leafSub.on('click', function(e){
    var lat = e.latlng.lat.toFixed(6), lng = e.latlng.lng.toFixed(6);
    document.getElementById('map-coords').textContent = lat + ', ' + lng;
    if (_leafSubPin) {
      _leafSubPin.setLatLng(e.latlng);
    } else {
      _leafSubPin = L.marker(e.latlng, {draggable:true}).addTo(_leafSub);
      _leafSubPin.on('dragend', function(){
        var p = _leafSubPin.getLatLng();
        document.getElementById('map-coords').textContent = p.lat.toFixed(6) + ', ' + p.lng.toFixed(6);
      });
    }
  });
}
"""

# Change 5: Filter JS for tempo/binary state + override findAwe() + dynamic walk cards
FILTER_JS = r"""
/* ── Temporality + binary filter state ─────────────────── */
var selectedTempo = 'timeless';
var activeBinaryFilters = [];

// Tempo chips
document.querySelectorAll('[data-tempo]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    document.querySelectorAll('[data-tempo]').forEach(function(b){ b.classList.remove('selected'); });
    btn.classList.add('selected');
    selectedTempo = btn.dataset.tempo;
    var note = document.getElementById('tempo-note');
    if (note) {
      var msgs = {
        'timeless':  'Always — these places are there whenever you arrive. No timing required.',
        'daily':     'Daily — available within an ordinary day, timed to diurnal rhythms or regular hours.',
        'recurring': 'Recurring — these places repeat on a schedule. Check before you go.',
        'seasonal':  'Seasonal — tied to a specific time of year. Come back at the right season.',
        'all':       'Showing all places regardless of when they\'re available.'
      };
      note.textContent = msgs[selectedTempo] || '';
    }
  });
});

// Binary toggles
var btStyles = '.binary-toggle{padding:5px 11px;border:1px solid rgba(140,69,24,.25);border-radius:20px;font-family:"Cormorant Garamond",serif;font-size:12px;font-style:italic;background:transparent;color:var(--muted);cursor:pointer;transition:all .15s;margin-bottom:3px}' +
  '.binary-toggle.active{background:var(--ink);border-color:var(--ink);color:var(--parchment);font-style:normal}' +
  '.binary-toggles{display:flex;flex-wrap:wrap;gap:5px}';
var btStyleEl = document.createElement('style');
btStyleEl.textContent = btStyles;
document.head.appendChild(btStyleEl);

document.querySelectorAll('[data-binary]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var key = btn.dataset.binary;
    if (btn.classList.contains('active')) {
      btn.classList.remove('active');
      activeBinaryFilters = activeBinaryFilters.filter(function(k){ return k !== key; });
    } else {
      btn.classList.add('active');
      activeBinaryFilters.push(key);
    }
  });
});

/* Override findAwe() to respect tempo + binary filters */
function findAwe() {
  document.getElementById('find-awe-label').textContent = 'Finding awe...';
  setTimeout(function() {
    var pool = places.filter(function(p) {
      if (selectedTempo !== 'all' && p.frequency !== selectedTempo) return false;
      for (var i = 0; i < activeBinaryFilters.length; i++) {
        if (!p[activeBinaryFilters[i]]) return false;
      }
      return true;
    });
    if (!pool.length) pool = places; // fallback: ignore filters if nothing matches
    var globalIdx = Math.floor(Math.random() * pool.length);
    var p = pool[globalIdx];
    currentPlaceIdx = places.indexOf(p);
    currentPlace = p;
    populatePlace();
    document.getElementById('find-awe-label').textContent = 'Find Awe \u2192';
    if (navMode === 'compass') { showCompassScreen(); } else { showAIDirScreen(); }
    setActiveTab('home');
  }, 700);
}

/* ── Dynamic walk cards from CSV walk places ─── */
(function() {
  var container = document.getElementById('walk-cards-container');
  if (!container || !window.walkPlaces || !walkPlaces.length) return;
  container.innerHTML = '';
  // Show up to 8 walk-eligible places
  var shown = walkPlaces.slice(0, 8);
  shown.forEach(function(wp, i) {
    var card = document.createElement('div');
    card.className = 'walk-card';
    card.innerHTML =
      '<div class="walk-card-top">' +
        '<div style="font-size:28px;flex-shrink:0">' + wp.emoji + '</div>' +
        '<div class="walk-card-info">' +
          '<div class="walk-card-name">' + wp.name + '</div>' +
          '<div class="walk-card-meta">' + wp.dist + ' \u00b7 ' + wp.type + '</div>' +
        '</div>' +
        '<span class="walk-type-badge">' + wp.type + '</span>' +
      '</div>' +
      '<div class="walk-card-footer" style="padding-top:8px">' +
        '<p style="font-size:12px;font-style:italic;color:var(--muted);line-height:1.5;margin:0">' + (wp.desc || '') + '</p>' +
      '</div>' +
      '<button class="join-walk-btn schedule-for-btn" data-name="' + wp.name.replace(/'/g,"\\\'") + '">Schedule a walk here</button>';
    container.appendChild(card);
  });
  // Wire schedule-for buttons
  container.querySelectorAll('.schedule-for-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var nameEl = document.getElementById('sched-place');
      if (nameEl) nameEl.value = btn.dataset.name;
      showScreen('screen-schedule');
    });
  });
})();
"""

# Inject Leaflet CSS override into the first </style> tag
html = html.replace('</style>', LEAFLET_OVERRIDES + '</style>', 1)

# Inject JS before the last </script> tag (handle \r\n endings)
last_script = html.rfind('</script>')
if last_script != -1:
    html = html[:last_script] + EXPORT_BTN_JS + LEAFLET_JS + FILTER_JS + html[last_script:]

# ── Schedule Walk: replace alert() with localStorage system ──────────────────
SCHEDULE_WALK_JS_OLD = r"""document.getElementById('submit-schedule-btn').addEventListener('click', function() {
  var place = document.getElementById('sched-place').value.trim();
  if (!place) { alert('Add a destination first.'); return; }
  alert('Your walk to "' + place + '" has been posted and sent to #walks-somerville on Discord.');
  showScreen('screen-walks');
});"""

SCHEDULE_WALK_JS_NEW = r"""
/* ============================================================
   SCHEDULED WALKS — localStorage persistence
   ============================================================ */
var AWE_WALKS_KEY = 'awe_walks_v1';

function getScheduledWalks() {
  try { return JSON.parse(localStorage.getItem(AWE_WALKS_KEY) || '[]'); }
  catch(e) { return []; }
}

function saveScheduledWalk(walk) {
  var all = getScheduledWalks();
  walk.id = Date.now();
  all.unshift(walk); // newest first
  localStorage.setItem(AWE_WALKS_KEY, JSON.stringify(all));
  return walk;
}

function renderScheduledWalks() {
  var walks = getScheduledWalks();
  var container = document.getElementById('walk-cards-container');
  if (!container) return;
  // Remove any previously rendered user walks
  container.querySelectorAll('.user-walk-card').forEach(function(el){ el.remove(); });
  if (!walks.length) return;
  var ref = container.firstChild;
  walks.forEach(function(w) {
    var d = w.date ? new Date(w.date + 'T12:00:00') : null;
    var monthStr = d ? d.toLocaleString('default',{month:'short'}) : '—';
    var dayStr   = d ? d.getDate() : '—';
    var card = document.createElement('div');
    card.className = 'walk-card user-walk-card';
    card.style.cssText = 'border-left:3px solid var(--nature);padding-left:10px';
    card.innerHTML =
      '<div style="font-family:\'Space Mono\',monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--nature);margin-bottom:6px">Your scheduled walk</div>' +
      '<div class="walk-card-top">' +
        '<div class="walk-card-date"><div class="walk-date-month">' + monthStr + '</div><div class="walk-date-day">' + dayStr + '</div></div>' +
        '<div class="walk-card-info">' +
          '<div class="walk-card-name">' + (w.place || 'Unnamed walk') + '</div>' +
          '<div class="walk-card-meta">' +
            (w.time || '') + (w.meet ? ' · ' + w.meet : '') + '<br>' +
            (w.type || '') + (w.size ? ' · ' + w.size : '') +
          '</div>' +
        '</div>' +
        '<span class="walk-type-badge" style="background:var(--nature)">' + (w.type || 'Walk') + '</span>' +
      '</div>' +
      (w.note ? '<p style="font-size:12px;font-style:italic;color:var(--muted);line-height:1.5;margin:6px 0 0">' + w.note + '</p>' : '') +
      '<button class="join-walk-btn" style="border-color:rgba(151,186,116,.4);color:var(--nature);margin-top:8px" onclick="this.textContent=\'Walk posted \u2713\';this.disabled=true">Share walk →</button>';
    container.insertBefore(card, ref);
  });
}

document.getElementById('submit-schedule-btn').addEventListener('click', function() {
  var place = document.getElementById('sched-place').value.trim();
  if (!place) { document.getElementById('sched-place').focus(); return; }

  function getSelectedChip(attr) {
    var el = document.querySelector('.schedule-form .form-chip[data-single="'+attr+'"].selected');
    return el ? el.textContent.trim() : '';
  }

  var walk = {
    place:  place,
    date:   document.getElementById('sched-date').value,
    time:   document.getElementById('sched-time').value,
    meet:   document.getElementById('sched-meet').value.trim(),
    type:   getSelectedChip('type'),
    size:   getSelectedChip('size'),
    note:   document.getElementById('sched-note').value.trim(),
  };
  saveScheduledWalk(walk);

  // Clear form
  ['sched-place','sched-date','sched-time','sched-meet','sched-note'].forEach(function(id){
    var el = document.getElementById(id); if (el) el.value = '';
  });
  document.querySelectorAll('.schedule-form .form-chip.selected').forEach(function(c){ c.classList.remove('selected'); });

  renderScheduledWalks();
  showScreen('screen-walks');
});
"""

html = html.replace(SCHEDULE_WALK_JS_OLD, SCHEDULE_WALK_JS_NEW, 1)

# Add renderScheduledWalks() call on walks screen entry
# Inject into the switchTab function to trigger render when tab shown
html = html.replace(
    "else if (tab === 'walks') { showScreen('screen-walks'); }",
    "else if (tab === 'walks') { showScreen('screen-walks'); renderScheduledWalks && renderScheduledWalks(); }",
    1
)

# ── Host Awe Talk: replace alert() handlers with real form screen ─────────────
HOST_TALK_SCREEN = r"""
<div class="screen" id="screen-host-talk">
  <div class="schedule-header">
    <div class="schedule-title">Host an Awe Talk</div>
    <div class="schedule-sub">A small gathering to share what moves you</div>
  </div>
  <div class="schedule-form">
    <div class="form-field">
      <div class="form-label">Talk title or question</div>
      <input class="form-input" type="text" placeholder="e.g. What has nature done to you?" id="talk-title">
    </div>
    <div class="form-row">
      <div class="form-field"><div class="form-label">Date</div><input class="form-input" type="date" id="talk-date"></div>
      <div class="form-field"><div class="form-label">Time</div><input class="form-input" type="time" id="talk-time"></div>
    </div>
    <div class="form-field">
      <div class="form-label">Location</div>
      <input class="form-input" type="text" placeholder="Café, home, park bench..." id="talk-location">
    </div>
    <div class="form-field">
      <div class="form-label">Opening prompt <span style="font-style:italic;font-family:'Cormorant Garamond',serif;text-transform:none;letter-spacing:0;font-size:12px;color:var(--muted)">(optional)</span></div>
      <textarea class="form-input" style="height:60px;resize:none" placeholder="The first question you'll ask the room..." id="talk-prompt"></textarea>
    </div>
    <div class="form-field">
      <div class="form-label">Awe theme</div>
      <div class="form-chips">
        <button class="form-chip" data-single="talk-type">Nature</button>
        <button class="form-chip" data-single="talk-type">Collective Effervescence</button>
        <button class="form-chip" data-single="talk-type">Moral Beauty</button>
        <button class="form-chip" data-single="talk-type">Epiphany / Knowledge</button>
        <button class="form-chip" data-single="talk-type">Music</button>
        <button class="form-chip" data-single="talk-type">Life &amp; Death</button>
        <button class="form-chip" data-single="talk-type">Visual Design</button>
      </div>
    </div>
    <div class="form-field">
      <div class="form-label">Max group size</div>
      <div class="form-chips">
        <button class="form-chip selected" data-single="talk-size">Up to 6</button>
        <button class="form-chip" data-single="talk-size">Up to 10</button>
        <button class="form-chip" data-single="talk-size">Up to 15</button>
        <button class="form-chip" data-single="talk-size">Open</button>
      </div>
    </div>
    <div class="form-field">
      <div class="form-label">Your name <span style="font-style:italic;font-family:'Cormorant Garamond',serif;text-transform:none;letter-spacing:0;font-size:12px;color:var(--muted)">(optional)</span></div>
      <input class="form-input" type="text" placeholder="Or leave anonymous" id="talk-host">
    </div>
  </div>
  <div class="schedule-footer">
    <button class="btn-primary" id="submit-host-talk-btn">Post this talk →</button>
    <button class="btn-ghost" id="cancel-host-talk-btn">← Cancel</button>
  </div>
</div>
"""

# ── Host talk JS ──────────────────────────────────────────────────────────────
HOST_TALK_JS = r"""
/* ============================================================
   AWE TALKS — localStorage persistence
   ============================================================ */
var AWE_TALKS_KEY = 'awe_talks_v1';

function getScheduledTalks() {
  try { return JSON.parse(localStorage.getItem(AWE_TALKS_KEY) || '[]'); }
  catch(e) { return []; }
}

function saveScheduledTalk(talk) {
  var all = getScheduledTalks();
  talk.id = Date.now();
  all.unshift(talk);
  localStorage.setItem(AWE_TALKS_KEY, JSON.stringify(all));
  return talk;
}

function renderScheduledTalks() {
  var talks = getScheduledTalks();
  var container = document.getElementById('user-talks-container');
  if (!container) return;
  container.innerHTML = '';
  if (!talks.length) return;
  talks.forEach(function(t) {
    var d = t.date ? new Date(t.date + 'T12:00:00') : null;
    var monthStr = d ? d.toLocaleString('default',{month:'short'}) : '—';
    var dayStr   = d ? d.getDate() : '—';
    var card = document.createElement('div');
    card.className = 'walk-card';
    card.style.cssText = 'border-left:3px solid var(--epiphany);padding-left:10px';
    card.innerHTML =
      '<div style="font-family:\'Space Mono\',monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--epiphany);margin-bottom:6px">Your hosted talk</div>' +
      '<div class="walk-card-top">' +
        '<div class="walk-card-date"><div class="walk-date-month">' + monthStr + '</div><div class="walk-date-day">' + dayStr + '</div></div>' +
        '<div class="walk-card-info">' +
          '<div class="walk-card-name"><em>' + (t.title || 'Untitled talk') + '</em></div>' +
          '<div class="walk-card-meta">' +
            (t.time || '') + (t.location ? ' · ' + t.location : '') + '<br>' +
            'Hosted by ' + (t.host || 'Anonymous') + ' · ' + (t.size || 'Open') +
          '</div>' +
          (t.prompt ? '<div class="awe-talk-prompt">Opening prompt: <em>"' + t.prompt + '"</em></div>' : '') +
        '</div>' +
        '<span class="walk-type-badge" style="background:var(--epiphany)">' + (t.type || 'Talk') + '</span>' +
      '</div>' +
      '<button class="join-walk-btn" style="border-color:rgba(107,91,138,.3);color:var(--epiphany);margin-top:8px" onclick="this.textContent=\'Talk posted \u2713\';this.disabled=true">Share talk →</button>';
    container.appendChild(card);
  });
}

// Wire form chips for talk screen
document.querySelectorAll('.form-chip[data-single="talk-type"], .form-chip[data-single="talk-size"]').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var attr = btn.dataset.single;
    document.querySelectorAll('.form-chip[data-single="'+attr+'"]').forEach(function(b){ b.classList.remove('selected'); });
    btn.classList.add('selected');
  });
});

document.getElementById('submit-host-talk-btn').addEventListener('click', function() {
  var title = document.getElementById('talk-title').value.trim();
  if (!title) { document.getElementById('talk-title').focus(); return; }

  function getSelectedChip(attr) {
    var el = document.querySelector('.form-chip[data-single="'+attr+'"].selected');
    return el ? el.textContent.trim() : '';
  }

  var talk = {
    title:    title,
    date:     document.getElementById('talk-date').value,
    time:     document.getElementById('talk-time').value,
    location: document.getElementById('talk-location').value.trim(),
    prompt:   document.getElementById('talk-prompt').value.trim(),
    type:     getSelectedChip('talk-type'),
    size:     getSelectedChip('talk-size'),
    host:     document.getElementById('talk-host').value.trim(),
  };
  saveScheduledTalk(talk);

  // Clear form
  ['talk-title','talk-date','talk-time','talk-location','talk-prompt','talk-host'].forEach(function(id){
    var el = document.getElementById(id); if (el) el.value = '';
  });
  document.querySelectorAll('.form-chip[data-single="talk-type"]').forEach(function(c){ c.classList.remove('selected'); });

  renderScheduledTalks();
  showScreen('screen-walks');
});

document.getElementById('cancel-host-talk-btn').addEventListener('click', function() {
  showScreen('screen-walks');
});

// Replace talk alert() handlers
var talkBtnIds = ['schedule-talk-btn', 'host-talk-cta'];
talkBtnIds.forEach(function(id) {
  var el = document.getElementById(id);
  if (el) {
    el.onclick = null;
    el.addEventListener('click', function(e) {
      e.preventDefault(); e.stopImmediatePropagation();
      showScreen('screen-host-talk');
    });
  }
});
"""

# Inject host-talk screen before </body> (alongside success screen)
host_talk_body = HOST_TALK_SCREEN
# Add user-talks-container div right before the "Host your own Awe Talk" button
html = html.replace(
    '<button class="btn-ghost" style="margin:4px 0 8px;width:100%;font-size:13px" id="host-talk-cta">',
    '<div id="user-talks-container"></div>\n      <button class="btn-ghost" style="margin:4px 0 8px;width:100%;font-size:13px" id="host-talk-cta">',
    1
)
html = html.replace('</body>', host_talk_body + '\n</body>', 1)

# ── Inject host-talk JS at the end of last script ────────────────────────────
last_script = html.rfind('</script>')
if last_script != -1:
    html = html[:last_script] + HOST_TALK_JS + html[last_script:]

# ── Replace the inline schedule-talk alert()s in the source script ───────────
html = html.replace(
    "document.getElementById('schedule-talk-btn').addEventListener('click', function() {\n  alert('Host an Awe Talk \u2014 coming soon. For now, propose one in #awe-talks on Discord.');\n});",
    "// schedule-talk-btn wired by HOST_TALK_JS override",
    1
)
html = html.replace(
    "document.getElementById('host-talk-cta').addEventListener('click', function() {\n  alert('Host an Awe Talk \u2014 coming soon. For now, propose one in #awe-talks on Discord.');\n});",
    "// host-talk-cta wired by HOST_TALK_JS override",
    1
)

# Change 7: Inject walkPlaces before the places array, then replace places and placeCoords
html = html.replace('var places = [', walk_places_js + '\nvar places = [', 1)

# Replace var places = [...];
html = re.sub(
    r'var places = \[[\s\S]*?\];',
    places_js,
    html,
    count=1
)

# Replace var placeCoords = [...];
html = re.sub(
    r'var placeCoords = \[[\s\S]*?\];',
    placecoords_js,
    html,
    count=1
)

# ── Write output ─────────────────────────────────────────────────────────────
with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"OK: Wrote {OUTPUT_HTML}  ({len(places_parts)} places, {len(coords_parts)} coords, {len(walk_places_parts)} walk places)")
