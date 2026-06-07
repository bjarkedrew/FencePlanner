@echo off
setlocal
title Fence Guide - byg APK
cd /d "%~dp0"
set "NODE_HOME=%~dp0..\..\.tools\node-v22.22.3-win-x64"
set "PATH=%NODE_HOME%;%PATH%"
npm install
npx eas-cli build -p android --profile preview
pause
