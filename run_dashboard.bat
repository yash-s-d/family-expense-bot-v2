@echo off
title Family Finance Dashboard
cd /d "%~dp0"

echo ====================================================
echo Starting Family Finance Neo-Fintech Dashboard (2026)
echo Connecting to Google Sheets...
echo Opening http://localhost:5050 in your browser...
echo ====================================================

:: Automatically open browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5050"

:: Start Flask server
python app_dashboard.py
pause
