"""From "twice as many chips" to "megawatts of new grid interconnection".

The article's argument runs:  units double  ->  power demand doubles  ->  the
grid cannot double  ->  gap.  Each arrow is a separate claim, and the middle
one is doing almost all of the work while being the least defended.

Written out, the quantity actually in contention is a product of seven factors:

    new grid MW required
      = d_units                    incremental units shipped year over year
      x share_accelerator          fraction of that basket that is a DC accelerator
      x watts_each / 1e6           IT megawatts each
      x pue                        facility overhead
      x share_us                   fraction landing in the United States
      x (1 - share_refresh)        fraction NOT going into an already-energized rack
      x (1 - share_offgrid)        fraction NOT served by behind-the-meter,
                                   curtailment-enabled or already-contracted capacity

Three of those seven factors are absent from the article entirely
(share_us, share_refresh, share_offgrid), and each one can move the answer by
more than the grid numbers it does discuss. Writing the chain down is most of
the analysis; the Sobol decomposition then says which factor the disagreement
is really about.

A multiplicative chain is also the right object for a different reason: the
relative width of the product is at least the widest single factor's relative
width, so a chain with one badly-known factor cannot be made precise by
measuring the others carefully. That is a statement about where effort should
go, and it is provable rather than rhetorical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from .exact import Interval

FACTORS = (
    "d_units",
    "share_accelerator",
    "watts_each",
    "pue",
    "share_us",
    "share_refresh",
    "share_offgrid",
)


@dataclass(frozen=True)
class ChainResult:
    required_mw: Interval
    steps: list[tuple[str, Interval]]
    as_entered: dict[str, Interval] = field(default_factory=dict)
    """Each factor as it MULTIPLIES the product, not as it was stated.

    This distinction is not cosmetic. `share_offgrid` stated as [0.10, 0.40]
    has a relative width of 1.20, but it enters as (1 - x) = [0.60, 0.90],
    whose relative width is 0.40. Ranking the stated forms puts the complemented
    shares at the top of the blame list where they do not belong.
    """

    def report(self) -> str:
        lines = ["  step                        running total (IT-MW unless noted)"]
        for name, v in self.steps:
            lines.append(f"    x {name:<24} {v.fmt(1):>26}")
        lines.append(f"  => new grid MW required   {self.required_mw.fmt(1):>26}")
        return "\n".join(lines)


def required_new_grid_mw(
    d_units: Interval,
    share_accelerator: Interval,
    watts_each: Interval,
    pue: Interval,
    share_us: Interval,
    share_refresh: Interval,
    share_offgrid: Interval,
) -> ChainResult:
    one = Interval.of(1)
    steps: list[tuple[str, Interval]] = []

    v = d_units
    steps.append(("d_units (count)", v))
    v = v * share_accelerator
    steps.append(("share_accelerator", v))
    v = (v * watts_each) / Interval.of(1_000_000)
    steps.append(("watts_each -> IT-MW", v))
    v = v * pue
    steps.append(("pue -> facility MW", v))
    v = v * share_us
    steps.append(("share_us", v))
    v = v * (one - share_refresh)
    steps.append(("(1 - share_refresh)", v))
    v = v * (one - share_offgrid)
    steps.append(("(1 - share_offgrid)", v))

    as_entered = {
        "d_units": d_units,
        "share_accelerator": share_accelerator,
        "watts_each": watts_each,
        "pue": pue,
        "share_us": share_us,
        "(1-share_refresh)": one - share_refresh,
        "(1-share_offgrid)": one - share_offgrid,
    }
    return ChainResult(required_mw=v, steps=steps, as_entered=as_entered)


def relative_width(iv: Interval) -> Fraction:
    """(hi - lo) / midpoint. Dimensionless, so factors are comparable."""
    mid = (iv.lo + iv.hi) / 2
    if mid == 0:
        return Fraction(0)
    return (iv.hi - iv.lo) / abs(mid)


def width_attribution(result: ChainResult) -> list[tuple[str, Fraction]]:
    """Rank factors by the relative width each contributes to the product.

    Takes a ChainResult rather than a dict so the factors are measured AS THEY
    ENTER -- see the note on ChainResult.as_entered.

    For a product of positive factors, relative widths compose roughly
    additively while they are small, so this ranking says where a measurement
    would actually buy precision. It is the first-order statement; the Sobol
    indices in `mc.py` are the non-linear version and the two should agree on
    ordering. If they disagree, the chain has interaction effects strong enough
    that the first-order reading is misleading and only Sobol should be quoted.
    """
    return sorted(
        ((k, relative_width(v)) for k, v in result.as_entered.items()),
        key=lambda kv: kv[1],
        reverse=True,
    )


def sample_chain(cols: dict[str, np.ndarray]) -> np.ndarray:
    """Float evaluation of the same chain, for Monte Carlo and Sobol."""
    return (
        cols["d_units"]
        * cols["share_accelerator"]
        * cols["watts_each"]
        / 1e6
        * cols["pue"]
        * cols["share_us"]
        * (1.0 - cols["share_refresh"])
        * (1.0 - cols["share_offgrid"])
    )
