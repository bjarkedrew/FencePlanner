$ErrorActionPreference = "Stop"

$appName = "AgOpenGPS Fence Planner"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) $appName
$startupShortcut = Join-Path ([Environment]::GetFolderPath("Startup")) "$appName.lnk"

Remove-Item -Force -ErrorAction SilentlyContinue $desktopShortcut
Remove-Item -Force -ErrorAction SilentlyContinue $startupShortcut
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $startMenuDir
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $installDir

Write-Host "AgOpenGPS Fence Planner er afinstalleret for denne bruger."
