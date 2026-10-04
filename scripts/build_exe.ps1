# Build CYPHERpc.exe (Windows)
# Requires: Python venv with dependencies already installed

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== Building CYPHERpc.exe ===" -ForegroundColor Cyan

if (-not (Test-Path .venv)) {
    Write-Host "Creating venv..."
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

Write-Host "Installing/updating deps + PyInstaller..."
pip install -U pip
pip install -r requirements.txt
pip install pyinstaller

# Clean previous build
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

Write-Host "Running PyInstaller..."
pyinstaller cypherpc.spec --noconfirm

if (Test-Path "dist\CYPHERpc.exe") {
    Write-Host ""
    Write-Host "OK: dist\CYPHERpc.exe" -ForegroundColor Green
    Write-Host "Zkopiruj vedle exe soubor .env (z .env.example) a spust CYPHERpc.exe"
    Write-Host ""
    # Copy helper files next to exe
    if (-not (Test-Path "dist\.env.example")) {
        Copy-Item .env.example dist\.env.example -ErrorAction SilentlyContinue
    }
    Copy-Item START_HERE.md dist\START_HERE.md -ErrorAction SilentlyContinue
} else {
    Write-Host "Build failed – zkontroluj vystup PyInstaller." -ForegroundColor Red
    exit 1
}
