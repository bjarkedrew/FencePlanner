@echo off
setlocal
title AgOpenGPS Fence Planner Setup

rem Indsaet download-linket til AgOpenGPS_FencePlanner_package.zip her:
set "PACKAGE_URL="

if "%PACKAGE_URL%"=="" (
    echo Mangler PACKAGE_URL i FencePlanner_Setup.bat
    echo.
    echo Aabn filen i Notesblok og indsaet linket til AgOpenGPS_FencePlanner_package.zip
    echo paa linjen:
    echo set "PACKAGE_URL=..."
    echo.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0FencePlanner_Setup.ps1" -PackageUrl "%PACKAGE_URL%"
if errorlevel 1 (
    echo.
    echo Installationen fejlede.
    pause
    exit /b 1
)

echo.
echo Faerdig. AgOpenGPS Fence Planner er installeret.
pause
