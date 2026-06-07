param(
    [switch]$ConfirmPublic
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$git = "C:\Program Files\Git\cmd\git.exe"

Set-Location $repo

Write-Host "Bygger mobilsky til docs\mobile..."
@'
from planner.cloud_export import export_repo_mobile_cloud
from pathlib import Path

dst, count = export_repo_mobile_cloud(Path.cwd())
print(f"{count} hegnsplaner eksporteret til {dst}")
'@ | python -

if (-not $ConfirmPublic) {
    Write-Host ""
    Write-Host "Mobilsky er bygget lokalt, men IKKE uploadet."
    Write-Host "OBS: GitHub-repoet er offentligt. Mobilsky indeholder marknavne og GPS-koordinater."
    Write-Host "Hvis du vil uploade offentligt til GitHub Pages, koer:"
    Write-Host "powershell -ExecutionPolicy Bypass -File publish_mobile_cloud.ps1 -ConfirmPublic"
    exit 0
}

if (-not (Test-Path $git)) {
    throw "Git blev ikke fundet: $git"
}

& $git add docs/mobile
& $git -c user.name='Bjark' -c user.email='bjark@users.noreply.github.com' commit -m "Update mobile cloud data"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ingen nye mobilsky-aendringer at committe."
}
& $git push origin main

Write-Host ""
Write-Host "Mobilsky klar. Hvis GitHub Pages er slaaet til, ligger siden her:"
Write-Host "https://bjarkedrew.github.io/FencePlanner/mobile/"
