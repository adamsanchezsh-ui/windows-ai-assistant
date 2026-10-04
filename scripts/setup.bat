@echo off
cd /d "%~dp0\.."
echo === CYPHERpc setup ===
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt
pip install edge-tts pygame
if not exist .env copy .env.example .env
if not exist data mkdir data
if not exist logs mkdir logs
echo.
echo Done. Edit .env then: python -m src.main
pause
