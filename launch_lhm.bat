@echo off
chcp 65001 >nul
title LHM Enhanced Engine Launcher
echo ========================================
echo LHM Enhanced Engine
echo ========================================
echo.
echo [1] Run engine in dry-run mode (safe)
echo [2] Run engine with stealth scraping
echo [3] Run prediction for specific match
echo [4] Test stealth scrapers
echo [5] Setup 24/7 hosting
echo [6] Exit
echo.
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto dry_run
if "%choice%"=="2" goto stealth
if "%choice%"=="3" goto predict
if "%choice%"=="4" goto test_scrapers
if "%choice%"=="5" goto hosting
if "%choice%"=="6" goto exit
goto end

:dry_run
echo.
echo Starting engine in dry-run mode...
cd /d "C:\Users\enock\Downloads"
python deepseek_python_20260707_a6bd19.py --dry-run
pause
goto end

:stealth
echo.
echo Starting engine with stealth scraping...
cd /d "C:\Users\enock\Downloads"
python deepseek_python_20260707_a6bd19.py --dry-run --use-free-scrapers
pause
goto end

:predict
echo.
set /p match="Enter match (e.g. France vs Spain): "
cd /d "C:\Users\enock\AppData\Local\Temp\kilo"
python predict_france_spain.py
pause
goto end

:test_scrapers
echo.
echo Testing stealth scrapers...
cd /d "C:\Users\enock\Downloads"
python -c "from stealth_scraper import BetPawaStealthScraper, BetikaStealthScraper; import asyncio; async def test(): bp=BetPawaStealthScraper(); await bp.initialize(); print('BetPawa:', len(await bp.fetch_odds()), 'odds'); await bp.close(); bk=BetikaStealthScraper(); await bk.initialize(); print('Betika:', len(await bk.fetch_odds()), 'odds'); await bk.close(); asyncio.run(test())"
pause
goto end

:hosting
echo.
echo Setting up 24/7 hosting...
cd /d "C:\Users\enock\Downloads"
python -c "from lhm_enhanced import HostingManager; from lhm_enhanced import SecureConfigManager; hm = HostingManager(SecureConfigManager()); print('Best free option:', hm.get_best_free_option()); hm.setup_local_service()"
pause
goto end

:exit
echo Exiting...
goto end

:end
