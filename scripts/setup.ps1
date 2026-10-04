# CYPHERpc setup for Windows (PowerShell)
Write-Host "=== CYPHERpc setup ===" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .venv)) {
    Write-Host "Creating venv..."
    python -m venv .venv
}

Write-Host "Activating venv..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
pip install -U pip
pip install -r requirements.txt
pip install edge-tts pygame 2>$null

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env — fill in API keys!" -ForegroundColor Yellow
}

New-Item -ItemType Directory -Force -Path data, logs | Out-Null

Write-Host ""
Write-Host "Done. Next:" -ForegroundColor Green
Write-Host "  1. Edit .env (OPENAI_API_KEY or XAI_API_KEY or ANTHROPIC_API_KEY)"
Write-Host "  2. .\.venv\Scripts\Activate.ps1"
Write-Host "  3. python -m src.main"
Write-Host "  4. python -m src.main --gui"
Write-Host ""
Write-Host "Voice: /voice  then  /persona grok_cs"
