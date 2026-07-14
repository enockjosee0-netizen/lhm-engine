@echo off
setlocal enabledelayedexpansion

:check_lock
if exist "C:\Users\enock\Downloads\lhm.lock" (
    set /p OLDPID=<"C:\Users\enock\Downloads\lhm.lock"
    if defined OLDPID (
        tasklist /FI "PID eq %OLDPID%" 2>NUL | find /I /N "python.exe" >NUL
        if %ERRORLEVEL% EQU 0 (
            echo [LHM] Instance %OLDPID% already running, waiting...
            timeout /t 30 /nobreak >nul
            goto check_lock
        )
    )
)

:loop
echo [LHM] Starting engine...
"C:\Users\enock\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py" --dry-run
echo [LHM] Engine exited. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
