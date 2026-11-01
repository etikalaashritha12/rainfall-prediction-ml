/* prediction.js - location picker + Leaflet map + prediction form. */
let locations = [], features = [], usesDate = false, selected = null, map, markers = {};

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await Api.locations();
    locations = data.locations; features = data.features; usesDate = data.uses_date;
  } catch (err) {
    showError($("#pred-error"), err);
    $("#loc-list").innerHTML = emptyState("Locations unavailable."); $("#form-fields").innerHTML = emptyState("Form unavailable until the backend is running and trained.");
    return;
  }
  renderList(""); buildForm(); initMap();
  $("#loc-search").addEventListener("input", (e) => renderList(e.target.value));
  $("#predict-form").addEventListener("submit", onSubmit);
  $("#fill-avg").addEventListener("click", fillTypical);
  if (State.selectedLocation && locations.some((l) => l.name === State.selectedLocation)) selectLocation(State.selectedLocation, false);
});

/* ---- location list + search ---- */
function renderList(query) {
  const q = query.trim().toLowerCase();
  const items = locations.filter((l) => (l.name + " " + (l.state || "")).toLowerCase().includes(q));
  $("#loc-list").innerHTML = items.length ? items.map((l) =>
    `<button type="button" data-name="${escapeHtml(l.name)}" class="${selected === l.name ? "sel" : ""}">${escapeHtml(l.name)}${l.state ? ` <span class="muted">· ${escapeHtml(l.state)}</span>` : ""}</button>`).join("")
    : emptyState("No supported location matches your search.");
  $("#loc-list").querySelectorAll("button").forEach((b) => b.onclick = () => selectLocation(b.dataset.name, true));
}

function selectLocation(name, pan) {
  selected = name; State.selectedLocation = name;
  const loc = locations.find((l) => l.name === name);
  $("#loc-selected-label").innerHTML = `Selected: <strong>${escapeHtml(name)}</strong>${loc.state ? " · " + escapeHtml(loc.state) : ""}`;
  renderList($("#loc-search").value);
  // Show the weather information that exists for this location in the training data
  const avg = Object.entries(loc.avg_weather || {});
  $("#loc-weather").innerHTML = avg.length ? `<h3 style="margin-top:.8rem">Typical weather (training-data averages)</h3>
    <dl class="kv">${avg.map(([k, v]) => `<dt>${escapeHtml(k)}</dt><dd>${fmt(v)}</dd>`).join("")}</dl>
    <p class="muted">${loc.records} historical records. These are averages, not a live forecast.</p>` : "";
  if (map && loc.latitude != null) {
    Object.values(markers).forEach((m) => m.setStyle({ fillColor: PALETTE.navy, radius: 7 }));
    markers[name].setStyle({ fillColor: PALETTE.cyan, radius: 11 });
    if (pan) map.setView([loc.latitude, loc.longitude], Math.max(map.getZoom(), 6));
  }
}

/* ---- map ---- */
function initMap() {
  map = L.map("map").setView([22.5, 79], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors", maxZoom: 18 }).addTo(map);
  const withCoords = locations.filter((l) => l.latitude != null);
  if (!withCoords.length) { $("#map").insertAdjacentHTML("afterend", '<div class="banner info">The dataset has no latitude/longitude columns, so the map cannot show markers.</div>'); return; }
  withCoords.forEach((l) => {
    markers[l.name] = L.circleMarker([l.latitude, l.longitude], { radius: 7, color: "#fff", weight: 2, fillColor: PALETTE.navy, fillOpacity: 1 })
      .addTo(map).bindTooltip(l.name).on("click", () => selectLocation(l.name, false));
  });
  map.fitBounds(withCoords.map((l) => [l.latitude, l.longitude]), { padding: [30, 30], maxZoom: 8 });
  setTimeout(() => map.invalidateSize(), 300);
}

/* ---- form (fields generated from the backend's feature list) ---- */
function buildForm() {
  const dateField = usesDate ? `<div class="field"><label for="f-date">Date</label><input type="date" id="f-date" value="${new Date().toISOString().slice(0, 10)}"><span class="err">Valid date required</span></div>` : "";
  $("#form-fields").innerHTML = dateField + features.map((f) => `<div class="field">
      <label for="f-${escapeHtml(f.name)}">${escapeHtml(f.name)}</label>
      <input type="number" step="any" id="f-${escapeHtml(f.name)}" name="${escapeHtml(f.name)}" placeholder="${fmt(f.min, 1)} – ${fmt(f.max, 1)}" data-min="${f.min}" data-max="${f.max}">
      <span class="err"></span></div>`).join("");
}
function fillTypical() {
  const loc = locations.find((l) => l.name === selected);
  if (!loc) return showToast("Select a location first.", "error");
  features.forEach((f) => { const v = (loc.avg_weather || {})[f.name]; if (v !== undefined) $("#f-" + f.name).value = fmt(v); });
}

/* ---- validation + submit ---- */
function validateForm() {
  let ok = true;
  if (!selected) { showToast("Please select a location.", "error"); ok = false; }
  const weather = {};
  features.forEach((f) => {
    const input = $("#f-" + f.name), field = input.closest(".field"), err = field.querySelector(".err");
    const value = input.value.trim(); field.classList.remove("invalid");
    if (value === "" || Number.isNaN(Number(value))) { err.textContent = "Enter a number"; field.classList.add("invalid"); ok = false; return; }
    const span = (f.max - f.min) || 1;
    if (Number(value) < f.min - 0.5 * span || Number(value) > f.max + 0.5 * span) { err.textContent = `Far outside training range (${fmt(f.min, 1)} – ${fmt(f.max, 1)})`; field.classList.add("invalid"); ok = false; return; }
    weather[f.name] = Number(value);
  });
  if (usesDate && !$("#f-date").value) { $("#f-date").closest(".field").classList.add("invalid"); ok = false; }
  return ok ? weather : null;
}

async function onSubmit(event) {
  event.preventDefault();
  const weather = validateForm(); if (!weather) return;
  const btn = $("#submit-btn"); btn.disabled = true; btn.textContent = "Predicting…";
  $("#result").innerHTML = loaderHtml();
  try {
    const payload = { location: selected, weather }; if (usesDate) payload.date = $("#f-date").value;
    const result = await Api.predict(payload);
    State.lastPrediction = result;
    renderResult(result);
  } catch (err) {
    let msg = err.message;
    if (err.body && err.body.details) msg = Object.entries(err.body.details).map(([k, v]) => `${k}: ${v}`).join(" | ");
    $("#result").innerHTML = `<div class="banner error">${escapeHtml(msg)}</div>`; showToast("Prediction failed", "error");
  } finally { btn.disabled = false; btn.textContent = "Predict rainfall"; }
}

/* ---- result ---- */
function renderResult(r) {
  const maxImp = Math.max(...r.explanation.top_features.map((f) => Math.abs(f.importance)), 1e-9);
  const prob = r.risk.heavy_rain_probability;
  $("#result").innerHTML = `
  <div class="card risk-panel ${r.risk.level}">
    <h2>Prediction result · ${escapeHtml(r.location)}</h2>
    <div class="result-hero"><div class="big">${fmt(r.predicted_rainfall_mm)} mm</div>
      <div><div><strong>${escapeHtml(r.category)}</strong> rainfall</div><div>${riskBadge(r.risk.level)}</div></div></div>
    <p>${escapeHtml(r.risk.message)}</p>
  </div>
  <div class="grid g2" style="margin-top:1.1rem">
    <div class="card"><h3>Inputs &amp; model</h3>
      <dl class="kv"><dt>Location</dt><dd>${escapeHtml(r.location)}</dd>
      ${r.input.date ? `<dt>Date</dt><dd>${escapeHtml(r.input.date)}${r.input.date_defaulted_to_today ? " (default)" : ""}</dd>` : ""}
      ${Object.entries(r.input.weather).map(([k, v]) => `<dt>${escapeHtml(k)}</dt><dd>${fmt(v)}</dd>`).join("")}
      <dt>Model used</dt><dd>${escapeHtml(r.model_used)}</dd>
      <dt>Heavy-rain probability</dt><dd>${prob === null ? "classifier not trained" : fmt(prob * 100, 1) + "%"}</dd></dl></div>
    <div class="card"><h3>Explanation</h3>
      <p class="muted">${escapeHtml(r.explanation.method)}. ${escapeHtml(r.explanation.note)}</p>
      ${r.explanation.top_features.map((f) => `<div class="bar-row"><span>${escapeHtml(f.feature)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(2, Math.abs(f.importance) / maxImp * 100)}%"></div></div></div>`).join("")}
      <div class="banner info" style="margin-top:.8rem">${escapeHtml(r.flood_risk.note)}</div></div>
  </div>
  <p style="margin-top:1rem"><a class="btn cyan" href="alerts.html">View early-warning details →</a></p>`;
  $("#result").scrollIntoView({ behavior: "smooth" });
}
