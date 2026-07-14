"""
LHM Full End-to-End Test with BetPawa Scraper
Tests all components and sends results to Telegram
"""
import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Downloads"))

import deepseek_python_20260707_a6bd19 as lhm
from lhm_enhanced import SecureTelegramBridge, SecureConfigManager, EnhancedDataFetcher
from betpawa_working import BetPawaScraper
import numpy as np


async def full_test():
    print("=" * 60)
    print("LHM ENGINE - FULL END-TO-END TEST")
    print("=" * 60)
    
    results = []
    
    # 1. Telegram
    print("\n[1/7] Testing Telegram...")
    try:
        cm = SecureConfigManager()
        bridge = SecureTelegramBridge(cm)
        result = await bridge.send_message("LHM Test: Telegram integration WORKING")
        results.append(("Telegram", "WORKING" if result else "FAILED"))
        print(f"    Result: {'SENT' if result else 'FAILED'}")
    except Exception as e:
        results.append(("Telegram", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 2. Math Engine
    print("\n[2/7] Testing Math Engine...")
    try:
        kelly = lhm.Calculator.kelly_fraction(0.6, 2.0)
        joint = lhm.Calculator.match_probs(1.5, 1.2, max_goals=10)
        math_ok = abs(joint.sum() - 1.0) < 1e-6 and kelly > 0
        results.append(("Math Engine", "WORKING" if math_ok else "FAILED"))
        print(f"    Kelly(0.6, 2.0) = {kelly:.4f}")
        print(f"    Match probs sum = {joint.sum():.6f}")
    except Exception as e:
        results.append(("Math Engine", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 3. Database
    print("\n[3/7] Testing Database...")
    try:
        import sqlite3
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            conn = sqlite3.connect(db_path)
            lhm.run_migrations(conn)
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            db_ok = 'bets' in table_names and 'bankroll' in table_names
            conn.close()
            results.append(("Database", "WORKING" if db_ok else "FAILED"))
            print(f"    Tables: {table_names}")
    except Exception as e:
        results.append(("Database", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 4. Config System
    print("\n[4/7] Testing Config System...")
    try:
        config = lhm.CONFIG
        config_ok = bool(config.telegram_token) and bool(config.secret_key)
        results.append(("Config", "WORKING" if config_ok else "FAILED"))
        print(f"    Telegram token: {'SET' if config.telegram_token else 'MISSING'}")
        print(f"    Secret key: {'SET' if config.secret_key else 'MISSING'}")
        print(f"    DRY_RUN: {config.dry_run}")
    except Exception as e:
        results.append(("Config", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 5. BetPawa Scraper
    print("\n[5/7] Testing BetPawa Scraper...")
    try:
        scraper = BetPawaScraper()
        odds = scraper.fetch_odds()
        scraper_ok = len(odds) > 0
        results.append(("BetPawa Scraper", f"WORKING ({len(odds)} matches)" if scraper_ok else "FAILED"))
        print(f"    Fetched {len(odds)} matches")
        if odds:
            print(f"    Sample: {odds[0]['home_team']} vs {odds[0]['away_team']}")
            print(f"    Odds: {odds[0]['odds']}")
    except Exception as e:
        results.append(("BetPawa Scraper", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 6. Betika Scraper
    print("\n[6/7] Testing Betika Scraper...")
    try:
        from betpawa_working import BetPawaScraper as BetikaScraper
        # Betika uses same parser but different URL
        scraper = BetPawaScraper()
        # Try Betika URL
        scraper.page.goto('https://www.betika.com/en-ke/sports/soccer/odds', wait_until="domcontentloaded")
        import time
        time.sleep(5)
        text = scraper.page.evaluate("document.body.innerText")
        scraper._close_browser()
        
        betika_ok = len(text) > 100  # Has some content
        results.append(("Betika Scraper", "PARTIAL" if betika_ok else "BLOCKED"))
        print(f"    Status: {'Content loaded' if betika_ok else 'Blocked/Empty'}")
    except Exception as e:
        results.append(("Betika Scraper", f"ERROR/ BLOCKED: {e}"))
        print(f"    Status: BLOCKED ({type(e).__name__})")
    
    # 7. Ghost Protocol
    print("\n[7/7] Testing Ghost Protocol...")
    try:
        ghost = lhm.GhostProtocol(lhm.GhostConfig(enabled=True))
        ghost_ok = ghost is not None
        results.append(("Ghost Protocol", "INITIALIZED" if ghost_ok else "FAILED"))
        print(f"    Status: Initialized (Pico not connected = simulation mode)")
    except Exception as e:
        results.append(("Ghost Protocol", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # Send summary to Telegram
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, status in results:
        print(f"  {name}: {status}")
    
    # Send summary to Telegram
    try:
        cm = SecureConfigManager()
        bridge = SecureTelegramBridge(cm)
        
        summary_msg = "LHM ENGINE TEST RESULTS\n\n"
        for name, status in results:
            summary_msg += f"{name}: {status}\n"
        
        await bridge.send_message(summary_msg)
        print("\nResults sent to Telegram!")
    except Exception as e:
        print(f"\nFailed to send to Telegram: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(full_test())
