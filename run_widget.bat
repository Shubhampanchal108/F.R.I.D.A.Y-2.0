@echo off
title F.R.I.D.A.Y 2.0 // Neural Widget Launcher
cd /d "%~dp0"
echo Starting F.R.I.D.A.Y Floating Corner Widget...
echo Shortcut: Press Ctrl + Space anywhere on Windows to toggle.
start "" ".\.venv\Scripts\pythonw.exe" friday_widget.py
exit
