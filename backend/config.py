"""Central configuration. Edit this file (not the code) to adapt to your dataset."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "dataset.csv"
SAVED_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "alerts.db"
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Column mapping. Leave a value as None to auto-detect using COLUMN_ALIASES.
# Or set the exact column name from YOUR csv, e.g. "target": "Rainfall".
# ---------------------------------------------------------------------------
COLUMN_OVERRIDES = {
    "date": None, "location": None, "state": None,
    "latitude": None, "longitude": None, "target": None,
}
COLUMN_ALIASES = {
    "date": ["date", "datetime", "time", "timestamp", "day"],
    "location": ["location", "city", "district", "station", "place", "region"],
    "state": ["state", "province"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng", "long"],
    "target": ["rainfall", "rainfall_mm", "rain", "precipitation", "precip", "prcp"],
}
# Numeric columns that must NOT be used as inputs (IDs, years, leakage such as
# "RainToday"/"RainTomorrow" flags derived from the target, etc.)
EXCLUDE_FEATURES = ["year", "id", "index", "unnamed: 0"]

# ---------------------------------------------------------------------------
# Rainfall categories (IMD daily-rainfall classes, in mm/day).
# !! If your target is hourly / monthly / yearly, CHANGE these thresholds. !!
# (upper_bound_exclusive, label)
# ---------------------------------------------------------------------------
RAIN_CATEGORIES = [
    (0.1, "No rain"), (15.6, "Light"), (64.5, "Moderate"),
    (115.6, "Heavy"), (204.5, "Very heavy"), (float("inf"), "Extremely heavy"),
]
HEAVY_RAIN_THRESHOLD_MM = 64.5      # >= this counts as a heavy-rainfall event
MODERATE_RISK_MM = 15.6             # >= this -> "moderate" risk
HIGH_RISK_PROBABILITY = 0.5         # classifier probability for a HIGH warning
MODERATE_RISK_PROBABILITY = 0.25
MIN_HEAVY_EVENTS_FOR_CLASSIFIER = 30

# Chronological split fractions (train / validation / test)
TRAIN_FRAC, VAL_FRAC = 0.70, 0.15
