@echo off
setlocal
title Fence Guide - Expo login
cd /d "%~dp0"
set "NODE_HOME=%~dp0..\..\.tools\node-v22.22.3-win-x64"
set "PATH=%NODE_HOME%;%PATH%"
npx eas-cli login
pause
