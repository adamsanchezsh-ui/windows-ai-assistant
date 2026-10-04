# Build CYPHERpc.exe – nejdrive zajisti Python (portable pokud treba)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "=== Building CYPHERpc.exe ===" -ForegroundColor Cyan

# Reuse full setup with -BuildExe
& "$PSScriptRoot\full_setup.ps1" -BuildExe
