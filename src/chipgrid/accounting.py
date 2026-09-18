"""Depreciation, early retirement, and the liability a life extension creates.

The article's accounting claim (C10/C11) is usually argued as a matter of
opinion about aggressiveness. It is not. Straight-line depreciation is an
identity, and the consequence of extending useful life is an exact quantity
that can be written down before any judgement is applied.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .exact import Interval


def net_book_value(cost: Interval, age: Interval, life: Interval,
                   salvage: Interval | None = None) -> Interval:
    """Straight-line NBV at a given age. Ages beyond life are not clamped here;
    the caller should not ask, and a negative result is a signal that they did."""
    one = Interval.of(1)
    salv = salvage or Interval.of(0)
    return salv + (cost - salv) * (one - age / life)


def excess_book_value_from_extension(
    cost: Interval, age: Interval, old_life: Interval, new_life: Interval
) -> Interval:
    """How much MORE book value is carried at `age` because the life was extended.

        NBV(new) - NBV(old) = cost * age * (1/old_life - 1/new_life)

    This is the exposure the extension created. It is not an accusation: the
    extension may be entirely justified by how long the gear really lasts. But
    the quantity is fixed by arithmetic, and it is precisely what an early
    retirement makes due at once. Extending 4 to 6 years and then pulling the
    asset at age 2 carries exactly cost/6 of extra unamortised value.
    """
    one = Interval.of(1)
    return cost * age * ((one / old_life) - (one / new_life))


def impairment_on_early_retirement(
    cost: Interval, age: Interval, life: Interval, resale: Interval | None = None
) -> Interval:
    """The charge taken when an asset is pulled before the end of its book life.

    Resale proceeds offset the charge, which is why the secondary market for
    prior-generation accelerators is load-bearing for the whole argument: a
    deep resale market converts an impairment into a disposal at close to book.
    A thin one does not.
    """
    nbv = net_book_value(cost, age, life)
    proceeds = resale or Interval.of(0)
    charge = nbv - proceeds
    lo = max(Fraction(0), charge.lo)
    hi = max(Fraction(0), charge.hi)
    return Interval(lo, hi)


@dataclass(frozen=True)
class DeferralLedger:
    """What a useful-life extension did to reported expense, period by period.

    Total depreciation over an asset's life is invariant to the schedule. The
    extension therefore does not reduce cost; it reshapes the path. This ledger
    makes the reshaping explicit so that 'deferred billions' can be checked
    rather than asserted, and so the reversal can be priced.
    """

    cost: Fraction
    old_life: int
    new_life: int

    def annual(self, life: int) -> Fraction:
        return self.cost / life

    def deferred_by_year(self) -> list[Fraction]:
        """Expense avoided in each year of the OLD life by moving to the new one."""
        return [self.annual(self.old_life) - self.annual(self.new_life)
                for _ in range(self.old_life)]

    def total_deferred(self) -> Fraction:
        return sum(self.deferred_by_year())

    def check_conservation(self) -> bool:
        """Total expense is identical under both schedules. If this ever fails,
        the model is wrong, not the company."""
        return self.annual(self.old_life) * self.old_life == self.annual(self.new_life) * self.new_life


def breakeven_resale_for_no_charge(cost: Interval, age: Interval, life: Interval) -> Interval:
    """The resale price at which pulling the asset costs nothing in the P&L.

    Expressed as a fraction of original cost this is just (1 - age/life), so an
    H100 pulled at 24 months against a 72-month book life needs to fetch 2/3 of
    its original price to avoid a charge. Whether the secondary market clears
    anywhere near there is the empirical question that decides C11.
    """
    one = Interval.of(1)
    return one - age / life
