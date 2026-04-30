/* ═══════════════════════════════════════════════════════════════
   map.js  —  Shortest Path Algorithm Simulator
   Features:
   • Click-on-map node selection (Source / Destination modes)
   • Algorithm checkboxes (run only selected)
   • Step-by-step exploration animation per algorithm
   • Clears all previous layers before each new run
   • Neon glow polylines on CartoDB Dark Matter tiles
═══════════════════════════════════════════════════════════════ */

const ALGO_CFG = {
  dijkstra:       { label:'Dijkstra',      color:'#00f5ff', weight:5, cardClass:'cyan'    },
  astar:          { label:'A* Search',     color:'#ff00e5', weight:5, cardClass:'magenta' },
  bellman_ford:   { label:'Bellman-Ford',  color:'#00ff88', weight:5, cardClass:'lime'    },
  floyd_warshall: { label:'Floyd-Warshall',color:'#ff8c00', weight:5, cardClass:'orange'  },
};

// ── State ──────────────────────────────────────────────────────
let map;
let allNodes      = [];          // [{node_id, node_num, lat, lon}]
let nodeMarkersLayer;            // L.layerGroup for all node dots
let routeLayer;                  // L.layerGroup for paths + markers (cleared each run)
let animDots      = {};          // algo → L.layerGroup for exploration dots
let srcId         = null;
let dstId         = null;
let selectionMode = 'src';       // 'src' | 'dst'
let animSpeed     = 30;          // ms per explored node step
let isRunning     = false;

// ── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadGraph();
});

function initMap() {
  map = L.map('map', { center:[18.5204,73.8567], zoom:15, zoomControl:true });

  // CartoDB Dark Matter — pure black tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution:'&copy; <a href="https://carto.com/">CARTO</a>',
    subdomains:'abcd', maxZoom:19,
  }).addTo(map);

  nodeMarkersLayer = L.layerGroup().addTo(map);
  routeLayer       = L.layerGroup().addTo(map);
}

// ── Load Graph ─────────────────────────────────────────────────
async function loadGraph() {
  setStatus('Loading Pune road network...');
  try {
    const res  = await fetch('/graph');
    const data = await res.json();
    allNodes   = data.nodes;

    document.getElementById('node-count-badge').textContent =
      `${allNodes.length} nodes · Pune OSM`;

    plotNodeMarkers(allNodes);
    setStatus(`Ready — ${allNodes.length} nodes. Click a node on the map to set SOURCE`);
  } catch(e) {
    setStatus('Error loading graph: ' + e.message);
  }
}

// ── Node Markers (clickable dots) ──────────────────────────────
function plotNodeMarkers(nodes) {
  nodeMarkersLayer.clearLayers();

  nodes.forEach(n => {
    const icon = makeNodeIcon(n.node_id);
    const marker = L.marker([n.lat, n.lon], { icon })
      .bindTooltip(`Node #${n.node_num}`, { sticky:true, direction:'top', offset:[0,-4] });
    marker.on('click', () => handleNodeClick(n));
    marker.addTo(nodeMarkersLayer);
    n._marker = marker;
  });
}

function makeNodeIcon(nodeId) {
  const isSrc = (nodeId === srcId);
  const isDst = (nodeId === dstId);
  let style;
  if (isSrc) {
    style = 'width:16px;height:16px;border-radius:50%;background:rgba(0,255,136,.35);border:2.5px solid #00ff88;box-shadow:0 0 14px #00ff88,0 0 28px rgba(0,255,136,.4);cursor:pointer;';
  } else if (isDst) {
    style = 'width:16px;height:16px;border-radius:50%;background:rgba(255,0,229,.35);border:2.5px solid #ff00e5;box-shadow:0 0 14px #ff00e5,0 0 28px rgba(255,0,229,.4);cursor:pointer;';
  } else {
    style = 'width:8px;height:8px;border-radius:50%;background:rgba(0,245,255,.35);border:1px solid rgba(0,245,255,.7);cursor:pointer;transition:transform .1s;';
  }
  return L.divIcon({ className:'', html:`<div style="${style}"></div>`,
    iconSize: isSrc||isDst ? [16,16] : [8,8],
    iconAnchor: isSrc||isDst ? [8,8] : [4,4],
  });
}

function refreshAllMarkerIcons() {
  allNodes.forEach(n => {
    if (n._marker) n._marker.setIcon(makeNodeIcon(n.node_id));
  });
}

// ── Node Click ─────────────────────────────────────────────────
function handleNodeClick(n) {
  if (isRunning) return;

  if (selectionMode === 'src') {
    srcId = n.node_id;
    updateNodeDisplay('src', n);
    setMode('dst');   // auto-switch to destination mode
  } else {
    if (n.node_id === srcId) { setStatus('Destination must be different from source.'); return; }
    dstId = n.node_id;
    updateNodeDisplay('dst', n);
    // Both selected: ready to run
    if (srcId !== null) {
      hideInstruction();
      updateComputeBtn();
    }
  }
  refreshAllMarkerIcons();
  updateComputeBtn();
}

function updateNodeDisplay(type, n) {
  const el = document.getElementById(`${type}-display`);
  const card = document.getElementById(`${type}-card`);
  el.innerHTML = `<span>Node #${n.node_num}</span>`;
  card.classList.add('has-value');
}

// ── Selection Mode ─────────────────────────────────────────────
window.setMode = function(mode) {
  selectionMode = mode;
  document.getElementById('mode-src-btn').classList.toggle('active', mode==='src');
  document.getElementById('mode-dst-btn').classList.toggle('active', mode==='dst');
  updateInstruction();
};

function updateInstruction() {
  const el   = document.getElementById('map-instruction');
  const text = document.getElementById('instruction-text');
  if (srcId !== null && dstId !== null) { hideInstruction(); return; }
  el.classList.remove('dst-mode','done');
  if (selectionMode === 'dst') {
    el.classList.add('dst-mode');
    text.innerHTML = 'Click any node to set <strong>DESTINATION</strong>';
  } else {
    text.innerHTML = 'Click any node to set <strong>SOURCE</strong>';
  }
}

function hideInstruction() {
  document.getElementById('map-instruction').classList.add('done');
}

// ── Clear controls ─────────────────────────────────────────────
window.clearSource = function() {
  srcId = null;
  document.getElementById('src-display').innerHTML = '<span class="node-placeholder">Click a node on the map</span>';
  document.getElementById('src-card').classList.remove('has-value');
  setMode('src');
  updateInstruction();
  refreshAllMarkerIcons();
  updateComputeBtn();
};
window.clearDest = function() {
  dstId = null;
  document.getElementById('dst-display').innerHTML = '<span class="node-placeholder">Click a node on the map</span>';
  document.getElementById('dst-card').classList.remove('has-value');
  if (srcId !== null) setMode('dst');
  updateInstruction();
  refreshAllMarkerIcons();
  updateComputeBtn();
};

window.clearAll = function() {
  clearSource();
  clearDest();
  clearRouteLayer();
  hideResults();
  setStatus('Cleared. Click a node on the map to set SOURCE.');
};

// ── Algorithm Toggles ──────────────────────────────────────────
window.onAlgoToggle = function() { updateComputeBtn(); };

function getSelectedAlgos() {
  return Array.from(document.querySelectorAll('.algo-toggle input:checked'))
              .map(cb => cb.value);
}

// ── Speed ──────────────────────────────────────────────────────
window.setSpeed = function(ms) {
  animSpeed = ms;
  document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
  const map = {80:'speed-slow', 30:'speed-med', 5:'speed-fast'};
  if (map[ms]) document.getElementById(map[ms]).classList.add('active');
};

// ── Compute Button State ───────────────────────────────────────
function updateComputeBtn() {
  const btn = document.getElementById('btn-compute');
  const ready = srcId !== null && dstId !== null && getSelectedAlgos().length > 0;
  btn.disabled = !ready || isRunning;
}

// ── Clear Route Layer (paths + anim dots) ─────────────────────
function clearRouteLayer() {
  routeLayer.clearLayers();
  Object.values(animDots).forEach(lg => lg.clearLayers());
  animDots = {};
}

// ── Compute Routes ─────────────────────────────────────────────
window.computeRoutes = async function() {
  if (isRunning || !srcId || !dstId) return;
  const selectedAlgos = getSelectedAlgos();
  if (!selectedAlgos.length) { setStatus('Select at least one algorithm.'); return; }

  // ─ Clear previous results ─
  clearRouteLayer();
  hideResults();

  isRunning = true;
  const btn = document.getElementById('btn-compute');
  btn.classList.add('loading');
  btn.disabled = true;
  setStatus('Sending to server...');

  try {
    const res  = await fetch('/route', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ src:srcId, dst:dstId, algorithms:selectedAlgos }),
    });
    const data = await res.json();

    if (!data.ok) { setStatus('Error: ' + (data.error||'Unknown')); return; }

    // Show result cards immediately (with animating state)
    showResultCards(selectedAlgos, data.results);

    // Run animations for each selected algo simultaneously
    setStatus('Animating exploration...');
    showAnimProgress();
    await animateAll(data.results, selectedAlgos);

    // Draw final paths
    drawAllPaths(data.results, selectedAlgos);
    drawEndpointMarkers();

    // Show comparison table
    showComparisonTable(data.results, selectedAlgos);

    // Update legend
    updateLegend(selectedAlgos);

    const fastest = findFastest(data.results, selectedAlgos);
    setStatus(`Done! ${selectedAlgos.length} algorithm${selectedAlgos.length>1?'s':''} compared. Fastest: ${ALGO_CFG[fastest]?.label||'—'}`);
    hideAnimProgress();

  } catch(e) {
    setStatus('Error: ' + e.message);
  } finally {
    isRunning = false;
    btn.classList.remove('loading');
    updateComputeBtn();
  }
};

// ── Step-by-step animation ─────────────────────────────────────
async function animateAll(results, algos) {
  const maxSteps = Math.max(...algos.map(a =>
    (results[a]?.explored_edge_coords || []).length
  ));

  // Create a layer group per algo for exploration edges + dots
  algos.forEach(algo => {
    animDots[algo] = L.layerGroup().addTo(map);
  });

  // Run all animations simultaneously
  const promises = algos.map(algo =>
    animateAlgo(algo, results[algo]?.explored_edge_coords || [], maxSteps)
  );
  await Promise.all(promises);
}

function animateAlgo(algo, edgeCoords, maxSteps) {
  return new Promise(resolve => {
    if (!edgeCoords.length) { resolve(); return; }

    const cfg   = ALGO_CFG[algo];
    const layer = animDots[algo];
    const card  = document.getElementById(`rc-${algo}`);
    if (card) card.classList.add('animating');

    let i = 0;
    const interval = setInterval(() => {
      if (i >= edgeCoords.length) {
        clearInterval(interval);
        if (card) card.classList.remove('animating');
        resolve();
        return;
      }

      const e = edgeCoords[i];

      // ── Draw the exploration edge (thin, semi-transparent dashed line) ──
      L.polyline(
        [[e.from_lat, e.from_lon], [e.to_lat, e.to_lon]],
        {
          color:     cfg.color,
          weight:    2,
          opacity:   0.45,
          dashArray: '5, 4',
          lineCap:   'round',
        }
      ).addTo(layer);

      // ── Draw a small glowing dot at the destination node ──
      L.circleMarker([e.to_lat, e.to_lon], {
        radius:      3.5,
        color:       cfg.color,
        fillColor:   cfg.color,
        fillOpacity: 0.85,
        opacity:     0.9,
        weight:      0,
      }).addTo(layer);

      // Update progress bar
      const pct = ((i + 1) / maxSteps) * 100;
      document.getElementById('anim-bar').style.width = Math.min(pct, 100) + '%';

      i++;
    }, animSpeed);
  });
}


// ── Draw Final Paths ───────────────────────────────────────────
function drawAllPaths(results, algos) {
  // Draw in reverse so Dijkstra is on top
  [...algos].reverse().forEach(algo => {
    const r = results[algo];
    if (!r || !r.coordinates || r.coordinates.length < 2) return;
    const cfg = ALGO_CFG[algo];
    const latlngs = r.coordinates.map(c => [c.lat, c.lon]);

    // Glow halo
    L.polyline(latlngs, { color:cfg.color, weight:cfg.weight+8, opacity:.12, lineCap:'round', lineJoin:'round' })
      .addTo(routeLayer);
    // Main line
    L.polyline(latlngs, { color:cfg.color, weight:cfg.weight, opacity:.92, lineCap:'round', lineJoin:'round' })
      .bindTooltip(`<strong style="color:${cfg.color}">${cfg.label}</strong><br>${r.distance_km} km · ${r.time_ms} ms`, {sticky:true})
      .addTo(routeLayer);
  });
}

function drawEndpointMarkers() {
  const src = allNodes.find(n => n.node_id === srcId);
  const dst = allNodes.find(n => n.node_id === dstId);

  if (src) L.marker([src.lat, src.lon], { icon: makeEndpointIcon('S','#00ff88') })
    .bindTooltip(`Source — Node #${src.node_num}`, {direction:'top'})
    .addTo(routeLayer);
  if (dst) L.marker([dst.lat, dst.lon], { icon: makeEndpointIcon('D','#ff00e5') })
    .bindTooltip(`Destination — Node #${dst.node_num}`, {direction:'top'})
    .addTo(routeLayer);
}

function makeEndpointIcon(letter, color) {
  return L.divIcon({
    className:'',
    html:`<div style="width:22px;height:22px;border-radius:50%;
      background:${color}22;border:2.5px solid ${color};
      box-shadow:0 0 14px ${color},0 0 30px ${color}44;
      display:flex;align-items:center;justify-content:center;
      font-size:10px;font-weight:800;color:${color};">${letter}</div>`,
    iconSize:[22,22], iconAnchor:[11,11],
  });
}

// ── Result Cards ───────────────────────────────────────────────
function showResultCards(algos, results) {
  const section = document.getElementById('results-section');
  const grid    = document.getElementById('results-grid');
  grid.innerHTML = '';
  section.style.display = 'block';

  algos.forEach(algo => {
    const cfg = ALGO_CFG[algo];
    const r   = results[algo];
    const card = document.createElement('div');
    card.className = `result-card ${cfg.cardClass} animating`;
    card.id = `rc-${algo}`;

    const explored = r?.explored_edge_coords?.length ?? 0;
    const timeVal  = r?.distance_km === -1 ? 'No path' : `${r?.time_ms} ms`;
    const distVal  = r?.distance_km === -1 ? '—' : `${r?.distance_km} km`;
    const fwNote   = algo==='floyd_warshall' && r?.precompute_ms
      ? `<br><span style="font-size:9px;color:#475569">Pre: ${r.precompute_ms}ms</span>` : '';

    card.innerHTML = `
      <div class="rc-dot"></div>
      <div class="rc-info">
        <div class="rc-name">${cfg.label}</div>
        <div class="rc-detail">Explored: ${explored} nodes${fwNote}</div>
      </div>
      <div class="rc-metrics">
        <div class="rc-time">${timeVal}</div>
        <div class="rc-dist">${distVal}</div>
      </div>`;
    grid.appendChild(card);
  });
}

// ── Comparison Table ───────────────────────────────────────────
function showComparisonTable(results, algos) {
  document.getElementById('table-section').style.display = 'block';
  const tbody = document.getElementById('comparison-tbody');
  tbody.innerHTML = '';

  // Find fastest
  let minTime = Infinity, fastest = null;
  algos.forEach(a => {
    const r = results[a];
    if (r && r.distance_km !== -1 && r.time_ms < minTime) { minTime = r.time_ms; fastest = a; }
  });

  algos.forEach(algo => {
    const cfg = ALGO_CFG[algo];
    const r   = results[algo];
    const explored = r?.explored_edge_coords?.length ?? '—';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <span style="display:inline-flex;align-items:center;gap:5px">
          <span style="width:7px;height:7px;border-radius:50%;background:${cfg.color};box-shadow:0 0 5px ${cfg.color};display:inline-block"></span>
          <span style="font-size:11px;font-weight:600;color:${cfg.color}">${cfg.label}</span>
          ${algo===fastest ? '<span class="fastest-badge">Fastest</span>' : ''}
        </span>
      </td>
      <td class="td-mono">${r?.distance_km===-1?'—':r?.time_ms+' ms'}</td>
      <td class="td-mono">${explored}</td>
      <td class="td-mono">${r?.distance_km===-1?'—':r?.distance_km+' km'}</td>`;
    tbody.appendChild(tr);
  });
}

// ── Legend ─────────────────────────────────────────────────────
function updateLegend(algos) {
  document.getElementById('map-legend').classList.remove('hidden');
  Object.keys(ALGO_CFG).forEach(a => {
    const el = document.getElementById(`legend-${a}`);
    if (el) el.style.display = algos.includes(a) ? 'flex' : 'none';
  });
}

// ── Helpers ────────────────────────────────────────────────────
function hideResults() {
  document.getElementById('results-section').style.display = 'none';
  document.getElementById('table-section').style.display = 'none';
  document.getElementById('results-grid').innerHTML = '';
  document.getElementById('comparison-tbody').innerHTML = '';
  document.getElementById('map-legend').classList.add('hidden');
}

function showAnimProgress()  {
  const el = document.getElementById('anim-progress');
  el.style.display = 'block';
  document.getElementById('anim-bar').style.width = '0%';
}
function hideAnimProgress()  {
  document.getElementById('anim-bar').style.width = '100%';
  setTimeout(() => { document.getElementById('anim-progress').style.display = 'none'; }, 400);
}

function findFastest(results, algos) {
  let min = Infinity, best = null;
  algos.forEach(a => {
    const r = results[a];
    if (r && r.distance_km !== -1 && r.time_ms < min) { min = r.time_ms; best = a; }
  });
  return best;
}

function setStatus(msg) {
  const el = document.getElementById('status-msg');
  if (el) el.textContent = msg;
}
