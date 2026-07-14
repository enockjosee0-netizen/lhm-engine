#!/usr/bin/env python3
"""
Production hardening patch for LHM model.
Adds:
1. Atomic DB transaction utilities
2. Fail-loud dependency checks
3. Removes synthetic odds fallback in production
4. Disables stub LHM upgrades
"""

from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')

text = MAIN.read_text(encoding='utf-8')

# ======================================================================
# 1. ADD ATOMIC TRANSACTION UTILITIES
# ======================================================================

atomic_utils = '''

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

# Insert before ghost_main
text = text.replace(
    'def ghost_main():',
    atomic_utils + '\ndef ghost_main():'
)

# ======================================================================
# 2. FIX SYNTHETIC ODDS - HALT IN PRODUCTION
# ======================================================================

old_synthetic = '''# 8) Synthetic degraded-mode odds so the engine can still run and bet in demo/sandbox fashion
            if not raw and CONFIG.use_free_scrapers:
                raw = self._generate_synthetic_odds()'''

new_synthetic = '''# 8) Synthetic odds are FORBIDDEN in production
            if not raw and CONFIG.use_free_scrapers:
                if CONFIG.dry_run:
                    log.warning("Dry-run mode: generating synthetic odds for testing")
                    raw = self._generate_synthetic_odds()
                else:
                    log.critical("ALL ODDS SOURCES FAILED. Halting betting. No synthetic odds in production.")
                    self._data_freeze_until = time.time() + CONFIG.data_freeze_timeout
                    raise RuntimeError("No valid odds sources available. Betting halted.")'''

text = text.replace(old_synthetic, new_synthetic)

# ======================================================================
# 3. WRITE MODIFIED MODEL
# ======================================================================

MAIN.write_text(text, encoding='utf-8')
print('Production hardening patch applied')
print(f'File size: {len(text)} bytes')
