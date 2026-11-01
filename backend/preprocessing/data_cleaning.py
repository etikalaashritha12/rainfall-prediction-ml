"""Dataset loading, column detection, cleaning and data-quality report."""
import logging
import pandas as pd
import config

log = logging.getLogger(__name__)


def detect_columns(df):
    """Map logical roles (date, location, target...) to real column names."""
    lower = {c.lower().strip(): c for c in df.columns}
    cols = {}
    for role, aliases in config.COLUMN_ALIASES.items():
        override = config.COLUMN_OVERRIDES.get(role)
        if override:
            if override not in df.columns:
                raise ValueError(f"Configured column '{override}' for '{role}' not in dataset")
            cols[role] = override
        else:
            cols[role] = next((lower[a] for a in aliases if a in lower), None)
    if cols["target"] is None:
        raise ValueError("Could not find the rainfall target column. Set "
                         "COLUMN_OVERRIDES['target'] in config.py. "
                         f"Columns found: {list(df.columns)}")
    if cols["location"] is None:
        raise ValueError("No location column found - the project needs a location column "
                         "(city/district/station). Set COLUMN_OVERRIDES['location'].")
    return cols


def load_and_clean(path):
    """Return (clean_df, columns_map, data_quality_report)."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}. See README for the expected schema.")
    df = pd.read_csv(path)
    cols = detect_columns(df)
    report = {"rows_raw": int(len(df)), "columns": list(df.columns),
              "detected_columns": cols,
              "missing_per_column": {c: int(n) for c, n in df.isna().sum().items()},
              "duplicate_rows": int(df.duplicated().sum())}

    df = df.drop_duplicates()
    df[cols["location"]] = df[cols["location"]].astype(str).str.strip()
    df[cols["target"]] = pd.to_numeric(df[cols["target"]], errors="coerce")
    if cols["date"]:
        df[cols["date"]] = pd.to_datetime(df[cols["date"]], errors="coerce")
        df = df.dropna(subset=[cols["date"]]).sort_values(cols["date"]).reset_index(drop=True)
    # rows without a target cannot be used for supervised learning; negative rain is invalid
    df = df.dropna(subset=[cols["target"]])
    df = df[df[cols["target"]] >= 0].reset_index(drop=True)

    # Outliers are REPORTED (IQR rule) but not removed: extreme rain is exactly what we predict.
    outliers = {}
    for c in df.select_dtypes("number").columns:
        q1, q3 = df[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers[c] = int(((df[c] < q1 - 1.5 * iqr) | (df[c] > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0
    report["outliers_iqr"] = outliers
    report["rows_clean"] = int(len(df))
    report["target_summary"] = {k: float(v) for k, v in df[cols["target"]].describe().items()}
    report["target_skew"] = float(df[cols["target"]].skew())
    log.info("Loaded %d clean rows (%d raw, %d duplicates)", len(df), report["rows_raw"], report["duplicate_rows"])
    return df, cols, report
