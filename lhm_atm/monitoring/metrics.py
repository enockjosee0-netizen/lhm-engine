"""Monitoring: Prometheus metrics + a lightweight health/metrics endpoint.

The review's #7: you had Telegram alerts but flew blind on real-time PnL,
slippage, fill rate and error rate. This exposes them as Prometheus metrics
so Grafana can chart them, plus a /health + /metrics HTTP endpoint.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _HAVE_PROM = True
except Exception:  # pragma: no cover
    _HAVE_PROM = False


class Metrics:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and _HAVE_PROM
        if self.enabled:
            self.bets_total = Counter("lhm_bets_total", "Total bets submitted", ["side", "venue"])
            self.pnl = Gauge("lhm_pnl", "Running PnL in currency units")
            self.bankroll = Gauge("lhm_bankroll", "Current bankroll")
            self.slippage = Histogram("lhm_slippage_bps", "Fill slippage in bps", buckets=[1, 3, 5, 10, 25, 50])
            self.fill_rate = Gauge("lhm_fill_rate", "Fraction of requested stake filled")
            self.error_rate = Counter("lhm_errors_total", "Total errors")
            self.latency = Histogram("lhm_exec_latency_ms", "Execution latency ms", buckets=[5, 10, 25, 50, 100, 250])
            self.drawdown = Gauge("lhm_drawdown", "Current drawdown fraction")
            self.var = Gauge("lhm_portfolio_var", "Latest portfolio VaR (fraction of bankroll)")

    def record_fill(self, side: str, venue: str, slippage_bps: float, fill_ratio: float, latency_ms: float) -> None:
        if not self.enabled:
            return
        self.bets_total.labels(side=side, venue=venue).inc()
        self.slippage.observe(slippage_bps)
        self.fill_rate.set(fill_ratio)
        self.latency.observe(latency_ms)

    def record_pnl(self, pnl: float, bankroll: float, drawdown: float, var: float) -> None:
        if not self.enabled:
            return
        self.pnl.set(pnl)
        self.bankroll.set(bankroll)
        self.drawdown.set(drawdown)
        self.var.set(var)

    def record_error(self) -> None:
        if self.enabled:
            self.error_rate.inc()


class HealthServer:
    """Serves /metrics (Prometheus) and /health (JSON) on a background thread."""

    def __init__(self, metrics: Metrics, port: int = 8001, state: Dict = None):
        self.metrics = metrics
        self.port = port
        self.state = state or {}
        self._server = None
        self._thread = None

    def _handler(self):
        m = self.metrics
        st = self.state
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/metrics" and m.enabled:
                    body = generate_latest()
                    self.send_response(200)
                    self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                    self.end_headers()
                    self.wfile.write(body)
                elif self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "ok",
                        "bankroll": st.get("bankroll"),
                        "bets": st.get("bets"),
                        "pnl": st.get("pnl"),
                        "drawdown": st.get("drawdown"),
                        "prometheus": m.enabled,
                    }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            def log_message(self, *a):
                pass
        return H

    def start(self) -> None:
        if self._server is not None:
            return
        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), self._handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
