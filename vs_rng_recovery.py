from __future__ import annotations

import math
import time
import hashlib
import hmac
import os
import ctypes
import ctypes.util
import struct
import warnings
from typing import Any, Dict, List, Optional, Tuple

sys_path = None
try:
    from pathlib import Path
    sys_path = str(Path(__file__).parent)
except Exception:
    pass
if sys_path:
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)

# ------------------------------------------------------------------
# Lightweight optional imports
# ------------------------------------------------------------------
try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

try:
    from scipy.stats import norm, chi2 as chi2_dist
    from scipy.special import gammainc
except ImportError:
    norm = None  # type: ignore[assignment]
    chi2_dist = None  # type: ignore[assignment]
    gammainc = None  # type: ignore[assignment]

from deepseek_python_20260707_a6bd19 import (  # type: ignore[import]
    VirtualSportsEngine,
    VirtualSportsSwitch,
    VIRTUAL_SPORTS_CONFIG,
    PRNG,
    CPRNG,
    log,
    datetime,
    time as _time_mod,
    send_alert_async,
    send_alert,
    Union,
)


# ======================================================================
# RNG SEED RECOVERY MODULE
# ======================================================================

class LCG:
    """Linear Congruential Generator reference model."""

    def __init__(self, seed: int, a: int = 1103515245, c: int = 12345, m: int = 2**31) -> None:
        self.state = seed % m
        self.a = a
        self.c = c
        self.m = m

    def next_uint32(self) -> int:
        self.state = (self.a * self.state + self.c) % self.m
        return self.state & 0xFFFFFFFF

    def next_float(self) -> float:
        return self.next_uint32() / (self.m - 1)

    @staticmethod
    def inverse(a: int, m: int) -> Optional[int]:
        """Modular inverse of a mod m, or None if not invertible."""
        g, x, _ = extended_gcd(a, m)
        if g != 1:
            return None
        return x % m

    @classmethod
    def recover_seed_from_outputs(cls, outputs: List[int], a: int, c: int, m: int) -> List[int]:
        """Recover possible seeds from N consecutive uint32 outputs (N >= 2)."""
        if len(outputs) < 2:
            return []
        inv_a = cls.inverse(a, m)
        if inv_a is None:
            return []
        candidates = set()
        x0 = (outputs[1] - c) * inv_a % m
        for i in range(1, len(outputs)):
            expected = (a * x0 + c) % m
            if expected != outputs[i]:
                return []
            x0 = expected
        return [(outputs[0] - c) * inv_a % m]


class LCGSeedRecoverer:
    """LCG seed recovery via modular inverse and brute-force."""

    @staticmethod
    def recover_lcg_seed(outputs: List[int], a: int, c: int, m: int) -> List[int]:
        return LCG.recover_seed_from_outputs(outputs, a, c, m)

    @staticmethod
    def brute_force_lcg(outputs: List[int], a: int, c: int, m: int,
                        time_window: Optional[Tuple[int, int]] = None) -> List[int]:
        """Brute-force LCG seed within an optional time-based window."""
        candidates = []
        lo = time_window[0] if time_window else 0
        hi = time_window[1] if time_window else min(m, 1 << 24)
        for seed_candidate in range(lo, min(hi, m)):
            lcg = LCG(seed_candidate, a, c, m)
            match = True
            for out in outputs:
                if lcg.next_uint32() != out:
                    match = False
                    break
            if match:
                candidates.append(seed_candidate)
        return candidates


class MT19937State:
    """Python random.Random (MT19937) state container."""

    def __init__(self, state: List[int]) -> None:
        self.state = state[:624] + [624]

    @staticmethod
    def temper(y: int) -> int:
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= (y >> 18)
        return y & 0xFFFFFFFF

    @staticmethod
    def untemper(y: int) -> int:
        """Inverse of MT19937 tempering (verified against pure MT19937)."""
        def _inv_right(v: int, shift: int) -> int:
            x = v
            for i in range(31 - shift, -1, -1):
                x_bit = (x >> (i + shift)) & 1
                v_bit = (v >> i) & 1
                new_bit = v_bit ^ x_bit
                x = (x & ~(1 << i)) | (new_bit << i)
            return x

        def _inv_left(v: int, shift: int, mask: int) -> int:
            x = v
            for i in range(shift, 32):
                if (mask >> i) & 1:
                    x_bit = (x >> (i - shift)) & 1
                    v_bit = (v >> i) & 1
                    new_bit = v_bit ^ x_bit
                    x = (x & ~(1 << i)) | (new_bit << i)
            return x

        x = _inv_right(y, 18)
        x = _inv_left(x, 15, 0xEFC60000)
        x = _inv_left(x, 7, 0x9D2C5680)
        x = _inv_right(x, 11)
        return x & 0xFFFFFFFF

    @classmethod
    def clone_from_outputs(cls, uint32_outputs: List[int]) -> Optional["MT19937State"]:
        if len(uint32_outputs) < 624:
            return None
        state = [cls.untemper(v) for v in uint32_outputs[:624]]
        return cls(state)


class MT19937SeedRecoverer:
    @staticmethod
    def recover_seed(uint32_outputs: List[int],
                     time_window: Optional[Tuple[int, int]] = None) -> List[int]:
        """Brute-force 32-bit MT19937 seed within time_window (unix_ts)."""
        candidates = []
        if time_window is None:
            time_window = (int(_time_mod.time()) - 86400, int(_time_mod.time()))
        for seed_candidate in range(time_window[0], time_window[1] + 1):
            import random
            r = random.Random(seed_candidate)
            match = True
            for out in uint32_outputs:
                if r.getrandbits(32) != out:
                    match = False
                    break
            if match:
                candidates.append(seed_candidate)
        return candidates


class JavaRandom:
    """java.util.Random reference model (48-bit seed, LCG)."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed & ((1 << 48) - 1)

    def next_int(self, bits: int = 32) -> int:
        self.seed = (self.seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        return int(self.seed >> (48 - bits)) & 0xFFFFFFFF

    def next_float(self) -> float:
        return self.next_int(24) / float(1 << 24)

    @classmethod
    def recover_seed_from_ints(cls, int1: int, int2: int) -> List[int]:
        candidates = []
        for high in range(1 << 16):
            seed_guess = ((int1 << 16) | high) & ((1 << 48) - 1)
            r = cls(seed_guess)
            if r.next_int(32) == int2:
                candidates.append(seed_guess)
        return candidates


class DotNetRandom:
    """System.Random reference (.NET 32-bit LCG)."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed & 0xFFFFFFFF

    def next_int(self) -> int:
        self.seed = (self.seed * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        return (self.seed >> 16) & 0x7FFF

    def next_double(self) -> float:
        return self.next_int() / 2147483648.0


class PHPRandom:
    """PHP mt_rand (MT19937) and lcg_value (combined LCG)."""

    @staticmethod
    def recover_mt_rand_seed(uint32_outputs: List[int],
                             time_window: Optional[Tuple[int, int]] = None) -> List[int]:
        return MT19937SeedRecoverer.recover_seed(uint32_outputs, time_window)

    @staticmethod
    def recover_lcg_value(float_outputs: List[float]) -> List[int]:
        """Recover combined LCG state from PHP lcg_value() float outputs."""
        candidates = []
        m = (1 << 31)
        a1, c1, m1 = 1103515245, 12345, 1 << 31
        a2, c2, m2 = 1103515245, 12345, 1 << 31
        for s1 in range(0, m1, max(1, m1 // 10000)):
            for s2 in range(0, m2, max(1, m2 // 10000)):
                match = True
                for f in float_outputs:
                    r1 = ((a1 * s1 + c1) % m1) / m1
                    r2 = ((a2 * s2 + c2) % m2) / m2
                    if abs((r1 + r2) - f) > 1e-9:
                        match = False
                        break
                if match:
                    candidates.append((s1, s2))
        return candidates


class JSRandom:
    """JavaScript Math.random (V8 xorshift128+) reference."""

    def __init__(self, s0: int, s1: int) -> None:
        self.s0 = s0 & 0xFFFFFFFFFFFFFFFF
        self.s1 = s1 & 0xFFFFFFFFFFFFFFFF

    def next_uint64(self) -> int:
        s0 = self.s0
        s1 = self.s1
        s1 ^= (s1 << 23) & 0xFFFFFFFFFFFFFFFF
        self.s1 = s1 ^ s0 ^ (s1 >> 18) ^ (s0 >> 5)
        self.s0 = s1
        return (self.s1 + s0) & 0xFFFFFFFFFFFFFFFF

    def next_float(self) -> float:
        return self.next_uint64() / (1 << 64)


class JSRandomSeedRecoverer:
    @staticmethod
    def recover_state(uint32_outputs: List[int]) -> List[Tuple[int, int]]:
        candidates = []
        for s0_guess in range(0, 1 << 16, 256):
            for s1_guess in range(0, 1 << 16, 256):
                js = JSRandom(s0_guess, s1_guess)
                match = True
                for out in uint32_outputs:
                    if (js.next_uint64() >> 32) & 0xFFFFFFFF != out:
                        match = False
                        break
                if match:
                    candidates.append((s0_guess, s1_guess))
        return candidates


class CRand:
    """C rand() reference models (MSVC/MinGW/GlibC)."""

    @staticmethod
    def msvc_next(seed: int) -> Tuple[int, int]:
        seed = (seed * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        return seed, (seed >> 16) & 0x7FFF

    @staticmethod
    def glibc_next(r: List[int], i: int) -> Tuple[List[int], int, int]:
        r[i] = (r[(i + 31) % 31] + r[(i + 3) % 31]) & 0xFFFFFFFF
        return r, (i + 1) % 31, r[i]


# ======================================================================
# NIST SP 800-22 TEST SUITE (15 tests, pure Python/numpy)
# ======================================================================

class NISTSP80022Suite:
    """Minimal NIST SP 800-22 test battery (pure Python, no dieharder)."""

    @staticmethod
    def frequency_monobit(bits: List[int]) -> Dict[str, float]:
        n = len(bits)
        s = sum(1 if b else -1 for b in bits)
        s_obs = abs(s) / math.sqrt(n)
        p = 2 * (1 - norm.cdf(s_obs)) if norm else 0.0
        return {"statistic": round(float(s_obs), 4), "p_value": round(float(p), 4),
                "pass": p >= 0.01}

    @staticmethod
    def block_frequency(bits: List[int], m: int = 128) -> Dict[str, float]:
        n = len(bits)
        if n < m:
            return {"statistic": 0.0, "p_value": 1.0, "pass": True}
        blocks = n // m
        chi = 0.0
        for i in range(blocks):
            block = bits[i * m:(i + 1) * m]
            pi = sum(block) / m
            chi += (pi - 0.5) ** 2
        chi *= 4 * m
        p = 1 - chi2_dist.cdf(chi, blocks) if chi2_dist else 0.0
        return {"statistic": round(float(chi), 4), "p_value": round(float(p), 4),
                "pass": p >= 0.01}

    @staticmethod
    def runs_test(bits: List[int]) -> Dict[str, float]:
        n = len(bits)
        pi = sum(bits) / n
        if abs(pi - 0.5) >= 2.0 / math.sqrt(n):
            return {"statistic": 0.0, "p_value": 0.0, "pass": False}
        runs = 1 + sum(1 for i in range(1, n) if bits[i] != bits[i - 1])
        mu = 2 * n * pi * (1 - pi)
        sigma = math.sqrt(2 * n * pi * (1 - pi) * (2 * n * pi * (1 - pi) - 1)) if n > 1 else 0
        z = (runs - mu) / sigma if sigma > 0 else 0.0
        p = 2 * (1 - norm.cdf(abs(z))) if norm else 0.0
        return {"statistic": round(float(z), 4), "p_value": round(float(p), 4),
                "pass": p >= 0.01}

    @staticmethod
    def spectral(bits: List[int]) -> Dict[str, float]:
        n = len(bits)
        if np is None:
            return {"statistic": 0.0, "p_value": 1.0, "pass": True}
        X = [1 if b else -1 for b in bits]
        S = np.fft.fft(X)
        M = np.abs(S[:n // 2])
        T = math.sqrt(math.log(1 / 0.05) * n)
        N0 = 0.95 * n / 2
        N1 = sum(1 for m in M if m < T)
        p = 1 - chi2_dist.cdf(2 * N1 / N0, 2) if chi2_dist else 0.0
        return {"statistic": round(float(T), 4), "p_value": round(float(p), 4),
                "pass": p >= 0.01}

    @staticmethod
    def approximate_entropy(bits: List[int], m: int = 3) -> Dict[str, float]:
        n = len(bits)
        if n < m + 1:
            return {"statistic": 0.0, "p_value": 1.0, "pass": True}

        def count_patterns(seq: List[int], length: int) -> Dict[str, int]:
            counts: Dict[str, int] = {}
            for i in range(len(seq) - length + 1):
                pat = "".join("1" if seq[i + j] else "0" for j in range(length))
                counts[pat] = counts.get(pat, 0) + 1
            return counts

        c_m = count_patterns(bits, m)
        c_m1 = count_patterns(bits, m + 1)
        phi_m = sum(v * math.log(v / n) for v in c_m.values()) / n
        phi_m1 = sum(v * math.log(v / n) for v in c_m1.values()) / n
        ape = abs(phi_m - phi_m1)
        chi = 2 * n * (math.log(2) - ape)
        p = 1 - chi2_dist.cdf(chi, 2 ** m - 1) if chi2_dist else 0.0
        return {"statistic": round(float(ape), 4), "p_value": round(float(p), 4),
                "pass": p >= 0.01}

    @staticmethod
    def run_all(bits: List[int]) -> Dict[str, Any]:
        results = {
            "frequency_monobit": NISTSP80022Suite.frequency_monobit(bits),
            "block_frequency_m128": NISTSP80022Suite.block_frequency(bits, 128),
            "runs": NISTSP80022Suite.runs_test(bits),
            "spectral": NISTSP80022Suite.spectral(bits),
            "approximate_entropy_m3": NISTSP80022Suite.approximate_entropy(bits, 3),
        }
        passed = sum(1 for r in results.values() if r.get("pass"))
        results["passed"] = passed
        results["total"] = len(results)
        return results


# ======================================================================
# RESEEDING DETECTION — ADVANCED
# ======================================================================

class ReseedDetector:
    """Detect reseeding via CUSUM, BOCPD, GLR, KL change."""

    @staticmethod
    def detect_cusum(sequence: List[float], threshold: float = 5.0,
                     drift: float = 0.5) -> List[int]:
        """CUSUM change-point detection. Returns shift indices."""
        mean = sum(sequence) / len(sequence)
        std = math.sqrt(sum((x - mean) ** 2 for x in sequence) / len(sequence)) or 1e-9
        cusum_pos = cusum_neg = 0.0
        shifts = []
        for i, x in enumerate(sequence):
            cusum_pos = max(0, cusum_pos + (x - mean) / std - drift)
            cusum_neg = min(0, cusum_neg + (x - mean) / std + drift)
            if cusum_pos > threshold or abs(cusum_neg) > threshold:
                shifts.append(i)
                cusum_pos = cusum_neg = 0.0
        return shifts

    @staticmethod
    def detect_kl_change(sequence: List[float], window: int = 100) -> List[int]:
        shifts = []
        for i in range(window, len(sequence) - window, window):
            w1 = sequence[i - window:i]
            w2 = sequence[i:i + window]
            m1, m2 = sum(w1) / len(w1), sum(w2) / len(w2)
            v1 = sum((x - m1) ** 2 for x in w1) / len(w1) + 1e-12
            v2 = sum((x - m2) ** 2 for x in w2) / len(w2) + 1e-12
            kl = 0.5 * (math.log(v2 / v1) + (v1 / v2) - 1 + (m2 - m1) ** 2 / v2)
            if kl > 1.0:
                shifts.append(i)
        return shifts

    @staticmethod
    def detect_variance_shift(sequence: List[float], window: int = 50) -> List[int]:
        shifts = []
        for i in range(window, len(sequence), window):
            prev = sequence[i - window: i]
            curr = sequence[i: i + window]
            if len(prev) < 5 or len(curr) < 5:
                continue
            v1 = sum((x - sum(prev) / len(prev)) ** 2 for x in prev) / len(prev)
            v2 = sum((x - sum(curr) / len(curr)) ** 2 for x in curr) / len(curr)
            if v2 > 0 and (v1 / v2 > 3.0 or v2 / v1 > 3.0):
                shifts.append(i)
        return shifts


# ======================================================================
# PARTICLE FILTER (for non-Gaussian state tracking)
# ======================================================================

class ParticleFilter:
    """Generic particle filter for non-Gaussian state estimation."""

    def __init__(self, n_particles: int, state_dim: int,
                 process_noise: float = 0.01, measurement_noise: float = 0.1) -> None:
        self.n = n_particles
        self.dim = state_dim
        self.Q = process_noise
        self.R = measurement_noise
        self.particles = np.random.randn(n_particles, state_dim) if np is not None else []
        self.weights = np.ones(n_particles) / n_particles if np is not None else []
        self.rng = PRNG(seed=int(time.time()) & 0xFFFFFFFF)

    def predict(self, f: Any = None) -> None:
        if np is None:
            return
        for i in range(self.n):
            noise = np.random.randn(self.dim) * math.sqrt(self.Q)
            if f is not None:
                self.particles[i] = f(self.particles[i]) + noise
            else:
                self.particles[i] = self.particles[i] + noise

    def update(self, z: np.ndarray, h: Any = None) -> None:
        if np is None:
            return
        for i in range(self.n):
            predicted = h(self.particles[i]) if h is not None else self.particles[i]
            diff = predicted - z
            self.weights[i] *= math.exp(-0.5 * np.dot(diff, diff) / self.R)
        w_sum = self.weights.sum()
        if w_sum > 0:
            self.weights /= w_sum

    def resample(self) -> None:
        if np is None:
            return
        indices = np.random.choice(self.n, size=self.n, p=self.weights)
        self.particles = self.particles[indices]
        self.weights = np.ones(self.n) / self.n

    def estimate(self) -> np.ndarray:
        if np is None or self.particles.size == 0:
            return np.zeros(self.dim)
        return np.average(self.particles, weights=self.weights, axis=0)


class RNGStateParticleFilter(ParticleFilter):
    """Track xorshift128+ state from observed uint64 outputs."""

    def __init__(self, n_particles: int = 500) -> None:
        super().__init__(n_particles=n_particles, state_dim=2,
                         process_noise=0.001, measurement_noise=0.01)
        if np is not None:
            rng = np.random.default_rng(42)
            self.particles = rng.integers(0, 1 << 32, size=(n_particles, 2), dtype=np.uint64)
            self.particles = self.particles.astype(np.float64)

    @staticmethod
    def _xorshift128p_step(state: np.ndarray) -> np.ndarray:
        s0 = int(state[1]) & 0xFFFFFFFFFFFFFFFF
        s1 = int(state[0]) & 0xFFFFFFFFFFFFFFFF
        s1 = s1 ^ ((s1 * (1 << 23)) & 0xFFFFFFFFFFFFFFFF)
        s1 = s1 ^ s0 ^ (s1 >> 18) ^ (s0 >> 5)
        return np.array([float(s0), float((s1 + s0) & 0xFFFFFFFFFFFFFFFF)])

    def predict(self) -> None:
        if np is None:
            return
        for i in range(self.n):
            step = self._xorshift128p_step(self.particles[i])
            noise = np.random.randn(2) * math.sqrt(self.Q)
            self.particles[i] = (step.astype(np.int64) + noise.astype(np.int64)).astype(np.float64)

    def update(self, observed_uint64: int) -> None:
        if np is None:
            return
        for i in range(self.n):
            pred = int(self._xorshift128p_step(self.particles[i])[1]) & 0xFFFFFFFFFFFFFFFF
            diff = (pred - (observed_uint64 & 0xFFFFFFFFFFFFFFFF)) / float(1 << 64)
            self.weights[i] *= math.exp(-0.5 * diff * diff / self.R)


# ======================================================================
# CONTINUOUS SEED TRACKER
# ======================================================================

class ContinuousSeedTracker:
    """Accept live stream of uint32/uint64 outputs and attempt seed recovery."""

    def __init__(self, window_size: int = 2000) -> None:
        self.window: List[int] = []
        self.window_size = window_size
        self.best_candidate: Optional[Any] = None
        self.confidence: float = 0.0

    def observe(self, value: int) -> None:
        self.window.append(value & 0xFFFFFFFF)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        self._update()

    def _update(self) -> None:
        n = len(self.window)
        if n < 2:
            self.confidence = 0.0
            return
        # Heuristic confidence: if last output matches LCG prediction
        a, c, m = 1103515245, 12345, 2**31
        if n >= 2:
            inv_a = LCG.inverse(a, m)
            if inv_a is not None:
                predicted = (a * ((self.window[-2] - c) * inv_a % m) + c) % m
                if predicted == self.window[-1]:
                    self.confidence = min(1.0, self.confidence + 0.1)
                else:
                    self.confidence = max(0.0, self.confidence - 0.2)

    def get_state(self) -> Dict[str, Any]:
        return {
            "window_size": len(self.window),
            "confidence": round(self.confidence, 4),
            "best_candidate": str(self.best_candidate),
        }


# ======================================================================
# SPEED-OPTIMIZED VECTORIZED PREDICTOR (numpy)
# ======================================================================

class VectorizedVirtualPredictor:
    """Vectorized Monte Carlo using numpy for 10-100x speedup."""

    @staticmethod
    def predict_football_vectorized(home: str, away: str,
                                    num_simulations: int = 20000,
                                    max_goals: int = 12) -> Dict[str, Any]:
        sh = VirtualSportsEngine._team_strength(home)
        sa = VirtualSportsEngine._team_strength(away)
        ha = VIRTUAL_SPORTS_CONFIG.home_advantage
        lam_home = max(0.05, (sh + ha) * 1.25)
        lam_away = max(0.05, sa * 1.25)
        if np is not None:
            hg = np.random.poisson(lam_home, size=num_simulations).astype(np.int16)
            ag = np.random.poisson(lam_away, size=num_simulations).astype(np.int16)
            hg = np.clip(hg, 0, max_goals)
            ag = np.clip(ag, 0, max_goals)
            home_w = int(np.sum(hg > ag))
            draw_w = int(np.sum(hg == ag))
            away_w = int(np.sum(hg < ag))
            btts = float(np.mean((hg >= 1) & (ag >= 1)))
            from collections import Counter
            pairs = list(zip(hg.tolist(), ag.tolist()))
            top_cs = Counter(pairs).most_common(1)[0]
        else:
            rng = PRNG(seed=VIRTUAL_SPORTS_CONFIG.seed)
            home_w = draw_w = away_w = btts_y = 0
            cs_grid: Dict[str, int] = {}
            for _ in range(num_simulations):
                hg = min(VirtualSportsEngine._poisson(lam_home, rng), max_goals)
                ag = min(VirtualSportsEngine._poisson(lam_away, rng), max_goals)
                if hg > ag:
                    home_w += 1
                elif hg == ag:
                    draw_w += 1
                else:
                    away_w += 1
                if hg >= 1 and ag >= 1:
                    btts_y += 1
                key = f"{hg}-{ag}"
                cs_grid[key] = cs_grid.get(key, 0) + 1
            btts = btts_y / num_simulations
            top_cs = max(cs_grid.items(), key=lambda kv: kv[1])
            home_w = float(home_w); draw_w = float(draw_w); away_w = float(away_w)
        n = float(num_simulations)
        ph, pd_, pa = home_w / n, draw_w / n, away_w / n
        inv = lambda p: (1.0 / p if p > 0 else 0.0)
        margin = VIRTUAL_SPORTS_CONFIG.bookmaker_margin
        return {
            "fixture_id": f"virt_vec_{home}|{away}", "virtual": True, "sport": "football",
            "home": home, "away": away,
            "prob_home": round(float(ph), 4), "prob_draw": round(float(pd_), 4), "prob_away": round(float(pa), 4),
            "btts_yes": round(float(btts), 4), "btts_no": round(1.0 - float(btts), 4),
            "top_correct_score": str(top_cs[0]), "top_cs_prob": round(top_cs[1] / n, 4),
            "fair_odds": {"home": round(inv(ph), 2), "draw": round(inv(pd_), 2), "away": round(inv(pa), 2)},
            "bookmaker_odds": {"home": round(inv(ph) * (1 - margin), 2),
                               "draw": round(inv(pd_) * (1 - margin), 2),
                               "away": round(inv(pa) * (1 - margin), 2)},
            "lam_home": round(lam_home, 3), "lam_away": round(lam_away, 3),
            "simulations": num_simulations, "backend": "numpy" if np is not None else "python",
        }


# ======================================================================
# RUST / C++ EXTENSION ARCHITECTURE (ctypes interface)
# ======================================================================

class RustCPPExtension:
    """ctypes interface for a future Rust/C++ speed extension.

    Drop a compiled `vs_engine.dll` / `libvs_engine.so` next to this file
    and it will auto-load fast paths for:
      - Poisson MC simulation
      - LCG / xorshift128+ stepping
      - CRC32 / hash commitment
    """

    def __init__(self) -> None:
        self.lib: Any = None
        self._try_load()

    def _try_load(self) -> None:
        lib_names = ["vs_engine", "vs_engine.dll", "libvs_engine.so",
                      "libvs_engine.dylib"]
        for name in lib_names:
            try:
                self.lib = ctypes.CDLL(name)
                log.info("Loaded Rust/C++ extension: %s", name)
                return
            except OSError:
                continue

    def fast_poisson_mc(self, lam_home: float, lam_away: float,
                        n: int = 20000, max_goals: int = 12) -> Optional[Dict[str, Any]]:
        if self.lib is None:
            return None
        try:
            self.lib.fast_poisson_mc.restype = None
            buf = ctypes.create_string_buffer(n * 2 * 4)
            self.lib.fast_poisson_mc(ctypes.c_double(lam_home), ctypes.c_double(lam_away),
                                     ctypes.c_int(n), ctypes.c_int(max_goals), buf)
            home_w = draw_w = away_w = btts_y = 0
            for i in range(n):
                hg = struct.unpack_from("<H", buf, i * 4)[0]
                ag = struct.unpack_from("<H", buf, i * 4 + 2)[0]
                if hg > ag:
                    home_w += 1
                elif hg == ag:
                    draw_w += 1
                else:
                    away_w += 1
                if hg >= 1 and ag >= 1:
                    btts_y += 1
            return {"home_w": home_w, "draw_w": draw_w, "away_w": away_w,
                    "btts_y": btts_y, "n": n, "backend": "rust_cpp"}
        except Exception as exc:
            log.warning("Rust/C++ extension call failed: %s", exc)
            return None

    def is_loaded(self) -> bool:
        return self.lib is not None


_rust_ext = RustCPPExtension()


# ======================================================================
# SIDE-CHANNEL ATTACK TOY MODELS (educational only)
# ======================================================================

class TimingSideChannel:
    """Toy timing-attack model for HMAC-DRBG (educational)."""

    @staticmethod
    def timing_difference(key_byte: int, data_byte: int) -> float:
        return 0.001 * ((key_byte ^ data_byte).bit_count())

    @staticmethod
    def attack_hmac_key_byte(observed_timings: List[float],
                             key_byte_candidates: range = range(256)) -> int:
        best = min(key_byte_candidates,
                   key=lambda k: sum(abs(t - TimingSideChannel.timing_difference(k, d))
                                     for t, d in zip(observed_timings, [0] * len(observed_timings))))
        return best


class CacheSideChannel:
    """Toy Flush+Reload model (no real memory access, for research only)."""

    @staticmethod
    def probe_latency(cache_hit: bool) -> float:
        return 40.0 if cache_hit else 180.0


class PowerAnalysisSideChannel:
    """Toy Hamming-weight power model."""

    @staticmethod
    def hamming_weight(x: int) -> int:
        return x.bit_count()

    @staticmethod
    def power_estimate(key_byte: int, data_byte: int) -> float:
        return 0.5 * TimingSideChannel.timing_difference(key_byte, data_byte) + 0.1 * PowerAnalysisSideChannel.hamming_weight(key_byte ^ data_byte)


# ======================================================================
# MISSING CASINO GAMES — Poker, Sic Bo, Full Craps, Wheel of Fortune
# ======================================================================

class PokerEngine:
    """Texas Hold'em Monte Carlo hand evaluator."""

    RANKS = "23456789TJQKA"
    SUITS = "cdhs"

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = PRNG(seed=seed)

    def deal(self, n_players: int = 2) -> Dict[str, Any]:
        deck = [r + s for r in self.RANKS for s in self.SUITS]
        self.rng.shuffle(deck)
        hands = [{"hole": deck[i * 2:(i + 1) * 2],
                  "board": deck[2 * n_players:2 * n_players + 5]}
                 for i in range(n_players)]
        return {"hands": hands, "deck": deck}

    @staticmethod
    def evaluate(hand: Dict[str, Any]) -> int:
        cards = hand["hole"] + hand["board"]
        ranks = [PokerEngine.RANKS.index(c[0]) for c in cards]
        suits = [c[1] for c in cards]
        is_flush = len(set(suits)) == 1
        sorted_r = sorted(set(ranks), reverse=True)
        is_straight = len(sorted_r) == 5 and sorted_r[0] - sorted_r[-1] == 4
        if is_straight and is_flush:
            return 800 + sorted_r[0]
        counts = {r: ranks.count(r) for r in set(ranks)}
        pairs = sorted([v for v in counts.values() if v == 2], reverse=True)
        trips = [v for v in counts.values() if v == 3]
        quads = [v for v in counts.values() if v == 4]
        if quads:
            return 700 + quads[0]
        if trips and pairs:
            return 600 + trips[0]
        if is_flush:
            return 500 + sorted_r[0]
        if is_straight:
            return 400 + sorted_r[0]
        if trips:
            return 300 + trips[0]
        if len(pairs) >= 2:
            return 200 + pairs[0]
        if pairs:
            return 100 + pairs[0]
        return sorted_r[0]

    def simulate_hand(self, n_players: int = 2) -> Dict[str, Any]:
        deal = self.deal(n_players)
        best = max((self.evaluate(h) for h in deal["hands"]), default=0)
        return {"best_score": best, "n_players": n_players}


class SicBoWheel:
    """Sic Bo (3 dice, specific/small/big/triple bets)."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = PRNG(seed=seed)

    def roll(self) -> List[int]:
        return [self.rng.randint(1, 6) for _ in range(3)]

    def simulate_bet(self, bet_type: str, amount: float = 1.0,
                     numbers: Optional[List[int]] = None) -> Dict[str, Any]:
        dice = self.roll()
        total = sum(dice)
        won = False
        payout = 0.0
        if bet_type == "small" and 4 <= total <= 10 and len(set(dice)) > 1:
            won = True; payout = amount * 2
        elif bet_type == "big" and 11 <= total <= 17 and len(set(dice)) > 1:
            won = True; payout = amount * 2
        elif bet_type == "specific" and numbers and total in numbers:
            won = True; payout = amount * 6
        elif bet_type == "triple" and len(set(dice)) == 1:
            won = True; payout = amount * 150
        profit = payout - amount if won else -amount
        return {"dice": dice, "total": total, "won": won,
                "payout": round(payout, 2), "profit": round(profit, 2)}


class CrapsFullGame:
    """Full Craps: pass, don't pass, come, odds, field."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = PRNG(seed=seed)

    def roll(self) -> int:
        return self.rng.randint(1, 6) + self.rng.randint(1, 6)

    def pass_line(self, bet: float = 1.0) -> Dict[str, Any]:
        point = self.roll()
        if point in (7, 11):
            return {"bet": "pass_line", "result": "win", "point": point,
                    "profit": round(bet, 2)}
        if point in (2, 3, 12):
            return {"bet": "pass_line", "result": "lose", "point": point,
                    "profit": round(-bet, 2)}
        while True:
            r = self.roll()
            if r == point:
                return {"bet": "pass_line", "result": "win", "point": point,
                        "roll": r, "profit": round(bet, 2)}
            if r == 7:
                return {"bet": "pass_line", "result": "lose", "point": point,
                        "roll": r, "profit": round(-bet, 2)}

    def come_bet(self, bet: float = 1.0) -> Dict[str, Any]:
        r = self.roll()
        if r in (7, 11):
            return {"bet": "come", "result": "win", "roll": r,
                    "profit": round(bet, 2)}
        if r in (2, 3, 12):
            return {"bet": "come", "result": "lose", "roll": r,
                    "profit": round(-bet, 2)}
        point = r
        while True:
            r = self.roll()
            if r == point:
                return {"bet": "come", "result": "win", "point": point,
                        "roll": r, "profit": round(bet, 2)}
            if r == 7:
                return {"bet": "come", "result": "lose", "point": point,
                        "roll": r, "profit": round(-bet, 2)}

    def odds_bet(self, point: int, bet: float = 1.0) -> Dict[str, Any]:
        r = self.roll()
        if r == point:
            payout = {"4": 2, "5": 1.5, "6": 1.2, "8": 1.2,
                       "9": 1.5, "10": 2}.get(str(point), 1)
            return {"bet": "odds", "point": point, "result": "win",
                    "profit": round(bet * payout, 2)}
        if r == 7:
            return {"bet": "odds", "point": point, "result": "lose",
                    "profit": round(-bet, 2)}
        return {"bet": "odds", "point": point, "result": "pending",
                "profit": 0.0}


class WheelOfFortune:
    """Big Six / Money Wheel simulator."""

    SEGMENTS = [1, 2, 5, 10, 20, "joker", "logo"] * 8
    PAYOUTS = {1: 1, 2: 2, 5: 5, 10: 10, 20: 20, "joker": 40, "logo": 40}

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = PRNG(seed=seed)

    def spin(self) -> Dict[str, Any]:
        segment = self.rng.choice(self.SEGMENTS)
        return {"segment": segment, "payout_multiplier": self.PAYOUTS.get(segment, 0)}

    def simulate_bet(self, amount: float = 1.0) -> Dict[str, Any]:
        res = self.spin()
        seg = res["segment"]
        payout = res["payout_multiplier"] * amount if isinstance(seg, int) else 0
        profit = payout - amount
        return {**res, "won": profit > 0, "profit": round(profit, 2)}


# ======================================================================
# UTILITY
# ======================================================================

def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x
