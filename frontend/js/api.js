/* api.js - the ONLY place that talks to the Flask backend. */
const API_BASE = localStorage.getItem("apiBase") || "http://127.0.0.1:5000";

class ApiError extends Error {
  constructor(message, status, body) { super(message); this.status = status; this.body = body; }
}

async function apiRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(API_BASE + path, { headers: { "Content-Type": "application/json" }, ...options });
  } catch (networkError) {
    throw new ApiError("Cannot reach the backend. Is Flask running on " + API_BASE + "?", 0, null);
  }
  let body = null;
  try { body = await response.json(); } catch (_) { /* non-JSON response */ }
  if (!response.ok) {
    const msg = (body && (body.message || body.error)) || "Request failed (" + response.status + ")";
    throw new ApiError(msg, response.status, body);
  }
  return body;
}

const Api = {
  health: () => apiRequest("/api/health"),
  locations: () => apiRequest("/api/locations"),
  predict: (payload) => apiRequest("/api/predict", { method: "POST", body: JSON.stringify(payload) }),
  modelPerformance: () => apiRequest("/api/model-performance"),
  featureImportance: () => apiRequest("/api/feature-importance"),
  rainfallHistory: (location) => apiRequest("/api/rainfall-history" + (location ? "?location=" + encodeURIComponent(location) : "")),
  alerts: () => apiRequest("/api/alerts"),
};
