"""Location-aware experiments: (1) are lat/lon useful? (2) does the model work on UNSEEN locations?"""
import logging
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
import config
from preprocessing.feature_engineering import build_preprocessor, feature_order, select_features

log = logging.getLogger(__name__)


def _rf(spec):
    return Pipeline([("prep", build_preprocessor(spec)),
                     ("model", RandomForestRegressor(n_estimators=100, min_samples_leaf=2, n_jobs=-1,
                                                     random_state=config.RANDOM_SEED))])


def evaluate_geo_features(train, val, cols, target):
    """Fit a quick RF with and without lat/lon; keep them only if validation RMSE improves >= 1%."""
    rmse = {}
    for use_geo in (False, True):
        spec = select_features(train, cols, use_geo)
        order = feature_order(spec)
        model = _rf(spec).fit(train[order], train[target])
        rmse[use_geo] = float(np.sqrt(mean_squared_error(val[target], model.predict(val[order]))))
    keep = rmse[True] < 0.99 * rmse[False]
    log.info("Geo experiment: RMSE without=%.3f with=%.3f -> use_geo=%s", rmse[False], rmse[True], keep)
    return keep, {"val_rmse_without_lat_lon": rmse[False], "val_rmse_with_lat_lon": rmse[True],
                  "lat_lon_used": bool(keep)}


def unseen_location_eval(df, cols, spec, target):
    """GroupKFold by location: train on some locations, test on locations never seen in training.
    Location one-hot columns are ignored for unseen places, so this shows how much the model
    depends on knowing the place."""
    groups = df[cols["location"]]
    n_loc = groups.nunique()
    if n_loc < 3:
        return None
    order = feature_order(spec)
    rmses, r2s = [], []
    for tr, te in GroupKFold(n_splits=min(3, n_loc)).split(df, groups=groups):
        m = _rf(spec).fit(df.iloc[tr][order], df.iloc[tr][target])
        pred = m.predict(df.iloc[te][order])
        rmses.append(float(np.sqrt(mean_squared_error(df.iloc[te][target], pred))))
        r2s.append(float(r2_score(df.iloc[te][target], pred)))
    return {"method": f"GroupKFold({min(3, n_loc)}) by location, Random Forest",
            "mean_rmse": float(np.mean(rmses)), "mean_r2": float(np.mean(r2s))}
