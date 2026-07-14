"""Feature engineering.

Turns a match row + a window of live ticks into the signals the models and
sharp-money logic consume. `feature_order()` exists because the monolith's
modular loader probes for it - returning a real, non-empty list keeps the
"FeatureEngine rejected" warning from firing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ..data.feed import Tick


@dataclass
class Match:
    market_id: str
    selection: str
    home_xg: float = 1.4
    away_xg: float = 1.0
    form_home: float = 0.5
    form_away: float = 0.5
    league: str = "default"
    team: str = "default"
    outcome: str = ""  # settled result selection, for backtest settling


class FeatureEngine:
    def feature_order(self) -> List[str]:
        return [
            "model_edge",
            "depth_imbalance",
            "sharp_move",
            "volatility",
            "staleness",
        ]

    def compute(self, match: Match, window: List[Tick]) -> Dict[str, float]:
        """window = recent ticks for (market_id, selection)."""
        feats: Dict[str, float] = {k: 0.0 for k in self.feature_order()}
        if not window:
            return feats

        prices = [t.back_price for t in window]
        feats["volatility"] = _std(prices) / max(prices)
        # depth imbalance: how much back liquidity vs lay liquidity
        back = sum(t.back_size for t in window)
        lay = sum(t.lay_size for t in window)
        feats["depth_imbalance"] = (back - lay) / max(1.0, back + lay)
        # sharp move: last vs first price change
        feats["sharp_move"] = (prices[-1] - prices[0]) / max(prices[0], 1e-9)
        feats["staleness"] = (window[-1].ts - window[0].ts)
        return feats


def _std(xs: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5
