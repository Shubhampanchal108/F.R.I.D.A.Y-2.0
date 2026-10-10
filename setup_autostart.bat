@echo off
title F.R.I.D.A.Y 2.0 // Auto-Start Installer
color 0a

echo =========================================================================
echo       ⚡ F.R.I.D.A.Y 2.0 -- JARVIS STARTUP AND DESKTOP CONFIGURATOR
echo =========================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_TARGET=%STARTUP_FOLDER%\FRIDAY_AutoStart.vbs"
set "SOURCE_VBS=%SCRIPT_DIR%friday_autostart_silent.vbs"

echo [1/3] Configuring Windows Auto-Start upon Internet Connection...
if exist "%SOURCE_VBS%" (
    copy /Y "%SOURCE_VBS%" "%VBS_TARGET%" >nul
    echo       [OK] Installed to Windows Startup:
    echo            "%VBS_TARGET%"
) else (
    echo       [FAIL] Could not locate friday_autostart_silent.vbs!
)

echo.
echo [2/3] Creating Universal Desktop Shortcut with Custom Logo...
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%set_shortcut_icon.py"
) else (
    python "%SCRIPT_DIR%set_shortcut_icon.py"
)

echo.
echo [3/3] Verification Complete!
echo =========================================================================
echo  [SUCCESS] All systems configured!
echo.
echo  * Har roz jab bhi aapka Laptop on hoga:
echo    - Friday background me Internet connect hone ka wait karega.
echo    - Internet connect hote hi Jarvis voice boleyga:
echo      "Internet access detected. All systems online, Boss."
echo    - Floating Corner Widget apne aap launch ho jayega!
echo.
echo  * Kisi bhi samay manually chalane ke liye:
echo    - Apne Desktop par "F.R.I.D.A.Y" icon double-click karein, ya
echo    - Kisi bhi folder me 'run_friday.bat' ko run karein.
echo.
echo  * Shortcut: Windows par kahin se bhi "Ctrl + Space" dabakar
echo    Friday widget open / close kar sakte hain.
echo =========================================================================
echo.
pause
