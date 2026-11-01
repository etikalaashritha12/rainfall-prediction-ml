"""Training script. Run ONCE:  python -m models.train
Produces saved_models/{best_model.pkl, risk_model.pkl, metadata.json} and reports/*."""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd

import config
from models.ensemble import ENSEMBLE, build_candidates
from models.location_model import evaluate_geo_features, unseen_location_eval
from models.model_evaluation import regression_metrics, save_plots
from models.risk_model import train_risk_model
from prediction.explainability import compute_importance
from prediction.risk_analysis import rainfall_category
from preprocessing.data_cleaning import load_and_clean
from preprocessing.feature_engineering import add_time_features, feature_order, select_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.StreamHandler(), logging.FileHandler(config.REPORTS_DIR / "training.log", mode="w")])
log = logging.getLogger("train")


def split_data(df, date_col):
    """Chronological split (past -> train, future -> test) so we never train on the future."""
    if not date_col:
        log.warning("No date column: using a RANDOM split (not ideal for time series).")
        df = df.sample(frac=1, random_state=config.RANDOM_SEED).reset_index(drop=True)
    n = len(df)
    a, b = int(n * config.TRAIN_FRAC), int(n * (config.TRAIN_FRAC + config.VAL_FRAC))
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def monthly_series(frame, date_col, target):
    s = frame.groupby(frame[date_col].dt.to_period("M"))[target].mean()
    return [{"period": str(p), "mean_rainfall": float(v)} for p, v in s.items()]


def risk_level_of(mm):
    return "high" if mm >= config.HEAVY_RAIN_THRESHOLD_MM else "moderate" if mm >= config.MODERATE_RISK_MM else "normal"


def main():
    config.SAVED_DIR.mkdir(exist_ok=True); config.REPORTS_DIR.mkdir(exist_ok=True)
    df, cols, quality = load_and_clean(config.DATA_PATH)
    target, loc_col, date_col = cols["target"], cols["location"], cols["date"]
    df = add_time_features(df, date_col)
    train, val, test = split_data(df, date_col)
    log.info("Split sizes train/val/test = %d/%d/%d", len(train), len(val), len(test))

    use_geo, geo_report = False, None
    if cols["latitude"] and cols["longitude"]:
        use_geo, geo_report = evaluate_geo_features(train, val, cols, target)
    spec = select_features(df, cols, use_geo)
    order = feature_order(spec)
    log.info("Features used: %s", order)

    # ---- Train + evaluate all candidates on the SAME validation and test sets ----
    results, fitted = {}, {}
    for name, pipe in build_candidates(spec).items():
        log.info("Training %s ...", name)
        pipe.fit(train[order], train[target])
        pv, pt = np.clip(pipe.predict(val[order]), 0, None), np.clip(pipe.predict(test[order]), 0, None)
        results[name] = {"validation": regression_metrics(val[target], pv), "test": regression_metrics(test[target], pt)}
        fitted[name] = (pipe, pt)
        log.info("%s -> val RMSE %.3f | test %s", name, results[name]["validation"]["rmse"], results[name]["test"])

    # Best model chosen on VALIDATION RMSE (test set stays untouched for the final report).
    best = min(results, key=lambda n: results[n]["validation"]["rmse"])
    best_pipe, best_test_pred = fitted[best]
    log.info("Best model: %s (ensemble is best: %s)", best, best == ENSEMBLE)

    importance = compute_importance(best_pipe, test[order], test[target])
    save_plots(results, best, test[target].values, best_test_pred, importance, config.REPORTS_DIR)
    unseen = unseen_location_eval(df, cols, spec, target)
    risk_pipe, risk_metrics = train_risk_model(spec, order, train, val, test, target)

    # ---- Metadata consumed by the API (everything the frontend displays comes from here) ----
    lat, lon, state = cols["latitude"], cols["longitude"], cols["state"]
    locations = []
    for name, g in df.groupby(loc_col):
        locations.append({"name": name,
                          "state": str(g[state].iloc[0]) if state else None,
                          "latitude": float(g[lat].iloc[0]) if lat else None,
                          "longitude": float(g[lon].iloc[0]) if lon else None,
                          "records": int(len(g)),
                          "avg_weather": {c: float(g[c].mean()) for c in spec["weather"] if g[c].notna().any()}})
    features = [{"name": c, "min": float(df[c].min()), "max": float(df[c].max()),
                 "mean": float(df[c].mean())} for c in spec["weather"]]

    history = {"series": monthly_series(df, date_col, target) if date_col else None,
               "series_by_location": ({n: monthly_series(g, date_col, target) for n, g in df.groupby(loc_col)}
                                      if date_col else None),
               "by_location": [{"location": n, "mean_rainfall": float(g[target].mean()),
                                "max_rainfall": float(g[target].max())} for n, g in df.groupby(loc_col)],
               "risk_distribution": {**{k: int(v) for k, v in
                                        df[target].map(risk_level_of).value_counts().items()},
                                     "basis": "historical observations classified by rainfall thresholds"}}
    for k in ("normal", "moderate", "high"):
        history["risk_distribution"].setdefault(k, 0)
    if date_col:
        tdf = test.assign(_pred=best_test_pred).groupby(test[date_col].dt.date).agg(
            actual=(target, "mean"), predicted=("_pred", "mean")).reset_index()
        tdf.columns = ["date", "actual", "predicted"]
        history["actual_vs_predicted"] = {"split": "test (chronological hold-out, daily mean over locations)",
                                          "points": [{"date": str(r.date), "actual": float(r.actual), "predicted": float(r.predicted)}
                                                     for r in tdf.itertuples()][-365:]}
    else:
        history["actual_vs_predicted"] = {"split": "test (random hold-out)", "points": [
            {"date": str(i), "actual": float(a), "predicted": float(p)}
            for i, (a, p) in enumerate(zip(test[target].values[:365], best_test_pred[:365]))]}

    meta = {"trained_at": datetime.now().isoformat(timespec="seconds"),
            "target": target, "uses_date": bool(date_col), "columns": cols, "features": features,
            "feature_order": order, "spec": spec, "locations": locations,
            "split": {"type": "chronological" if date_col else "random", "train": len(train),
                      "validation": len(val), "test": len(test)},
            "models": results, "best_model": best, "ensemble_is_best": best == ENSEMBLE,
            "selection_metric": "validation RMSE",
            "feature_importance": {"method": "permutation importance on the test set (increase in RMSE)", "features": importance},
            "risk_model": risk_metrics,
            "thresholds": {"heavy_mm": config.HEAVY_RAIN_THRESHOLD_MM, "moderate_mm": config.MODERATE_RISK_MM,
                           "categories": [{"upper_mm": (None if u == float("inf") else u), "label": l}
                                          for u, l in config.RAIN_CATEGORIES]},
            "geo_experiment": geo_report, "unseen_location_eval": unseen,
            "data_quality": quality, "history": history,
            "demo_data": (config.DATA_PATH.parent / "DATA_IS_SYNTHETIC.txt").exists()}
    joblib.dump(best_pipe, config.SAVED_DIR / "best_model.pkl")
    if risk_pipe is not None:
        joblib.dump(risk_pipe, config.SAVED_DIR / "risk_model.pkl")
    elif (config.SAVED_DIR / "risk_model.pkl").exists():
        (config.SAVED_DIR / "risk_model.pkl").unlink()
    (config.SAVED_DIR / "metadata.json").write_text(json.dumps(meta, indent=2))
    write_report(meta)
    log.info("Training complete. Artifacts saved to %s", config.SAVED_DIR)


def write_report(meta):
    lines = [f"# Evaluation report ({meta['trained_at']})", "",
             f"Split: {meta['split']}", "", "## Regression models (test set)", "",
             "| Model | MAE | RMSE | R2 |", "|---|---|---|---|"]
    for n, r in meta["models"].items():
        t = r["test"]; lines.append(f"| {n} | {t['mae']:.3f} | {t['rmse']:.3f} | {t['r2']:.3f} |")
    lines += ["", f"Best model (by validation RMSE): **{meta['best_model']}**", "",
              "## Heavy-rainfall classifier", "", "```", json.dumps(meta["risk_model"], indent=2), "```"]
    (config.REPORTS_DIR / "evaluation_report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
