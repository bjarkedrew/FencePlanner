@echo off
setlocal
title Afinstaller AgOpenGPS Fence Planner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\uninstall.ps1"
echo.
pause
