<# :
@echo off
setlocal
title AgOpenGPS Fence Planner Online Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression ([System.IO.File]::ReadAllText('%~f0'))"
if errorlevel 1 (
    echo.
    echo Installationen fejlede.
    pause
    exit /b 1
)
echo.
echo Faerdig. AgOpenGPS Fence Planner er installeret.
pause
exit /b 0
#>

$ErrorActionPreference = "Stop"

$PackageUrl = "https://github.com/bjarkedrew/FencePlanner/releases/latest/download/AgOpenGPS_FencePlanner_package.zip"
$AppName = "AgOpenGPS Fence Planner"
$work = Join-Path $env:TEMP ("FencePlannerSetup_" + [guid]::NewGuid().ToString("N"))
$zip = Join-Path $work "package.zip"
$extract = Join-Path $work "package"

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host "== $Text =="
}

New-Item -ItemType Directory -Force -Path $work | Out-Null

try {
    Write-Host "$AppName - online installation"
    Write-Host "Downloader nyeste version fra GitHub."

    Write-Step "Henter installationspakke"
    Write-Host $PackageUrl
    Invoke-WebRequest -Uri $PackageUrl -OutFile $zip

    Write-Step "Pakker ud"
    Expand-Archive -Path $zip -DestinationPath $extract -Force

    $installScript = Get-ChildItem -Path $extract -Recurse -Filter install_release.ps1 | Select-Object -First 1
    if (-not $installScript) {
        throw "install_release.ps1 blev ikke fundet i pakken."
    }

    Write-Step "Installerer programmet"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installScript.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Installationen fejlede med exitkode $LASTEXITCODE."
    }

    Write-Step "Installation fuldfoert"
}
finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
