@echo off
cd /d "%~dp0\.."
echo === Building CYPHERpc.exe ===
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt
pip install pyinstaller
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
pyinstaller cypherpc.spec --noconfirm
if exist dist\CYPHERpc.exe (
  echo.
  echo OK: dist\CYPHERpc.exe
  copy /Y .env.example dist\.env.example >nul
  copy /Y START_HERE.md dist\START_HERE.md >nul 2>nul
) else (
  echo BUILD FAILED
  exit /b 1
)
pause
