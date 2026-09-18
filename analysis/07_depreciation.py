#!/usr/bin/env python
"""C10 / C11 — the depreciation claim, which is the article's strongest."""
import sys; sys.path.insert(0, "src")
from fractions import Fraction as F

from chipgrid.accounting import breakeven_resale_for_no_charge
from chipgrid.exact import Interval as I
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("C10 — CONFIRMED, and the dollar amounts are all filed")
print("""
  Every extension the article describes is real and quantified in a 10-K:

    Microsoft  FY2023   server + network   4 -> 6 yr   +$3.7bn operating income
    Alphabet   2023     servers 4 -> 6, certain network 5 -> 6
                                                      -$3.9bn depreciation
    Amazon     2022     servers 4 -> 5, networking 5 -> 6
                                                      -$3.6bn D&A
    Amazon     2024     servers 5 -> 6                -$3.2bn D&A
    Oracle     FY2023   servers 4 -> 5                -$434m opex
    Oracle     FY2025   servers + networking 5 -> 6   -$733m opex
    Meta       2021-22  3 -> 4 -> 4.5 -> 5 yr         -$860m (2022 alone)

  "Deferred billions" is exact, not rhetorical. An independent reconstruction
  puts the five-company FY2025 effect at $43.8bn of operating income, 11% of
  the $438.5bn they reported. The article is right about this.
""")

H("C11 — CONFIRMED, and it had ALREADY HAPPENED before the article was written")
print("""
  The article frames early retirement as a consequence operators will face.
  Amazon faced it two years ago and disclosed it. FY2024 10-K, Note 1:

    "We completed our most recent servers and networking equipment useful
     life study in Q4 2024, and are changing the useful lives of a subset of
     our servers and networking equipment, effective January 1, 2025, FROM
     SIX YEARS TO FIVE YEARS... In 2024, we also determined, primarily in the
     fourth quarter, TO RETIRE EARLY certain of our servers and networking
     equipment. We recorded approximately $920 MILLION OF ACCELERATED
     DEPRECIATION and related charges... These two changes above are due to
     AN INCREASED PACE OF TECHNOLOGY DEVELOPMENT, PARTICULARLY IN THE AREA OF
     ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING."

  That is the article's mechanism, in the filing, in the company's own words.
  This is the one claim that survives intact -- and it is retrospective.
""")
gross = r["amzn_gross_servers_networking_2025"]
charge = r["amzn_accelerated_depreciation_q4_2024"]
rev_effect = r["amzn_useful_life_reversal_fy2025_actual"]
print(f"  Amazon early-retirement charge                   ${charge.fmt(0):>10} M")
print(f"  against gross servers and networking             ${gross.fmt(0):>10} M")
print(f"  => the charge as a share of the fleet             {((charge/gross)*I.of(100)).fmt(2):>10} %")
print(f"  FY2025 effect of the 6->5 reversal (actual)      ${rev_effect.fmt(0):>10} M of D&A")
print(f"  guided at                                        $       700 M of operating income")
print("""
  Two things the article's framing misses, both visible in the same filings:

  (1) THE CHARGE IS TINY. $920m against a $172bn gross fleet is 0.53%. It is
      a rounding error on the balance sheet, which is consistent with the
      break-even analysis: where the swap clears, the write-down is about one
      year of the incremental revenue it buys.

  (2) AMAZON NETTED IT OUT IN THE SAME BREATH. On the same call it extended
      HEAVY EQUIPMENT from 10 to 13 years, worth +$0.9bn to 2025 operating
      income -- almost exactly cancelling the -$0.7bn server hit, in a
      different segment. The earnings effect the article predicts was
      neutralised by an unrelated estimate change disclosed on the same day.
""")

H("The claim the article makes that the evidence contradicts")
print("""
  "You cannot maintain the position that server assets have a six-year useful
   life for accounting purposes while simultaneously cycling hardware every
   twenty-four months."

  As a statement about consistency, fine. As a statement about what happens to
  the P&L, it assumes book value exceeds market value at the moment of the
  pull. That is an empirical question, and straight-line depreciation is
  LINEAR while resale decay is EXPONENTIAL -- so the two curves cross, and
  after the crossing an early retirement produces a GAIN, not a charge.
""")
print(f"  {'age (yr)':>9} {'book: 6-yr SL':>15} {'H100 resale @ -17%/yr':>23} {'outcome':>22}")
decay = I.of(1) - r["h100_sxm5_resale_decay_per_year"]
for a in range(0, 7):
    book = I.of(1) - I.of(a) / I.of(6)
    resale = I.of(1)
    for _ in range(a):
        resale = resale * decay
    if book.lo > resale.hi:
        out = f"charge of {((book-resale)*I.of(100)).fmt(1)} pts"
    elif resale.lo > book.hi:
        out = f"GAIN of {((resale-book)*I.of(100)).fmt(1)} pts"
    else:
        out = "break-even"
    print(f"  {a:>9} {book.fmt(3):>15} {resale.fmt(3):>23} {out:>22}")

print(f"""
  The curves cross at about 1.4 years. Beyond that, a six-year straight-line
  book carries the asset BELOW what the secondary market pays for it, and
  pulling it early books a gain.

  The article's break-even is exact and I computed it before seeing this data:
  an asset pulled at 24 months against a 72-month book must fetch
  {breakeven_resale_for_no_charge(I.of(1), I.of(24), I.of(72)).fmt(4)} of original cost to avoid a charge. The observed H100 curve
  puts a two-year-old part at roughly 0.69. It clears.
""")

H("Corroboration from the whole observed resale series")
print(f"  {'part':<18} {'age':>6} {'resale':>9} {'6-yr SL book':>14} {'verdict':>16}")
for key, age, label in (("h100_sxm5_resale_fraction_of_basis", "3.9", "H100 80GB SXM5"),
                        ("a100_80gb_resale_fraction_of_basis", "5.8", "A100 80GB SXM4"),
                        ("v100_32gb_resale_fraction_of_basis", "8.5", "V100 32GB")):
    resale = r[key]
    a = I.of(age)
    book = I.of(1) - a / I.of(6)
    book = I(max(F(0), book.lo), max(F(0), book.hi))
    verdict = "GAIN" if resale.lo > book.hi else "charge" if book.lo > resale.hi else "break-even"
    print(f"  {label:<18} {age:>6} {resale.fmt(3):>9} {book.fmt(3):>14} {verdict:>16}")
print("""
  Every observed point sits at or above the six-year straight-line book.
  On this evidence the hyperscalers' six-year life is CONSERVATIVE relative
  to what the market pays, not aggressive -- which is the opposite of the
  claim the depreciation debate is built on.

  Three caveats that must travel with this, because they are large:
    - n = 10 for H100 and 14 for A100 over 90 days. Only V100 (n=122) has a
      real sample. These are thin markets.
    - CCIR's "launch basis" is a system-allocated per-GPU cost, not chip
      MSRP. Re-basing on MSRP roughly DOUBLES the residual percentages, which
      would strengthen this conclusion, not weaken it.
    - H100 SXM5 prints 48.4% and H100 PCIe 79.4% at the same age on the same
      silicon. A 31-point spread within one part number is a warning about
      how much weight any single figure can carry.
""")

H("Why the two sides of the debate keep talking past each other")
print("""
  The depreciation argument has bifurcated into two claims that need scoring
  separately, because the evidence points in opposite directions:

  THE TIMING CLAIM -- that extensions deferred expense which must now arrive.
  Being confirmed quarter by quarter. Oracle PP&E depreciation $3.1bn (FY24)
  -> $3.9bn (FY25) -> $7.6bn (FY26). Meta server/network depreciation $7.3bn
  -> $11.3bn -> $13.4bn, and H1 2026 is +43.7% year on year DESPITE the
  extension to 5.5 years. Amazon's AWS segment D&A $13.3bn -> $21.5bn.

  THE OBSOLESCENCE CLAIM -- that the hardware stops earning. Being actively
  contradicted. Oracle: 97.9% GPU utilisation, and GPUs coming up for renewal
  "renewed or resold at a 20% premium to prior contracts... the majority of
  those GPUs are 4 years or older." AWS CEO: "we have never retired an A100
  server." CoreWeave signed an A100 contract running to 2029 on a 2020 part.

  The article inherits the second claim to motivate cannibalization and the
  first to price it. They do not hold together: hardware that is still
  renewing at a premium is not hardware anyone is ripping out.
""")

H("And the cleanest evidence that book life is judgment, not measurement")
print("""
  On 1 January 2025, on comparable hardware, citing the same industry
  conditions:

    AMAZON shortened a subset of servers and networking from 6 to 5 years,
      because of "the increased pace of technology development, particularly
      in the area of artificial intelligence and machine learning."

    META extended most servers and network assets from 5 to 5.5 years.

  Same date. Opposite directions. Same stated environment. No single filing's
  useful life should be treated as a measurement of how long the hardware
  lasts, and any model that keys off one company's life is keying off that
  company's judgement.
""")
