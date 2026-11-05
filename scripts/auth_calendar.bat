@echo off
cd /d "%~dp0\.."
echo Launching Google Calendar Authorization for F.R.I.D.A.Y...
.\.venv\Scripts\python.exe scripts\auth_calendar.py
pause

