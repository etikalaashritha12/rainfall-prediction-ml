/* dashboard.js - overview KPIs + charts, all from real API data. */
document.addEventListener("DOMContentLoaded", async () => {
  // Show whatever the user last predicted in this browser
  const last = State.lastPrediction;
  if (State.selectedLocation) $("#kpi-selected").textContent = State.selectedLocation;
  if (last) {
    $("#kpi-latest").textContent = fmt(last.predicted_rainfall_mm) + " mm";
    $("#kpi-latest-sub").textContent = last.category + " · " + last.location;
    $("#kpi-risk").innerHTML = riskBadge(last.risk.level);
    $("#kpi-risk-sub").textContent = last.risk.message;
  }

  const [loc, perf, hist] = await Promise.allSettled([Api.locations(), Api.modelPerformance(), Api.rainfallHistory(State.selectedLocation).catch(() => Api.rainfallHistory())]);

  if (loc.status === "fulfilled") $("#kpi-locations").textContent = loc.value.count;
  else { $("#kpi-locations").textContent = "—"; showError($("#dash-error"), loc.reason); }

  // Model performance summary - ONLY real backend metrics
  const box = $("#perf-summary");
  if (perf.status === "fulfilled") {
    const best = perf.value.models.find((m) => m.is_best);
    box.innerHTML = `<dl class="kv"><dt>Best model</dt><dd>${escapeHtml(perf.value.best_model)}</dd>
      <dt>Test MAE</dt><dd>${fmt(best.test.mae)}</dd><dt>Test RMSE</dt><dd>${fmt(best.test.rmse)}</dd><dt>Test R²</dt><dd>${fmt(best.test.r2, 3)}</dd>
      <dt>Ensemble best?</dt><dd>${perf.value.ensemble_is_best ? "Yes" : "No (selected by validation RMSE)"}</dd></dl>`;
  } else box.innerHTML = emptyState("Model metrics unavailable: " + perf.reason.message);

  if (hist.status === "fulfilled") {
    const h = hist.value, rd = h.risk_distribution;
    drawChart("chart-risk", { type: "doughnut", data: { labels: ["Normal", "Moderate", "High"],
      datasets: [{ data: [rd.normal, rd.moderate, rd.high], backgroundColor: [PALETTE.green, PALETTE.orange, PALETTE.red] }] } });
    drawChart("chart-locations", { type: "bar", data: { labels: h.by_location.map((l) => l.location),
      datasets: [{ label: "Mean rainfall", data: h.by_location.map((l) => l.mean_rainfall), backgroundColor: PALETTE.cyan }] },
      options: { plugins: { legend: { display: false } } } });
    if (h.series && h.series.length) {
      $("#trend-label").textContent = h.location ? "· " + h.location : "· all locations";
      drawChart("chart-trend", { type: "line", data: { labels: h.series.map((p) => p.period),
        datasets: [{ label: "Mean monthly rainfall", data: h.series.map((p) => p.mean_rainfall), borderColor: PALETTE.navy, tension: .3, pointRadius: 0 }] } });
    } else { $("#chart-trend").parentElement.classList.add("hidden"); $("#trend-empty").innerHTML = emptyState("The dataset has no date column, so no trend is available."); }
  } else {
    ["chart-risk", "chart-locations", "chart-trend"].forEach((id) => { const c = document.getElementById(id).parentElement; c.outerHTML = emptyState("No data: " + hist.reason.message); });
  }
});
