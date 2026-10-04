@echo off
cd /d "%~dp0\.."
echo === CYPHERpc full setup ===
powershell -ExecutionPolicy Bypass -File "%~dp0full_setup.ps1" %*
if errorlevel 1 pause
