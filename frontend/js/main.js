/* main.js - shared shell (sidebar, topbar, API status) and helpers used by every page. */
const NAV_ITEMS = [
  ["dashboard.html", "🏠", "Dashboard"], ["prediction.html", "🌧️", "Rainfall Prediction"],
  ["locations.html", "📍", "Location Explorer"], ["analytics.html", "📊", "Model Analytics"],
  ["alerts.html", "⚠️", "Early Warning"], ["about.html", "ℹ️", "About Project"],
];

/* ---------- small helpers ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n, d = 2) => (n === null || n === undefined || Number.isNaN(n)) ? "—" : Number(n).toFixed(d);
const emptyState = (msg) => `<div class="empty">${escapeHtml(msg)}</div>`;
const loaderHtml = () => '<div class="loader" aria-label="Loading"></div>';
const riskBadge = (level) => `<span class="badge ${level || "none"}">${level ? level.toUpperCase() : "NO DATA"}</span>`;

function showToast(message, type = "info") {
  let box = $("#toasts"); if (!box) { box = document.createElement("div"); box.id = "toasts"; document.body.appendChild(box); }
  const t = document.createElement("div"); t.className = "toast " + type; t.textContent = message; box.appendChild(t);
  setTimeout(() => t.remove(), 4500);
}
function showError(container, error) {
  container.innerHTML = `<div class="banner error">${escapeHtml(error.message || error)}</div>`;
}

/* Persisted state shared between pages */
const State = {
  get selectedLocation() { return localStorage.getItem("selectedLocation"); },
  set selectedLocation(v) { localStorage.setItem("selectedLocation", v); },
  get lastPrediction() { try { return JSON.parse(localStorage.getItem("lastPrediction")); } catch (_) { return null; } },
  set lastPrediction(v) { localStorage.setItem("lastPrediction", JSON.stringify(v)); },
};

/* Chart.js: keep one chart per canvas so re-renders do not stack */
const charts = {};
function drawChart(canvasId, config) {
  if (charts[canvasId]) charts[canvasId].destroy();
  const ctx = document.getElementById(canvasId);
  config.options = { responsive: true, maintainAspectRatio: false, ...(config.options || {}) };
  charts[canvasId] = new Chart(ctx, config);
}
const PALETTE = { navy: "#1b3a73", cyan: "#22b8cf", green: "#2f9e6b", orange: "#d9822b", red: "#d64545", grey: "#9fb0d0" };

/* ---------- shell ---------- */
function buildShell() {
  const page = document.body.dataset.page, title = document.body.dataset.title || "";
  const content = $("#page-content"); if (!content) return;
  const app = document.createElement("div"); app.className = "app";
  app.innerHTML = `
    <aside class="sidebar" id="sidebar">
      <a class="brand" href="index.html"><i>☔</i><span>Rainfall<br>Prediction ML</span></a>
      <nav class="nav">${NAV_ITEMS.map(([href, icon, label]) =>
        `<a href="${href}" class="${href.startsWith(page) ? "active" : ""}"><span>${icon}</span>${label}</a>`).join("")}</nav>
      <div class="sidebar-foot">API: <span id="api-base-label"></span></div>
    </aside>
    <div class="main">
      <header class="topbar">
        <button class="menu-btn" id="menu-btn" aria-label="Menu">☰</button>
        <div class="title">${escapeHtml(title)}</div>
        <span class="status" id="api-status">Checking…</span>
      </header>
    </div>`;
  content.parentNode.insertBefore(app, content);
  $(".main", app).appendChild(content);
  $("#api-base-label").textContent = API_BASE;
  $("#menu-btn").onclick = () => $("#sidebar").classList.toggle("open");
  pollHealth(); setInterval(pollHealth, 20000);
}

async function pollHealth() {
  const el = $("#api-status"); if (!el) return;
  try {
    const h = await Api.health();
    el.className = "status " + (h.models_loaded ? "online" : "degraded");
    el.textContent = h.models_loaded ? "API connected" : "API up · models not trained";
    if (h.demo_data && !$("#demo-banner")) $(".topbar").insertAdjacentHTML("afterend", '<div class="banner warn" id="demo-banner" style="margin:0;border-radius:0">Demo mode: models are trained on a SYNTHETIC sample dataset, not real weather data.</div>');
  } catch (_) { el.className = "status offline"; el.textContent = "API offline"; }
}

document.addEventListener("DOMContentLoaded", buildShell);
