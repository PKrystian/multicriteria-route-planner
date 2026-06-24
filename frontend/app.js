"use strict";

const API = location.protocol.startsWith("http") ? "" : "http://127.0.0.1:8000";

const COLORS = ["#e6194B", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#469990"];
const PUT_CAMPUS = [52.4022, 16.9499];

const map = L.map("map").setView(PUT_CAMPUS, 14);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const state = {
  source: null,
  target: null,
  sourceMarker: null,
  targetMarker: null,
  routeLayers: [],
  multiAlgorithms: new Set(),
  criteria: [],
};

const el = (id) => document.getElementById(id);

async function loadConfig() {
  const [algos, crit] = await Promise.all([
    fetch(`${API}/algorithms`).then((r) => r.json()),
    fetch(`${API}/criteria`).then((r) => r.json()),
  ]);

  const select = el("algorithm");
  for (const name of algos.single_objective) {
    select.add(new Option(`${name} (single)`, name));
  }
  for (const name of algos.multi_objective) {
    select.add(new Option(`${name} (Pareto)`, name));
    state.multiAlgorithms.add(name);
  }

  state.criteria = crit.criteria;
  const weights = el("weights");
  for (const name of crit.criteria) {
    const value = crit.default_weights[name] ?? 0;
    const row = document.createElement("div");
    row.className = "weight-row";
    row.innerHTML = `
      <div class="weight-label"><span>${name}</span><span id="wv-${name}">${value.toFixed(2)}</span></div>
      <input type="range" id="w-${name}" min="0" max="1" step="0.05" value="${value}">`;
    weights.appendChild(row);
    el(`w-${name}`).addEventListener("input", (e) => {
      el(`wv-${name}`).textContent = Number(e.target.value).toFixed(2);
    });
  }

  el("strength").value = crit.default_strength;
  el("strength-val").textContent = crit.default_strength;
  el("axes").value = crit.pareto_axes.join(", ");

  select.addEventListener("change", togglePanels);
  togglePanels();
}

function isMulti() {
  return state.multiAlgorithms.has(el("algorithm").value);
}

function togglePanels() {
  const multi = isMulti();
  el("weights-panel").hidden = multi;
  el("axes-panel").hidden = !multi;
}

el("strength").addEventListener("input", (e) => {
  el("strength-val").textContent = e.target.value;
});

map.on("click", (e) => {
  if (!state.source || state.target) {
    resetPoints();
    state.source = e.latlng;
    state.sourceMarker = L.marker(e.latlng, { title: "Start" }).addTo(map).bindPopup("Start").openPopup();
    el("status").textContent = "Now click the destination.";
  } else {
    state.target = e.latlng;
    state.targetMarker = L.marker(e.latlng, { title: "Destination" }).addTo(map).bindPopup("Destination");
    el("status").textContent = "Ready. Adjust preferences and click Find route.";
    el("find").disabled = false;
  }
});

function resetPoints() {
  for (const m of [state.sourceMarker, state.targetMarker]) if (m) map.removeLayer(m);
  clearRoutes();
  state.source = state.target = state.sourceMarker = state.targetMarker = null;
  el("find").disabled = true;
  el("metrics").innerHTML = "";
  el("status").textContent = "Click the map to set the start, then the destination.";
}

function clearRoutes() {
  for (const layer of state.routeLayers) map.removeLayer(layer);
  state.routeLayers = [];
}

el("reset").addEventListener("click", resetPoints);
el("find").addEventListener("click", findRoute);

async function findRoute() {
  if (!state.source || !state.target) return;
  el("find").disabled = true;
  el("status").textContent = "Computing...";

  const body = {
    source: { lat: state.source.lat, lon: state.source.lng },
    target: { lat: state.target.lat, lon: state.target.lng },
    algorithm: el("algorithm").value,
  };
  if (isMulti()) {
    body.pareto_axes = el("axes").value.split(",").map((s) => s.trim()).filter(Boolean);
  } else {
    body.weights = {};
    for (const name of state.criteria) body.weights[name] = Number(el(`w-${name}`).value);
    body.strength = Number(el("strength").value);
  }

  try {
    const resp = await fetch(`${API}/route`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) {
      el("status").textContent = `Error: ${data.detail || resp.status}`;
      el("find").disabled = false;
      return;
    }
    renderRoutes(data);
  } catch (err) {
    el("status").textContent = `Request failed: ${err}`;
  }
  el("find").disabled = false;
}

function renderRoutes(data) {
  clearRoutes();
  const features = data.geojson.features;
  const bounds = [];

  features.forEach((feature, i) => {
    const color = COLORS[i % COLORS.length];
    const layer = L.geoJSON(feature, { style: { color, weight: 5, opacity: 0.8 } }).addTo(map);
    state.routeLayers.push(layer);
    bounds.push(...feature.geometry.coordinates.map((c) => [c[1], c[0]]));
  });
  if (bounds.length) map.fitBounds(bounds, { padding: [40, 40] });

  el("status").textContent = `${data.algorithm}: ${data.routes.length} route(s).`;
  el("metrics").innerHTML = data.multi_objective ? multiTable(data) : singleTable(data);
}

function singleTable(data) {
  const r = data.routes[0];
  const rows = [
    ["length (m)", r.length_m.toFixed(0)],
    ["total cost", r.total_cost.toFixed(1)],
    ["visited nodes", r.visited_nodes],
    ["runtime (ms)", r.runtime_ms.toFixed(2)],
  ];
  for (const [k, v] of Object.entries(r.per_criterion)) {
    rows.push([`penalty: ${k}`, v.toFixed(1)]);
  }
  const body = rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("");
  return `<table><tbody>${body}</tbody></table>`;
}

function multiTable(data) {
  const axes = Object.keys(data.routes[0].cost_vector);
  const head = `<tr><th>#</th>${axes.map((a) => `<th>${a}</th>`).join("")}<th>nodes</th></tr>`;
  const rows = data.routes
    .map((r, i) => {
      const color = COLORS[i % COLORS.length];
      const cells = axes.map((a) => `<td>${r.cost_vector[a].toFixed(1)}</td>`).join("");
      return `<tr><td><span class="swatch" style="background:${color}"></span>${i}</td>${cells}<td>${r.n_nodes}</td></tr>`;
    })
    .join("");
  const meta = `<p class="hint">expanded ${data.routes[0].visited_nodes} labels in ${data.routes[0].runtime_ms.toFixed(1)} ms</p>`;
  return `<table><thead>${head}</thead><tbody>${rows}</tbody></table>${meta}`;
}

loadConfig().catch((err) => {
  el("status").textContent = `Could not load API config: ${err}`;
});
