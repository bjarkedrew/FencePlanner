@echo off
title AgOpenGPS Fence Planner
set "INSTALLED=%LOCALAPPDATA%\Programs\AgOpenGPS Fence Planner\AgOpenGPS Fence Planner.exe"
if exist "%INSTALLED%" (
    start "" "%INSTALLED%"
    exit /b 0
)

if not exist .venv (
    echo Opretter Python miljo...
    py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installerer pakker hvis de mangler...
python -m pip install -r requirements.txt
echo Starter program...
python main.py
pause
