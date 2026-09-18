"""Tests. The important ones are the cross-checks between the two models.

The Python regime classifier and the TLA+ spec are independent implementations
of the same claim. Agreement between them is evidence; a divergence means one
of them is wrong and the analysis built on it is void.
"""

from fractions import Fraction

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from chipgrid.exact import Interval, as_fraction
from chipgrid.invariants import (
    I1_FLEET,
    I2_ENVELOPE,
    I4_BOOK,
    State,
    implied_asp_growth,
    littles_law_wait,
)
from chipgrid.regime import Regime, classify, forced_writedown_mw, stranded_mw


# --------------------------------------------------------------- cross-checks

# (S, E, B) -> the regime TLC established for the matching .cfg
TLC_CASES = {
    "Abundant.cfg": ((8, 10, 2), Regime.A_FREE),
    "Tight.cfg": ((4, 4, 4), Regime.B_ENVELOPE_BOUND),
    "Constrained.cfg": ((8, 6, 2), Regime.C_SUPPLY_BOUND),
}


@pytest.mark.parametrize("cfg,case", TLC_CASES.items())
def test_classifier_agrees_with_tlc(cfg, case):
    (S, E, B), expected = case
    v = classify(Interval.of(S), Interval.of(E), Interval.of(B))
    assert v.regime is expected, f"{cfg}: python says {v.regime}, TLC says {expected}"


def test_regime_c_strands_regardless_of_cannibalization():
    """D2: in regime C, pulling the whole installed base still leaves hardware idle."""
    v = classify(Interval.of(8), Interval.of(6), Interval.of(2))
    assert v.regime is Regime.C_SUPPLY_BOUND
    assert stranded_mw(Interval.of(8), Interval.of(6), Interval.of(2)).lo == 2


# ------------------------------------------------------------- the arithmetic

def test_article_asp_arithmetic_is_multiplicative():
    """C3: 100% units against 70% revenue is -15%, not -30 points."""
    g = implied_asp_growth(Interval.of("0.70"), Interval.of("1.00"))
    assert g.is_point
    assert g.lo == Fraction(-15, 100)
    assert g.lo != Fraction(-30, 100)


def test_growth_composition_round_trips():
    """(1+g_u)(1+g_a) must reconstruct (1+g_r) exactly."""
    g_rev, g_units = Interval.of("0.70"), Interval.of("1.00")
    g_asp = implied_asp_growth(g_rev, g_units)
    one = Interval.of(1)
    assert ((one + g_units) * (one + g_asp)).lo == (one + g_rev).lo


@settings(max_examples=200, deadline=None)
@given(
    r=st.fractions(min_value=Fraction(-9, 10), max_value=Fraction(5), max_denominator=20),
    u=st.fractions(min_value=Fraction(-9, 10), max_value=Fraction(5), max_denominator=20),
)
def test_additive_shortcut_error_is_exactly_characterised(r, u):
    """Hypothesis rejected the first version of this property, which claimed the
    additive shortcut is right only at u = 0. It is also right at r = u. The
    exact statement is stronger and is what gets asserted:

        exact - additive = -u(r - u) / (1 + u)

    so the shortcut is correct iff u = 0 or r = u, and its error grows with unit
    growth -- largest in exactly the high-volume case the article is about."""
    exact = implied_asp_growth(Interval.of(r), Interval.of(u)).lo
    additive = r - u
    assert exact - additive == -u * (r - u) / (1 + u)
    assert (exact == additive) == (u == 0 or r == u)


# ----------------------------------------------------------- state invariants

def _state(**kw) -> State:
    base = dict(
        t=0, produced=Fraction(0), warehoused=Fraction(0), deployed=Fraction(0),
        retired=Fraction(0), energized=Fraction(0), committed=Fraction(0),
        gross_cost=Fraction(0), accum_depr=Fraction(0), book_value=Fraction(0),
        impaired=Fraction(0),
    )
    base.update({k: as_fraction(v) if k != "t" else v for k, v in kw.items()})
    return State(**base)


def test_fleet_conservation_catches_a_missing_stock():
    ok = _state(produced=10, warehoused=3, deployed=6, retired=1)
    assert I1_FLEET.check(ok)
    bad = _state(produced=10, warehoused=3, deployed=6, retired=0)
    assert not I1_FLEET.check(bad)
    assert I1_FLEET.evaluate(bad).slack == 1


def test_power_envelope_binds():
    assert I2_ENVELOPE.check(_state(deployed=5, energized=5))
    assert not I2_ENVELOPE.check(_state(deployed=6, energized=5))


def test_book_conservation_is_exact():
    """Depreciation moves cost between periods; it cannot change the total."""
    assert I4_BOOK.check(_state(gross_cost=100, accum_depr=40, book_value=60))
    early = _state(gross_cost=100, accum_depr=40, book_value=0, impaired=60)
    assert I4_BOOK.check(early), "an early write-off must land in `impaired`"
    lost = _state(gross_cost=100, accum_depr=40, book_value=0)
    assert not I4_BOOK.check(lost), "value cannot simply vanish"


# ------------------------------------------------------------------- exactness

def test_floats_are_refused():
    with pytest.raises(TypeError):
        Interval.of(0.1)


def test_interval_gives_the_honest_third_answer():
    """A predicate over an interval has three outcomes, and the third is the
    reason to do this exactly at all."""
    wide = classify(Interval.of(5, 9), Interval.of(6, 8), Interval.of(2))
    assert wide.regime is Regime.UNDECIDED
    assert len(wide.candidates) > 1


def test_littles_law_is_monotone_in_throughput():
    slow = littles_law_wait(Interval.of(1000), Interval.of(50))
    fast = littles_law_wait(Interval.of(1000), Interval.of(100))
    assert slow.lo > fast.hi
