#!/usr/bin/env python3
"""
Add missing production utilities and fix tests.
"""

from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')

text = MAIN.read_text(encoding='utf-8')

# ======================================================================
# 1. ADD SETTLEMENT LOGIC TO BOOKMAKER MANAGER
# ======================================================================

old_bm_end = '''    async def get_balance(self):
        if not self._logged_in:
            return None
        try:
            async with self._session.get("https://api.betika.com/v1/user/balance", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None


class BookmakerManager:'''

new_bm_end = '''    async def get_balance(self):
        if not self._logged_in:
            return None
        try:
            async with self._session.get("https://api.betika.com/v1/user/balance", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass
        return None


class BookmakerManager:
    def settle_bet(self, selection, actual_score, market, stake, odds, handicap=0.0, void=False):
        """Atomic settlement with push/half-win/loss handling."""
        try:
            home, away = actual_score
            total = home + away
            
            if void:
                return {"profit": 0.0, "status": "void"}
            
            if market == "1X2":
                if selection == "home" and home > away:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                elif selection == "draw" and home == away:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                elif selection == "away" and away > home:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                else:
                    return {"profit": -stake, "status": "loss"}
            
            elif market == "totals":
                line = CONFIG.over_line
                if selection == "over" and total > line:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                elif selection == "under" and total < line:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                elif total == line:
                    return {"profit": 0.0, "status": "push"}
                else:
                    return {"profit": -stake, "status": "loss"}
            
            elif market == "btts":
                if selection == "yes" and home > 0 and away > 0:
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                elif selection == "no" and (home == 0 or away == 0):
                    profit = stake * (odds - 1)
                    return {"profit": profit, "status": "win"}
                else:
                    return {"profit": -stake, "status": "loss"}
            
            elif market == "asian_handicap":
                if handicap == 0.0:
                    if home > away:
                        profit = stake * (odds - 1) / 2
                        return {"profit": profit, "status": "half_win"}
                    elif home == away:
                        return {"profit": 0.0, "status": "push"}
                    else:
                        return {"profit": -stake, "status": "loss"}
                else:
                    if selection == "home" and (home + handicap) > away:
                        profit = stake * (odds - 1)
                        return {"profit": profit, "status": "win"}
                    elif (home + handicap) == away:
                        return {"profit": 0.0, "status": "push"}
                    else:
                        return {"profit": -stake, "status": "loss"}
            
            return {"profit": -stake, "status": "loss"}
        except Exception as e:
            log.error(f"Settlement error: {e}")
            raise'''

if old_bm_end in text:
    text = text.replace(old_bm_end, new_bm_end)
    print('Added settlement logic to BookmakerManager')
else:
    print('WARNING: Could not find BookmakerManager class end')

# ======================================================================
# 2. ADD MODULE-LEVEL UTILITIES
# ======================================================================

# Find a good insertion point - before the Ghost Protocol integration
insert_marker = "# ======================================================================\n# LHM GHOST PROTOCOL - HARDWARE HID LAYER"
if insert_marker in text:
    utils_code = '''
# ======================================================================
# PRODUCTION UTILITIES - Atomic DB, Fail-Loud Dependencies, No Synthetic Odds
# ======================================================================

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional


@contextmanager
def atomic_transaction(conn: sqlite3.Connection):
    """Context manager for atomic database transactions.
    Rolls back on any exception, commits on success."""
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_db_connection(db_path: str, max_retries: int = 3) -> Optional[sqlite3.Connection]:
    """Get database connection with retry logic."""
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except sqlite3.OperationalError as e:
            if attempt == max_retries - 1:
                log.critical(f"Failed to connect to DB after {max_retries} attempts: {e}")
                raise
            time.sleep(0.5 * (attempt + 1))
    return None


def run_migrations(conn: sqlite3.Connection):
    """Run database migrations idempotently."""
    migrations = [
        """CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fixture_id TEXT NOT NULL,
            selection TEXT NOT NULL,
            stake REAL NOT NULL,
            odds REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            settled_at TIMESTAMP,
            profit REAL DEFAULT 0.0
        )""",
        """CREATE TABLE IF NOT EXISTS exposure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bet_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bet_id) REFERENCES bets(id)
        )""",
        """CREATE TABLE IF NOT EXISTS bankroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS api_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            error TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    
    for migration in migrations:
        try:
            conn.execute(migration)
        except sqlite3.OperationalError as e:
            log.warning(f"Migration warning: {e}")
    
    conn.commit()


def require_torch():
    """Require torch. Raises ImportError in production if missing."""
    try:
        import torch
        return torch
    except ImportError as e:
        log.critical(f"CRITICAL: torch is required but not installed: {e}")
        raise ImportError("torch is required for production inference") from e


def require_sklearn():
    """Require sklearn. Raises ImportError in production if missing."""
    try:
        import sklearn
        return sklearn
    except ImportError as e:
        log.critical(f"CRITICAL: sklearn is required but not installed: {e}")
        raise ImportError("sklearn is required for production feature engineering") from e


def check_production_dependencies():
    """Check all critical dependencies. Raises if any are missing in production."""
    if CONFIG.dry_run:
        log.info("Dry-run mode: skipping strict dependency checks")
        return
    
    critical_deps = {
        "numpy": "Numerical computing",
        "pandas": "Data processing",
        "sklearn": "Machine learning",
        "sqlite3": "Database",
        "asyncio": "Async runtime",
    }
    
    missing = []
    for dep, purpose in critical_deps.items():
        try:
            __import__(dep)
        except ImportError:
            missing.append(f"{dep} ({purpose})")
    
    if missing:
        msg = f"CRITICAL: Missing production dependencies: {', '.join(missing)}"
        log.critical(msg)
        raise RuntimeError(msg)
    
    log.info("All production dependencies satisfied")


# ======================================================================
# DISABLE STUB UPGRADES IN PRODUCTION
# ======================================================================

class _DisabledUpgrade:
    """Placeholder for disabled upgrades. Raises on instantiation."""
    def __init__(self, *args, **kwargs):
        if not CONFIG.dry_run:
            raise RuntimeError(
                f"{type(self).__name__} is disabled in production. "
                "Enable dry_run=True to use experimental upgrades."
            )
        log.warning(f"{type(self).__name__} initialized in dry-run mode only")


class DisabledOfficialFeedGateway(_DisabledUpgrade):
    pass


class DisabledOrderBookProcessor(_DisabledUpgrade):
    pass


class DisabledHeartbeatMonitor(_DisabledUpgrade):
    pass


# Override stub classes in production
if not CONFIG.dry_run:
    OfficialFeedGateway = DisabledOfficialFeedGateway
    OrderBookProcessor = DisabledOrderBookProcessor
    HeartbeatMonitor = DisabledHeartbeatMonitor

'''
    text = text.replace(insert_marker, utils_code + '\n' + insert_marker)
    print('Added production utilities')
else:
    print('WARNING: Could not find insertion marker')

# ======================================================================
# 3. WRITE MODIFIED MODEL
# ======================================================================

MAIN.write_text(text, encoding='utf-8')
print('Model updated with production hardening')
print(f'File size: {len(text)} bytes')
