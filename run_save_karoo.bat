@echo off
title SAVE KAROO - Public Safety Platform
echo ========================================================
echo   🛡️ Starting SAVE KAROO Public Safety Platform...
echo ========================================================
cd /d "%~dp0"
.\venv\Scripts\python.exe -m streamlit run app.py
pause
