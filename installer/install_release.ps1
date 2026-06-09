param(
    [switch]$Autostart
)

$ErrorActionPreference = "Stop"

function New-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$WorkingDirectory,
        [string]$Description
    )

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.Description = $Description
    $shortcut.IconLocation = $TargetPath
    $shortcut.Save()
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$packageDir = Split-Path -Parent $scriptDir
$appName = "AgOpenGPS Fence Planner"
$exeName = "$appName.exe"
$sourceExe = Join-Path $packageDir $exeName
$sourceTools = Join-Path $packageDir ".tools"
$sourceSyncServer = Join-Path $packageDir "sync_server"
$sourceQrServerBat = Join-Path $packageDir "start_qr_sync_server.bat"
$sourceInstaller = Join-Path $packageDir "installer"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$installedExe = Join-Path $installDir $exeName

if (-not (Test-Path $sourceExe)) {
    throw "Programfil mangler i pakken: $sourceExe"
}

Write-Host "Installerer $appName..."
Write-Host "Fra: $packageDir"
Write-Host "Til:  $installDir"

New-Item -ItemType Directory -Force -Path $installDir | Out-Null

Get-Process | Where-Object {
    $_.Path -and ($_.Path -ieq $installedExe)
} | ForEach-Object {
    Write-Host "Lukker koerende program: $($_.Id)"
    Stop-Process -Id $_.Id -Force
}

Copy-Item -Force $sourceExe $installedExe

if (Test-Path $sourceTools) {
    $targetTools = Join-Path $installDir ".tools"
    if (Test-Path $targetTools) {
        Remove-Item -LiteralPath $targetTools -Recurse -Force
    }
    Copy-Item -Recurse -Force $sourceTools $targetTools
}

if (Test-Path $sourceSyncServer) {
    $targetSyncServer = Join-Path $installDir "sync_server"
    if (Test-Path $targetSyncServer) {
        Remove-Item -LiteralPath $targetSyncServer -Recurse -Force
    }
    Copy-Item -Recurse -Force $sourceSyncServer $targetSyncServer
}

if (Test-Path $sourceQrServerBat) {
    Copy-Item -Force $sourceQrServerBat (Join-Path $installDir "start_qr_sync_server.bat")
}

if (Test-Path $sourceInstaller) {
    $targetInstaller = Join-Path $installDir "installer"
    if (Test-Path $targetInstaller) {
        Remove-Item -LiteralPath $targetInstaller -Recurse -Force
    }
    Copy-Item -Recurse -Force $sourceInstaller $targetInstaller
}

$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) $appName
$startMenuShortcut = Join-Path $startMenuDir "$appName.lnk"
New-Item -ItemType Directory -Force -Path $startMenuDir | Out-Null

New-Shortcut -ShortcutPath $desktopShortcut -TargetPath $installedExe -WorkingDirectory $installDir -Description $appName
New-Shortcut -ShortcutPath $startMenuShortcut -TargetPath $installedExe -WorkingDirectory $installDir -Description $appName

if ($Autostart) {
    $startupShortcut = Join-Path ([Environment]::GetFolderPath("Startup")) "$appName.lnk"
    New-Shortcut -ShortcutPath $startupShortcut -TargetPath $installedExe -WorkingDirectory $installDir -Description $appName
}

Write-Host ""
Write-Host "Faerdig."
Write-Host "Installeret EXE: $installedExe"
Write-Host "Skrivebordsgenvej: $desktopShortcut"
