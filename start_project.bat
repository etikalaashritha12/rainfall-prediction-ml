@echo off
cd /d "%~dp0"

echo Starting Rainfall Prediction Project...

start "Rainfall Backend" cmd /k "cd /d "%~dp0" && "%~dp0venv\Scripts\python.exe" backend\app.py"

timeout /t 5 /nobreak >nul

start "Rainfall Frontend" cmd /k "cd /d "%~dp0frontend" && "%~dp0venv\Scripts\python.exe" -m http.server 8000"

timeout /t 3 /nobreak >nul

start "" "http://127.0.0.1:8000"

exit