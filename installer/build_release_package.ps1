$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
$releaseDir = Join-Path $projectDir "release"
$packageRoot = Join-Path $releaseDir "AgOpenGPS_FencePlanner_package"
$packageZip = Join-Path $releaseDir "AgOpenGPS_FencePlanner_package.zip"
$appName = "AgOpenGPS Fence Planner"
$exeName = "$appName.exe"
$builtExe = Join-Path $projectDir "dist\$exeName"
$nodeSource = Join-Path $projectDir ".tools\node-v22.22.3-win-x64"

if (-not (Test-Path $builtExe)) {
    throw "EXE mangler. Koer install_program.bat eller installer\install.ps1 foerst: $builtExe"
}
if (-not (Test-Path $nodeSource)) {
    throw "Portable Node mangler: $nodeSource"
}

Remove-Item -LiteralPath $packageRoot, $packageZip -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $packageRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageRoot "installer") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageRoot ".tools") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageRoot "sync_server") | Out-Null

Copy-Item -Force $builtExe (Join-Path $packageRoot $exeName)
Copy-Item -Force (Join-Path $scriptDir "install_release.ps1") (Join-Path $packageRoot "installer\install_release.ps1")
Copy-Item -Force (Join-Path $scriptDir "uninstall.ps1") (Join-Path $packageRoot "installer\uninstall.ps1")
Copy-Item -Force (Join-Path $projectDir "start_qr_sync_server.bat") (Join-Path $packageRoot "start_qr_sync_server.bat")
Copy-Item -Force (Join-Path $projectDir "sync_server\server.js") (Join-Path $packageRoot "sync_server\server.js")
Copy-Item -Recurse -Force $nodeSource (Join-Path $packageRoot ".tools\node-v22.22.3-win-x64")

Compress-Archive -Path (Join-Path $packageRoot "*") -DestinationPath $packageZip -Force

Write-Host "Release-pakke lavet:"
Write-Host $packageZip
