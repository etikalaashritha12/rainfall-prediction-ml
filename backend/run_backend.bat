@echo off
cd /d %~dp0
if not exist venv ( python -m venv venv )
call venv\Scripts\activate
pip install -r requirements.txt
if not exist saved_models\best_model.pkl ( python -m models.train )
python app.py
pause
