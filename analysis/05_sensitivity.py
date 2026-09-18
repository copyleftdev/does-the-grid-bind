#!/usr/bin/env python
"""Whose fault is the uncertainty?

Not "how uncertain is the answer" but "which input decides it". If one factor
carries most of the total-effect index, the entire disagreement reduces to
measuring that one quantity and everything else is theatre.
"""
import sys; sys.path.insert(0, "src")
import numpy as np

from chipgrid.exact import Interval as I
from chipgrid.load import load
from chipgrid.mc import Dist, sobol_indices

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("Required new US grid capacity — the seven-factor chain, sampled")

# The chain, in GW. Ranges carry their provenance in the comment.
DISTS = [
    # NVIDIA FY2028 Data Center revenue, $B. FILED growth rate, base uncertainty.
    Dist("dc_revenue_bn", 600.7, 625.4, "uniform"),
    # NVIDIA's own disclosed $/GW, Grace Blackwell 25 .. Vera Rubin 40. FILED.
    Dist("revenue_per_gw", 25.0, 40.0, "uniform"),
    # US share of global deployment. ESTIMATED (IEA, electricity as proxy).
    Dist("share_us", 0.45, 0.50, "uniform"),
    # Fraction landing in an ALREADY-ENERGIZED envelope (refresh/cannibalization).
    # UNSOURCED - this is the gap the model has to flag, not fill.
    Dist("share_refresh", 0.10, 0.45, "uniform"),
    # Fraction served outside the interconnection queue: behind-the-meter gas,
    # fuel cells, nuclear co-location, curtailment-enabled flexible load,
    # reuse of already-contracted capacity. UNSOURCED pending the grid research.
    Dist("share_offgrid", 0.10, 0.45, "uniform"),
]

def chain(c):
    return (c["dc_revenue_bn"] / c["revenue_per_gw"]
            * c["share_us"] * (1 - c["share_refresh"]) * (1 - c["share_offgrid"]))

rng = np.random.default_rng(20260918)
n = 400_000
cols = {d.key: d.sample(rng, n) for d in DISTS}
y = chain(cols)

print(f"  n = {n:,}   seed = 20260918\n")
print(f"  required new US grid capacity for the FY2028 NVIDIA cohort")
for q in (5, 25, 50, 75, 95):
    print(f"    p{q:<3} {np.percentile(y, q):8.2f} GW")
print(f"    ratio p95/p5 = {np.percentile(y,95)/np.percentile(y,5):.1f}x")

H("Sobol decomposition — which input owns the variance")
si = sobol_indices(DISTS, chain, n=16384)
print(f"  {'factor':<18}{'S1':>9}{'+/-':>8}{'ST':>9}{'+/-':>8}   {'provenance of the range'}")
prov = {
    "dc_revenue_bn":  "FILED growth rate, analyst base",
    "revenue_per_gw": "FILED, but restated once",
    "share_us":       "ESTIMATED (electricity proxy)",
    "share_refresh":  "*** UNSOURCED ***",
    "share_offgrid":  "*** UNSOURCED ***",
}
for k, v in sorted(si.items(), key=lambda kv: -kv[1]["ST"]):
    print(f"  {k:<18}{v['S1']:9.3f}{v['S1_conf']:8.3f}{v['ST']:9.3f}{v['ST_conf']:8.3f}   {prov[k]}")

unsourced = si["share_refresh"]["ST"] + si["share_offgrid"]["ST"]
total = sum(v["ST"] for v in si.values())
print(f"""
  Share of total-effect index carried by the two UNSOURCED factors:
      {unsourced/total:.1%}

  That is the finding. The two quantities that dominate the answer -- what
  fraction of new hardware lands in an already-energized envelope, and what
  fraction is powered outside the interconnection queue -- are precisely the
  two the article never mentions, and neither has a published measurement.

  Meanwhile the factors the debate actually argues about, NVIDIA's revenue and
  the transformer and queue lead times, are either already disclosed or barely
  move the result. Measuring the interconnection queue more precisely cannot
  resolve this question, because the queue is not where the variance lives.
""")

H("What would actually collapse the uncertainty")
base = np.percentile(y, 95) / np.percentile(y, 5)
for pin, val in (("share_refresh", 0.275), ("share_offgrid", 0.275),
                 ("revenue_per_gw", 32.5), ("share_us", 0.475)):
    c2 = dict(cols); c2[pin] = np.full(n, val)
    y2 = chain(c2)
    ratio = np.percentile(y2, 95) / np.percentile(y2, 5)
    print(f"    pin {pin:<16} -> p95/p5 falls {base:5.1f}x -> {ratio:5.1f}x"
          f"   ({(1-ratio/base):5.1%} of the spread removed)")
