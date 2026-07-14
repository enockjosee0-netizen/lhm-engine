@echo off
setlocal
set SOURCE=C:\Users\enock\Downloads
set DEST=C:\Users\enock\Downloads\lhm_recovery_package
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%

echo Creating LHM Recovery Package...
if exist "%DEST%" rmdir /S /Q "%DEST%"
mkdir "%DEST%"
mkdir "%DEST%\engine"
mkdir "%DEST%\integrations"
mkdir "%DEST%\config"

xcopy "%SOURCE%\deepseek_python_20260707_a6bd19.py" "%DEST%\engine\" /Y /Q >nul
xcopy "%SOURCE%\.env" "%DEST%\config\" /Y /Q >nul
xcopy "%SOURCE%\requirements_deploy.txt" "%DEST%\config\" /Y /Q >nul
xcopy "%SOURCE%\Procfile" "%DEST%\config\" /Y /Q >nul
xcopy "%SOURCE%\.gitignore" "%DEST%\config\" /Y /Q >nul
xcopy "%SOURCE%\run_engine.bat" "%DEST%\engine\" /Y /Q >nul
xcopy "%SOURCE%\engine_autostart.bat" "%DEST%\engine\" /Y /Q >nul
xcopy "%SOURCE%\backup_now.bat" "%DEST%\engine\" /Y /Q >nul
xcopy "%SOURCE%\run_betpawa_scraper.py" "%DEST%\engine\" /Y /Q >nul 2>nul
xcopy "%SOURCE%\run_betika_scraper.py" "%DEST%\engine\" /Y /Q >nul 2>nul
xcopy "%SOURCE%\setup_data_sources.py" "%DEST%\engine\" /Y /Q >nul 2>nul

xcopy "C:\Users\enock\AppData\Local\Programs\Microsoft VS Code\integrations\odds-scraper\*.*" "%DEST%\integrations\odds-scraper\" /E /I /Y /Q >nul 2>nul
xcopy "C:\Users\enock\AppData\Local\Programs\Microsoft VS Code\integrations\betpawa-web-scraper\*.*" "%DEST%\integrations\betpawa-web-scraper\" /E /I /Y /Q >nul 2>nul
xcopy "C:\Users\enock\AppData\Local\Programs\Microsoft VS Code\integrations\smartBetika\*.*" "%DEST%\integrations\smartBetika\" /E /I /Y /Q >nul 2>nul

if exist "C:\Users\enock\Downloads\*.db" (
    xcopy "C:\Users\enock\Downloads\*.db" "%DEST%\config\" /Y /Q >nul 2>nul
)

echo.
echo =============================================
echo   LHM RECOVERY PACKAGE CREATED
echo =============================================
echo.
echo Location: %DEST%
echo.
echo BACKUP THIS FOLDER TO:
echo   1. USB drive
echo   2. Google Drive / OneDrive
echo   3. Email to yourself
echo   4. Any cloud storage
echo.
echo If laptop is lost, just copy this folder
echo to a new PC and run: engine\run_engine.bat
echo =============================================
echo.
pause
