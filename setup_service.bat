@echo off
chcp 65001 >nul
title LHM Engine - 24/7 Hosting Setup
echo ========================================
echo LHM Engine - 24/7 Hosting Setup
echo ========================================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
) else (
    echo [WARNING] Not running as Administrator
    echo Some hosting options may require admin privileges
    echo.
)

:: Check Python
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Python found
    python --version
) else (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installing Windows Service (nssm)
echo ========================================
echo.

:: Download nssm if not present
if not exist "C:\nssm.exe" (
    echo Downloading nssm...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"
    copy "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" "C:\nssm.exe"
    echo [OK] nssm installed to C:\nssm.exe
) else (
    echo [OK] nssm already installed
)

echo.
echo ========================================
echo Setting up LHM Engine Service
echo ========================================
echo.

:: Set variables
set PYTHON_EXE=%ProgramFiles%\Python312\python.exe
set SERVICE_NAME=LHMEngine
set DISPLAY_NAME=LHM Betting Engine
set WORK_DIR=C:\Users\enock\Downloads
set SCRIPT_PATH=C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py

:: Check if Python 3.12 exists
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

:: Install service
echo Installing service: %SERVICE_NAME%
"C:\nssm.exe" install %SERVICE_NAME% "%PYTHON_EXE%" "%SCRIPT_PATH%" --dry-run

:: Configure service
echo Configuring service...
"C:\nssm.exe" set %SERVICE_NAME% DisplayName "%DISPLAY_NAME%"
"C:\nssm.exe" set %SERVICE_NAME% Start SERVICE_AUTO_START
"C:\nssm.exe" set %SERVICE_NAME% AppRestartDelay 5000
"C:\nssm.exe" set %SERVICE_NAME% AppStdout "%WORK_DIR%\lhm_service.log"
"C:\nssm.exe" set %SERVICE_NAME% AppStderr "%WORK_DIR%\lhm_service_err.log"
"C:\nssm.exe" set %SERVICE_NAME% AppParameters "--dry-run"
"C:\nssm.exe" set %SERVICE_NAME% AppDirectory "%WORK_DIR%"
"C:\nssm.exe" set %SERVICE_NAME% OnFailure "restart" 5000
"C:\nssm.exe" set %SERVICE_NAME% OnFailure "restart" 10000
"C:\nssm.exe" set %SERVICE_NAME% OnFailure "restart" 30000
"C:\nssm.exe" set %SERVICE_NAME% OnFailure "none" 0

echo.
echo ========================================
echo Service installed successfully!
echo ========================================
echo.
echo To start the service:
echo   net start %SERVICE_NAME%
echo.
echo To stop the service:
echo   net stop %SERVICE_NAME%
echo.
echo To view logs:
echo   type "%WORK_DIR%\lhm_service.log"
echo.
echo To remove the service:
echo   "C:\nssm.exe" remove %SERVICE_NAME% confirm
echo.

pause
