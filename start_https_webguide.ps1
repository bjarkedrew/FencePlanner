$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$tools = Join-Path $projectDir ".tools"
$nodeHome = Join-Path $tools "node-v22.22.3-win-x64"
$npx = Join-Path $nodeHome "npx.cmd"
$outLog = Join-Path $tools "localtunnel-webguide.log"
$errLog = Join-Path $tools "localtunnel-webguide.err.log"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcut = Join-Path $desktop "Fence Webguide.url"

if (-not (Test-Path $npx)) {
    throw "Node/npm blev ikke fundet i $nodeHome. Koer setup/build en gang foerst."
}

function Test-LocalWebguide {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8765/guide.json" -UseBasicParsing -TimeoutSec 5
        return ($response.StatusCode -eq 200 -and $response.Content.Contains('"FenceGuide"'))
    } catch {
        return $false
    }
}

function Read-TunnelUrl {
    $text = ""
    if (Test-Path $outLog) { $text += Get-Content $outLog -Raw -ErrorAction SilentlyContinue }
    if (Test-Path $errLog) { $text += Get-Content $errLog -Raw -ErrorAction SilentlyContinue }
    $matches = [regex]::Matches($text, "https://[a-zA-Z0-9-]+\.loca\.lt")
    if ($matches.Count -eq 0) { return $null }
    return $matches[$matches.Count - 1].Value
}

function Test-WebguideUrl {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri "$Url/guide.json" -UseBasicParsing -TimeoutSec 15
        return ($response.StatusCode -eq 200 -and $response.Content.Contains('"FenceGuide"'))
    } catch {
        return $false
    }
}

Get-Process node -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "$nodeHome*" } |
    Stop-Process -Force

if (-not (Test-LocalWebguide)) {
    throw "Fence Planner webguide koerer ikke. Aabn Fence Planner, vaelg/generer marken, og tryk 'Start traadloes sync' foerst."
}

Remove-Item -LiteralPath $outLog, $errLog -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Starter klikbart HTTPS-link til Fence Webguide..."
Write-Host "Husk: Start traadloes sync i Fence Planner foerst."
Write-Host ""

$env:PATH = "$nodeHome;$env:PATH"
$process = Start-Process -FilePath $npx `
    -ArgumentList @("localtunnel", "--port", "8765") `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

$url = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    if ($process.HasExited) { break }
    $candidate = Read-TunnelUrl
    if (-not $candidate) { continue }
    Write-Host "Tester link: $candidate"
    if (Test-WebguideUrl $candidate) {
        $url = $candidate
        break
    }
}

if (-not $url) {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
    $details = ""
    if (Test-Path $outLog) { $details += Get-Content $outLog -Raw -ErrorAction SilentlyContinue }
    if (Test-Path $errLog) { $details += Get-Content $errLog -Raw -ErrorAction SilentlyContinue }
    throw "Kunne ikke lave et virkende HTTPS-link.`n$details"
}

Set-Clipboard -Value $url
Set-Content -Path $shortcut -Encoding ASCII -Value @"
[InternetShortcut]
URL=$url
"@

Write-Host ""
Write-Host "Klar:"
Write-Host ""
Write-Host $url
Write-Host ""
Write-Host "Linket er kopieret til udklipsholderen."
Write-Host "Der er lavet en klikbar genvej paa skrivebordet: Fence Webguide.url"
Write-Host ""
Write-Host "Aabn linket paa mobilen og tryk GPS."
Write-Host "Luk ikke dette vindue mens du bruger webguiden."
Write-Host ""

try {
    Start-Process $url
} catch {
    Write-Host "Kunne ikke aabne browseren automatisk."
}

while (-not $process.HasExited) {
    Start-Sleep -Seconds 2
}
