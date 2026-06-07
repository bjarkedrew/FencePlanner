param(
    [string]$PackageUrl = "",
    [switch]$Autostart
)

$ErrorActionPreference = "Stop"

if (-not $PackageUrl) {
    $PackageUrl = $env:FENCE_PLANNER_PACKAGE_URL
}

if (-not $PackageUrl) {
    throw "Mangler PackageUrl. Koer fx: powershell -ExecutionPolicy Bypass -File FencePlanner_Setup.ps1 -PackageUrl 'https://.../AgOpenGPS_FencePlanner_package.zip'"
}

$work = Join-Path $env:TEMP ("FencePlannerSetup_" + [guid]::NewGuid().ToString("N"))
$zip = Join-Path $work "package.zip"
$extract = Join-Path $work "package"

New-Item -ItemType Directory -Force -Path $work | Out-Null

try {
    Write-Host "Henter AgOpenGPS Fence Planner..."
    Write-Host $PackageUrl
    Invoke-WebRequest -Uri $PackageUrl -OutFile $zip

    Write-Host "Pakker ud..."
    Expand-Archive -Path $zip -DestinationPath $extract -Force

    $installScript = Get-ChildItem -Path $extract -Recurse -Filter install_release.ps1 | Select-Object -First 1
    if (-not $installScript) {
        throw "install_release.ps1 blev ikke fundet i pakken."
    }

    Write-Host "Installerer..."
    $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $installScript.FullName)
    if ($Autostart) {
        $args += "-Autostart"
    }
    & powershell.exe @args
    if ($LASTEXITCODE -ne 0) {
        throw "Installationen fejlede med exitkode $LASTEXITCODE."
    }
}
finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
