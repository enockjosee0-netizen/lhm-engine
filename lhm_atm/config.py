"""Centralised configuration for the LHM modular chassis.

Every magic number the review flagged as "under-tuned" lives here so it can be
walk-forward optimised in one place. Real-money execution is gated behind
`live_execution=False`; nothing places a real bet unless you explicitly flip it
AND supply credentials in the environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Config:
    # ---- Capital / sizing ----
    bankroll: float = 1000.0
    min_edge: float = 0.03          # global floor (realistic, near-efficient markets)
    kelly_fraction: float = 0.15    # base Kelly fraction
    fractional_kelly: float = 0.25  # de-rate applied on top
    max_stake_per_bet: float = 0.018
    min_stake_per_bet: float = 0.001
    max_stake_per_match: float = 0.05
    max_bets_per_day: int = 50

    # ---- Real-world friction (the review says these were under-estimated) ----
    commission: float = 0.02        # exchange commission on net winnings
    slippage_bps: float = 3.0       # basis points of adverse price move at entry
    execution_latency_ms: float = 50.0  # target; co-lo gets you here
    partial_fill_threshold: float = 0.2  # stake/liquidity above this -> partial fill

    # ---- Exposure caps ----
    exposure_limit_per_league: float = 0.10
    exposure_limit_per_market: float = 0.05
    exposure_limit_per_team: float = 0.03
    max_correlation: float = 0.6    # correlation between two open positions

    # ---- Risk hardening (portfolio-level, not per-position) ----
    max_drawdown: float = 0.20
    stop_loss_drawdown: float = 0.15
    portfolio_var_limit: float = 0.05   # 1-day 95% VaR cap on bankroll
    var_confidence: float = 0.95
    correlation_drawdown_halt: float = 0.10  # stop if correlation-driven DD exceeds

    # ---- Feeds / venues ----
    venues: List[str] = field(default_factory=lambda: ["betfair", "pinnacle", "synthetic"])
    primary_feed: str = "synthetic"
    live_execution: bool = False    # NEVER true unless you mean it
    stealth_stake_variance: float = 0.12  # disguise intent via stake jitter

    # ---- Shadow mode ----
    shadow_days: int = 7
    shadow_max_divergence_bps: float = 25.0  # fail shadow if expected vs filled worse than this

    # ---- Walk-forward ----
    wf_train_days: int = 90
    wf_test_days: int = 30
    wf_min_test_bets: int = 50
    wf_metric: str = "roi"          # optimise on out-of-sample ROI

    # ---- Backtest ----
    backtest_seed: int = 42
    tick_volatility: float = 0.004  # per-tick odds random walk std
    bookmaker_limit_chase: bool = True  # model adaptive limits (retail limits you fast)


def load_from_env() -> Config:
    """Override any field from LHM_<UPPER_FIELD> env vars (non-secret only)."""
    import os
    cfg = Config()
    for f in cfg.__dataclass_fields__:  # type: ignore[attr-defined]
        env = os.environ.get(f"LHM_{f.upper()}")
        if env is None:
            continue
        cur = getattr(cfg, f)
        if isinstance(cur, bool):
            setattr(cfg, f, env.lower() in {"1", "true", "yes"})
        elif isinstance(cur, (int, float)):
            setattr(cfg, f, type(cur)(env))
        elif isinstance(cur, list):
            setattr(cfg, f, [x.strip() for x in env.split(",") if x.strip()])
    return cfg
