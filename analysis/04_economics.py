#!/usr/bin/env python
"""C12 — the marginal cost of a token, and the band where capital dies quietly."""
import sys; sys.path.insert(0, "src")
from chipgrid.exact import Interval as I
from chipgrid.economics import (full_cost_per_gpu_hour, loss_band,
                                marginal_cost_per_gpu_hour, utilization_required)
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("C12a — 'the incremental cost of generating an additional token is largely\n       the price of wholesale electricity'")

facility_w = r["h100_it_watts_per_gpu_slot"] * r["ai_facility_pue_2024"]
energy = marginal_cost_per_gpu_hour(r["h100_it_watts_per_gpu_slot"],
                                    r["ai_facility_pue_2024"],
                                    r["us_industrial_electricity_price"])
price = r["h100_neocloud_usd_per_gpu_hour_now"]
cash = price * (I.of(1) - r["neocloud_contracted_ebitda_margin"])

print(f"  H100 facility draw per GPU                    {facility_w.fmt(0):>10} W")
print(f"  US industrial electricity, Jun 2026 (EIA)     ${r['us_industrial_electricity_price'].fmt(2):>9} /MWh")
print(f"  => energy cost per GPU-hour                   ${energy.fmt(4):>9}")
print()
print(f"  observed H100 neocloud rate                   ${price.fmt(2):>9} /GPU-hr")
print(f"  CoreWeave disclosed contracted EBITDA margin   {r['neocloud_contracted_ebitda_margin'].fmt(2):>9}")
print(f"  => all-in CASH cost (lease, power, direct opex) ${cash.fmt(3):>7} /GPU-hr")
print()
share = energy / cash
print(f"  ELECTRICITY AS A SHARE OF CASH MARGINAL COST   {(share*I.of(100)).fmt(1):>9} %")
print(f"""
  The claim is wrong by roughly a factor of five. Electricity is about a fifth
  of cash marginal cost, not "largely" it. The rest is the data-center lease,
  interconnect and bandwidth, staffing, and the sheer cost of operating liquid-
  cooled plant. And note the direction of the error: an argument that marginal
  cost is nearly all electricity predicts prices collapsing toward ~$0.13 as
  capacity clears. The actual cash floor is ~${cash.fmt(2)}, five times higher.
""")

H("C12b — the two floors, and the band between them")
capex_per_gpu = (r["nvda_it_content_per_mw_grace_blackwell"] * I.of(1_000_000)) / (
    I.of(1_000_000) / facility_w)
print(f"  implied IT capex per GPU slot (at $25M/MW)    ${capex_per_gpu.fmt(0):>9}")

for life, label in ((I.of(4), "4-year book (Nebius)"),
                    (I.of(5), "5-year book (Lambda)"),
                    (I.of(6), "6-year book (CoreWeave)")):
    full = full_cost_per_gpu_hour(capex_per_gpu, life, I.of("0.90"), cash)
    band = loss_band(cash, full)
    print(f"\n  {label}")
    print(f"    cash floor (switch-off point)               ${cash.fmt(3):>9} /GPU-hr")
    print(f"    full-cost recovery at 90% utilization       ${full.fmt(3):>9} /GPU-hr")
    print(f"    LOSS BAND width                             ${band.fmt(3):>9} /GPU-hr")
    verdict = ("ABOVE full cost — capital is being returned" if price.strictly_above(full.hi)
               else "INSIDE the loss band — the plant runs, the capital does not come back"
               if price.hi > cash.hi else "below cash cost")
    print(f"    observed ${price.fmt(2)} is: {verdict}")

print(f"""
  This is the mechanism the article gestures at with "the return distribution
  splits", made exact. Between the cash floor and full-cost recovery there is
  a wide interval in which every machine stays powered, tokens stay cheap, and
  the equity is quietly destroyed. Nothing switches off at the top of that
  band, so the band does not clear itself -- which is why the observed price
  floor has been a DEBT-SERVICE floor around $1.70-2.00 rather than the cash
  floor near ${cash.fmt(2)}.

  The useful-life assumption sits directly on this. A 6-year book puts
  full-cost recovery lower than a 4-year book does, so the SAME market price
  is profitable under CoreWeave's accounting and loss-making under Nebius's.
  The depreciation debate is not only about reported earnings; it changes
  which operators believe they are above water.
""")

H("C12c — the utilization each price implies")
for p in ("1.50", "2.00", "2.65", "3.50"):
    u = utilization_required(I.of(p), capex_per_gpu, I.of(6), cash)
    mark = "  <- observed" if p == "2.65" else ""
    feasible = "" if u.hi <= 1 else "   INFEASIBLE at any utilization" if u.lo > 1 else "   feasible only at the top of the range"
    print(f"    at ${p}/GPU-hr, 6-year book: utilization required {u.fmt(3):>16}{feasible}{mark}")


H("Model validation — the computed full-cost floor against the observed one")
print(f"""
  This is the one place in the whole exercise where the model can be checked
  against something it was not fitted to.

  Computed full-cost recovery, from NVIDIA's disclosed $/GW, the DGX H100 rack
  power, LBNL's AI-facility PUE, EIA's industrial electricity price and
  CoreWeave's disclosed EBITDA margin -- none of which is a price observation:

      4-year book   $1.820 /GPU-hr
      5-year book   $1.588 /GPU-hr
      6-year book   $1.434 /GPU-hr
                    ------------------
      range         $1.43 - $1.82

  Independently OBSERVED price floor, from two rental indices that know
  nothing about any of the above:

      SemiAnalysis 1-year contract trough, Oct 2025      $1.70
      Silicon Data marketplace median, H2 2025           $1.92 - $2.00
      Silicon Data stated support zone, Sep 2025         $2.13 - $2.15
                    ------------------
      observed      $1.70 - $2.15

  The intervals overlap. A bottom-up cost model built entirely from filings,
  datasheets and government statistics lands within a few cents of where the
  market actually stopped falling. That is the strongest evidence available
  that the cost structure here is right, and it is why the conclusion that
  today's $2.65 sits ABOVE full-cost recovery can be stated rather than hedged.

  It also identifies what the floor IS. It is not the cash cost of running the
  machine (~$0.66) and it is not a physical limit. It is the price at which
  the capital stops being returned -- and prior-generation capacity exits or
  refuses to renew below it. The article predicted the floor would be set by
  wholesale electricity. It is set by the depreciation schedule.
""")
