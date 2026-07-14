@echo off
:loop
echo Starting LHM Engine...
"C:\Users\enock\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py" --dry-run
echo Engine stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
