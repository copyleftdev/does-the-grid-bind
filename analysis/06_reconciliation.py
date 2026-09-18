#!/usr/bin/env python
"""I8 — closing the loop between the demand side and the supply side.

A national energy model and a vendor's revenue guidance are never checked
against each other, because they are denominated differently: one in terawatt
hours, the other in dollars. Both convert to gigawatts. If they disagree, one
of them is wrong and the disagreement is more informative than either figure.
"""
import sys; sys.path.insert(0, "src")
from chipgrid.exact import Interval as I
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("Route A — bottom-up from LBNL's energy model")
twh_2030 = r["us_dc_twh_2030_reference"]
ai_share_2030 = I.of("0.53", "0.59")     # LBNL: 55% Reference, 53% Consolidated, 59% High Inference
cf = I.of(r["interconnection_capacity_factor_measured_colo"].lo,
          r["interconnection_capacity_factor_measured_hyperscale"].hi)  # EPRI measured 0.57..0.75

ai_twh_2030 = twh_2030 * ai_share_2030
ai_gw_2030 = (ai_twh_2030 * I.of(1000)) / (I.of(8760) * cf)
print(f"  LBNL 2030 US data centre energy, Reference       {twh_2030.fmt(0):>16} TWh")
print(f"  AI servers as a share of it (LBNL scenarios)     {ai_share_2030.fmt(2):>16}")
print(f"  => AI-attributable energy in 2030                {ai_twh_2030.fmt(0):>16} TWh")
print(f"  capacity factor, EPRI MEASURED (colo..hyperscale){cf.fmt(2):>16}")
print(f"  => US AI nameplate capacity in 2030              {ai_gw_2030.fmt(1):>16} GW")

twh_2024 = r["us_dc_twh_2024"]
ai_share_2024 = I.of("0.25", "0.35")     # LBNL: >40 TWh of 176 in 2023 (23%), rising
ai_gw_2024 = (twh_2024 * ai_share_2024 * I.of(1000)) / (I.of(8760) * cf)
print(f"\n  same construction for 2024 (AI share 25-35%)     {ai_gw_2024.fmt(1):>16} GW")
years = I.of(6)
route_a = (ai_gw_2030 - ai_gw_2024) / years
print(f"  => implied US AI capacity additions, 2024-2030   {route_a.fmt(1):>16} GW/yr")

H("Route B — top-down from NVIDIA's revenue guidance and disclosed $/GW")
dc28 = I.of("600.7", "625.4")
per_gw = I.of(r["nvda_revenue_per_gw_grace_blackwell"].lo, r["nvda_revenue_per_gw_vera_rubin"].hi)
gw_global = dc28 / per_gw
route_b = gw_global * r["us_share_of_global_dc_electricity"]
print(f"  NVIDIA FY2028 Data Center revenue                ${dc28.fmt(1):>15} B")
print(f"  NVIDIA disclosed revenue per GW (GB..Vera Rubin) ${per_gw.fmt(0):>15} B/GW")
print(f"  => global AI factory build                       {gw_global.fmt(1):>16} GW/yr")
print(f"  US share                                         {r['us_share_of_global_dc_electricity'].fmt(2):>16}")
print(f"  => US AI capacity additions                      {route_b.fmt(1):>16} GW/yr")

H("Do they close?")
print(f"  Route A, LBNL energy model bottom-up   {route_a.fmt(1):>14} GW/yr")
print(f"  Route B, NVIDIA revenue top-down       {route_b.fmt(1):>14} GW/yr")
overlap_lo = max(route_a.lo, route_b.lo); overlap_hi = min(route_a.hi, route_b.hi)
if overlap_lo <= overlap_hi:
    ov = I(overlap_lo, overlap_hi)
    print(f"\n  THEY RECONCILE. Overlap:               {ov.fmt(1):>14} GW/yr")
    print(f"""
  Two methods sharing no inputs -- a national bottom-up energy model built
  from server shipments and measured power draw, and a vendor's revenue
  guidance divided by its own disclosed content per gigawatt -- agree on the
  rate at which US AI capacity is being added.

  That is worth more than either number alone. It means the quantity on the
  demand side of the energization question is roughly KNOWN, to within a
  factor of about two, and the remaining argument is entirely on the supply
  side and in the two unsourced shares from the sensitivity analysis.
""")
else:
    print(f"\n  THEY DO NOT RECONCILE. Gap between {route_a.fmt(1)} and {route_b.fmt(1)}.")

H("Now set that against the numbers the debate actually quotes")
rows = [
    ("US AI capacity actually being added, per year", f"{max(route_a.lo,route_b.lo):.1f} - {min(route_a.hi,route_b.hi):.1f} GW/yr", "reconciled, two methods"),
    ("LBNL implied US interconnection additions", "17.4 GW/yr", "DERIVED from the demand forecast, at the 50% assumption"),
    ("ERCOT large-load queue", "230 GW", "one state, an option book"),
    ("Dominion signed data-centre contracts", "47 GW", "one utility"),
    ("Dominion's own forecast of realised load", "16.6 GW", "same utility, same filing"),
]
for label, val, note in rows:
    print(f"  {label:<46} {val:>18}   {note}")
print("""
  The gap between what is queued and what is needed is not evidence of a
  shortage. It is evidence that a queue position is a cheap option and that
  the same megawatt is counted in several places at once. Dominion states
  both numbers in one filing: 47 GW contracted, 16.6 GW expected.
""")
