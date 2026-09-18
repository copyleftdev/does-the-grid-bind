"""The distribution, not the point estimate.

The article closes by asking for the distribution. This produces it, and then
asks the question that matters more: WHICH uncertain input decides the answer.

Division of labour between this module and `exact.py` is deliberate. Floating
point is used here to find the shape of the surface -- where the mass sits,
which way it is skewed, which parameter moves it. No headline number leaves
this module. Anything that decides something gets recomputed in exact rational
arithmetic from the sampled quantiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Sequence

import numpy as np

from .exact import Interval
from .regime import Regime

SEED = 20260918  # fixed: a run that cannot be reproduced is an anecdote


@dataclass(frozen=True)
class Dist:
    """A parameter's uncertainty, stated as a distribution over an interval.

    `kind` records how the interval was turned into a distribution, because
    that choice is an assumption and deserves to be visible. `uniform` says the
    source gave a range and nothing about where inside it the truth sits;
    `triangular` says a central figure was given with a range around it;
    `lognormal_ci` says the source reported a multiplicative confidence
    interval.
    """

    key: str
    lo: float
    hi: float
    kind: str = "uniform"
    mode: float | None = None

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.lo == self.hi:
            return np.full(n, self.lo)
        if self.kind == "uniform":
            return rng.uniform(self.lo, self.hi, n)
        if self.kind == "triangular":
            m = self.mode if self.mode is not None else (self.lo + self.hi) / 2
            return rng.triangular(self.lo, m, self.hi, n)
        if self.kind == "lognormal_ci":
            # lo/hi read as a 90% interval on a positive quantity
            mu = (np.log(self.lo) + np.log(self.hi)) / 2
            sigma = (np.log(self.hi) - np.log(self.lo)) / (2 * 1.6448536269514722)
            return rng.lognormal(mu, sigma, n)
        raise ValueError(f"unknown distribution kind {self.kind!r}")

    @property
    def interval(self) -> Interval:
        return Interval.of(Fraction(self.lo).limit_denominator(10**9),
                           Fraction(self.hi).limit_denominator(10**9))


def _regime_codes(S: np.ndarray, E: np.ndarray, B: np.ndarray) -> np.ndarray:
    """0 = A free, 1 = B write-down forced, 2 = C stranding forced."""
    free = E - B
    out = np.full(S.shape, 1, dtype=np.int8)
    out[S <= free] = 0
    out[S > E] = 2
    return out


@dataclass
class MCResult:
    n: int
    seed: int
    regime_share: dict[str, float]
    stranded_mw: np.ndarray
    writedown_mw: np.ndarray
    samples: dict[str, np.ndarray]

    def quantile_interval(self, arr: np.ndarray, lo: float = 0.05, hi: float = 0.95) -> tuple[float, float]:
        return float(np.quantile(arr, lo)), float(np.quantile(arr, hi))

    def summary(self) -> str:
        lines = [f"n = {self.n:,}  seed = {self.seed}", "", "regime probability"]
        for k, v in sorted(self.regime_share.items()):
            bar = "#" * int(round(v * 40))
            lines.append(f"  {k:<34} {v:6.1%}  {bar}")
        s5, s95 = self.quantile_interval(self.stranded_mw)
        w5, w95 = self.quantile_interval(self.writedown_mw)
        lines += [
            "",
            f"stranded IT-MW   median {np.median(self.stranded_mw):10,.0f}   "
            f"p5-p95 [{s5:,.0f}, {s95:,.0f}]",
            f"forced write-down IT-MW  median {np.median(self.writedown_mw):10,.0f}   "
            f"p5-p95 [{w5:,.0f}, {w95:,.0f}]",
        ]
        return "\n".join(lines)


def run(dists: Sequence[Dist], n: int = 200_000, seed: int = SEED) -> MCResult:
    """Sample (S, E, B) and classify. Requires keys 'S', 'E', 'B'."""
    rng = np.random.default_rng(seed)
    samples = {d.key: d.sample(rng, n) for d in dists}
    missing = {"S", "E", "B"} - set(samples)
    if missing:
        raise KeyError(f"missing required parameters {sorted(missing)}")
    S, E, B = samples["S"], samples["E"], samples["B"]

    codes = _regime_codes(S, E, B)
    names = {0: Regime.A_FREE.value, 1: Regime.B_ENVELOPE_BOUND.value, 2: Regime.C_SUPPLY_BOUND.value}
    share = {names[c]: float((codes == c).mean()) for c in (0, 1, 2)}

    stranded = np.maximum(0.0, S - E)
    absorbed = np.minimum(S, E)
    writedown = np.maximum(0.0, absorbed - (E - B))

    return MCResult(n=n, seed=seed, regime_share=share, stranded_mw=stranded,
                    writedown_mw=writedown, samples=samples)


def sobol_indices(dists: Sequence[Dist], output: Callable[[dict[str, np.ndarray]], np.ndarray],
                  n: int = 8192, seed: int = SEED) -> dict[str, dict[str, float]]:
    """Saltelli first-order and total-effect indices.

    The question this answers is not "how uncertain is the answer" but "whose
    fault is it". If one input carries most of the total-effect index, the
    entire disagreement reduces to measuring that one quantity, and arguing
    about the others is theatre.
    """
    from SALib.analyze import sobol as sobol_analyze
    from SALib.sample import sobol as sobol_sample

    varying = [d for d in dists if d.hi > d.lo]
    fixed = [d for d in dists if d.hi <= d.lo]
    problem = {
        "num_vars": len(varying),
        "names": [d.key for d in varying],
        "bounds": [[d.lo, d.hi] for d in varying],
    }
    X = sobol_sample.sample(problem, n, calc_second_order=False, seed=seed)
    cols = {d.key: X[:, i] for i, d in enumerate(varying)}
    for d in fixed:
        cols[d.key] = np.full(X.shape[0], d.lo)
    Y = output(cols)
    Si = sobol_analyze.analyze(problem, Y, calc_second_order=False, print_to_console=False, seed=seed)
    return {
        name: {"S1": float(Si["S1"][i]), "S1_conf": float(Si["S1_conf"][i]),
               "ST": float(Si["ST"][i]), "ST_conf": float(Si["ST_conf"][i])}
        for i, name in enumerate(problem["names"])
    }
