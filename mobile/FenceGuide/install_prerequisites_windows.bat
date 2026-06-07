@echo off
setlocal
title Installer Fence Guide Android vaerktoejer
echo Dette installerer Node.js LTS og Android Studio via winget.
echo Android Studio er stor og kan tage noget tid.
echo.
pause
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Google.AndroidStudio -e
echo.
echo Faerdig. Genstart computeren eller aabn et nyt PowerShell-vindue.
pause
