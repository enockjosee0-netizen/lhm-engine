@echo off
REM LHM Ghost Protocol + Engine Persistent Launcher
REM This starts both the hardware HID layer and the main engine
REM Survives reboots when placed in Startup folder

echo ============================================================
echo LHM Ghost Protocol + Engine Launcher
echo ============================================================
echo.

REM Wait for system to stabilize
timeout /t 10 /nobreak >nul

REM Start Ghost Protocol HID layer
echo [1/2] Starting Ghost Protocol HID Layer...
start /B "" pythonw.exe "%~dp0ghost_protocol_service.py"
timeout /t 5 /nobreak >nul

REM Start Main LHM Engine
echo [2/2] Starting LHM Engine...
start /B "" pythonw.exe "%~dp0deepseek_python_20260707_a6bd19.py"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo Both services started
echo Ghost Protocol: Hardware HID active
echo LHM Engine: Running in background
echo ============================================================

REM Keep window open briefly to show status
timeout /t 5 /nobreak >nul
