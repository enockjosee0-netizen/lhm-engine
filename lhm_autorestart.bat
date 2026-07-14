@echo off
:loop
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *deepseek_python_20260707_a6bd19*" 2>NUL | find /I /N "python.exe" | find /I /N "deepseek" >NUL
if %ERRORLEVEL% EQU 0 (
    echo [LHM] Engine already running, waiting...
    timeout /t 30 /nobreak >nul
    goto loop
)
echo [LHM] Starting engine...
"C:\Users\enock\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py" --dry-run
echo [LHM] Engine exited with error %ERRORLEVEL%. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
