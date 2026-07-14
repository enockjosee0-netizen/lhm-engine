"""Execution layer: smart order router + realistic fill simulation.

The review's #2/#3/#4: your execution under-estimated latency, slippage,
partial fills and adaptive limits. This module:

  * `SmartOrderRouter` splits one parent order across venues to maximise net
    fill price (best venue first) and randomises child stakes to disguise
    intent / avoid rapid limiting.
  * `FillSimulator` models what ACTUALLY happens when you hit the book:
      - market impact: adverse price move ~ stake / available liquidity
      - partial fills: if you're bigger than the queue, you only get part
      - latency: you don't get the price you saw, you get the next one
      - commission charged on net winnings
  * `Venue` is an interface; `SyntheticVenue` works now, `ExchangeVenue`
    shows exactly where Betfair/Pinnacle API calls plug in (not faked).
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..config import Config
from ..data.feed import Tick


@dataclass
class ChildOrder:
    venue: str
    market_id: str
    selection: str
    side: str
    stake: float


@dataclass
class ExecutionReport:
    venue: str
    side: str
    requested: float
    filled: float
    avg_price: float
    requested_price: float
    slippage_bps: float
    commission: float
    partial: bool
    latency_ms: float

    @property
    def net_stake(self) -> float:
        # stake at risk (BACK) or liability (LAY simplified as stake here)
        return self.filled


class Venue:
    name: str = "base"

    def quote(self, market_id: str, selection: str) -> Optional[Tick]:
        raise NotImplementedError

    def submit(self, order: ChildOrder, price: float) -> ExecutionReport:
        raise NotImplementedError


class SyntheticVenue(Venue):
    """Backs the dev feed. Depth comes from the latest tick snapshot."""

    def __init__(self, name: str, ticks: Dict[str, Tick], cfg: Config, rng: random.Random):
        self.name = name
        self.ticks = ticks
        self.cfg = cfg
        self.rng = rng

    def quote(self, market_id: str, selection: str) -> Optional[Tick]:
        return self.ticks.get(f"{market_id}:{selection}")

    def submit(self, order: ChildOrder, price: float) -> ExecutionReport:
        import copy
        # routed through the fill simulator
        sim = FillSimulator(self.cfg, self.rng)
        snap = self.ticks.get(f"{order.market_id}:{order.selection}")
        depth = snap.back_size if order.side == "BACK" else snap.lay_size
        return sim.simulate(order, price, depth, latency_ms=self.cfg.execution_latency_ms)


class ExchangeVenue(Venue):
    """Real exchange adapter skeleton (Betfair / Pinnacle / Sportmonks).

    Wire `client` to the venue SDK (e.g. betfairlightweight) and implement
    `quote`/`submit` against their API. NOT faked here - no credentials/keys
    exist on this machine, and real-money execution is gated in Config.
    """

    def __init__(self, name: str, api_key: str = "", client=None):
        self.name = name
        self.api_key = api_key
        self.client = client

    def quote(self, market_id: str, selection: str) -> Optional[Tick]:
        raise NotImplementedError("ExchangeVenue.quote: connect venue SDK and parse market book.")

    def submit(self, order: ChildOrder, price: float) -> ExecutionReport:
        raise NotImplementedError("ExchangeVenue.submit: route through venue SDK order gateway.")


class FillSimulator:
    """Market-impact + partial-fill + latency model. No free lunches."""

    def __init__(self, cfg: Config, rng: random.Random):
        self.cfg = cfg
        self.rng = rng

    def simulate(self, order: ChildOrder, seen_price: float, available_liquidity: float,
                 latency_ms: float = 50.0) -> ExecutionReport:
        # 1) latency: by the time your order arrives, price already moved
        latency_move = self.rng.gauss(0, self.cfg.tick_volatility) * seen_price * (latency_ms / 50.0)
        arrived_price = max(1.01, seen_price + latency_move)

        # 2) market impact: your size eats the book and moves the price
        participation = order.stake / max(available_liquidity, 1e-9)
        impact = participation * seen_price * 0.5  # 50% of participation as adverse move
        impacted_price = max(1.01, arrived_price - impact) if order.side == "BACK" else arrived_price + impact

        # 3) partial fill: if bigger than the queue, you only get what's there
        if participation > self.cfg.partial_fill_threshold:
            fill_ratio = min(1.0, available_liquidity / max(order.stake, 1e-9))
            # queue dynamics: you get filled as liquidity refreshes
            fill_ratio = max(fill_ratio, self.rng.uniform(0.3, 0.9))
        else:
            fill_ratio = 1.0
        filled = order.stake * fill_ratio

        avg_price = impacted_price
        slippage_bps = (seen_price - avg_price) / seen_price * 1e4 if order.side == "BACK" else (avg_price - seen_price) / seen_price * 1e4
        commission = filled * (avg_price - 1.0) * self.cfg.commission if order.side == "BACK" else 0.0
        return ExecutionReport(
            venue=order.venue, side=order.side, requested=order.stake,
            filled=filled, avg_price=avg_price, requested_price=seen_price,
            slippage_bps=abs(slippage_bps), commission=commission,
            partial=fill_ratio < 1.0, latency_ms=latency_ms,
        )


class SmartOrderRouter:
    """Splits a parent order across venues for best net price + stealth."""

    def __init__(self, cfg: Config, venues: List[Venue], rng: random.Random):
        self.cfg = cfg
        self.venues = venues
        self.rng = rng

    def route(self, market_id: str, selection: str, side: str, total_stake: float) -> List[ChildOrder]:
        # collect quotes across all venues, sort by best price
        quotes = []
        for v in self.venues:
            t = v.quote(market_id, selection)
            if t is None:
                continue
            price = t.back_price if side == "BACK" else t.lay_price
            depth = t.back_size if side == "BACK" else t.lay_size
            quotes.append((price, depth, v))
        if not quotes:
            return []
        quotes.sort(key=lambda q: q[0], reverse=(side == "BACK"))

        children: List[ChildOrder] = []
        remaining = total_stake
        for price, depth, v in quotes:
            if remaining <= 0:
                break
            # don't take more than ~70% of one venue's depth (stealth + fill)
            take = min(remaining, depth * 0.7)
            # randomise child stake to disguise intent / avoid rapid limiting
            jitter = self.rng.uniform(1 - self.cfg.stealth_stake_variance, 1 + self.cfg.stealth_stake_variance)
            take = max(self.cfg.min_stake_per_bet, take * jitter)
            if take <= 0:
                continue
            children.append(ChildOrder(v.name, market_id, selection, side, round(take, 4)))
            remaining -= take
        return children

    def execute(self, market_id: str, selection: str, side: str, total_stake: float) -> List[ExecutionReport]:
        children = self.route(market_id, selection, side, total_stake)
        reports: List[ExecutionReport] = []
        for c in children:
            venue = next(v for v in self.venues if v.name == c.venue)
            t = venue.quote(market_id, selection)
            price = t.back_price if side == "BACK" else t.lay_price
            reports.append(venue.submit(c, price))
        return reports
