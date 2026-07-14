"""
LHM Full End-to-End Test with Real BetPawa Data
"""
import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Downloads"))

import deepseek_python_20260707_a6bd19 as lhm
from lhm_enhanced import SecureTelegramBridge, SecureConfigManager
from betpawa_async import AsyncBetPawaScraper
import numpy as np


async def full_test():
    print("=" * 70)
    print("LHM ENGINE - FULL END-TO-END TEST WITH REAL DATA")
    print("=" * 70)
    
    results = []
    
    # 1. Telegram
    print("\n[1/7] Testing Telegram Integration...")
    try:
        cm = SecureConfigManager()
        bridge = SecureTelegramBridge(cm)
        result = await bridge.send_message("LHM ENGINE: Starting full end-to-end test...")
        results.append(("Telegram Integration", "WORKING" if result else "FAILED"))
        print(f"    Result: {'SENT' if result else 'FAILED'}")
    except Exception as e:
        results.append(("Telegram Integration", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 2. Config System
    print("\n[2/7] Testing Config System...")
    try:
        config = lhm.CONFIG
        config_ok = bool(config.telegram_token) and bool(config.secret_key)
        results.append(("Config System", "WORKING" if config_ok else "FAILED"))
        print(f"    Telegram token: {'SET' if config.telegram_token else 'MISSING'}")
        print(f"    Secret key: {'SET' if config.secret_key else 'MISSING'}")
        print(f"    DRY_RUN: {config.dry_run}")
    except Exception as e:
        results.append(("Config System", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 3. Math Engine
    print("\n[3/7] Testing Math Engine...")
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
    
    # 4. Database
    print("\n[4/7] Testing Database...")
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
    
    # 5. BetPawa Scraper (REAL DATA)
    print("\n[5/7] Testing BetPawa Scraper (REAL DATA)...")
    try:
        scraper = AsyncBetPawaScraper()
        odds = await scraper.fetch_odds()
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
        from stealth_scraper import BetikaStealthScraper
        scraper = BetikaStealthScraper()
        await scraper.initialize()
        odds = await scraper.fetch_odds()
        
        if odds:
            results.append(("Betika Scraper", f"WORKING ({len(odds)} matches)"))
            print(f"    Status: WORKING ({len(odds)} matches)")
            for match in odds[:3]:
                print(f"    {match['home_team']} vs {match['away_team']}: {match['odds']}")
        else:
            results.append(("Betika Scraper", "BLOCKED (no odds returned)"))
            print("    Status: BLOCKED (no odds returned)")
    except Exception as e:
        results.append(("Betika Scraper", f"ERROR: {e}"))
        print(f"    Status: ERROR ({type(e).__name__}: {e})")
    
    # 7. Ghost Protocol
    print("\n[7/7] Testing Ghost Protocol...")
    try:
        ghost = lhm.GhostProtocol(lhm.GhostConfig(enabled=True))
        ghost_ok = ghost is not None
        results.append(("Ghost Protocol", "INITIALIZED" if ghost_ok else "FAILED"))
        print(f"    Status: Initialized (simulation mode, Pico not connected)")
    except Exception as e:
        results.append(("Ghost Protocol", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # 8. Send BetPawa matches to Telegram
    print("\n[8/8] Sending BetPawa matches to Telegram...")
    try:
        cm = SecureConfigManager()
        bridge = SecureTelegramBridge(cm)
        
        # Fetch matches again for Telegram
        scraper = AsyncBetPawaScraper()
        odds = await scraper.fetch_odds()
        
        if odds:
            # Send top matches
            msg = "LHM ENGINE - LIVE BETPAWA MATCHES\n\n"
            for i, match in enumerate(odds[:10], 1):
                msg += f"{i}. {match['home_team']} vs {match['away_team']}\n"
                msg += f"   League: {match['league']}\n"
                msg += f"   Kickoff: {match['kickoff']}\n"
                msg += f"   Odds: {match['odds'].get('home', 'N/A')} / {match['odds'].get('draw', 'N/A')} / {match['odds'].get('away', 'N/A')}\n\n"
            
            result = await bridge.send_message(msg)
            results.append(("Telegram Matches", f"SENT ({len(odds[:10])} matches)" if result else "FAILED"))
            print(f"    Sent {len(odds[:10])} matches to Telegram")
        else:
            results.append(("Telegram Matches", "NO DATA"))
            print("    No matches to send")
    except Exception as e:
        results.append(("Telegram Matches", f"ERROR: {e}"))
        print(f"    Error: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    for name, status in results:
        print(f"  {name}: {status}")
    
    working = sum(1 for _, s in results if "WORKING" in s or "SENT" in s)
    total = len(results)
    print(f"\nResult: {working}/{total} tests passed")
    
    # Send final summary to Telegram
    try:
        cm = SecureConfigManager()
        bridge = SecureTelegramBridge(cm)
        
        summary_msg = f"LHM ENGINE TEST RESULTS\n\n"
        for name, status in results:
            summary_msg += f"{name}: {status}\n"
        summary_msg += f"\n{working}/{total} tests passed"
        
        await bridge.send_message(summary_msg)
        print("\nFinal results sent to Telegram!")
    except Exception as e:
        print(f"\nFailed to send final results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(full_test())
