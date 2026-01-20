@echo off
title Android Wireless ADB Connector

REM ================================
REM Get IP Address from Argument
REM ================================
set DEVICE_IP=%1

if "%DEVICE_IP%"=="" (
    echo ERROR: IP Address not provided!
    exit /b
)

REM ================================
REM ADB Port
REM ================================
set ADB_PORT=5555
set ADB_PATH=adb

echo Device IP: %DEVICE_IP%

REM ================================
REM Restart ADB Server
REM ================================
echo Restarting ADB Server...
%ADB_PATH% kill-server
%ADB_PATH% start-server

REM ================================
REM Enable TCPIP Mode
REM ================================
echo Switching device to TCPIP mode...
%ADB_PATH% tcpip %ADB_PORT%

echo Waiting for device...
timeout /t 3 >nul

REM ================================
REM Disconnect old connections
REM ================================
echo Disconnecting old connections...
%ADB_PATH% disconnect

REM ================================
REM Connect Device
REM ================================
echo Connecting to device %DEVICE_IP%:%ADB_PORT% ...
%ADB_PATH% connect %DEVICE_IP%:%ADB_PORT%

echo DONE!
