@echo off
setlocal
title Fence Guide - Expo dev
cd /d "%~dp0"
set "NODE_HOME=%~dp0..\..\.tools\node-v22.22.3-win-x64"
set "PATH=%NODE_HOME%;%PATH%"
npm install
npx expo start -c
pause
