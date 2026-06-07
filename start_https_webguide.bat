@echo off
setlocal
title Fence Planner HTTPS Webguide
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_https_webguide.ps1"
if errorlevel 1 (
    echo.
    echo Kunne ikke starte HTTPS Webguide.
    pause
)
