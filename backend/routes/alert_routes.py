"""Alert history stored in SQLite (only warnings/moderate risks are stored)."""
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request
import config

bp = Blueprint("alerts", __name__)


def _conn():
    c = sqlite3.connect(config.DB_PATH); c.row_factory = sqlite3.Row; return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT,
                     location TEXT, predicted_mm REAL, category TEXT, risk_level TEXT, probability REAL, message TEXT)""")


def log_alert(result):
    risk = result["risk"]
    if risk["level"] == "normal":
        return
    with _conn() as c:
        c.execute("INSERT INTO alerts (created_at, location, predicted_mm, category, risk_level, probability, message) "
                  "VALUES (?,?,?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"), result["location"], result["predicted_rainfall_mm"],
                   result["category"], risk["level"], risk["heavy_rain_probability"], risk["message"]))


@bp.get("/api/alerts")
def get_alerts():
    limit = min(int(request.args.get("limit", 50)), 500)
    with _conn() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))]
    return jsonify({"alerts": rows, "count": len(rows),
                    "note": "Alerts are generated from predictions made through this system."})
