param(
    [switch]$Autostart
)

$ErrorActionPreference = "Stop"

function Get-PythonLauncher {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @("py", "-3")
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @("python")
    }

    throw "Python blev ikke fundet. Installer Python 3 fra python.org eller Microsoft Store og koer install_program.bat igen."
}

function Invoke-Tool {
    param(
        [string[]]$Command,
        [string]$WorkingDirectory
    )

    $exe = $Command[0]
    $args = @()
    if ($Command.Count -gt 1) {
        $args = $Command[1..($Command.Count - 1)]
    }

    Push-Location $WorkingDirectory
    try {
        & $exe @args
        if ($LASTEXITCODE -ne 0) {
            throw "'$exe $($args -join ' ')' fejlede med exitkode $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

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
$projectDir = Split-Path -Parent $scriptDir
$venvDir = Join-Path $projectDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$appName = "AgOpenGPS Fence Planner"
$exeName = "$appName.exe"
$installDir = Join-Path $env:LOCALAPPDATA "Programs\$appName"
$installedExe = Join-Path $installDir $exeName

Write-Host "AgOpenGPS Fence Planner - installation"
Write-Host "Projekt: $projectDir"

if (-not (Test-Path $venvPython)) {
    Write-Host "Opretter Python-miljoe..."
    $launcher = Get-PythonLauncher
    Invoke-Tool -Command ($launcher + @("-m", "venv", $venvDir)) -WorkingDirectory $projectDir
}

Write-Host "Installerer Python-pakker..."
Invoke-Tool -Command @($venvPython, "-m", "pip", "install", "--upgrade", "pip") -WorkingDirectory $projectDir
Invoke-Tool -Command @($venvPython, "-m", "pip", "install", "-r", "requirements.txt", "pyinstaller") -WorkingDirectory $projectDir

Write-Host "Bygger Windows EXE..."
Invoke-Tool -Command @(
    $venvPython,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--icon",
    "assets\app_icon.ico",
    "--add-data",
    "assets\app_icon.ico;assets",
    "--name",
    $appName,
    "main.py"
) -WorkingDirectory $projectDir

$builtExe = Join-Path $projectDir "dist\$exeName"
if (-not (Test-Path $builtExe)) {
    throw "EXE blev ikke fundet efter build: $builtExe"
}

Write-Host "Installerer programmet i $installDir..."
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Get-Process | Where-Object {
    $_.Path -and ($_.Path -ieq $installedExe)
} | ForEach-Object {
    Write-Host "Lukker koerende program: $($_.Id)"
    Stop-Process -Id $_.Id -Force
}
Copy-Item -Force $builtExe $installedExe

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
Write-Host "Start-menu: $startMenuShortcut"
