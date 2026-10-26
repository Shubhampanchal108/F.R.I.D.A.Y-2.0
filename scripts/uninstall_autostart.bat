@echo off
title F.R.I.D.A.Y 2.0 // Auto-Start Uninstaller
color 0c

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_TARGET=%STARTUP_FOLDER%\FRIDAY_AutoStart.vbs"

echo =========================================================================
echo       ⚡ F.R.I.D.A.Y 2.0 -- REMOVE AUTO-START
echo =========================================================================
echo.

if exist "%VBS_TARGET%" (
    del /f /q "%VBS_TARGET%"
    echo [OK] Auto-Start file removed successfully from Startup folder:
    echo      "%VBS_TARGET%"
    echo.
    echo Friday will no longer start automatically when Windows boots.
) else (
    echo [INFO] Auto-Start was not installed or already removed.
)

echo.
pause
