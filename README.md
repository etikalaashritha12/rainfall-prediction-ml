# Rainfall Prediction Using ML

```
rainfall-project/
  backend/   Flask API + ML training      frontend/  HTML/CSS/JS dashboard
```

## Quick start (easiest)
- A **synthetic demo dataset** is already at `backend/data/dataset.csv` (35,064 rows, 12 Indian cities, 2015-2022) so everything runs immediately. It is NOT real data - the dashboard shows a "Demo mode" banner. To use real data: replace the CSV, delete `backend/data/DATA_IS_SYNTHETIC.txt`, delete `backend/saved_models/*.pkl`, and retrain.
- Windows: double-click `backend/run_backend.bat` (installs, trains the first time ~1-2 min, starts API), then `frontend/run_frontend.bat`.
- Mac/Linux: `backend/run_backend.sh` then `frontend/run_frontend.sh`.
- In VS Code, open the `rainfall-project` folder, then use the terminal steps below if you prefer.

## Run it (manual)
1. **Dataset** - copy your CSV to `backend/data/dataset.csv` (see `backend/data/README_DATASET.md`).
   Check `config.py`: column names and `HEAVY_RAIN_THRESHOLD_MM` / `RAIN_CATEGORIES` must match your rainfall unit (default: mm per day, IMD classes).
2. **Backend**
   ```
   cd backend
   python -m venv venv && venv\Scripts\activate      (Linux/Mac: source venv/bin/activate)
   pip install -r requirements.txt
   python -m models.train      # trains ONCE, saves saved_models/ + reports/
   python app.py               # API on http://127.0.0.1:5000
   ```
3. **Frontend** (second terminal)
   ```
   cd frontend
   python -m http.server 8000
   ```
   Open http://127.0.0.1:8000. The status pill (top right) shows API connection.
   To use another API address: browser console -> `localStorage.setItem("apiBase","http://HOST:PORT")`.

## Architecture / data flow
CSV -> clean (dedupe, parse dates, drop missing target) -> features (weather + month sin/cos + location one-hot + optional lat/lon)
-> chronological split 70/15/15 -> train 4 models on the same split -> choose best by **validation RMSE** -> report on **test**
-> heavy-rain classifier (class_weight='balanced') -> permutation importance -> save `best_model.pkl`, `risk_model.pkl`, `metadata.json`.
Flask only **loads** these files; the API never retrains.

## API (all JSON)
| Endpoint | Returns |
|---|---|
| GET /api/health | `{status, models_loaded, risk_model_loaded, trained_at, message}` |
| GET /api/locations | `{count, locations[{name,state,latitude,longitude,records,avg_weather}], features[{name,min,max,mean}], uses_date}` |
| POST /api/predict | body `{location, date?, weather:{feature:number}}` -> `{location, input, predicted_rainfall_mm, category, model_used, risk{level,warning,heavy_rain_probability,message,precautions}, explanation, flood_risk}` ; 400 `{error:"validation_failed", details}` ; 503 if not trained |
| GET /api/model-performance | `{best_model, ensemble_is_best, models[{name,validation,test{mae,rmse,r2},is_best}], risk_model, thresholds, geo_experiment, unseen_location_eval}` |
| GET /api/feature-importance | `{method, features[{feature,importance,std}]}` |
| GET /api/rainfall-history?location= | `{series, by_location, risk_distribution, actual_vs_predicted}` |
| GET /api/alerts | `{alerts[{created_at,location,predicted_mm,category,risk_level,...}], count}` |

## Viva notes (plain-language)
- **Ensemble**: averaging several different models usually reduces error; here Voting = mean of Random Forest + Gradient Boosting. It is kept only if validation RMSE says so.
- **Chronological split**: train on the past, test on the future - random splitting would leak future information.
- **MAE / RMSE / R2**: average error in mm / error that punishes big misses / share of variance explained.
- **Class imbalance**: heavy rain is rare, so the classifier gives rare events more weight; judge it by precision, recall, F1 - not accuracy.
- **Permutation importance**: shuffle one feature; if error rises a lot, the model depends on it.
- **Heavy rain != flood**: floods also depend on soil, rivers, terrain and drainage, which are not in the data - so the system says "heavy-rainfall early warning".
