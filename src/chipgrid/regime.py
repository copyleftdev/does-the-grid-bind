"""Which regime is the buildout actually in?

`Energization.tla` proves the outcome space has exactly three regions, divided
by two thresholds in three quantities. This module decides which region the
real numbers put us in.

The decision is made in exact interval arithmetic, which means it has four
possible answers, not three. The fourth is UNDECIDED: the evidence straddles a
boundary and does not settle the question. Reporting UNDECIDED is the whole
value of doing it exactly -- a point estimate would have picked a side and
sounded certain about it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .exact import Interval


class Regime(str, Enum):
    A_FREE = "A: absorption is free"
    B_ENVELOPE_BOUND = "B: absorption forces a write-down"
    C_SUPPLY_BOUND = "C: stranding is forced"
    UNDECIDED = "UNDECIDED: the evidence straddles a boundary"


@dataclass(frozen=True)
class RegimeVerdict:
    regime: Regime
    shipped: Interval          # S, IT-MW of new hardware over the horizon
    energized: Interval        # E, IT-MW of energized capacity at horizon end
    base: Interval             # B, IT-MW already occupying the envelope at t0
    free_headroom: Interval    # E - B
    surplus: Interval          # S - E : positive means forced stranding
    candidates: tuple[Regime, ...]

    @property
    def decided(self) -> bool:
        return self.regime is not Regime.UNDECIDED

    def report(self) -> str:
        lines = [
            f"  S  shipped over horizon      {self.shipped.fmt(1):>22} IT-MW",
            f"  E  energized at horizon end  {self.energized.fmt(1):>22} IT-MW",
            f"  B  installed base at t0      {self.base.fmt(1):>22} IT-MW",
            f"  E-B free headroom            {self.free_headroom.fmt(1):>22} IT-MW",
            f"  S-E forced stranding         {self.surplus.fmt(1):>22} IT-MW",
            "",
            f"  VERDICT: {self.regime.value}",
        ]
        if not self.decided:
            lines.append(f"  consistent with: {', '.join(r.name for r in self.candidates)}")
        return "\n".join(lines)


def classify(shipped: Interval, energized: Interval, base: Interval) -> RegimeVerdict:
    """Decide the regime, or decline to.

    Boundaries:  S <= E-B  -> A      E-B < S <= E -> B      S > E -> C
    """
    free = energized - base
    surplus = shipped - energized

    # Which regimes are consistent with SOME point in the input intervals?
    candidates: list[Regime] = []
    # A is possible iff S can be <= E-B, i.e. S.lo <= free.hi
    if shipped.lo <= free.hi:
        candidates.append(Regime.A_FREE)
    # C is possible iff S can exceed E, i.e. S.hi > E.lo
    if shipped.hi > energized.lo:
        candidates.append(Regime.C_SUPPLY_BOUND)
    # B is possible iff some point has free < S <= E
    if shipped.hi > free.lo and shipped.lo <= energized.hi:
        candidates.append(Regime.B_ENVELOPE_BOUND)

    order = [Regime.A_FREE, Regime.B_ENVELOPE_BOUND, Regime.C_SUPPLY_BOUND]
    candidates = [r for r in order if r in candidates]

    regime = candidates[0] if len(candidates) == 1 else Regime.UNDECIDED
    return RegimeVerdict(
        regime=regime,
        shipped=shipped,
        energized=energized,
        base=base,
        free_headroom=free,
        surplus=surplus,
        candidates=tuple(candidates),
    )


def stranded_mw(shipped: Interval, energized: Interval, base: Interval) -> Interval:
    """IT-MW that cannot be energized by ANY strategy: max(0, S - E).

    Note B does not appear. Cannibalizing the entire installed base is already
    assumed; this is what is stranded after doing so. It is a floor, not an
    estimate, and it is the number the article's "excess hardware" refers to.
    """
    surplus = shipped - energized
    lo = max(Fraction(0), surplus.lo)
    hi = max(Fraction(0), surplus.hi)
    return Interval(lo, hi)


def forced_writedown_mw(shipped: Interval, energized: Interval, base: Interval) -> Interval:
    """IT-MW of installed base that must be pulled to absorb what CAN be absorbed.

    Absorbable = min(S, E). Free headroom = E - B. Anything absorbed beyond the
    free headroom displaces working gear:  max(0, min(S,E) - (E-B)).
    """
    free = energized - base
    lo_absorb = min(shipped.lo, energized.lo)
    hi_absorb = min(shipped.hi, energized.hi)
    lo = max(Fraction(0), lo_absorb - free.hi)
    hi = max(Fraction(0), hi_absorb - free.lo)
    if lo > hi:
        lo = hi
    return Interval(lo, hi)
