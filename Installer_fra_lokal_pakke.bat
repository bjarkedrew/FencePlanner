@echo off
setlocal
title Installer AgOpenGPS Fence Planner fra lokal pakke

set "ZIP=%~dp0AgOpenGPS_FencePlanner_package.zip"
set "WORK=%TEMP%\FencePlannerLocalSetup_%RANDOM%%RANDOM%"

if not exist "%ZIP%" (
    echo Pakken blev ikke fundet:
    echo %ZIP%
    pause
    exit /b 1
)

mkdir "%WORK%" >nul 2>nul
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%ZIP%' -DestinationPath '%WORK%' -Force"
if errorlevel 1 (
    echo Kunne ikke pakke zippen ud.
    pause
    exit /b 1
)

for /r "%WORK%" %%F in (install_release.ps1) do (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%%F"
    goto done
)

echo install_release.ps1 blev ikke fundet i pakken.
pause
exit /b 1

:done
rmdir /s /q "%WORK%" >nul 2>nul
echo.
echo Faerdig.
pause
