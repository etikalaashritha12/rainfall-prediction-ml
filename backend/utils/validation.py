"""Request validation helpers."""
from datetime import date, datetime


def validate_predict_payload(payload, meta):
    """Return (clean, errors). `meta` is the metadata.json produced by training."""
    errors, clean = {}, {}
    if not isinstance(payload, dict):
        return None, {"body": "JSON object expected"}

    supported = {loc["name"] for loc in meta["locations"]}
    location = payload.get("location")
    if not location:
        errors["location"] = "location is required"
    elif location not in supported:
        errors["location"] = f"'{location}' is not a supported location (not in training data)"
    clean["location"] = location

    weather = payload.get("weather")
    if not isinstance(weather, dict):
        errors["weather"] = "weather must be an object of feature -> number"
        weather = {}
    clean_weather = {}
    for feat in meta["features"]:
        name = feat["name"]
        raw = weather.get(name)
        if raw in (None, ""):
            continue  # missing values are imputed with training medians
        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors[f"weather.{name}"] = "must be a number"
            continue
        span = (feat["max"] - feat["min"]) or 1.0
        lo, hi = feat["min"] - 0.5 * span, feat["max"] + 0.5 * span
        if not (lo <= value <= hi):
            errors[f"weather.{name}"] = (f"{value} is far outside the training range "
                                         f"[{feat['min']:.2f}, {feat['max']:.2f}]")
            continue
        clean_weather[name] = value
    unknown = set(weather) - {f["name"] for f in meta["features"]}
    if unknown:
        errors["weather"] = f"unknown features: {sorted(unknown)}"
    clean["weather"] = clean_weather

    if meta.get("uses_date"):
        raw_date = payload.get("date")
        if raw_date:
            try:
                clean["date"] = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                errors["date"] = "date must be YYYY-MM-DD"
        else:
            clean["date"] = date.today()
            clean["date_defaulted"] = True
    return clean, errors
