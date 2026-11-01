from flask import Blueprint, jsonify, request
from prediction.predictor import store

bp = Blueprint("analytics", __name__)


def _need_models():
    return (jsonify({"error": "models_unavailable", "message": store.error}), 503) if not store.ready else None


@bp.get("/api/model-performance")
def model_performance():
    if (r := _need_models()): return r
    m = store.meta
    return jsonify({"trained_at": m["trained_at"], "split": m["split"], "selection_metric": m["selection_metric"],
                    "best_model": m["best_model"], "ensemble_is_best": m["ensemble_is_best"],
                    "models": [{"name": n, **v, "is_best": n == m["best_model"]} for n, v in m["models"].items()],
                    "risk_model": m["risk_model"], "thresholds": m["thresholds"],
                    "geo_experiment": m["geo_experiment"], "unseen_location_eval": m["unseen_location_eval"]})


@bp.get("/api/feature-importance")
def feature_importance():
    if (r := _need_models()): return r
    return jsonify(store.meta["feature_importance"])


@bp.get("/api/rainfall-history")
def rainfall_history():
    if (r := _need_models()): return r
    h, loc = store.meta["history"], request.args.get("location")
    series = h["series"]
    if loc:
        if not h["series_by_location"] or loc not in h["series_by_location"]:
            return jsonify({"error": "unknown_location", "message": f"'{loc}' not found"}), 404
        series = h["series_by_location"][loc]
    return jsonify({"location": loc, "series": series, "by_location": h["by_location"],
                    "risk_distribution": h["risk_distribution"], "actual_vs_predicted": h["actual_vs_predicted"]})
