"""Feature selection and the sklearn preprocessing pipeline (used in training AND inference)."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import config

DERIVED_TIME = ["month", "month_sin", "month_cos"]


def add_time_features(df, date_col):
    """Seasonality features. sin/cos make December and January 'neighbours'."""
    df = df.copy()
    if date_col:
        df["month"] = df[date_col].dt.month
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def month_features(month):
    return {"month": month, "month_sin": float(np.sin(2 * np.pi * month / 12)),
            "month_cos": float(np.cos(2 * np.pi * month / 12))}


def select_features(df, cols, use_geo):
    """Decide which columns feed the model, based on the ACTUAL dataset."""
    roles = {v for v in cols.values() if v}
    exclude = {e.lower() for e in config.EXCLUDE_FEATURES} | set(DERIVED_TIME)
    weather = []
    for c in df.select_dtypes("number").columns:
        if c in roles or c.lower() in exclude:
            continue
        if df[c].isna().mean() > 0.6 or df[c].nunique() <= 1:
            continue  # mostly-empty or constant columns carry no signal
        weather.append(c)
    geo = [cols["latitude"], cols["longitude"]] if use_geo and cols["latitude"] and cols["longitude"] else []
    return {"weather": weather,
            "derived": DERIVED_TIME if cols["date"] else [],
            "geo": geo,
            "categorical": [cols["location"]]}


def feature_order(spec):
    return spec["weather"] + spec["derived"] + spec["geo"] + spec["categorical"]


def build_preprocessor(spec):
    numeric = spec["weather"] + spec["derived"] + spec["geo"]
    return ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), spec["categorical"]),
    ])
