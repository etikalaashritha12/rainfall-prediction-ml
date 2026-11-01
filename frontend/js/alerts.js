/* alerts.js - latest warning status (from the last prediction) + stored alert history from the API. */
document.addEventListener("DOMContentLoaded", async () => {
  const last = State.lastPrediction;
  if (last) {
    $("#status-card").className = "card risk-panel " + last.risk.level;
    $("#status-body").innerHTML = `<div class="result-hero"><div class="big">${fmt(last.predicted_rainfall_mm)} mm</div><div>${riskBadge(last.risk.level)}<div>${escapeHtml(last.category)} · ${escapeHtml(last.location)}</div></div></div>
      <dl class="kv"><dt>Heavy-rainfall warning</dt><dd>${last.risk.warning ? "ACTIVE" : "Not active"}</dd><dt>Heavy-rain probability</dt><dd>${last.risk.heavy_rain_probability === null ? "classifier not trained" : fmt(last.risk.heavy_rain_probability * 100, 1) + "%"}</dd></dl><p>${escapeHtml(last.risk.message)}</p>`;
    $("#precautions").innerHTML = `<ul class="plain-list">${last.risk.precautions.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>`;
    $("#flood-state").textContent = last.flood_risk.available ? "available" : "not available for this system";
  } else {
    $("#status-body").innerHTML = emptyState("No prediction yet. Make one on the Rainfall Prediction page.");
    $("#precautions").innerHTML = emptyState("Precautions appear after a prediction.");
    $("#flood-state").textContent = "not available for this system";
  }

  const [perf, alerts] = await Promise.allSettled([Api.modelPerformance(), Api.alerts()]);
  if (perf.status === "fulfilled") {
    const t = perf.value.thresholds;
    $("#legend").innerHTML = `<div class="legend"><span class="badge normal">NORMAL</span> below ${t.moderate_mm} mm</div>
      <div class="legend" style="margin-top:.5rem"><span class="badge moderate">MODERATE</span> ${t.moderate_mm} – ${t.heavy_mm} mm, or elevated heavy-rain probability</div>
      <div class="legend" style="margin-top:.5rem"><span class="badge high">HIGH</span> ≥ ${t.heavy_mm} mm, or high heavy-rain probability (warning issued)</div>
      <p class="muted" style="margin-top:.6rem">Thresholds are configured in the backend (config.py) for the dataset's rainfall unit.</p>`;
  } else $("#legend").innerHTML = emptyState("Thresholds unavailable: " + perf.reason.message);

  if (alerts.status === "fulfilled") {
    const rows = alerts.value.alerts;
    $("#history").innerHTML = rows.length ? `<table><thead><tr><th>Time</th><th>Location</th><th>Predicted (mm)</th><th>Category</th><th>Risk</th></tr></thead><tbody>
      ${rows.map((a) => `<tr><td>${escapeHtml(a.created_at.replace("T", " "))}</td><td>${escapeHtml(a.location)}</td><td>${fmt(a.predicted_mm)}</td><td>${escapeHtml(a.category)}</td><td>${riskBadge(a.risk_level)}</td></tr>`).join("")}</tbody></table>`
      : emptyState("No alerts recorded yet. Moderate/high-risk predictions are stored here automatically.");
  } else showError($("#history"), alerts.reason);
});
