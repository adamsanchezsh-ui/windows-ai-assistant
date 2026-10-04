# Stahne prenosny Python pro Windows (64-bit) do .\python\
# Oficiální odkazy:
#   Instalátor: https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
#   Embeddable: https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip
#   Přehled:    https://www.python.org/downloads/

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$PyDir = Join-Path (Get-Location) "python"
$PyExe = Join-Path $PyDir "python.exe"
$Version = "3.12.7"
$Url = "https://www.python.org/ftp/python/$Version/python-$Version-embed-amd64.zip"
$GetPip = "https://bootstrap.pypa.io/get-pip.py"
$Zip = Join-Path $env:TEMP "python-embed-$Version.zip"

Write-Host "=== CYPHERpc: stahuji Python $Version (portable) ===" -ForegroundColor Cyan
Write-Host "Zdroj: $Url"

if (Test-Path $PyExe) {
    Write-Host "Python uz je: $PyExe"
    & $PyExe --version
    exit 0
}

New-Item -ItemType Directory -Force -Path $PyDir | Out-Null

try {
    Write-Host "Downloading..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $Zip -UseBasicParsing
} catch {
    Write-Host "Download selhal: $_" -ForegroundColor Red
    Write-Host "Stahni rucne:"
    Write-Host "  $Url"
    Write-Host "Nebo plny installer:"
    Write-Host "  https://www.python.org/ftp/python/$Version/python-$Version-amd64.exe"
    exit 1
}

Write-Host "Rozbaluji do $PyDir ..."
Expand-Archive -Path $Zip -DestinationPath $PyDir -Force
Remove-Item $Zip -Force -ErrorAction SilentlyContinue

$Pth = Get-ChildItem -Path $PyDir -Filter "python*._pth" | Select-Object -First 1
if ($Pth) {
    $lines = Get-Content $Pth.FullName
    $out = @()
    foreach ($line in $lines) {
        if ($line -match '^#\s*import\s+site') { $out += 'import site' }
        else { $out += $line }
    }
    if ($out -notcontains 'import site') { $out += 'import site' }
    if ($out -notcontains '.\Lib\site-packages') { $out += '.\Lib\site-packages' }
    Set-Content -Path $Pth.FullName -Value $out
}

Write-Host "Instaluji pip..."
$GetPipPath = Join-Path $env:TEMP "get-pip.py"
Invoke-WebRequest -Uri $GetPip -OutFile $GetPipPath -UseBasicParsing
& $PyExe $GetPipPath --no-warn-script-location
Remove-Item $GetPipPath -Force -ErrorAction SilentlyContinue

if (-not (Test-Path $PyExe)) {
    Write-Host "python.exe nenalezen v $PyDir" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "OK: $PyExe" -ForegroundColor Green
& $PyExe --version
