/* analytics.js - model comparison, feature importance, actual-vs-predicted. All data from the API. */
document.addEventListener("DOMContentLoaded", async () => {
  const [perf, imp, hist] = await Promise.allSettled([Api.modelPerformance(), Api.featureImportance(), Api.rainfallHistory()]);

  if (perf.status === "rejected") { showError($("#an-error"), perf.reason); $("#model-table").innerHTML = emptyState("No model results. Train the models first (python -m models.train)."); return; }
  const p = perf.value;
  $("#model-table").innerHTML = `<table><thead><tr><th>Model</th><th>Val RMSE</th><th>Test MAE</th><th>Test RMSE</th><th>Test R²</th><th></th></tr></thead><tbody>
    ${p.models.map((m) => `<tr class="${m.is_best ? "best" : ""}"><td>${escapeHtml(m.name)}</td><td>${fmt(m.validation.rmse, 3)}</td><td>${fmt(m.test.mae, 3)}</td><td>${fmt(m.test.rmse, 3)}</td><td>${fmt(m.test.r2, 3)}</td><td>${m.is_best ? '<span class="badge normal">BEST</span>' : ""}</td></tr>`).join("")}</tbody></table>`;
  $("#model-note").textContent = `Best model chosen by ${p.selection_metric}. ${p.ensemble_is_best ? "The ensemble won." : "The ensemble did not win in this experiment — the best model is reported honestly."} Split: ${p.split.type} (train ${p.split.train} / val ${p.split.validation} / test ${p.split.test}).`;

  const names = p.models.map((m) => m.name.split(" (")[0]);
  drawChart("chart-models", { type: "bar", data: { labels: names, datasets: [
    { label: "MAE", data: p.models.map((m) => m.test.mae), backgroundColor: PALETTE.cyan },
    { label: "RMSE", data: p.models.map((m) => m.test.rmse), backgroundColor: PALETTE.navy }] } });
  drawChart("chart-r2", { type: "bar", data: { labels: names, datasets: [{ label: "R²", data: p.models.map((m) => m.test.r2), backgroundColor: p.models.map((m) => m.is_best ? PALETTE.green : PALETTE.grey) }] },
    options: { plugins: { legend: { display: false } } } });

  // Feature importance
  if (imp.status === "fulfilled") {
    const top = imp.value.features.slice(0, 12);
    drawChart("chart-importance", { type: "bar", data: { labels: top.map((f) => f.feature), datasets: [{ label: "Importance", data: top.map((f) => f.importance), backgroundColor: PALETTE.cyan }] },
      options: { indexAxis: "y", plugins: { legend: { display: false } } } });
    $("#imp-method").textContent = imp.value.method;
  } else $("#chart-importance").parentElement.outerHTML = emptyState("Feature importance unavailable.");

  // Actual vs predicted
  if (hist.status === "fulfilled" && hist.value.actual_vs_predicted && hist.value.actual_vs_predicted.points.length) {
    const pts = hist.value.actual_vs_predicted.points;
    drawChart("chart-avp", { type: "line", data: { labels: pts.map((x) => x.date), datasets: [
      { label: "Actual", data: pts.map((x) => x.actual), borderColor: PALETTE.navy, pointRadius: 0, tension: .2 },
      { label: "Predicted", data: pts.map((x) => x.predicted), borderColor: PALETTE.cyan, pointRadius: 0, tension: .2 }] },
      options: { scales: { x: { ticks: { maxTicksLimit: 8 } } } } });
    $("#avp-note").textContent = hist.value.actual_vs_predicted.split;
  } else $("#chart-avp").parentElement.outerHTML = emptyState("No actual-vs-predicted data available.");

  // Classifier
  const r = p.risk_model, rb = $("#risk-metrics");
  rb.innerHTML = r && r.trained ? `<dl class="kv"><dt>Heavy-rain threshold</dt><dd>≥ ${r.threshold_mm} mm</dd><dt>Precision</dt><dd>${fmt(r.precision, 3)}</dd><dt>Recall</dt><dd>${fmt(r.recall, 3)}</dd>
      <dt>F1-score</dt><dd>${fmt(r.f1, 3)}</dd><dt>ROC-AUC</dt><dd>${fmt(r.roc_auc, 3)}</dd><dt>Heavy events (train/val/test)</dt><dd>${r.heavy_event_counts.train}/${r.heavy_event_counts.val}/${r.heavy_event_counts.test}</dd></dl>
      <p class="muted">Confusion matrix [[TN, FP],[FN, TP]]: ${JSON.stringify(r.confusion_matrix)}</p>`
    : emptyState(r ? r.reason : "Classifier not available.");

  // Location experiments
  const g = p.geo_experiment, u = p.unseen_location_eval;
  $("#geo-box").innerHTML = (g ? `<h3>Are latitude/longitude useful?</h3><dl class="kv"><dt>Val RMSE without</dt><dd>${fmt(g.val_rmse_without_lat_lon, 3)}</dd><dt>Val RMSE with</dt><dd>${fmt(g.val_rmse_with_lat_lon, 3)}</dd><dt>Used in final model</dt><dd>${g.lat_lon_used ? "Yes" : "No"}</dd></dl>` : '<p class="muted">No latitude/longitude columns in the dataset.</p>')
    + (u ? `<h3 style="margin-top:.8rem">Unseen-location test</h3><dl class="kv"><dt>Method</dt><dd>${escapeHtml(u.method)}</dd><dt>Mean RMSE</dt><dd>${fmt(u.mean_rmse, 3)}</dd><dt>Mean R²</dt><dd>${fmt(u.mean_r2, 3)}</dd></dl>` : '<p class="muted">Too few locations for an unseen-location test.</p>');
});
