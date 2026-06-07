@echo off
title Lav AgOpenGPS Fence Planner EXE
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\install.ps1"
echo.
echo Faerdig. Programmet er bygget, installeret og har faaet genveje.
pause
