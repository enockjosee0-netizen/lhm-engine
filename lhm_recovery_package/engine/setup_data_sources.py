#!/usr/bin/env python3
"""Setup data sources for the betting engine.
Run this to install scraper dependencies and configure free APIs.
"""
import os
import sys

def install_requirements():
    reqs = [
        "pyyaml>=6.0",
        "aiohttp",
        "selenium",
        "pandas",
        "beautifulsoup4",
        "lxml",
        "requests",
    ]
    print("Installing dependencies...")
    for pkg in reqs:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

    # Try installing the odds-scraper package
    scraper_dir = os.path.join(os.path.dirname(__file__), "integrations", "odds-scraper")
    if os.path.exists(scraper_dir):
        print("Installing odds-scraper package...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", scraper_dir])
        except subprocess.CalledProcessError:
            print("WARNING: odds-scraper install failed (likely needs bookieskit).")
            print("  You can still use the engine's built-in scrapers.")

def print_setup_guide():
    print("""
============================================================
  BETTING ENGINE - DATA SOURCE SETUP GUIDE
============================================================

Your engine now has MULTIPLE data sources built in:

1. THE ODDS API (https://the-odds-api.com/)
   - Free tier: 25 requests/day, NBA+MLB, US books
   - Sign up: https://the-odds-api.com/
   - Add key to Settings.odds_api_key or env var ODDS_API_KEY

2. ODDS-API.IO (https://odds-api.io/)
   - Free tier: 100 requests/hour, 265+ bookmakers, 12,000+ leagues
   - Sign up: https://odds-api.io/ (no credit card)
   - Add key to Settings.odds_api_io_key

3. API-FOOTBALL (https://www.api-football.com/)
   - Free tier: 100 requests/day, all competitions
   - Sign up: https://dashboard.api-football.com/register
   - Add key to Settings.api_football_key

4. BETPAWA SCRAPER (integrations/odds-scraper/)
   - Scrapes BetPawa, SportyBet, Bet9ja, Betway
   - Run: python run_betpawa_scraper.py
   - Data feeds into engine automatically via SQLite cache

5. BETIKA SCRAPER (integrations/smartBetika/)
   - Scrapes Betika odds
   - Run: python run_betika_scraper.py
   - Or run directly: cd integrations/smartBetika && pip install -e . && betika --normal --upcoming

6. FBREF FALLBACK (built-in)
   - No API key needed
   - Scrapes fbref.com for Premier League fixtures

HOW TO CONFIGURE API KEYS:
---------------------------
Option A - Edit the engine file directly:
   deepseek_python_20260707_a6bd19.py (Settings class)

Option B - Use environment variables:
   ODDS_API_KEY=your_key
   ODDS_API_IO_KEY=your_key
   API_FOOTBALL_KEY=your_key

Option C - Create a .env file in Downloads/:
   ODDS_API_KEY=your_key
   ODDS_API_IO_KEY=your_key
   API_FOOTBALL_KEY=your_key

HOW TO START BETTING:
---------------------
1. Get at least ONE free API key (OddsAPI.io recommended - no credit card)
2. Run the engine in dry-run mode:
   cd C:\\Users\\enock\\Downloads
   py -3.12 deepseek_python_20260707_a6bd19.py --dry-run

3. To run scrapers in background:
   python run_betpawa_scraper.py

4. When ready for real betting:
   - Add exchange/bookmaker credentials to Settings
   - Remove --dry-run flag
   - The engine will place bets via BookmakerManager

WARNING: Always start with --dry-run until you validate picks!
============================================================
""")

if __name__ == "__main__":
    import subprocess
    install_requirements()
    print_setup_guide()
