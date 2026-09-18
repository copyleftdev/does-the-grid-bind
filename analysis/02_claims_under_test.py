#!/usr/bin/env python
"""Test the article's claims against the data. Every number exact."""
import sys; sys.path.insert(0, "src")
from fractions import Fraction as F

from chipgrid.exact import Interval as I
from chipgrid.invariants import implied_asp_growth
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

# ---------------------------------------------------------------------- C2/C3
H("C2 / C3 — the revenue, the units, and the implied ASP")

print("""
The article: "Nvidia outlined long-term expectations pointing toward fiscal 2028
revenue of roughly 673 billion dollars, an increase of approximately 70 percent."

What NVIDIA actually said (Kress, CFO, Q2 FY2027 call, 2026-08-26):
  "We expect to grow revenue by approximately 70% in fiscal 2028.
   This is a supply-constrained outlook."

The 70% is real and is a filed-equivalent disclosure. The $673B is not NVIDIA's
number at all -- it is CNBC's arithmetic, $396B of LSEG ANALYST CONSENSUS times
1.70. The string "673" appears zero times in the 8-K, the 10-Q, and the
corrected transcript, and neither filing contains any FY2028 revenue statement.
""")

h1 = r["nvda_fy2027_h1_actual"]; q3 = r["nvda_q3_fy2027_guidance_midpoint"]
three_q = h1 + q3
print(f"  FY2027 H1 actual (filed)            ${(h1/I.of(1000)).fmt(1):>10} B")
print(f"  Q3 FY2027 guidance midpoint (filed) ${(q3/I.of(1000)).fmt(1):>10} B")
print(f"  three quarters on the record        ${(three_q/I.of(1000)).fmt(1):>10} B")
q2 = I.of("96.221")
print(f"  Q3 guided q/q growth                 {((q3/I.of(1000)/q2)-I.of(1)).fmt(4)}")

print("\n  FY2028 revenue at +70%, by the Q4 FY2027 growth rate assumed:")
print(f"    {'Q4 q/q':>8}  {'FY2027':>10}  {'FY2028 @ +70%':>15}")
base_q3 = q3 / I.of(1000)
for g in ("0.00", "0.02", "0.05", "0.10", "0.12", "0.15"):
    q4 = base_q3 * (I.of(1) + I.of(g))
    fy27 = three_q / I.of(1000) + q4
    fy28 = fy27 * I.of("1.70")
    tag = "  <- CNBC's implied Q4" if g == "0.02" else ("  <- Q3's own guided rate" if g == "0.12" else "")
    print(f"    {g:>8}  ${fy27.fmt(1):>9}  ${fy28.fmt(1):>14}{tag}")

print("""
  CNBC's $396B base requires Q4 FY2027 to grow +2.0% q/q in a quarter NVIDIA
  guided to +12.2%. The five prior sequential Data Center prints were
  +5, +25, +22, +21, +18 percent. If Q4 grows at Q3's own guided rate the
  figure is ~$692B, not $673B.
""")

print("  The ASP inference:")
asp = implied_asp_growth(I.of("0.70"), I.of("1.00"))
print(f"    exact  (1+0.70)/(1+1.00) - 1  = {asp.lo}  = {asp.fmt(4)}")
print(f"    the article's additive figure = -0.30")
print(f"    the shortcut overstates the decline by a factor of {(I.of('0.30')/I.of('0.15')).fmt(1)}")

print("""
  But the arithmetic error is the smaller problem. The inference has three
  further defects, each independently fatal:

  (1) DIFFERENT SPEAKERS, DATES AND PERIODS. Huang's unit remark was made to
      reporters at a private summit in Scotland on 2026-09-17 and refers to
      "next year". Kress's 70% was given on an earnings call on 2026-08-26 and
      refers to fiscal 2028, ending January 2028. Dividing one by the other
      assumes a coincidence of periods that nobody asserted.

  (2) THE BASKET WAS NEVER DEFINED. Huang said "chips". CNBC's own reporter
      flagged the ambiguity in the same article. NVIDIA guides Vera CPU revenue
      to more than double, ships Groq 3 LPX racks holding 256 LPUs each, and
      sells five distinct networking chip families per rack-scale system. A
      unit count over that basket is not a data-center-GPU count.

  (3) NVIDIA ALREADY EXPLAINED THE GAP, AND IT IS NOT ASP. From the same call:
        "Customers' forecasts point to our growth doubling next year.
         However... we expect to grow approximately 70% as we are
         supply-constrained."
      The company attributes the shortfall to SUPPLY, not to price. The
      article's reading requires the opposite mechanism.
""")

print("  And the direction is wrong. ASP is rising, not compressing:")
gm = r["nvda_gross_margin_fy2028_guided"]
print(f"    revenue per GW, Hopper -> Grace Blackwell -> Vera Rubin:  "
      f"${r['nvda_revenue_per_gw_hopper'].fmt(0)}B -> ${r['nvda_revenue_per_gw_grace_blackwell'].fmt(0)}B -> ${r['nvda_revenue_per_gw_vera_rubin'].fmt(0)}B per GW")
gb200_to_vr = r["nvda_revenue_per_gw_vera_rubin"] / r["nvda_revenue_per_gw_grace_blackwell"]
print(f"    Grace Blackwell -> Vera Rubin uplift per GW:              {gb200_to_vr.fmt(3)}x")
print(f"    FY2028 gross margin guided                                {gm.fmt(3)} (EXPANDING, on 'executed price increases')")
print("    NVIDIA notified top-5 customers of >15% price increases for early-2027 shipments")


# ------------------------------------------------------------------------ C4
H("C4 — 'fab capacity can double within several quarters'")
print("""
The article's asymmetry rests on this: silicon is fast, the grid is slow. The
claim was true in 2024 and 2025. It is not true now, and the people who build
the capacity say so on the record.
""")
yrs = [2023, 2024, 2025, 2026, 2027, 2028]
prev = None
print(f"  TSMC CoWoS capacity (all figures ESTIMATED -- TSMC has never disclosed a wpm number)")
print(f"    {'year':>6} {'wafers/month':>14} {'YoY':>10}")
for y in yrs:
    v = r[f"cowos_wpm_{y}"]
    g = "" if prev is None else ((v / prev) - I.of(1)).fmt(3)
    print(f"    {y:>6} {v.fmt(0):>14} {g:>10}")
    prev = v
print("""
  The doubling regime ended in 2025. Growth decays monotonically:
  +169% -> +121% -> +68% -> +54% -> +30%.

  And on how long new capacity takes, from the CEO who builds it -- C.C. Wei,
  TSMC, on three consecutive earnings calls:
    "two to three years to build a new fab. No shortcuts. And it takes
     another one to two years to ramp it up."            (1Q26, said 3x)
    "The lead time to develop a new technology such as A14, building the
     capacity, and then ramp it up now takes five to seven years."  (2Q26)
    of 2026 capex: "the contribution to this year is almost none, and
     2027, a little bit... we are looking for 2028-2029 supply."    (4Q25)
""")
build = r["fab_build_years"] + r["fab_ramp_years"]
print(f"  greenfield wafer fab, build + ramp:  {build.fmt(1)} years")
print(f"  transformer lead time as stated in the article: [3.0, 4.0] years")
print("""
  The two lead times now OVERLAP. The article's premise is an asymmetry
  between a fast side and a slow side; on the record, both sides are
  multi-year. The fastest observed advanced-packaging datapoint -- TSMC's AP8
  at ~15 months -- was a brownfield conversion of an already-built,
  already-powered LCD fab, and there is a finite supply of those.
""")

# ----------------------------------------------------------------- C12 and C9
H("C12 / C9 — spot compute pricing, and whether old silicon decays")
print("""
The article: "spot market pricing per GPU-hour must adjust downward to clear
available capacity", and accelerators "halve in economic competitiveness
within three to four years".

Both are falsified by the current data, and the second is falsified in a way
that matters for the article's own mechanism.
""")
trough = r["h100_neocloud_usd_per_gpu_hour_trough"]
now = r["h100_neocloud_usd_per_gpu_hour_now"]
a100 = r["a100_neocloud_usd_per_gpu_hour_now"]
print(f"  H100 neocloud index, trough 2025-12-09      ${trough.fmt(2)}")
print(f"  H100 neocloud index, 2026-09-18             ${now.fmt(2)}")
print(f"  change off the trough                        {((now/trough)-I.of(1)).fmt(4)}")
print(f"  A100 neocloud index, 2026-09-18             ${a100.fmt(2)}   (a 2020 part)")
print("""
  Corroborated by the issuer itself. NVIDIA, Q1 FY2027 call, 2026-05-20:
    "The price of renting an H100 has risen 20% year to date, while
     A100 cloud pricing is up nearly 15%."
  And by CoreWeave's March 2026 investor deck:
    "average A100 pricing increased in 2025."

  An A100 launched in 2020. On C9's schedule it should have lost half its
  economic competitiveness twice over. It is appreciating.
""")
res = r["h100_reserve_12mo_usd_per_gpu_hour"]; spot = I.of("2.63")
print(f"  12-month reserve ${res.fmt(2)} against spot ${spot.fmt(2)}  =>  {((res/spot)-I.of(1)).fmt(4)}")
print("""
  The forward curve is BACKWARDATED: committed capacity is cheaper than spot at
  every observed tenor. That is the opposite sign from a scarcity-premium
  story, and it is the opposite sign from an oversupply story too -- an
  expected glut would put contango in the curve, not backwardation.
""")

print("  Why this matters for the article's own argument:")
print("""
  The article's mechanism is that POWER is scarce. Take that seriously and it
  predicts the observed prices rather than the ones the article forecasts. If
  the binding constraint is energized megawatts rather than silicon, then an
  accelerator that already occupies an energized slot carries option value on
  that slot. Its floor price is set by the scarcity of the envelope it sits
  in, not by its FLOPS. That is exactly why a six-year-old A100 is
  appreciating while newer parts ship.

  So the two halves of the article are in tension. If the grid constraint
  binds, prior-generation hardware does NOT decay on schedule -- which
  removes the premise of the cannibalization path, and largely removes the
  impairment with it.
""")


# ------------------------------------------------- the demand side, in GW
H("The bridge: NVIDIA's revenue guidance, converted to gigawatts")
print("""
The grid debate is conducted in gigawatts and the chip debate in dollars, which
is why they are never checked against each other. NVIDIA closed that gap itself
on the Q2 FY2027 call by disclosing revenue per gigawatt of AI factory, by
generation. That single disclosure turns a revenue forecast into a power
forecast, and it is the most useful number in this entire exercise.
""")
dc_share = r["nvda_datacenter_revenue_fy2026"] / r["nvda_revenue_fy2026"]
print(f"  Data Center share of FY2026 revenue (filed):  {dc_share.fmt(4)}")

fy28_lo, fy28_hi = I.of("669.5"), I.of("697.1")     # from the Q4 sensitivity above
fy28 = I.of(fy28_lo.lo, fy28_hi.hi)
dc28 = fy28 * dc_share
print(f"  FY2028 revenue at +70%, across Q4 assumptions: ${fy28.fmt(1)} B")
print(f"  implied FY2028 Data Center revenue:            ${dc28.fmt(1)} B")

print("\n  Converted to gigawatts of AI factory, at NVIDIA's own disclosed rates:")
for label, key in (("Vera Rubin  $40B/GW", "nvda_revenue_per_gw_vera_rubin"),
                   ("Grace Blackwell $25B/GW", "nvda_revenue_per_gw_grace_blackwell"),
                   ("Hopper      $18B/GW", "nvda_revenue_per_gw_hopper")):
    gw = dc28 / r[key]
    print(f"    {label:<26} {gw.fmt(1):>16} GW of global AI factory in FY2028")

gw_global = I.of((dc28 / r["nvda_revenue_per_gw_vera_rubin"]).lo,
                 (dc28 / r["nvda_revenue_per_gw_grace_blackwell"]).hi)
print(f"\n  global, across the plausible generation mix:  {gw_global.fmt(1)} GW/yr")
us = r["us_share_of_global_dc_electricity"]
gw_us = gw_global * us
print(f"  US share (IEA, electricity as a proxy):      {us.fmt(2)}")
print(f"  => NVIDIA-driven US AI factory build          {gw_us.fmt(1)} GW/yr")

print("""
  Cross-checks, all independent of the above:
    NVIDIA (Q2 FY27 call): neocloud partners exit 2026 with 8 GW installed,
      up from ~3 GW at end-2025 -- i.e. +5 GW in one year, neoclouds alone.
    IEA (Apr 2026): ~20 GW/yr of accelerated-server capacity added by 2030,
      IT only, excluding cooling and conventional servers.
    LBNL (Jun 2026): +17.4 GW/yr of US interconnection capacity 2024-2030
      in the Reference Case -- though that figure is DERIVED FROM the demand
      forecast and carries the 50% capacity-factor assumption, so it is not
      an independent measure of what the grid can deliver.
""")

print("  Now hold that against the queue numbers the debate actually quotes:")
ercot = r["ercot_large_load_queue_gw"]
print(f"    ERCOT large-load interconnection queue        {ercot.fmt(0):>8} GW   (vs an 85 GW state peak)")
print(f"    Dominion signed data-center contracts         {r['dominion_contracted_gw'].fmt(1):>8} GW")
print(f"    Dominion's own forecast of realised load      {r['dominion_forecast_gw'].fmt(1):>8} GW")
disc = r["dominion_forecast_gw"] / r["dominion_contracted_gw"]
print(f"    realisation ratio inside ONE utility          {disc.fmt(3):>8}")
print(f"    ERCOT queue as a multiple of US annual need   {(ercot/gw_us).fmt(1):>8} x")
print("""
  The queue is not a demand signal. It is an option book. Developers file in
  several interconnection queues for the same project because filing is cheap
  and priority is scarce, so the same megawatt is counted many times. Dominion
  is the cleanest measurement of the discount: one utility, 47 GW of SIGNED
  contracts, 16.6 GW of forecast load -- a realisation ratio of 0.35. Air
  Street counts ~94% of announced GB200/GB300 GPUs as not yet deployed.

  Any argument that reads a 230 GW queue as 230 GW of demand has mistaken the
  option book for the order book.
""")
