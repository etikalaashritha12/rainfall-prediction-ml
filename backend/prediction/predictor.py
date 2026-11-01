"""Loads saved artifacts ONCE and serves predictions. Never trains."""
import json
import logging
import joblib
import numpy as np
import pandas as pd
import config
from preprocessing.feature_engineering import month_features
from prediction.risk_analysis import assess_risk, rainfall_category

log = logging.getLogger(__name__)


class ModelStore:
    def __init__(self):
        self.meta = self.model = self.risk_model = None
        self.error = None

    @property
    def ready(self):
        return self.model is not None and self.meta is not None

    def load(self):
        try:
            self.meta = json.loads((config.SAVED_DIR / "metadata.json").read_text())
            self.model = joblib.load(config.SAVED_DIR / "best_model.pkl")
            rp = config.SAVED_DIR / "risk_model.pkl"
            self.risk_model = joblib.load(rp) if rp.exists() else None
            self.error = None
            log.info("Model artifacts loaded (best=%s)", self.meta["best_model"])
        except Exception as exc:  # missing files before first training is a normal situation
            self.meta = self.model = self.risk_model = None
            self.error = f"Model artifacts not available: {exc}. Run `python -m models.train` first."
            log.warning(self.error)


store = ModelStore()


def predict(clean):
    """`clean` comes from utils.validation.validate_predict_payload."""
    meta, spec = store.meta, store.meta["spec"]
    loc = next(l for l in meta["locations"] if l["name"] == clean["location"])
    cols = meta["columns"]
    row = {c: clean["weather"].get(c, np.nan) for c in spec["weather"]}
    imputed = [c for c in spec["weather"] if c not in clean["weather"]]
    if spec["derived"]:
        row.update(month_features(clean["date"].month))
    if spec["geo"]:
        row[cols["latitude"]], row[cols["longitude"]] = loc["latitude"], loc["longitude"]
    row[cols["location"]] = clean["location"]
    X = pd.DataFrame([row])[meta["feature_order"]]  # SAME column order as training

    mm = float(max(store.model.predict(X)[0], 0.0))
    prob = float(store.risk_model.predict_proba(X)[0][1]) if store.risk_model is not None else None
    risk = assess_risk(mm, prob)
    top = meta["feature_importance"]["features"][:5]
    return {
        "location": clean["location"],
        "input": {"weather": clean["weather"], "date": str(clean["date"]) if "date" in clean else None,
                  "date_defaulted_to_today": bool(clean.get("date_defaulted")), "imputed_features": imputed},
        "predicted_rainfall_mm": round(mm, 2),
        "category": rainfall_category(mm),
        "model_used": meta["best_model"],
        "risk": risk,
        "explanation": {"scope": "global", "method": meta["feature_importance"]["method"],
                        "top_features": top,
                        "note": "Importance describes the model overall, not only this single prediction."},
        "flood_risk": {"available": False,
                       "note": "Heavy-rainfall early warning only. No soil, river, terrain or flood-record "
                               "data was used, so flooding is NOT predicted."},
    }
