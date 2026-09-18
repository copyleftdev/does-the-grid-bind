"""The invariants.

An invariant here is a predicate that must hold in EVERY state of the system
for structural reasons — conservation, definition, or physics — and therefore
holds regardless of how uncertain the parameters are. That is the whole point:
a forecast is only as good as its inputs, but an invariant constrains the
outcome space even when every input is disputed.

Each invariant carries:
  - `kind`   : why it must hold (IDENTITY / PHYSICAL / THEOREM / ACCOUNTING)
  - `check`  : an executable predicate over a State
  - `slack`  : how much room is left before it binds (signed, exact)

`kind` matters. An IDENTITY cannot be violated by the world, only by bad
bookkeeping — a violation means our numbers are wrong. A PHYSICAL invariant
cannot be violated by the world either, but a violation of the *modelled*
version means a flow we did not model is absorbing the difference. A THEOREM
follows from other assumptions and can be violated if those assumptions fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Callable

from .exact import Interval, as_fraction


class Kind(str, Enum):
    IDENTITY = "IDENTITY"        # true by definition; violation => bad data
    PHYSICAL = "PHYSICAL"        # true by physics; violation => unmodelled flow
    THEOREM = "THEOREM"          # follows from stated assumptions
    ACCOUNTING = "ACCOUNTING"    # forced by GAAP/IFRS double entry


@dataclass(frozen=True)
class State:
    """One period of the accelerator fleet, denominated in IT megawatts.

    Power is the accounting currency, not chip count. The article's thesis is a
    power constraint, and a chip count cannot be compared to a substation.
    Every stock below is IT-MW of nameplate draw; facility MW is IT-MW x PUE.
    """

    t: int                          # period index (months since epoch)
    produced: Fraction              # cumulative IT-MW shipped by vendors
    warehoused: Fraction            # shipped, not energized
    deployed: Fraction              # racked and drawing power
    retired: Fraction               # decommissioned
    energized: Fraction             # IT-MW of energized capacity available
    committed: Fraction             # IT-MW with executed interconnect, not yet live
    gross_cost: Fraction            # cumulative $ spent on the fleet
    accum_depr: Fraction            # cumulative $ depreciated
    book_value: Fraction            # unamortized $ still capitalized
    impaired: Fraction              # cumulative $ written off early
    pue: Fraction = Fraction(13, 10)

    @property
    def facility_mw(self) -> Fraction:
        return self.deployed * self.pue

    @property
    def headroom(self) -> Fraction:
        return self.energized - self.deployed

    @property
    def stranded_fraction(self) -> Fraction:
        if self.produced == 0:
            return Fraction(0)
        return self.warehoused / self.produced


@dataclass(frozen=True)
class Invariant:
    name: str
    kind: Kind
    statement: str
    check: Callable[[State], bool]
    slack: Callable[[State], Fraction]
    why: str

    def evaluate(self, s: State) -> "Verdict":
        return Verdict(self, s.t, self.check(s), self.slack(s))


@dataclass(frozen=True)
class Verdict:
    invariant: Invariant
    t: int
    holds: bool
    slack: Fraction

    def __str__(self) -> str:
        mark = "ok " if self.holds else "XX "
        return f"{mark}{self.invariant.name:<26} t={self.t:>3}  slack={float(self.slack):+.6g}"


# ---------------------------------------------------------------------------
# I1. Fleet conservation.  Nothing produced vanishes.
# ---------------------------------------------------------------------------
I1_FLEET = Invariant(
    name="I1_fleet_conservation",
    kind=Kind.IDENTITY,
    statement="produced == warehoused + deployed + retired",
    check=lambda s: s.produced == s.warehoused + s.deployed + s.retired,
    slack=lambda s: s.produced - (s.warehoused + s.deployed + s.retired),
    why=(
        "Every accelerator shipped is in exactly one of three places. A narrative "
        "that grows shipments without naming which stock absorbs them is not a "
        "forecast, it is a wish. This is the invariant the bull case usually skips."
    ),
)

# ---------------------------------------------------------------------------
# I2. Power envelope.  You cannot run more load than you have energized.
# ---------------------------------------------------------------------------
I2_ENVELOPE = Invariant(
    name="I2_power_envelope",
    kind=Kind.PHYSICAL,
    statement="deployed <= energized",
    check=lambda s: s.deployed <= s.energized,
    slack=lambda s: s.energized - s.deployed,
    why=(
        "The article's thesis, operationalised. Note this binds on ENERGIZED "
        "capacity, not on capacity under construction and not on capacity in a "
        "queue. Slack is the only quantity that can absorb a shipment surge."
    ),
)

# ---------------------------------------------------------------------------
# I3. Lead-time causality.  Today's energized MW was committed L months ago.
# ---------------------------------------------------------------------------
def i3_factory(lead_months: int, history: dict[int, Fraction], e0: Fraction) -> Invariant:
    """energized(t) <= e0 + sum of commitments made at or before t - L.

    This is the sharpest invariant in the model and the reason the exercise is
    worth doing. It makes near-term grid supply a READ-ONLY variable: for the
    next L months, energized capacity is already determined by commitments
    already on the books. No forecast, no scenario, no demand curve can move it.
    """

    def _available(s: State) -> Fraction:
        cutoff = s.t - lead_months
        return e0 + sum(v for k, v in history.items() if k <= cutoff)

    return Invariant(
        name="I3_lead_time_causality",
        kind=Kind.PHYSICAL,
        statement=f"energized(t) <= e0 + sum(commitments at or before t-{lead_months})",
        check=lambda s: s.energized <= _available(s),
        slack=lambda s: _available(s) - s.energized,
        why=(
            "Transformers and interconnection studies have irreducible latency. "
            "Capacity arriving in the next L months left the starting gate already; "
            "capacity committed today cannot help until t+L. This converts the "
            "near-term supply question from a forecast into a lookup."
        ),
    )


# ---------------------------------------------------------------------------
# I4. Book value conservation.  Depreciation moves cost between periods; it
#     cannot create or destroy it.
# ---------------------------------------------------------------------------
I4_BOOK = Invariant(
    name="I4_book_conservation",
    kind=Kind.ACCOUNTING,
    statement="gross_cost == accum_depr + book_value + impaired",
    check=lambda s: s.gross_cost == s.accum_depr + s.book_value + s.impaired,
    slack=lambda s: s.gross_cost - (s.accum_depr + s.book_value + s.impaired),
    why=(
        "The deep reason the depreciation-extension debate is not about whether "
        "the cost is real. Extending useful life from 4 to 6 years defers expense; "
        "it does not reduce it. Early retirement pulls the deferred expense "
        "forward. The two are exact inverses, so the extension created a liability "
        "that the cannibalization path immediately calls."
    ),
)

# ---------------------------------------------------------------------------
# I5. Monotonicity of irreversible stocks.
# ---------------------------------------------------------------------------
def i5_monotone(prev: State, cur: State) -> list[tuple[str, bool]]:
    return [
        ("produced", cur.produced >= prev.produced),
        ("retired", cur.retired >= prev.retired),
        ("accum_depr", cur.accum_depr >= prev.accum_depr),
        ("impaired", cur.impaired >= prev.impaired),
        ("gross_cost", cur.gross_cost >= prev.gross_cost),
    ]


# ---------------------------------------------------------------------------
# I6. Little's Law on the interconnection queue.
# ---------------------------------------------------------------------------
def littles_law_wait(queue_gw: Interval, throughput_gw_per_yr: Interval) -> Interval:
    """W = L / lambda, in years. A THEOREM for any queue in steady state.

    Departures include withdrawals, not only energizations. Using completions
    alone as lambda overstates the wait; using all departures understates the
    wait experienced by projects that actually complete. Both bounds matter and
    the caller should compute both.
    """
    return queue_gw / throughput_gw_per_yr


# ---------------------------------------------------------------------------
# I7. Growth composition.  Revenue growth is MULTIPLICATIVE in units and ASP.
# ---------------------------------------------------------------------------
def implied_asp_growth(rev_growth: Interval, unit_growth: Interval) -> Interval:
    """(1+g_rev) = (1+g_units)(1+g_asp)  =>  g_asp = (1+g_rev)/(1+g_units) - 1.

    Subtracting one growth rate from another is the single most common error in
    this genre. "100% units against 70% revenue" is not a 30-point ASP decline;
    it is 1.70/2.00 - 1 = -15%. The difference is not pedantry: -30% and -15%
    sit on opposite sides of most gross-margin break-evens.
    """
    one = Interval.of(1)
    return (one + rev_growth) / (one + unit_growth) - one


# ---------------------------------------------------------------------------
# I8. Energy closure.  Tokens are bounded by energized watts.
# ---------------------------------------------------------------------------
def required_it_mw(
    annual_tokens: Interval,
    tokens_per_gpu_second: Interval,
    watts_per_gpu: Interval,
    utilization: Interval,
) -> Interval:
    """Invert demand into the megawatts it requires.

    The point of this direction of travel: a token-demand forecast and a grid
    forecast are usually stated in incomparable units, so they are never checked
    against each other. Expressed in MW they must reconcile, and I2 then decides
    whether the demand case is physically admissible at all.
    """
    seconds_per_year = Interval.of(31_536_000)
    gpu_seconds = annual_tokens / tokens_per_gpu_second
    gpu_count = gpu_seconds / (seconds_per_year * utilization)
    watts = gpu_count * watts_per_gpu
    return watts / Interval.of(1_000_000)


# ---------------------------------------------------------------------------
# I9. Cannibalization break-even.
# ---------------------------------------------------------------------------
def cannibalization_breakeven_ratio(
    age_months: Interval,
    life_months: Interval,
    cost_per_mw_old: Interval,
    revenue_per_mw_year_old: Interval,
    remaining_years: Interval,
) -> Interval:
    """The performance-per-watt ratio at which ripping out working silicon pays.

    Freeing P MW by retiring gear of age a costs its unamortized book value,
    cost_old * (1 - a/life). It buys (rho - 1) * revenue_old per MW-year for the
    remaining horizon, where rho = perf/W_new over perf/W_old. Setting the two
    equal gives the ratio the new generation must beat. Below it, warehousing
    the new hardware is cheaper than the write-down; above it, the write-down is
    the cheaper of two bad options. This is the article's dichotomy as a
    decidable predicate rather than a mood.
    """
    one = Interval.of(1)
    unamortised = cost_per_mw_old * (one - age_months / life_months)
    gain_per_unit_ratio = revenue_per_mw_year_old * remaining_years
    return one + unamortised / gain_per_unit_ratio


CORE_INVARIANTS = [I1_FLEET, I2_ENVELOPE, I4_BOOK]


# ---------------------------------------------------------------------------
# I10. Sector budget closure.  One firm's revenue is another firm's capex.
# ---------------------------------------------------------------------------
def buyer_capex_required(
    vendor_revenue: Interval,
    accelerator_share_of_buyer_capex: Interval,
    vendor_share_of_accelerator_spend: Interval,
) -> Interval:
    """Total buyer capex implied by a vendor revenue figure.

    This is an accounting identity across the sector, not a behavioural model:
    every dollar of NVIDIA data-center revenue is a dollar of somebody's
    capital expenditure in the same period, up to channel inventory and
    payment timing. So a revenue forecast is simultaneously a forecast of the
    buyers' capex budgets, and it can be checked against those budgets as
    they are actually guided.

    It is an independent test of C1 and C2 that never mentions the grid. If
    the implied buyer capex exceeds what the buyers have guided to, the
    shipment forecast fails for a reason that has nothing to do with
    transformers -- and the article's mechanism is then not the binding one.

    Two caveats, both of which cut the same way and neither of which is small:

    - Vendor financing breaks the independence the identity assumes. When a
      vendor takes equity in a customer that then buys its product, the same
      dollar is counted as an investment and as revenue. The identity still
      holds; what fails is the inference that the revenue reflects
      independent third-party demand.
    - Neoclouds funded by debt secured on the GPUs themselves make buyer capex
      a function of the resale value of the collateral, which is the very
      quantity the cannibalization argument puts in doubt. That is a feedback
      loop, not an exogenous budget.
    """
    return vendor_revenue / (
        accelerator_share_of_buyer_capex * vendor_share_of_accelerator_spend
    )


I10_BUDGET_NOTE = (
    "I10 is the check the energization argument does not need but should not "
    "skip: shipments are bounded by buyers' budgets as well as by buyers' "
    "substations, and whichever bound binds first is the one that decides the "
    "outcome. An analysis that establishes a grid constraint has not thereby "
    "established that the grid is the binding constraint."
)
