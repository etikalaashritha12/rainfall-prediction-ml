"""Heavy-rainfall classifier (early-warning). Label = rainfall >= HEAVY_RAIN_THRESHOLD_MM."""
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import config
from models.model_evaluation import classification_metrics
from preprocessing.feature_engineering import build_preprocessor

log = logging.getLogger(__name__)


def train_risk_model(spec, order, train, val, test, target):
    """Returns (pipeline, metrics) or (None, reason) when there are too few heavy-rain events."""
    y = {k: (d[target] >= config.HEAVY_RAIN_THRESHOLD_MM).astype(int) for k, d in
         {"train": train, "val": val, "test": test}.items()}
    counts = {k: int(v.sum()) for k, v in y.items()}
    log.info("Heavy-rain events (train/val/test): %s", counts)
    if counts["train"] < config.MIN_HEAVY_EVENTS_FOR_CLASSIFIER or counts["test"] == 0:
        return None, {"trained": False, "heavy_event_counts": counts,
                      "reason": (f"Not enough heavy-rainfall events (>= {config.HEAVY_RAIN_THRESHOLD_MM}) "
                                 "to train a reliable classifier. Adjust HEAVY_RAIN_THRESHOLD_MM in config.py "
                                 "if your target is not daily mm.")}
    # class_weight='balanced' handles imbalance: rare heavy events get larger weight.
    clf = Pipeline([("prep", build_preprocessor(spec)),
                    ("model", RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight="balanced",
                                                     n_jobs=-1, random_state=config.RANDOM_SEED))])
    clf.fit(train[order], y["train"])
    prob = clf.predict_proba(test[order])[:, 1]
    pred = (prob >= config.HIGH_RISK_PROBABILITY).astype(int)
    m = classification_metrics(y["test"], pred, prob)
    m.update({"trained": True, "heavy_event_counts": counts, "threshold_mm": config.HEAVY_RAIN_THRESHOLD_MM,
              "decision_probability": config.HIGH_RISK_PROBABILITY})
    return clf, m
