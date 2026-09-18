#!/usr/bin/env python
"""C8/C11 — is ripping out working silicon actually irrational, or merely ugly?"""
import sys; sys.path.insert(0, "src")
from chipgrid.exact import Interval as I
from chipgrid.invariants import cannibalization_breakeven_ratio
from chipgrid.accounting import (breakeven_resale_for_no_charge,
                                 excess_book_value_from_extension,
                                 impairment_on_early_retirement)
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("C8 / C11 — the cannibalization trade, priced")
print("""
The article treats the write-down as a deterrent: pulling two-year-old H100s
forces accelerated depreciation or impairment, and "you cannot maintain the
position that server assets have a six-year useful life while simultaneously
cycling hardware every twenty-four months."

That is true as accounting. The question the article does not ask is whether
the charge is large enough to change the decision. It is a one-off balance-
sheet event weighed against a recurring revenue gain, so the comparison is
decidable once a revenue-per-megawatt figure exists. Nebius disclosed one.
""")

# Nebius's $20-25M/MW-year is a CURRENT-GENERATION neocloud yield. Applying it
# to the Hopper megawatt being retired would overstate that asset's revenue and
# so understate the break-even ratio. Derive Hopper's own revenue instead, from
# the observed H100 rental price and the DGX H100 rack power NVIDIA publishes.
gpu_slot_w = I.of("1275")                     # DGX H100: 10.2 kW / 8 GPUs, IT
facility_w = gpu_slot_w * r["ai_facility_pue_2024"]
gpus_per_mw = I.of(1_000_000) / facility_w
util = I.of("0.85", "1.00")                   # NVIDIA: "our GPU installed base... is fully utilized"
rev = (gpus_per_mw * r["h100_neocloud_usd_per_gpu_hour_now"]
       * I.of(8760) * util) / I.of(1_000_000)   # $M per MW-year
print(f"  derived: {gpus_per_mw.fmt(0)} H100 per facility MW at PUE {r['ai_facility_pue_2024'].fmt(3)}")
print(f"  Hopper revenue per MW-year at ${r['h100_neocloud_usd_per_gpu_hour_now'].fmt(2)}/GPU-hr, util {util.fmt(2)}: ${rev.fmt(1)} M/MW/yr")
print(f"  (Nebius's disclosed CURRENT-generation yield, for contrast: ${r['nebius_yield_per_mw_year_midterm'].fmt(1)} M/MW/yr)")

cost = I.of(r["nvda_it_content_per_mw_hopper"].lo,
            r["nvda_it_content_per_mw_grace_blackwell"].hi)  # $M per MW
age, life = I.of(24), I.of(72)
remaining = (life - age) / I.of(12)

print(f"  IT content per MW, Hopper..Grace Blackwell (filed)  ${cost.fmt(1)} M/MW")
print(f"  revenue per MW-year of the RETIRED asset (derived)  ${rev.fmt(1)} M/MW/yr")
print(f"  asset age / book life                                {age.fmt(0)} / {life.fmt(0)} months")
print(f"  remaining book life                                  {remaining.fmt(2)} years")

nbv = impairment_on_early_retirement(cost, age, life)
print(f"\n  unamortised book value written off (no resale)      ${nbv.fmt(2)} M/MW")

rho_star = cannibalization_breakeven_ratio(age, life, cost, rev, remaining)
print(f"  BREAK-EVEN performance-per-watt ratio rho*           {rho_star.fmt(3)}")
print("""
  rho* is the factor by which the new generation's performance per watt must
  beat the old one's for the swap to repay the write-down over the retired
  asset's remaining book life.
""")
obs_fp8 = r["rack_dense_fp8_tflops_per_watt_gb300"] / r["rack_dense_fp8_tflops_per_watt_h100"]
obs_fp4 = r["rack_dense_fp4_tflops_per_watt_gb300"] / r["rack_dense_fp4_tflops_per_watt_gb200"]
print(f"  observed, rack-level dense FP8, H100 -> GB300        {obs_fp8.fmt(3)}")
print(f"  observed, rack-level dense FP4, GB200 -> GB300       {obs_fp4.fmt(3)}")
print(f"\n  does the observed ratio clear the bar?")
for name, obs in (("dense FP8, two generations", obs_fp8), ("dense FP4, one generation", obs_fp4)):
    verdict = ("YES, by every point of the interval" if obs.strictly_above(rho_star.hi)
               else "UNDECIDED — the intervals overlap" if obs.hi > rho_star.lo
               else "NO")
    print(f"    {name:<30} {obs.fmt(2):>14}  vs  {rho_star.fmt(2):<16} {verdict}")

print("""
  Read the margins, not just the verdicts. The two-generation swap clears its
  break-even by a wide margin. The ONE-generation swap clears by about two
  percent of the ratio -- inside the error of every input feeding it, and it
  would not clear at all if the retired asset's utilization sat at the low end
  while its book life ran to six years.

  So the model's prediction is narrower and more falsifiable than either the
  article's or my own first pass at it:

    operators should cycle the installed base roughly every TWO generations,
    not every one, and the cycling decision should be visibly sensitive to the
    rental price of the OUTGOING part rather than to the specification of the
    incoming one.

  Where the swap does clear, the write-down is not a deterrent: it is roughly
  one year of the incremental revenue it buys. That inverts the article's
  conclusion without disputing its premise. The impairment is an
  EARNINGS-OPTICS event, not an economic constraint -- which is exactly why one
  would expect to observe operators taking the charge and disclosing it,
  rather than protecting the useful-life assumption by declining the trade.
""")

H("And the resale market decides how much of the charge is even real")
print(f"""
  An asset pulled at {age.fmt(0)} months against a {life.fmt(0)}-month book life needs to
  resell for exactly {breakeven_resale_for_no_charge(I.of(1), age, life).fmt(4)} of original cost to avoid any P&L charge.
""")
for resale_frac in ("0.00", "0.25", "0.50", "0.6667"):
    ch = impairment_on_early_retirement(cost, age, life, cost * I.of(resale_frac))
    print(f"    resale at {resale_frac:>6} of cost  ->  charge ${ch.fmt(2)} M/MW")
print("""
  And prior-generation hardware is not cheap right now. NVIDIA disclosed A100
  cloud pricing up ~15% year to date; CoreWeave disclosed average A100 pricing
  ROSE in 2025. A part launched in 2020 is appreciating in the rental market,
  which supports its residual value and shrinks the charge further.
""")

H("The liability the life extension created")
print("""
  I4 (book conservation) says depreciation moves cost between periods and
  cannot reduce it. Extending useful life therefore does not make the expense
  go away; it defers it, and an early retirement calls the deferral.
""")
for old, new in ((4, 6), (3, 6), (4, 5), (5, 6)):
    ex = excess_book_value_from_extension(I.of(1), I.of(2), I.of(old), I.of(new))
    print(f"    life {old}y -> {new}y, asset pulled at age 2:  extra unamortised value "
          f"= {ex.fmt(4)} of gross cost")
print("""
  The 4-to-6-year extension that Microsoft and Alphabet made is worth exactly
  one sixth of gross cost in additional exposure at age two. That is the
  quantity at risk per dollar of fleet, and it is fixed by arithmetic before
  any judgement about whether the extension was justified.
""")
