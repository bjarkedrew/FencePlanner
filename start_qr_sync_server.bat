@echo off
setlocal
title FencePlanner QR Sync Server
cd /d "%~dp0"

set "NODE=%~dp0.tools\node-v22.22.3-win-x64\node.exe"
if not exist "%NODE%" set "NODE=node"

echo Starter FencePlanner QR Sync Server...
echo.
echo Mobilside lokalt: http://127.0.0.1:8787
set "FENCE_SYNC_DATA=%USERPROFILE%\Documents\FencePlanner\SyncServer"
echo Data gemmes i: %FENCE_SYNC_DATA%
echo.
"%NODE%" sync_server\server.js
pause
