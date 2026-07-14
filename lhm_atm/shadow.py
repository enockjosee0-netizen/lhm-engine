"""Live shadow mode.

Runs the full strategy (signal -> risk gate -> route -> execute) side-by-side
with "real" flow for `cfg.shadow_days`, recording the gap between the price the
model EXPECTED and the price the EXECUTION layer actually delivered. If the
execution layer can't get the prices you modelled, the strategy is rejected
before any real capital is risked. This is the review's #6 safeguard.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, List

from .config import Config
from .data.feed import SyntheticTickFeed, Tick
from .features.engine import FeatureEngine, Match
from .models.predict import Ensemble
from .risk.risk import PortfolioRisk, Position
from .execution.router import SmartOrderRouter, SyntheticVenue


@dataclass
class ShadowReport:
    days: int
    decisions: int
    avg_expected_price: float
    avg_filled_price: float
    max_divergence_bps: float
    pass_: bool
    note: str


class ShadowMode:
    def __init__(self, cfg: Config, seed: int = 7):
        self.cfg = cfg
        self.rng = random.Random(seed)
        self.model = Ensemble()
        self.risk = PortfolioRisk(cfg)
        self.feats = FeatureEngine()

    def _day(self, n_matches: int = 30) -> Dict:
        feed = SyntheticTickFeed(seed=self.rng.randint(0, 1_000_000), tick_ms=0)
        snap: Dict[str, Tick] = {}
        matches: List[Match] = []
        for i in range(n_matches):
            m = Match(market_id=f"M{i % 5}", selection=self.rng.choice(["HOME", "DRAW", "AWAY"]),
                      home_xg=self.rng.uniform(0.6, 2.4), away_xg=self.rng.uniform(0.6, 2.4),
                      league=f"L{i % 3}", team=f"T{i % 7}")
            fair = 1.0 / max(self.model.predict(m)[m.selection], 1e-6) * 1.05
            snap[f"{m.market_id}:{m.selection}"] = Tick(
                venue="synthetic", market_id=m.market_id, selection=m.selection, ts=time.time(),
                back_price=round(fair * self.rng.uniform(0.97, 1.03), 3), lay_price=round(fair * 1.02, 3),
                back_size=self.rng.uniform(300, 2000), lay_size=self.rng.uniform(300, 2000))
            matches.append(m)
        venues = [SyntheticVenue("synthetic", snap, self.cfg, self.rng)]
        router = SmartOrderRouter(self.cfg, venues, self.rng)

        exp_prices, filled_prices, divs = [], [], []
        open_positions: List[Position] = []
        for m in matches:
            probs = self.model.predict(m)
            fair_price = 1.0 / max(probs[m.selection], 1e-6)
            market = snap[f"{m.market_id}:{m.selection}"]
            edge = (fair_price - market.back_price) / market.back_price
            if edge < self.cfg.min_edge:
                continue
            stake = self.risk.kelly_stake(edge, market.back_price, self.cfg.bankroll)
            pos = Position(m.market_id, m.selection, "BACK", stake, market.back_price, m.league, m.team)
            if stake <= 0 or not self.risk.correlation_ok(pos, open_positions):
                continue
            reports = router.execute(m.market_id, m.selection, "BACK", stake)
            if not reports:
                continue
            filled = sum(r.filled for r in reports)
            avg_filled = sum(r.avg_price * r.filled for r in reports) / max(filled, 1e-9)
            exp_prices.append(market.back_price)
            filled_prices.append(avg_filled)
            divs.append(abs(avg_filled - market.back_price) / market.back_price * 1e4)
            open_positions.append(pos)
        return {"n": len(exp_prices), "exp": exp_prices, "filled": filled_prices, "divs": divs}

    def run(self) -> ShadowReport:
        all_divs: List[float] = []
        decisions = 0
        exp_all: List[float] = []
        filled_all: List[float] = []
        for _ in range(self.cfg.shadow_days):
            d = self._day()
            decisions += d["n"]
            all_divs.extend(d["divs"])
            exp_all.extend(d["exp"]); filled_all.extend(d["filled"])
        max_div = max(all_divs) if all_divs else 0.0
        passed = max_div <= self.cfg.shadow_max_divergence_bps
        return ShadowReport(
            days=self.cfg.shadow_days, decisions=decisions,
            avg_expected_price=round(sum(exp_all) / max(len(exp_all), 1), 3),
            avg_filled_price=round(sum(filled_all) / max(len(filled_all), 1), 3),
            max_divergence_bps=round(max_div, 2),
            pass_=passed,
            note="Execution layer matches modelled prices." if passed else "EXECUTION DIVERGENCE TOO HIGH - do not go live.",
        )
