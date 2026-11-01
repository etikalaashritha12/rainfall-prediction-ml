# Dataset requirements
Place your CSV at `backend/data/dataset.csv`. No dataset is bundled and none is fabricated.

| Role | Required? | Accepted column names (auto-detected, case-insensitive) |
|---|---|---|
| Rainfall amount (target) | YES | rainfall, rainfall_mm, rain, precipitation, precip, prcp |
| Location | YES | location, city, district, station, place, region |
| Date | recommended | date, datetime, time, timestamp, day |
| State | optional | state, province |
| Latitude / Longitude | optional (needed for the map) | latitude/lat, longitude/lon/lng |
| Weather features | any numeric columns | e.g. temperature, humidity, pressure, wind_speed, cloud_cover |

Every other numeric column becomes a weather input automatically. If your names differ, set
`COLUMN_OVERRIDES` in `config.py`. Remove leakage columns (e.g. "RainToday") via `EXCLUDE_FEATURES`.
