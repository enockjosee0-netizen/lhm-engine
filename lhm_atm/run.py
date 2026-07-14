"""Orchestrator / CLI for the modular LHM chassis.

Run it with the explicit 3.12 interpreter (the 3.13 install on this box is
broken and hijacks `python`):

  python lhm_atm/run.py --health-check
  python lhm_atm/run.py --backtest
  python lhm_atm/run.py --shadow
  python lhm_atm/run.py --walk-forward
  python lhm_atm/run.py --optimize
  python lhm_atm/run.py --monitor

Everything defaults to SIMULATION. Real-money execution only happens if you
set live_execution=True in Config AND supply real venue credentials.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time

from .config import Config, load_from_env
from .features.engine import FeatureEngine, Match
from .models.predict import Ensemble, WalkForwardTrainer
from .risk.risk import PortfolioRisk
from .execution.router import SmartOrderRouter, SyntheticVenue
from .data.feed import SyntheticTickFeed, Tick
from .monitoring.metrics import Metrics, HealthServer
from .backtest.engine import BacktestEngine
from .shadow import ShadowMode


def _quick_self_test(cfg: Config) -> None:
    """Prove the whole chassis imports and executes end-to-end."""
    print("LHM modular chassis - self test")
    print(f"  Python import OK | live_execution={cfg.live_execution}")
    m = Match(market_id="M1", selection="HOME", home_xg=1.8, away_xg=1.1, league="L1", team="T1")
    model = Ensemble()
    probs = model.predict(m)
    risk = PortfolioRisk(cfg)
    stake = risk.kelly_stake(0.05, 2.0, cfg.bankroll)
    var = risk.historical_var(__import__("numpy").array([-0.01, 0.02, -0.03, 0.01]))
    print(f"  model P(HOME)={probs['HOME']:.3f} | kelly stake={stake:.4f} | VaR={var:.4f}")
    res = BacktestEngine(cfg, seed=1).run(n_matches=60)
    print(f"  backtest: bets={res.bets} roi={res.roi} slip_bps={res.avg_slippage_bps} fill={res.fill_rate} dd={res.max_drawdown}")
    assert res.bets > 0, "backtest produced no bets - chassis broken"
    print("  SELF TEST PASSED - chassis is awake.")


def cmd_health(cfg: Config) -> int:
    _quick_self_test(cfg)
    return 0


def cmd_backtest(cfg: Config) -> int:
    res = BacktestEngine(cfg, seed=cfg.backtest_seed).run(n_matches=300)
    print("\n=== BACKTEST (tick-level, market-impact + slippage + partial fills) ===")
    for k in ["bets", "wins", "stakes", "pnl", "roi", "max_drawdown", "avg_slippage_bps", "fill_rate", "final_bankroll", "stopped_early", "var_breaches"]:
        print(f"  {k:20s}: {getattr(res, k)}")
    return 0


def cmd_shadow(cfg: Config) -> int:
    rep = ShadowMode(cfg).run()
    print("\n=== SHADOW MODE (verifies execution gets modelled prices) ===")
    print(f"  days={rep.days} decisions={rep.decisions}")
    print(f"  avg_expected={rep.avg_expected_price} avg_filled={rep.avg_filled_price}")
    print(f"  max_divergence_bps={rep.max_divergence_bps} (limit {cfg.shadow_max_divergence_bps})")
    print(f"  PASS={rep.pass_} | {rep.note}")
    return 0 if rep.pass_ else 1


def cmd_walk_forward(cfg: Config) -> int:
    trainer = WalkForwardTrainer(cfg, train_days=60, test_days=20)
    matches = [Match(market_id=f"M{i % 5}", selection=["HOME", "DRAW", "AWAY"][i % 3],
                     home_xg=1.2, away_xg=1.0, league=f"L{i % 3}", team=f"T{i % 7}") for i in range(200)]
    out = trainer.optimise(matches, [
        {"min_edge": 0.02}, {"min_edge": 0.03}, {"min_edge": 0.05}, {"min_edge": 0.08},
    ])
    print("\n=== WALK-FORWARD (out-of-sample threshold tuning) ===")
    print(f"  windows={out['windows']} best_overrides={out['best']} oos_score={out['oos_score']:.3f}")
    return 0


def cmd_optimize(cfg: Config) -> int:
    # Grid-search the three thresholds the review said were under-tuned.
    trainer = WalkForwardTrainer(cfg, train_days=60, test_days=20)
    matches = [Match(market_id=f"M{i % 5}", selection=["HOME", "DRAW", "AWAY"][i % 3],
                     home_xg=1.2, away_xg=1.0, league=f"L{i % 3}", team=f"T{i % 7}") for i in range(200)]
    grid = [{"min_edge": me, "kelly_fraction": kf, "max_stake_per_bet": ms}
            for me in (0.02, 0.03, 0.05)
            for kf in (0.10, 0.15, 0.25)
            for ms in (0.01, 0.018, 0.03)]
    best, best_score = None, float("-inf")
    for c in grid:
        s = trainer.optimise(matches, [c])["oos_score"]
        if s > best_score:
            best, best_score = c, s
    print("\n=== WALK-FORWARD GRID OPTIMISATION ===")
    print(f"  best(out-of-sample): {best}  score={best_score:.3f}")
    return 0


def cmd_run_once(cfg: Config) -> int:
    _quick_self_test(cfg)
    cmd_backtest(cfg)
    cmd_shadow(cfg)
    return 0


def cmd_monitor(cfg: Config) -> int:
    metrics = Metrics(enabled=True)
    state = {"bankroll": cfg.bankroll, "bets": 0, "pnl": 0.0, "drawdown": 0.0}
    server = HealthServer(metrics, port=cfg.venues and 8001 or 8001, state=state)
    server.start()
    print(f"Monitoring live at http://0.0.0.0:8001/metrics and /health (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lhm_atm")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument("--backtest", action="store_true")
    parser.add_argument("--shadow", action="store_true")
    parser.add_argument("--walk-forward", action="store_true")
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--monitor", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_from_env()
    if cfg.live_execution:
        print("[WARN] live_execution=True - this chassis will attempt REAL orders if venues are wired.")

    if args.monitor:
        return cmd_monitor(cfg)
    if args.backtest:
        return cmd_backtest(cfg)
    if args.shadow:
        return cmd_shadow(cfg)
    if args.walk_forward:
        return cmd_walk_forward(cfg)
    if args.optimize:
        return cmd_optimize(cfg)
    if args.run_once:
        return cmd_run_once(cfg)
    # default: health check
    return cmd_health(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
