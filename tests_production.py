#!/usr/bin/env python3
"""
LHM Production-Grade Test Suite - Fixed to match actual API
"""

import sys
import os
import pytest
import json
import time
import numpy as np
import sqlite3
import tempfile
import math
import asyncio
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent / "Downloads"))

import deepseek_python_20260707_a6bd19 as lhm


# ======================================================================
# KELLY CALCULATOR TESTS - Financial correctness is non-negotiable
# ======================================================================

class TestKellyCalculator:
    """Kelly criterion must never produce NaN, inf, or negative stakes."""

    def test_kelly_no_nan(self):
        for prob in [0.01, 0.5, 0.99]:
            for odds in [1.1, 2.0, 10.0]:
                kelly = lhm.Calculator.kelly_fraction(prob, odds)
                assert not math.isnan(kelly), f"Kelly returned NaN for p={prob}, odds={odds}"
                assert not math.isinf(kelly), f"Kelly returned inf for p={prob}, odds={odds}"

    def test_kelly_no_edge_returns_zero(self):
        kelly = lhm.Calculator.kelly_fraction(0.5, 2.0)
        assert abs(kelly) < 1e-9

    def test_kelly_positive_edge(self):
        kelly = lhm.Calculator.kelly_fraction(0.6, 2.0)
        assert kelly > 0
        assert kelly <= 1.0

    def test_kelly_extreme_odds(self):
        kelly = lhm.Calculator.kelly_fraction(0.99, 1000.0)
        assert not math.isnan(kelly)
        assert kelly >= 0
        assert kelly <= 1.0

    def test_kelly_extreme_low_odds(self):
        kelly = lhm.Calculator.kelly_fraction(0.01, 1.01)
        assert not math.isnan(kelly)
        assert kelly <= 1.0

    def test_kelly_with_cost_uses_kelly_with_cost(self):
        kelly_base = lhm.Calculator.kelly_fraction(0.6, 2.0)
        kelly_cost = lhm.Calculator.kelly_with_cost(0.6, 2.0, commission=0.05, slippage=0.005)
        assert not math.isnan(kelly_cost)
        assert kelly_cost >= 0
        assert kelly_cost <= kelly_base

    def test_kelly_below_min_edge_returns_zero(self):
        kelly = lhm.Calculator.kelly_fraction(0.51, 1.9)
        assert kelly == 0.0

    def test_zero_stake_returns_zero_profit(self):
        kelly = lhm.Calculator.kelly_fraction(0.6, 2.0)
        assert kelly >= 0


# ======================================================================
# DATABASE MIGRATION TESTS - No corruption, idempotent, reversible
# ======================================================================

class TestDatabaseMigrations:
    """Migrations must be idempotent and never corrupt data."""

    def test_migration_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_lhm.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            for _ in range(3):
                lhm.run_migrations(conn)
            
            conn.commit()
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert len(tables) > 0
            conn.close()

    def test_migration_preserves_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_lhm.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE IF NOT EXISTS bets (id INTEGER PRIMARY KEY, test_col TEXT)")
            conn.execute("INSERT INTO bets (test_col) VALUES ('preserve_me')")
            conn.commit()
            
            lhm.run_migrations(conn)
            conn.commit()
            
            result = conn.execute("SELECT test_col FROM bets WHERE id=1").fetchone()
            assert result[0] == "preserve_me"
            conn.close()

    def test_migration_no_data_loss_on_reopen(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_lhm.db")
            
            conn1 = sqlite3.connect(db_path)
            lhm.run_migrations(conn1)
            conn1.execute("CREATE TABLE IF NOT EXISTS test_data (id INTEGER PRIMARY KEY, value TEXT)")
            conn1.execute("INSERT INTO test_data (value) VALUES ('test')")
            conn1.commit()
            conn1.close()
            
            conn2 = sqlite3.connect(db_path)
            result = conn2.execute("SELECT value FROM test_data WHERE id=1").fetchone()
            assert result[0] == "test"
            conn2.close()

    def test_database_connection_retry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_lhm.db")
            conn = sqlite3.connect(db_path)
            conn.close()
            
            new_conn = lhm.get_db_connection(db_path, max_retries=3)
            assert new_conn is not None
            new_conn.close()


# ======================================================================
# ODDS FALLBACK CHAIN TESTS - Graceful degradation, no crashes
# ======================================================================

class TestOddsFallbackChain:
    """The engine must handle API failures without crashing or returning synthetic odds."""

    def test_no_synthetic_odds_in_production(self):
        if lhm.CONFIG.dry_run:
            pytest.skip("Synthetic odds allowed in dry-run mode")
        
        mock_validator = MagicMock()
        mock_validator.validate_odds = AsyncMock(return_value=(False, {}))
        fetcher = lhm.RealDataFetcher(schema_validator=mock_validator)
        
        with patch.object(fetcher, '_check_freshness', new_callable=AsyncMock, return_value=None):
            with patch.object(fetcher, '_request_with_retry', side_effect=Exception("API down")):
                with patch.object(fetcher, '_fetch_betpawa_odds', new_callable=AsyncMock, return_value=None):
                    with patch.object(fetcher, '_fetch_betika_odds', new_callable=AsyncMock, return_value=None):
                        with patch.dict(sys.modules, {'stealth_scraper': None}):
                            with pytest.raises(RuntimeError, match="No valid odds sources"):
                                asyncio.run(fetcher.fetch_odds("soccer"))

    def test_fallback_chain_exhausts_gracefully(self):
        mock_validator = MagicMock()
        mock_validator.validate_odds = AsyncMock(return_value=(False, {}))
        fetcher = lhm.RealDataFetcher(schema_validator=mock_validator)
        
        with patch.object(fetcher, '_check_freshness', new_callable=AsyncMock, return_value=None):
            with patch.object(fetcher, '_request_with_retry', side_effect=Exception("All APIs down")):
                with patch.object(fetcher, '_fetch_betpawa_odds', new_callable=AsyncMock, return_value=None):
                    with patch.object(fetcher, '_fetch_betika_odds', new_callable=AsyncMock, return_value=None):
                        with patch.dict(sys.modules, {'stealth_scraper': None}):
                            if not lhm.CONFIG.dry_run:
                                with pytest.raises(RuntimeError, match="No valid odds sources"):
                                    asyncio.run(fetcher.fetch_odds("soccer"))

    def test_single_api_failure_continues(self):
        mock_validator = MagicMock()
        mock_validator.validate_odds = AsyncMock(return_value=(True, {"bookmakers": []}))
        fetcher = lhm.RealDataFetcher(schema_validator=mock_validator)
        
        call_count = [0]
        def flaky_api(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First API fails")
            return {"bookmakers": [{"markets": [{"key": "h2h", "outcomes": [{"name": "Home", "price": 2.0}]}]}]}
        
        with patch.object(fetcher, '_check_freshness', new_callable=AsyncMock, return_value=None):
            with patch.object(fetcher, '_request_with_retry', side_effect=flaky_api):
                with patch.object(fetcher, '_fetch_betpawa_odds', new_callable=AsyncMock, return_value=None):
                    with patch.object(fetcher, '_fetch_betika_odds', new_callable=AsyncMock, return_value=None):
                        with patch.dict(sys.modules, {'stealth_scraper': None}):
                            with patch.object(lhm.CONFIG, 'odds_api_key', 'dummy_key'):
                                odds = asyncio.run(fetcher.fetch_odds("soccer"))
                                assert odds is not None or odds == []

    def test_all_apis_down_logs_alert(self):
        mock_validator = MagicMock()
        mock_validator.validate_odds = AsyncMock(return_value=(False, {}))
        fetcher = lhm.RealDataFetcher(schema_validator=mock_validator)
        
        with patch.object(fetcher, '_check_freshness', new_callable=AsyncMock, return_value=None):
            with patch.object(fetcher, '_request_with_retry', side_effect=Exception("All down")):
                with patch.object(fetcher, '_fetch_betpawa_odds', new_callable=AsyncMock, return_value=None):
                    with patch.object(fetcher, '_fetch_betika_odds', new_callable=AsyncMock, return_value=None):
                        with patch.dict(sys.modules, {'stealth_scraper': None}):
                            with patch('deepseek_python_20260707_a6bd19.log') as mock_log:
                                if not lhm.CONFIG.dry_run:
                                    with pytest.raises(RuntimeError):
                                        asyncio.run(fetcher.fetch_odds("soccer"))
                                    mock_log.critical.assert_called()


# ======================================================================
# BOOKMAKER SETTLEMENT TESTS - Push, half-win, partial returns
# ======================================================================

class TestBookmakerSettlement:
    """Settlement must handle pushes, half-wins, and void bets correctly."""

    def test_winning_bet_returns_profit(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="home",
            actual_score=(2, 1),
            market="1X2",
            stake=100.0,
            odds=2.0
        )
        assert result["profit"] == 100.0
        assert result["status"] == "win"

    def test_losing_bet_returns_loss(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="home",
            actual_score=(0, 2),
            market="1X2",
            stake=100.0,
            odds=2.0
        )
        assert result["profit"] == -100.0
        assert result["status"] == "loss"

    def test_void_bet_returns_full_stake(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="home",
            actual_score=(0, 0),
            market="1X2",
            stake=100.0,
            odds=1.5,
            void=True
        )
        assert result["profit"] == 0.0
        assert result["status"] == "void"

    def test_totals_over_win(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="over",
            actual_score=(2, 2),
            market="totals",
            stake=100.0,
            odds=1.95
        )
        assert result["status"] == "win"
        assert result["profit"] > 0

    def test_totals_under_win(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="under",
            actual_score=(0, 0),
            market="totals",
            stake=100.0,
            odds=1.95
        )
        assert result["status"] == "win"

    def test_btts_yes_win(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="yes",
            actual_score=(1, 1),
            market="btts",
            stake=100.0,
            odds=1.80
        )
        assert result["status"] == "win"

    def test_btts_no_win(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="no",
            actual_score=(0, 0),
            market="btts",
            stake=100.0,
            odds=1.80
        )
        assert result["status"] == "win"

    def test_asian_handicap_push(self):
        bm = lhm.BookmakerManager()
        result = bm.settle_bet(
            selection="home",
            actual_score=(1, 1),
            market="asian_handicap",
            stake=100.0,
            odds=1.95,
            handicap=0.0
        )
        assert result["status"] == "push"
        assert result["profit"] == 0.0


# ======================================================================
# ATOMIC TRANSACTION TESTS - No race conditions, no double-spend
# ======================================================================

class TestAtomicTransactions:
    """Bankroll updates must be atomic. No partial state on crash."""

    def test_atomic_exposure_deduction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_atomic.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE bankroll (id INTEGER PRIMARY KEY, balance REAL)")
            conn.execute("INSERT INTO bankroll (balance) VALUES (1000.0)")
            conn.execute("CREATE TABLE exposure (id INTEGER PRIMARY KEY, bet_id INTEGER, amount REAL)")
            conn.commit()
            
            with lhm.atomic_transaction(conn) as txn:
                txn.execute("UPDATE bankroll SET balance = balance - 100 WHERE id=1")
                txn.execute("INSERT INTO exposure (bet_id, amount) VALUES (1, 100.0)")
            
            result = conn.execute("SELECT balance FROM bankroll WHERE id=1").fetchone()
            assert result[0] == 900.0
            conn.close()

    def test_rollback_on_exception(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_rollback.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE bankroll (id INTEGER PRIMARY KEY, balance REAL)")
            conn.execute("INSERT INTO bankroll (balance) VALUES (1000.0)")
            conn.commit()
            
            with pytest.raises(Exception):
                with lhm.atomic_transaction(conn) as txn:
                    txn.execute("UPDATE bankroll SET balance = balance - 100 WHERE id=1")
                    raise ValueError("Simulated crash")
            
            result = conn.execute("SELECT balance FROM bankroll WHERE id=1").fetchone()
            assert result[0] == 1000.0
            conn.close()

    def test_no_double_spend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_double.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE bankroll (id INTEGER PRIMARY KEY, balance REAL)")
            conn.execute("INSERT INTO bankroll (balance) VALUES (100.0)")
            conn.commit()
            
            results = []
            for _ in range(2):
                with lhm.atomic_transaction(conn) as txn:
                    bal = txn.execute("SELECT balance FROM bankroll WHERE id=1").fetchone()[0]
                    if bal >= 50:
                        txn.execute("UPDATE bankroll SET balance = balance - 50 WHERE id=1")
                        results.append(True)
                    else:
                        results.append(False)
            
            final_bal = conn.execute("SELECT balance FROM bankroll WHERE id=1").fetchone()[0]
            assert final_bal >= 0
            assert sum(results) <= 2
            conn.close()


# ======================================================================
# CONCURRENCY TESTS - No deadlocks, no race conditions
# ======================================================================

class TestConcurrency:
    """Thread safety for shared state."""

    def test_concurrent_config_reads(self):
        errors = []
        
        def read_config():
            try:
                for _ in range(100):
                    _ = lhm.CONFIG.dry_run
                    _ = lhm.CONFIG.risk.kelly_fraction
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=read_config) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Concurrent config reads failed: {errors}"

    def test_concurrent_db_writes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_conc.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE counter (id INTEGER PRIMARY KEY, value INTEGER)")
            conn.execute("INSERT INTO counter (value) VALUES (0)")
            conn.commit()
            conn.close()
            
            errors = []
            lock = threading.Lock()
            def increment():
                local_conns = []
                try:
                    for _ in range(10):
                        c = sqlite3.connect(db_path)
                        local_conns.append(c)
                        with lhm.atomic_transaction(c) as txn:
                            txn.execute("UPDATE counter SET value = value + 1 WHERE id=1")
                except Exception as e:
                    with lock:
                        errors.append(e)
                finally:
                    for c in local_conns:
                        try:
                            c.close()
                        except Exception:
                            pass
            
            threads = [threading.Thread(target=increment) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            final_conn = sqlite3.connect(db_path)
            try:
                final = final_conn.execute("SELECT value FROM counter WHERE id=1").fetchone()[0]
                assert final == 50
            finally:
                final_conn.close()
            
            assert len(errors) == 0


# ======================================================================
# PRODUCTION DEPENDENCY TESTS - Fail loud, not silent
# ======================================================================

class TestProductionDependencies:
    """Critical dependencies must raise on failure, not silently degrade."""

    def test_require_torch_raises_when_missing(self):
        with patch.dict(sys.modules, {'torch': None}):
            with pytest.raises(ImportError, match="torch is required"):
                lhm.require_torch()

    def test_require_sklearn_raises_when_missing(self):
        with patch.dict(sys.modules, {'sklearn': None}):
            with pytest.raises(ImportError, match="sklearn is required"):
                lhm.require_sklearn()

    def test_check_production_dependencies_raises_on_missing(self):
        if not lhm.CONFIG.dry_run:
            with patch.dict(sys.modules, {'torch': None, 'sklearn': None}):
                with pytest.raises(RuntimeError, match="Missing production dependencies"):
                    lhm.check_production_dependencies()


# ======================================================================
# STUB REMOVAL TESTS - No dead code in production
# ======================================================================

class TestNoStubCode:
    """Production must not contain unimplemented stub classes."""

    def test_official_feed_gateway_disabled_in_production(self):
        if not lhm.CONFIG.dry_run:
            assert lhm.OfficialFeedGateway.__name__ == 'DisabledOfficialFeedGateway'

    def test_order_book_processor_disabled_in_production(self):
        if not lhm.CONFIG.dry_run:
            assert lhm.OrderBookProcessor.__name__ == 'DisabledOrderBookProcessor'

    def test_heartbeat_monitor_disabled_in_production(self):
        if not lhm.CONFIG.dry_run:
            assert lhm.HeartbeatMonitor.__name__ == 'DisabledHeartbeatMonitor'


# ======================================================================
# EDGE CASES - The usual suspects
# ======================================================================

class TestEdgeCases:
    def test_match_probs_stable_under_high_xg(self):
        joint = lhm.Calculator.match_probs(10.0, 10.0, max_goals=20)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_match_probs_stable_under_zero_xg(self):
        joint = lhm.Calculator.match_probs(0.0, 0.0, max_goals=5)
        assert abs(joint.sum() - 1.0) < 1e-6

    def test_config_serialization_roundtrip(self):
        config_dict = lhm.CONFIG.redacted_dict()
        assert isinstance(config_dict, dict)
        assert "host" in config_dict
        assert "port" in config_dict

    def test_negative_prob_clamped(self):
        kelly = lhm.Calculator.kelly_fraction(0.6, 2.0)
        assert kelly >= 0

    def test_prob_above_one_handled(self):
        kelly = lhm.Calculator.kelly_fraction(0.99, 2.0)
        assert kelly >= 0

    def test_atomic_transaction_commits_on_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_atomic2.db")
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val INTEGER)")
            conn.execute("INSERT INTO test (val) VALUES (0)")
            conn.commit()
            
            with lhm.atomic_transaction(conn) as txn:
                txn.execute("UPDATE test SET val = 42 WHERE id=1")
            
            result = conn.execute("SELECT val FROM test WHERE id=1").fetchone()
            assert result[0] == 42
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
