# Stahne prenosny Python 3.12 pro Windows (64-bit) do .\python\
# Funguje bez admin prav a bez systemove instalace Pythonu.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$PyDir = Join-Path (Get-Location) "python"
$PyExe = Join-Path $PyDir "python.exe"
$Version = "3.12.7"
$Url = "https://www.python.org/ftp/python/$Version/python-$Version-embed-amd64.zip"
$GetPip = "https://bootstrap.pypa.io/get-pip.py"
$Zip = Join-Path $env:TEMP "python-embed-$Version.zip"

Write-Host "=== CYPHERpc: stahuji Python $Version (portable) ===" -ForegroundColor Cyan

if (Test-Path $PyExe) {
    Write-Host "Python uz je: $PyExe"
    & $PyExe --version
    exit 0
}

New-Item -ItemType Directory -Force -Path $PyDir | Out-Null

Write-Host "Downloading $Url ..."
Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing

Write-Host "Rozbaluji do $PyDir ..."
Expand-Archive -Path $Zip -DestinationPath $PyDir -Force
Remove-Item $Zip -Force -ErrorAction SilentlyContinue

# Embeddable Python: povolit site-packages (odkomentovat import site v ._pth)
$Pth = Get-ChildItem -Path $PyDir -Filter "python*._pth" | Select-Object -First 1
if ($Pth) {
    $content = Get-Content $Pth.FullName
    $content = $content | ForEach-Object {
        if ($_ -match '^#\s*import\s+site') { 'import site' }
        else { $_ }
    }
    if ($content -notcontains 'import site') { $content += 'import site' }
    # Pridej Lib\site-packages cestu
    if ($content -notcontains '.\Lib\site-packages') { $content += '.\Lib\site-packages' }
    Set-Content -Path $Pth.FullName -Value $content
}

# get-pip
Write-Host "Instaluji pip..."
$GetPipPath = Join-Path $env:TEMP "get-pip.py"
Invoke-WebRequest -Uri $GetPip -OutFile $GetPipPath -UseBasicParsing
& $PyExe $GetPipPath --no-warn-script-location
Remove-Item $GetPipPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "OK: $PyExe" -ForegroundColor Green
& $PyExe --version
Write-Host "Dale: .\scripts\full_setup.ps1"
