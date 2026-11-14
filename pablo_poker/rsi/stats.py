"""Statistics for the RSI lab: copied unchanged from lab/stats.py (pure standard library).

Deterministic SHA-256 random stream, Bonferroni-adjusted alpha, percentile bootstrap
interval, minimum detectable effect, drawdown and payoff summaries."""
from __future__ import annotations

import hashlib
import math
from fractions import Fraction
from statistics import NormalDist


class DeterministicRandom:
    """SHA-256 counter stream. `below(n)` is unbiased (rejection sampling)."""

    def __init__(self, seed: str):
        self._seed, self._counter, self._buffer = seed.encode("utf-8"), 0, b""

    def _bytes(self, n: int) -> bytes:
        while len(self._buffer) < n:
            self._buffer += hashlib.sha256(self._seed + self._counter.to_bytes(8, "big")).digest()
            self._counter += 1
        out, self._buffer = self._buffer[:n], self._buffer[n:]
        return out

    def below(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be positive")
        limit = (1 << 64) - ((1 << 64) % n)
        while True:
            x = int.from_bytes(self._bytes(8), "big")
            if x < limit:
                return x % n


def adjusted_alpha(alpha: Fraction, trials: int) -> Fraction:
    """Bonferroni: the more configurations were tried on the same data, the stricter the level."""
    if trials < 1:
        raise ValueError("at least one trial")
    return Fraction(alpha) / trials


def bootstrap_mean_interval(values: list[int], *, alpha: Fraction, resamples: int, seed: str) -> tuple[Fraction, Fraction]:
    """Percentile bootstrap interval for the mean at two-sided level alpha."""
    n = len(values)
    if n == 0:
        raise ValueError("no data")
    rng = DeterministicRandom(seed)
    sums = sorted(sum(values[rng.below(n)] for _ in range(n)) for _ in range(resamples))
    tail = float(alpha) / 2
    lo_index = min(resamples - 1, max(0, math.floor(tail * resamples)))
    hi_index = min(resamples - 1, max(0, math.ceil((1 - tail) * resamples) - 1))
    return Fraction(sums[lo_index], n), Fraction(sums[hi_index], n)


def sample_sd(values: list) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((float(v) - float(mean)) ** 2 for v in values) / (n - 1))


def minimum_detectable_effect(*, sd: float, n: int, alpha: Fraction, power: Fraction) -> float:
    """Smallest true mean difference a sample of n can detect (two-sided alpha, given power), normal approximation."""
    if n < 2:
        raise ValueError("need at least two observations")
    z = NormalDist().inv_cdf(1 - float(alpha) / 2) + NormalDist().inv_cdf(float(power))
    return z * sd / math.sqrt(n)


def max_drawdown(curve: list[int]) -> dict:
    out = {"amount": 0, "fraction": Fraction(0), "peak_index": None, "trough_index": None, "longest_underwater_points": 0}
    peak, peak_i, under, longest = None, 0, 0, 0
    for i, v in enumerate(curve):
        if peak is None or v >= peak:
            peak, peak_i, under = v, i, 0
            continue
        under += 1
        longest = max(longest, under)
        if peak - v > out["amount"]:
            out.update(amount=peak - v, fraction=Fraction(peak - v, peak) if peak > 0 else Fraction(0), peak_index=peak_i, trough_index=i)
    out["longest_underwater_points"] = longest
    return out


def payoff_summary(pnls: list[int]) -> dict:
    wins, losses = [p for p in pnls if p > 0], [p for p in pnls if p < 0]
    n = len(pnls)
    return {"trades": n, "total": sum(pnls), "win_rate": Fraction(len(wins), n) if n else None,
            "average_win": Fraction(sum(wins), len(wins)) if wins else None, "average_loss": Fraction(sum(losses), len(losses)) if losses else None,
            "payoff_ratio": Fraction(sum(wins) * len(losses), len(wins) * -sum(losses)) if wins and losses else None,
            "profit_factor": Fraction(sum(wins), -sum(losses)) if wins and losses else None,
            "worst": min(pnls) if pnls else None, "best": max(pnls) if pnls else None}


def risk_of_ruin(pnls: list[int], *, start: int, floor: int, trades: int, paths: int, seed: str) -> Fraction:
    """Share of resampled trade sequences in which equity falls below `floor` (the capital-exhausted level)."""
    if not pnls or paths <= 0 or trades <= 0:
        return Fraction(0)
    rng = DeterministicRandom(seed)
    ruined = 0
    for _ in range(paths):
        equity = start
        for _ in range(trades):
            equity += pnls[rng.below(len(pnls))]
            if equity < floor:
                ruined += 1
                break
    return Fraction(ruined, paths)
