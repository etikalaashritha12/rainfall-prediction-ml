"""Rainfall categories and heavy-rainfall early-warning logic."""
import config

PRECAUTIONS = {
    "high": ["Follow official IMD / local-authority weather advisories.",
             "Avoid unnecessary travel and low-lying or waterlogged roads.",
             "Keep emergency contacts, torch and phone power ready.",
             "Move vehicles and valuables away from flood-prone spots if local water levels are rising."],
    "moderate": ["Carry rain protection and allow extra travel time.",
                 "Check drains around your home and keep an eye on forecasts."],
    "normal": ["No special precautions needed. Continue to monitor forecasts."],
}


def rainfall_category(mm):
    for upper, label in config.RAIN_CATEGORIES:
        if mm < upper:
            return label
    return config.RAIN_CATEGORIES[-1][1]


def assess_risk(predicted_mm, heavy_probability):
    """Combine regression output + classifier probability into normal / moderate / high."""
    p = heavy_probability
    if predicted_mm >= config.HEAVY_RAIN_THRESHOLD_MM or (p is not None and p >= config.HIGH_RISK_PROBABILITY):
        level = "high"
    elif predicted_mm >= config.MODERATE_RISK_MM or (p is not None and p >= config.MODERATE_RISK_PROBABILITY):
        level = "moderate"
    else:
        level = "normal"
    msgs = {"high": "Heavy-rainfall early warning: heavy rain is likely.",
            "moderate": "Moderate rainfall expected. Stay alert.",
            "normal": "No heavy-rainfall warning."}
    return {"level": level, "warning": level == "high", "heavy_rain_probability": p,
            "message": msgs[level], "precautions": PRECAUTIONS[level]}
