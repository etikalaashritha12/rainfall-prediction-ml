from flask import Blueprint, jsonify
from prediction.predictor import store

bp = Blueprint("locations", __name__)


@bp.get("/api/locations")
def locations():
    if not store.ready:
        return jsonify({"error": "models_unavailable", "message": store.error}), 503
    m = store.meta
    return jsonify({"count": len(m["locations"]), "locations": m["locations"], "features": m["features"],
                    "uses_date": m["uses_date"], "target": m["target"]})
