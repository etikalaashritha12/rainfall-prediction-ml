/* locations.js - table + map of supported locations */
let locs = [], lmap, lmarkers = {};
document.addEventListener("DOMContentLoaded", async () => {
  try { locs = (await Api.locations()).locations; } catch (err) { showError($("#loc-error"), err); $("#loc-body").innerHTML = `<tr><td colspan="4">${emptyState("No data")}</td></tr>`; return; }
  lmap = L.map("map").setView([22.5, 79], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors" }).addTo(lmap);
  const pts = locs.filter((l) => l.latitude != null);
  pts.forEach((l) => { lmarkers[l.name] = L.marker([l.latitude, l.longitude]).addTo(lmap).bindPopup(`<strong>${escapeHtml(l.name)}</strong><br>${l.records} records`); });
  if (pts.length) lmap.fitBounds(pts.map((l) => [l.latitude, l.longitude]), { padding: [30, 30], maxZoom: 8 });
  render(""); $("#loc-q").addEventListener("input", (e) => render(e.target.value));
});
function render(q) {
  q = q.toLowerCase();
  const rows = locs.filter((l) => (l.name + (l.state || "")).toLowerCase().includes(q));
  $("#loc-body").innerHTML = rows.length ? rows.map((l) => `<tr><td><a href="#" data-n="${escapeHtml(l.name)}">${escapeHtml(l.name)}</a></td><td>${escapeHtml(l.state || "—")}</td><td>${l.records}</td>
    <td><button class="btn ghost" data-p="${escapeHtml(l.name)}">Predict</button></td></tr>`).join("") : `<tr><td colspan="4">${emptyState("No matches")}</td></tr>`;
  document.querySelectorAll("[data-n]").forEach((a) => a.onclick = (e) => { e.preventDefault(); const m = lmarkers[a.dataset.n]; if (m) { lmap.setView(m.getLatLng(), 8); m.openPopup(); } });
  document.querySelectorAll("[data-p]").forEach((b) => b.onclick = () => { State.selectedLocation = b.dataset.p; location.href = "prediction.html"; });
}
