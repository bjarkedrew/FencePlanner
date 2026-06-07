@echo off
setlocal
title Installer AgOpenGPS Fence Planner
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1"
if errorlevel 1 (
    echo.
    echo Installationen fejlede.
    pause
    exit /b 1
)
echo.
echo Faerdig. Du kan nu starte programmet fra skrivebordet eller Start-menuen.
pause
