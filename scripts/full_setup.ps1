# Kompletni setup CYPHERpc na Windows:
# 1) stahne Python pokud chybi
# 2) nainstaluje zavislosti
# 3) vytvori .env
# 4) smoke test
# 5) volitelne sestavi CYPHERpc.exe

param(
    [switch]$BuildExe
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

function Get-CypherPython {
    $portable = Join-Path (Get-Location) "python\python.exe"
    if (Test-Path $portable) { return $portable }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command py -ErrorAction SilentlyContinue
    if ($cmd) { return "py" }
    return $null
}

Write-Host "=== CYPHERpc full setup ===" -ForegroundColor Cyan

$Py = Get-CypherPython
if (-not $Py) {
    Write-Host "Python nenalezen – stahuji portable..."
    & "$PSScriptRoot\download_python.ps1"
    $Py = Join-Path (Get-Location) "python\python.exe"
}

if (-not (Test-Path $Py) -and $Py -ne "py") {
    Write-Host "Nepodarilo se ziskat Python." -ForegroundColor Red
    exit 1
}

Write-Host "Python: $Py"
& $Py --version

# venv (u embeddable muze selhat – pak instaluj primo)
$UseVenv = $true
if ($Py -like "*\python\python.exe") {
    # portable embeddable – bez venv, pip primo
    $UseVenv = $false
    $Pip = & $Py -m pip --version 2>$null
    Write-Host "Portable Python – instalace do lokalniho python\"
}

if ($UseVenv) {
    if (-not (Test-Path .venv)) {
        Write-Host "Vytvarim .venv..."
        & $Py -m venv .venv
    }
    $Py = (Resolve-Path .\.venv\Scripts\python.exe).Path
    $PipCmd = @($Py, "-m", "pip")
} else {
    $PipCmd = @($Py, "-m", "pip")
}

Write-Host "Instaluji zavislosti..."
& $PipCmd[0] $PipCmd[1] $PipCmd[2] install -U pip
& $PipCmd[0] $PipCmd[1] $PipCmd[2] install -r requirements.txt
& $PipCmd[0] $PipCmd[1] $PipCmd[2] install edge-tts pygame pyinstaller 2>$null

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Vytvoren .env – dopln API klic az budes chtit." -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path data, logs | Out-Null

Write-Host "Smoke test..."
& $Py scripts\smoke_test.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Smoke test selhal – zkontroluj chyby vyse." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setup OK. Spusteni:" -ForegroundColor Green
Write-Host "  & '$Py' -m src.main"
Write-Host "  & '$Py' -m src.main --gui"

if ($BuildExe) {
    Write-Host ""
    Write-Host "Sestavuji CYPHERpc.exe..."
    & $PipCmd[0] $PipCmd[1] $PipCmd[2] install pyinstaller
    if (Test-Path dist) { Remove-Item -Recurse -Force dist }
    if (Test-Path build) { Remove-Item -Recurse -Force build }
    & $Py -m PyInstaller cypherpc.spec --noconfirm
    if (Test-Path "dist\CYPHERpc.exe") {
        Copy-Item .env.example dist\.env.example -Force
        if (Test-Path .env) { Copy-Item .env dist\.env -Force }
        Write-Host "EXE: dist\CYPHERpc.exe" -ForegroundColor Green
    } else {
        Write-Host "EXE build selhal." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Chces exe? Spust: .\scripts\full_setup.ps1 -BuildExe"
}
