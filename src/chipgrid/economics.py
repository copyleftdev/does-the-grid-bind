"""Spot price, marginal cost, and the band where capital dies but capacity stays.

C12 claims spot GPU-hour pricing must fall toward marginal cost. The economics
that matter are not in the direction of that claim -- it is obviously right in
direction -- but in the WIDTH of the interval between the two relevant prices:

    p_marginal : electricity plus variable opex. Below this, running the
                 machine loses money on every hour, and it gets switched off.
    p_full     : the price that also recovers capex over the asset's life at
                 the assumed utilization. Below this, the capital is not
                 returned, but the machine keeps running because the capex is
                 sunk.

Between them is a band in which the fleet stays powered, tokens stay cheap,
and the equity is being destroyed quietly. That band, not the direction of the
price move, is what the article's "return distribution splits" actually is.
"""

from __future__ import annotations

from fractions import Fraction

from .exact import Interval

HOURS_PER_YEAR = Interval.of(8760)


def marginal_cost_per_gpu_hour(
    gpu_watts: Interval,
    pue: Interval,
    power_price_per_mwh: Interval,
    variable_opex_per_gpu_hour: Interval | None = None,
) -> Interval:
    """Cash cost of running one GPU for one hour.

    Facility watts = IT watts x PUE, so cooling is inside the number. Networking
    and storage draw are folded into PUE here, which understates them slightly;
    the caller should widen PUE rather than add a fudge term.
    """
    facility_mw = (gpu_watts * pue) / Interval.of(1_000_000)
    energy = facility_mw * power_price_per_mwh
    return energy + (variable_opex_per_gpu_hour or Interval.of(0))


def full_cost_per_gpu_hour(
    capex_per_gpu: Interval,
    life_years: Interval,
    utilization: Interval,
    marginal: Interval,
    fixed_opex_fraction_of_capex: Interval | None = None,
) -> Interval:
    """Price that recovers capex plus marginal cost at the given utilization.

    Undiscounted on purpose: adding a cost of capital only widens the band and
    strengthens the conclusion, so leaving it out keeps the result conservative.
    """
    billable_hours = HOURS_PER_YEAR * utilization
    capex_recovery = capex_per_gpu / (life_years * billable_hours)
    fixed = (capex_per_gpu * (fixed_opex_fraction_of_capex or Interval.of(0))) / billable_hours
    return capex_recovery + fixed + marginal


def loss_band(marginal: Interval, full: Interval) -> Interval:
    """Width of the price range in which the machine runs and the capital does not
    come back. Reported per GPU-hour."""
    return full - marginal


def utilization_required(
    price_per_gpu_hour: Interval,
    capex_per_gpu: Interval,
    life_years: Interval,
    marginal: Interval,
    fixed_opex_fraction_of_capex: Interval | None = None,
) -> Interval:
    """Utilization needed to break even at a given spot price.

    Solving p = capex/(L*8760*u) + f*capex/(8760*u) + m for u:

        u = capex * (1/L + f) / (8760 * (p - m))

    A result above 1 is the honest answer that the price does not clear at any
    utilization -- worth surfacing rather than clamping.
    """
    one = Interval.of(1)
    f = fixed_opex_fraction_of_capex or Interval.of(0)
    margin = price_per_gpu_hour - marginal
    if margin.hi <= 0:
        return Interval.of(10**9)  # unreachable: price is at or below cash cost
    numerator = capex_per_gpu * ((one / life_years) + f)
    return numerator / (HOURS_PER_YEAR * margin)


def revenue_per_it_mw_year(
    price_per_gpu_hour: Interval, gpu_watts: Interval, utilization: Interval
) -> Interval:
    """Convert a $/GPU-hour price into $/IT-MW-year, so that revenue and grid
    capacity are finally in commensurable units."""
    gpus_per_mw = Interval.of(1_000_000) / gpu_watts
    return gpus_per_mw * price_per_gpu_hour * HOURS_PER_YEAR * utilization
