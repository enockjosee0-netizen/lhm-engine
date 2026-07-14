#!/usr/bin/env python3
# pyright: reportMissingImports=false
from __future__ import annotations
"""
LHM Prediction Runner
Runs the listed fixtures through the LHM advanced core math and prints
a full prediction table including:
  - Model 1X2 probabilities
  - Bookie implied probabilities (from generated/synthetic odds)
  - Correct score top probabilities
  - BTTS probability
  - Over/Under 2.5
  - Edge / Kelly stake suggestion
Optionally sends results to Telegram if env vars are set.
"""
import os, sys, json, time, math, random, hashlib
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import scipy.stats as stats
    from scipy.stats import poisson, skellam, norm
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ------------------------------------------------------------------
# Math helpers
# ------------------------------------------------------------------
def _poisson_pmf(k: int, lam: float) -> float:
    lam = max(float(lam), 1e-9)
    if k < 0:
        return 0.0
    if HAS_NUMPY:
        log_p = -lam + k * np.log(lam) - np.sum(np.log(np.arange(1, k + 1, dtype=np.float64)))
        return float(np.exp(log_p)) if np.isfinite(log_p) else 0.0
    log_p = -lam + k * math.log(lam) - sum(math.log(i) for i in range(1, k + 1))
    return math.exp(log_p) if math.isfinite(log_p) else 0.0

def _bivariate_poisson_pmf(hg: int, ag: int, lam_h: float, lam_a: float, lam3: float) -> float:
    p = _poisson_pmf(hg, lam_h) * _poisson_pmf(ag, lam_a)
    if lam3 > 1e-9:
        if HAS_NUMPY:
            p *= float(np.exp(-lam3))
        else:
            p *= math.exp(-lam3)
        if hg == ag:
            common = lam3 / math.sqrt(lam_h * lam_a + 1e-9)
            p *= (1.0 + common)
    return max(p, 0.0)

def _copula_corrected_probs(lam_h: float, lam_a: float, cov_factor: float = 0.2, max_goals: int = 10):
    lam3 = max(0.01, cov_factor * math.sqrt(lam_h * lam_a))
    size = max_goals + 1
    probs = np.zeros((size, size), dtype=np.float64) if HAS_NUMPY else [[0.0]*size for _ in range(size)]
    total = 0.0
    for hg in range(size):
        for ag in range(size):
            p = _bivariate_poisson_pmf(hg, ag, lam_h, lam_a, lam3)
            if HAS_NUMPY:
                probs[hg, ag] = p
            else:
                probs[hg][ag] = p
            total += p
    if total > 1e-12:
        if HAS_NUMPY:
            probs /= total
        else:
            probs = [[p/total for p in row] for row in probs]
    return probs

def _extract_1x2(probs) -> Tuple[float, float, float]:
    home = draw = away = 0.0
    if HAS_NUMPY and hasattr(probs, 'shape'):
        size = probs.shape[0]
        for hg in range(size):
            for ag in range(size):
                p = float(probs[hg, ag])
                if hg > ag:
                    home += p
                elif hg == ag:
                    draw += p
                else:
                    away += p
    else:
        size = len(probs)
        for hg in range(size):
            for ag in range(size):
                p = float(probs[hg][ag])
                if hg > ag:
                    home += p
                elif hg == ag:
                    draw += p
                else:
                    away += p
    return home, draw, away

def _top_correct_scores(probs, top_n: int = 8) -> List[Tuple[str, float]]:
    scores = []
    if HAS_NUMPY and hasattr(probs, 'shape'):
        size = probs.shape[0]
        for hg in range(size):
            for ag in range(size):
                p = float(probs[hg, ag])
                if p > 1e-4:
                    scores.append((f"{hg}-{ag}", p))
    else:
        size = len(probs)
        for hg in range(size):
            for ag in range(size):
                p = float(probs[hg][ag])
                if p > 1e-4:
                    scores.append((f"{hg}-{ag}", p))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

def _btts_probability(probs) -> float:
    total = 0.0
    if HAS_NUMPY and hasattr(probs, 'shape'):
        size = probs.shape[0]
        for hg in range(1, size):
            for ag in range(1, size):
                total += float(probs[hg, ag])
    else:
        size = len(probs)
        for hg in range(1, size):
            for ag in range(1, size):
                total += float(probs[hg][ag])
    return total

def _over_under_prob(probs, line: float = 2.5) -> Tuple[float, float]:
    if HAS_NUMPY and hasattr(probs, 'shape'):
        size = probs.shape[0]
        over = sum(float(probs[hg, ag]) for hg in range(size) for ag in range(size) if hg + ag > line)
        under = 1.0 - over
        return over, under
    size = len(probs)
    over = sum(float(probs[hg][ag]) for hg in range(size) for ag in range(size) if hg + ag > line)
    under = 1.0 - over
    return over, under

def _implied_prob(odds: float) -> float:
    return 1.0 / max(odds, 1.001)

def _kelly_stake(prob: float, odds: float, bankroll: float = 1000.0, frac: float = 0.25) -> float:
    b = max(odds - 1.0, 0.01)
    q = 1.0 - prob
    kelly = (b * prob - q) / b
    kelly = max(0.0, min(kelly, 0.05))
    return bankroll * kelly * frac

def _team_strength(team_name: str, seed_offset: int = 0) -> float:
    h = hashlib.md5(f"{team_name.lower()}:{seed_offset}".encode()).hexdigest()
    n = int(h[:8], 16)
    return 0.6 + (n % 10000) / 10000.0 * 0.8

def _generate_odds(home_strength: float, away_strength: float, is_women: bool = False, league_tier: str = "tier3") -> Dict[str, float]:
    base_home = 1.0 / max(home_strength, 0.1)
    base_away = 1.0 / max(away_strength, 0.1)
    draw = 3.2 + random.uniform(-0.4, 0.4)
    if is_women:
        draw += 0.3
    if league_tier == "tier2":
        draw += 0.2
    home_odds = max(1.1, min(8.0, base_home * random.uniform(0.9, 1.1)))
    away_odds = max(1.1, min(8.0, base_away * random.uniform(0.9, 1.1)))
    draw_odds = max(1.1, min(8.0, draw * random.uniform(0.9, 1.1)))
    return {
        "home": round(home_odds, 2), "draw": round(draw_odds, 2), "away": round(away_odds, 2),
        "btts_yes": round(random.uniform(1.6, 2.4), 2), "btts_no": round(random.uniform(1.6, 2.4), 2),
        "over_2_5": round(random.uniform(1.7, 2.5), 2), "under_2_5": round(random.uniform(1.7, 2.5), 2)
    }

# ------------------------------------------------------------------
# Match list
# ------------------------------------------------------------------
MATCHES = [
    {"home": "RKC Third Coast", "away": "River Light FC", "league": "USL", "tier": "tier3", "women": False},
    {"home": "Brave SC", "away": "Shark Coast FC", "league": "USL", "tier": "tier3", "women": False},
    {"home": "CS Emelec", "away": "Barcelona SC", "league": "Ecuador", "tier": "tier1", "women": False},
    {"home": "CF Montreal", "away": "Vancouver FC", "league": "MLS", "tier": "tier1", "women": False},
    {"home": "CD Real Tomayapo", "away": "Independiente Petrolero", "league": "Bolivia", "tier": "tier2", "women": False},
    {"home": "Ballard FC", "away": "Snohomish United", "league": "USL2", "tier": "tier3", "women": False},
    {"home": "El Farolito", "away": "Sun City FC", "league": "NPSL", "tier": "tier3", "women": False},
    {"home": "San Juan FC", "away": "Marin FC Legends", "league": "NPSL", "tier": "tier3", "women": False},
    {"home": "CR Brasil AL", "away": "Goias EC GO", "league": "Serie B", "tier": "tier2", "women": False},
    {"home": "Lakeland United FC USL 2", "away": "Fort Lauderdale United FC", "league": "USL2", "tier": "tier3", "women": False},
    {"home": "New Haven United FC", "away": "American Soccer Club New York", "league": "UPSL", "tier": "tier3", "women": False},
    {"home": "Rubio Nu Women", "away": "Sportivo Ameliano Women", "league": "Paraguay W", "tier": "tier2", "women": True},
    {"home": "Botafogo FC PB", "away": "AD Confianca SE", "league": "Serie C", "tier": "tier2", "women": False},
    {"home": "Bigfoot FC", "away": "Midlakes United", "league": "USL2", "tier": "tier3", "women": False},
    {"home": "Universidad Catolica Women", "away": "Coquimbo Unido Women", "league": "Chile W", "tier": "tier2", "women": True},
    {"home": "Weston FC", "away": "Miami AC", "league": "USL2", "tier": "tier3", "women": False},
    {"home": "Denver Summit FC Women", "away": "Houston Dash Women", "league": "NWSL", "tier": "tier1", "women": True},
    {"home": "RKC Third Coast", "away": "River Light FC", "league": "USL", "tier": "tier3", "women": False},
    {"home": "Brave SC", "away": "Shark Coast FC", "league": "USL", "tier": "tier3", "women": False},
    {"home": "CS Emelec", "away": "Barcelona SC", "league": "Ecuador", "tier": "tier1", "women": False},
    {"home": "CF Montreal", "away": "Vancouver FC", "league": "MLS", "tier": "tier1", "women": False},
]

# ------------------------------------------------------------------
# Main prediction loop
# ------------------------------------------------------------------
def run_predictions(matches: List[Dict[str, str]], cov_base: float = 0.22) -> List[Dict[str, Any]]:
    results = []
    for idx, m in enumerate(matches):
        home = m["home"]
        away = m["away"]
        women = m.get("women", False)
        tier = m.get("tier", "tier3")
        seed = int(hashlib.md5(f"{home}:{away}:{idx}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        home_str = _team_strength(home, seed_offset=0)
        away_str = _team_strength(away, seed_offset=1000)
        if tier == "tier1":
            home_str *= 1.1
            away_str *= 1.0
            cov = cov_base * 0.9
        elif tier == "tier2":
            home_str *= 1.0
            away_str *= 0.95
            cov = cov_base * 1.05
        else:
            home_str *= random.uniform(0.8, 1.0)
            away_str *= random.uniform(0.7, 0.95)
            cov = cov_base * random.uniform(0.9, 1.3)
        lam_home = max(0.3, home_str * random.uniform(0.8, 1.3))
        lam_away = max(0.2, away_str * random.uniform(0.6, 1.1))
        if women:
            lam_home *= 0.85
            lam_away *= 0.85
        cov = max(0.05, min(0.4, cov))
        regime = "normal"
        if tier == "tier3":
            regime = rng.choice(["normal", "normal", "high_intensity"])
        else:
            regime = "normal"
        probs = _copula_corrected_probs(lam_home, lam_away, cov, max_goals=10)
        home_p, draw_p, away_p = _extract_1x2(probs)
        total_p = home_p + draw_p + away_p
        if total_p > 1e-6:
            home_p /= total_p
            draw_p /= total_p
            away_p /= total_p
        top_scores = _top_correct_scores(probs, top_n=8)
        btts = _btts_probability(probs)
        over, under = _over_under_prob(probs, 2.5)
        odds = _generate_odds(home_str, away_str, is_women=women, league_tier=tier)
        bookie_home = _implied_prob(odds["home"])
        bookie_draw = _implied_prob(odds["draw"])
        bookie_away = _implied_prob(odds["away"])
        bookie_total = bookie_home + bookie_draw + bookie_away
        bookie_home /= bookie_total
        bookie_draw /= bookie_total
        bookie_away /= bookie_total
        bookie_btts = _implied_prob(odds["btts_yes"]) / (_implied_prob(odds["btts_yes"]) + _implied_prob(odds["btts_no"]))
        bookie_over = _implied_prob(odds["over_2_5"]) / (_implied_prob(odds["over_2_5"]) + _implied_prob(odds["under_2_5"]))
        edge_home = home_p - bookie_home
        edge_draw = draw_p - bookie_draw
        edge_away = away_p - bookie_away
        max_edge = max(edge_home, edge_draw, edge_away)
        best_outcome = "H" if max_edge == edge_home else ("D" if max_edge == edge_draw else "A")
        kelly = _kelly_stake(
            (home_p if best_outcome == "H" else (draw_p if best_outcome == "D" else away_p)),
            (odds["home"] if best_outcome == "H" else (odds["draw"] if best_outcome == "D" else odds["away"])),
            bankroll=1000.0,
            frac=0.25,
        )
        results.append({
            "fixture": f"{home} vs {away}",
            "league": m.get("league", ""),
            "model_home": round(home_p, 4),
            "model_draw": round(draw_p, 4),
            "model_away": round(away_p, 4),
            "bookie_home": round(bookie_home, 4),
            "bookie_draw": round(bookie_draw, 4),
            "bookie_away": round(bookie_away, 4),
            "edge_home": round(edge_home, 4),
            "edge_draw": round(edge_draw, 4),
            "edge_away": round(edge_away, 4),
            "max_edge": round(max_edge, 4),
            "best_outcome": best_outcome,
            "lam_home": round(lam_home, 3),
            "lam_away": round(lam_away, 3),
            "cov_factor": round(cov, 3),
            "btts_model": round(btts, 4),
            "btts_bookie": round(bookie_btts, 4),
            "over_2_5_model": round(over, 4),
            "over_2_5_bookie": round(bookie_over, 4),
            "regime": regime,
            "top_scores": top_scores,
            "kelly_stake": round(kelly, 2),
            "odds_home": odds["home"],
            "odds_draw": odds["draw"],
            "odds_away": odds["away"],
        })
    return results

def build_table(results: List[Dict[str, Any]]) -> str:
    header = (
        f"{'#':<3} {'Fixture':<42} {'M_H':>7} {'M_D':>7} {'M_A':>7} "
        f"{'B_H':>7} {'B_D':>7} {'B_A':>7} {'Edge':>6} {'BTTS':>7} {'O2.5':>7} "
        f"{'TopScore':>10} {'Kelly':>7}"
    )
    sep = "-" * 175
    lines = [sep, header, sep]
    for i, r in enumerate(results, 1):
        top_scores_str = "; ".join(f"{s}:{p:.3f}" for s, p in r["top_scores"][:2])
        line = (
            f"{i:<3} {r['fixture']:<42} {r['model_home']:>7.3f} {r['model_draw']:>7.3f} {r['model_away']:>7.3f} "
            f"{r['bookie_home']:>7.3f} {r['bookie_draw']:>7.3f} {r['bookie_away']:>7.3f} "
            f"{r['max_edge']:>6.3f} {r['btts_model']:>7.3f} {r['over_2_5_model']:>7.3f} "
            f"{top_scores_str:>10} {r['kelly_stake']:>7.2f}"
        )
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)

def build_detailed_results(results: List[Dict[str, Any]]) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"\n{'='*90}")
        lines.append(f"MATCH {i}: {r['fixture']} [{r['league']}]")
        lines.append(f"{'='*90}")
        lines.append(f"Regime            : {r['regime']}")
        lines.append(f"Lambda params     : home={r['lam_home']}, away={r['lam_away']}, cov={r['cov_factor']}")
        lines.append(f"Odds              : Home={r['odds_home']}, Draw={r['odds_draw']}, Away={r['odds_away']}")
        lines.append(f"Model 1X2         : H={r['model_home']:.4f}, D={r['model_draw']:.4f}, A={r['model_away']:.4f}")
        lines.append(f"Bookie 1X2        : H={r['bookie_home']:.4f}, D={r['bookie_draw']:.4f}, A={r['bookie_away']:.4f}")
        lines.append(f"Edge              : H={r['edge_home']:+.4f}, D={r['edge_draw']:+.4f}, A={r['edge_away']:+.4f}  => Best={r['best_outcome']} ({r['max_edge']:+.4f})")
        lines.append(f"BTTS              : Model={r['btts_model']:.4f}, Bookie={r['btts_bookie']:.4f}")
        lines.append(f"Over/Under 2.5    : Model O={r['over_2_5_model']:.4f}, Bookie O={r['over_2_5_bookie']:.4f}")
        lines.append(f"Correct scores    : " + "; ".join(f"{s}:{p:.4f}" for s, p in r["top_scores"][:6]))
        lines.append(f"Kelly stake ($1k)  : ${r['kelly_stake']:.2f}")
    return "\n".join(lines)

async def try_send_telegram(text: str, token: str = "", chat_id: str = "", dry_run: bool = True) -> bool:
    if dry_run:
        print("\n[TELEGRAM DRY RUN] Would send this to Telegram (truncated):")
        print(text[:1200])
        return True
    if not token or not chat_id:
        print("[TELEGRAM] No token/chat_id provided. Set env vars or edit runner.")
        return False
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            chunks = [text[i:i+3800] for i in range(0, len(text), 3800)]
            for chunk in chunks:
                async with session.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"},
                    timeout=20,
                ) as resp:
                    if resp.status != 200:
                        txt = await resp.text()
                        print(f"[TELEGRAM] Failed: {resp.status} {txt}")
                        return False
            return True
    except Exception as exc:
        print(f"[TELEGRAM] Error: {exc}")
        return False

def main():
    print("="*90)
    print("LHM ADVANCED CORE — PREDICTION RUNNER")
    print("="*90)
    results = run_predictions(MATCHES, cov_base=0.22)
    table = build_table(results)
    detailed = build_detailed_results(results)
    print("\n\nFULL PREDICTION TABLE\n")
    print(table)
    print("\n\nDETAILED RESULTS\n")
    print(detailed)
    token = os.environ.get("LHM_TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("LHM_TELEGRAM_CHAT_ID", "")
    dry_run = not (token and chat_id)
    message = f"<pre>{table}</pre>\n\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    import asyncio
    asyncio.run(try_send_telegram(message, token=token, chat_id=chat_id, dry_run=dry_run))
    return results

if __name__ == "__main__":
    main()
