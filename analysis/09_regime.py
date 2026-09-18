#!/usr/bin/env python
"""The verdict: which regime is the US AI buildout actually in?

Everything in this repository exists to answer this one question, because
`Energization.tla` proved the answer determines the consequence.
"""
import sys; sys.path.insert(0, "src")
import numpy as np

from chipgrid.exact import Interval as I
from chipgrid.load import load
from chipgrid.regime import Regime, classify

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

# ------------------------------------------------------------ Little's Law
H("First, an independent check on the queue numbers (I6, Little's Law)")
queue = r["queue_active_gw_2025"]
completed = r["queue_annual_throughput_gw"]
withdrew = I.of(750)
departures = completed + withdrew
w_all = I.of(2290) / departures
print(f"  active queue, end-2025                       {queue.fmt(0):>10} GW")
print(f"  reached operation in 2025                    {completed.fmt(0):>10} GW")
print(f"  withdrew in 2025                             {withdrew.fmt(0):>10} GW")
print(f"  => Little's Law residence, ALL departures    {w_all.fmt(2):>10} years")
print(f"  LBNL's MEASURED median for completers        {(r['queue_median_ir_to_cod_months_2025']/I.of(12)).fmt(2):>10} years")
print("""
  These are consistent and they are different quantities. A queue where 75%
  of capacity leaves by withdrawal has a short average residence and a long
  completion time: withdrawals exit early and drag the mean down. Completers
  wait about 1.8x the average departure. The two independent statistics
  reconcile, which is the point of running the check.

  VERDICT ON C6 ("queues average four to seven years"): the measured median
  interconnection-request-to-COD is 61 months (5.1 years) for 2025
  completions and 59 months for 200+ MW projects. The article's range
  brackets the median correctly. C6 STANDS.

  But the number that matters more is one the article does not cite: of
  3,501 GW of requests in the 2000-2020 cohort, 13% by capacity reached
  operation and 75% withdrew. Even an EXECUTED interconnection agreement
  converts only 43% of the time. A queue is not a pipeline.
""")

H("C5 — transformer lead times")
art = r["transformer_lead_months_article_claim"]
meas = r["transformer_lead_months_power"]
base = r["transformer_lead_months_baseline_2019"]
print(f"  article's claim                              {art.fmt(0):>12} months")
print(f"  Wood Mackenzie Q2 2025, power transformers   {meas.fmt(0):>12} months")
print(f"  ... generator step-up units                  {I.of(33).fmt(0):>12} months")
print(f"  ... HV circuit breakers                      {I.of(35).fmt(0):>12} months")
print(f"  2019/20 baseline (DOE)                       {base.fmt(0):>12} months")
print(f"  => increase since 2019/20                    {(meas/I.of(base.hi)).fmt(1):>12} x")
print("""
  VERDICT ON C5: directionally right, somewhat high, and resting on thinner
  evidence than its confidence implies. The best current survey figure is 29
  months for power transformers and 33 for GSUs, against the article's 36-48.
  DOE's "36 months, up to 60" traces to vendor interviews conducted 15-23
  June 2023; the 80-210 week range is proprietary survey data whose method
  and sample size are unpublished, and 210 weeks is an outer extreme, not a
  mean. NERC's widely-quoted 120 weeks footnotes the same article. There is
  no independent government measurement of transformer lead times at all.
""")

# ---------------------------------------------------------------- the regime
H("The regime test")
print("""
  Annual flows for the United States. S is new AI capacity needing power, E
  is newly available energized capacity. The installed-base term B is already
  netted out through share_refresh, bounded in analysis/08.
""")
s_gross = I.of("6.8", "11.6")                 # reconciled two independent ways
refresh = I.of("0.00", "0.23")                # bounded in 08_refresh
s_net = s_gross * (I.of(1) - refresh)

ercot = r["ercot_large_load_energized_gw_per_yr"]
dom = r["dominion_dc_connected_gw_per_yr"]
two = ercot + dom
share_of_us = I.of("0.25", "0.45")            # ERCOT + Northern Virginia share of US DC
grid_e = two / share_of_us
btm = I.of("0.2", "4.5")                      # Enverus 4.5 GW/yr projected; 1.0 GW measured
e_total = grid_e + btm

print(f"  S gross, US AI capacity additions (reconciled)     {s_gross.fmt(1):>16} GW/yr")
print(f"  share absorbed by refresh (bounded, analysis/08)   {refresh.fmt(2):>16}")
print(f"  S net, needing NEW power                           {s_net.fmt(1):>16} GW/yr")
print()
print(f"  ERCOT large load energized (MEASURED)              {ercot.fmt(2):>16} GW/yr")
print(f"  Dominion data centres connected (MEASURED)         {dom.fmt(2):>16} GW/yr")
print(f"  the two markets together                           {two.fmt(2):>16} GW/yr")
print(f"  their share of US data centre capacity (assumed)   {share_of_us.fmt(2):>16}")
print(f"  => implied US grid energization                    {grid_e.fmt(1):>16} GW/yr")
print(f"  + behind-the-meter (1.0 GW measured .. 4.5 proj.)  {btm.fmt(1):>16} GW/yr")
print(f"  E total                                            {e_total.fmt(1):>16} GW/yr")

v = classify(s_net, e_total, I.of(0))
print()
print(f"  VERDICT: {v.regime.value}")
if not v.decided:
    print(f"  consistent with: {', '.join(x.name for x in v.candidates)}")

H("The distribution, since the intervals do not decide it")
rng = np.random.default_rng(20260918)
n = 500_000
S = rng.uniform(6.8, 11.6, n) * (1 - rng.uniform(0.0, 0.23, n))
E = (rng.uniform(1.244, 1.877, n) / rng.uniform(0.25, 0.45, n)) + rng.triangular(0.2, 1.0, 4.5, n)
short = S - E
p_c = float((S > E).mean())
print(f"  n = {n:,}   seed = 20260918")
print(f"  P(regime C — stranding forced)                 {p_c:>8.1%}")
print(f"  P(regime A — absorption free)                  {1-p_c:>8.1%}")
print()
print(f"  annual shortfall S - E:")
for q in (5, 25, 50, 75, 95):
    print(f"    p{q:<3} {np.percentile(short, q):+7.2f} GW/yr")
print(f"  median stranded as a share of shipments        "
      f"{float(np.median(np.maximum(0,short)/S)):>8.1%}")
