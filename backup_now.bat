@echo off
setlocal
set SOURCE=C:\Users\enock\Downloads
set BACKUP=C:\Users\enock\Downloads\backup_recovery
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

echo [BACKUP] Starting backup at %TIMESTAMP%...

if not exist "%BACKUP%" mkdir "%BACKUP%"

xcopy "%SOURCE%\deepseek_python_20260707_a6bd19.py" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\.env" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\requirements_deploy.txt" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\Procfile" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\.gitignore" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\run_engine.bat" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\engine_autostart.bat" "%BACKUP%\" /Y /Q >nul
xcopy "%SOURCE%\run_betpawa_scraper.py" "%BACKUP%\" /Y /Q >nul 2>nul
xcopy "%SOURCE%\run_betika_scraper.py" "%BACKUP%\" /Y /Q >nul 2>nul
xcopy "%SOURCE%\setup_data_sources.py" "%BACKUP%\" /Y /Q >nul 2>nul

if exist "C:\Users\enock\Downloads\*.db" (
    xcopy "C:\Users\enock\Downloads\*.db" "%BACKUP%\" /Y /Q >nul 2>nul
)

echo [BACKUP] Complete. Files backed up to %BACKUP%
endlocal
