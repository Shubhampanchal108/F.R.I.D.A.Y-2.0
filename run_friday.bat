@echo off
title F.R.I.D.A.Y 2.0 // Universal Neural Launcher
color 0b

:: Resolve Friday Project Directory
set "FRIDAY_DIR=c:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y"
if not exist "%FRIDAY_DIR%" (
    set "FRIDAY_DIR=%~dp0"
)

cd /d "%FRIDAY_DIR%"

:: Locate Python executable
set "PYTHONW_BIN=%FRIDAY_DIR%\.venv\Scripts\pythonw.exe"
set "PYTHON_BIN=%FRIDAY_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHONW_BIN%" (
    set "PYTHONW_BIN=pythonw.exe"
    set "PYTHON_BIN=python.exe"
)

:: Check CLI flag
if "%~1"=="--cli" (
    echo [F.R.I.D.A.Y] Starting in Interactive Terminal Mode...
    "%PYTHON_BIN%" index.py
    pause
    exit /b
)

:: Default: Launch Floating Corner Widget HUD
echo =========================================================================
echo      ⚡ F.R.I.D.A.Y 2.0 -- AI Super-Agent Launcher
echo =========================================================================
echo   Starting Floating Corner Widget & Neural HUD...
echo   Shortcut: Press Ctrl + Space anywhere on Windows to toggle HUD.
echo =========================================================================
start "" "%PYTHONW_BIN%" friday_widget.py
timeout /t 2 /nobreak >nul
exit
