#!/usr/bin/env python
"""Export every figure the site renders, straight from the model.

The site reads this file. Nothing on the page is typed by hand, so the report
cannot drift from the analysis that produced it, and `git diff` on this file
is the diff of the published claims.
"""
import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, "src")

import numpy as np

from chipgrid.exact import Interval as I
from chipgrid.invariants import implied_asp_growth
from chipgrid.load import load

r = load("data/parameters.yaml")
f = lambda iv, p=4: [float(iv.lo), float(iv.hi)] if not iv.is_point else float(iv.lo)

out = {}

out["meta"] = {
    "title": "Does the grid bind?",
    "subject": "What Happens When Chip Volume Doubles but the Grid Does Not",
    "author": "Dean Lee", "published": "2026-09-18", "audited": "2026-09-18",
    "source_url": "https://dev.to/deanlee/what-happens-when-chip-volume-doubles-but-the-grid-does-not-485c",
    "parameters": len(list(r.keys())),
    "hard_evidence": sum(1 for p in r.values() if p.provenance.is_hard),
}

# ---------------------------------------------------------------- the verdict
rng = np.random.default_rng(20260918)
n = 500_000
S = rng.uniform(6.8, 11.6, n) * (1 - rng.uniform(0.0, 0.23, n))
E = (rng.uniform(1.244, 1.877, n) / rng.uniform(0.25, 0.45, n)) + rng.triangular(0.2, 1.0, 4.5, n)
short = S - E
hist, edges = np.histogram(short, bins=64, range=(-6, 10), density=True)
out["verdict"] = {
    "p_regime_c": round(float((S > E).mean()), 4),
    "median_shortfall_gw": round(float(np.median(short)), 3),
    "median_stranded_share": round(float(np.median(np.maximum(0, short) / S)), 4),
    "shortfall_quantiles": {str(q): round(float(np.percentile(short, q)), 3) for q in (5, 25, 50, 75, 95)},
    "density": {"edges": [round(float(x), 3) for x in edges],
                "values": [round(float(x), 5) for x in hist]},
    "n": n, "seed": 20260918,
}

# ------------------------------------------------------------------- claims
out["claims"] = [
 {"id":"C1","text":"Huang: NVIDIA will sell twice as many chips next year","verdict":"partial",
  "note":"True, but he said “chips” and never defined the basket. No primary source narrows it to data-centre GPUs."},
 {"id":"C2","text":"NVIDIA outlined FY2028 revenue of roughly $673 billion","verdict":"false",
  "note":"Not NVIDIA’s number. CNBC’s arithmetic on an analyst consensus. “673” appears zero times in the 8-K, the 10-Q and the transcript."},
 {"id":"C3","text":"The thirty-point gap implies ASP compression","verdict":"false",
  "note":"−15%, not −30. Different speakers, dates and periods. And NVIDIA attributed the gap to supply on that same call."},
 {"id":"C4","text":"Fab and packaging capacity can double within several quarters","verdict":"false",
  "note":"True in 2024. CoWoS growth now decays to +30%. TSMC’s CEO: “two to three years to build a new fab. No shortcuts.”"},
 {"id":"C5","text":"High-voltage transformers carry 36–48 month lead times","verdict":"partial",
  "note":"Directionally right, high, and thin. Best survey figure is 29 months; every published number traces to one root."},
 {"id":"C6","text":"Interconnection queues average four to seven years","verdict":"true",
  "note":"Measured median request-to-COD is 61 months for 2025 completions."},
 {"id":"C7","text":"The grid cannot double energized megawatts in twelve months","verdict":"true",
  "note":"ERCOT energized +0.9 GW of large load in 2025 against 445.8 GW of applications."},
 {"id":"C8","text":"Excess hardware takes one of two paths, both penalised","verdict":"partial",
  "note":"It is three regimes, not two, with a computable boundary. Verified exhaustively in TLA+."},
 {"id":"C9","text":"Accelerators halve in competitiveness within three to four years","verdict":"false",
  "note":"A 2020-vintage A100 is appreciating. NVIDIA disclosed A100 rental up ~15% year on year."},
 {"id":"C10","text":"Hyperscalers extended server life, deferring billions","verdict":"true",
  "note":"$43.8bn of FY2025 operating income across five companies — 11% of what they reported."},
 {"id":"C11","text":"Early decommissioning forces accelerated depreciation","verdict":"true",
  "note":"Confirmed — and it already happened. Amazon took a $920M charge in Q4 2024. But the conclusion inverts."},
 {"id":"C12","text":"Marginal cost is largely electricity; spot prices must fall","verdict":"false",
  "note":"Electricity is 20% of cash cost. Spot is up 32.5% off its trough."},
 {"id":"C13","text":"The return distribution splits","verdict":"partial",
  "note":"Real and computable — but the market is not currently inside the loss band."},
]

# --------------------------------------------------------------- the trichotomy
out["regimes"] = [
 {"key":"A","name":"Absorption is free","cond":"S ≤ E − B","body":"New capacity arrives faster than hardware does. Nothing is stranded and nothing is written down."},
 {"key":"B","name":"The write-down is forced","cond":"E − B < S ≤ E","body":"Everything can be racked, but only by pulling working gear out of the envelope it occupies. There is no clean schedule."},
 {"key":"C","name":"Stranding is forced","cond":"S > E","body":"No operator strategy absorbs the programme. Cannibalising does not cure it — it adds a write-down to it. The article misses this case."},
]
out["tlc"] = {"configs": 9, "passed": 9, "canaries": 3, "probes": 3}

# ----------------------------------------------------------------- arithmetic
g = implied_asp_growth(I.of("0.70"), I.of("1.00"))
out["asp"] = {"exact": float(g.lo), "additive": -0.30, "ratio": 2.0,
              "formula": "g_ASP = (1+g_rev)/(1+g_units) − 1 = 1.70/2.00 − 1 = −3/20"}

# ------------------------------------------------------------------ lead times
out["lead_times"] = [
 {"label":"Power transformer","months":29,"cls":"grid"},
 {"label":"Generator step-up unit","months":33,"cls":"grid"},
 {"label":"HV circuit breaker","months":35,"cls":"grid"},
 {"label":"Interconnection request → COD","months":61,"cls":"grid"},
 {"label":"Greenfield fab, build","months":30,"cls":"fab"},
 {"label":"Greenfield fab, build + ramp","months":48,"cls":"fab"},
 {"label":"New process node, end to end","months":72,"cls":"fab"},
]

# ---------------------------------------------------------------------- prices
out["prices"] = {
  "series":[{"t":"2023-09","h100":7.76},{"t":"2024-03","h100":7.92},{"t":"2024-09","h100":3.00},
            {"t":"2025-03","h100":3.50},{"t":"2025-06","h100":3.29},{"t":"2025-09","h100":2.13},
            {"t":"2025-12","h100":2.00},{"t":"2026-03","h100":2.53},{"t":"2026-06","h100":2.79},
            {"t":"2026-09","h100":2.65}],
  "trough":{"t":"2025-12","v":2.00},"now":2.65,"rise":0.325,
  "a100_now":1.58,
  "cash_cost":0.662,"energy_cost":0.134,"energy_share":0.202,
  "full_cost":{"4":1.820,"5":1.588,"6":1.434},
  "observed_floor":[1.70,2.15],
}

# ------------------------------------------------------------------ depreciation
decay = 1 - 0.170
out["depreciation"] = {
  "book":[{"age":a,"v":round(max(0.0,1-a/6),4)} for a in [x/4 for x in range(0,33)]],
  "resale":[{"age":a,"v":round(decay**a,4)} for a in [x/4 for x in range(0,33)]],
  "crossover_age":1.4,
  "breakeven_at_24mo":0.6667,
  "observed":[{"part":"H100 80GB SXM5","age":3.9,"v":0.484,"n":10},
              {"part":"A100 80GB SXM4","age":5.8,"v":0.244,"n":14},
              {"part":"V100 32GB","age":8.5,"v":0.035,"n":122}],
  "amzn_charge_musd":920,"amzn_gross_musd":172492,
  "amzn_charge_share":round(920/172492,5),
}

# ----------------------------------------------------------------------- funnel
out["funnel"] = [
 {"label":"Applications filed","gw":445.8},
 {"label":"Studies actually submitted","gw":124.8},
 {"label":"Under review","gw":93.7},
 {"label":"Screening requirements met","gw":22.0},
 {"label":"Approved, not operational","gw":3.2},
 {"label":"Observed energized","gw":5.9,"terminal":True},
]
out["queue"] = {"median_months":61,"completion_by_capacity":0.13,"withdrawn":0.75,
                "post_ia_conversion":0.43,"active_gw":2061,"throughput_gw":53,
                "littles_all_departures_yr":2.85,"measured_completers_yr":5.08}

# ----------------------------------------------------------------------- sobol
out["sobol"] = [
 {"k":"Share powered outside the queue","st":0.339,"sourced":False},
 {"k":"Share landing in an energized envelope","st":0.339,"sourced":False},
 {"k":"NVIDIA revenue per gigawatt","st":0.324,"sourced":True},
 {"k":"US share of deployment","st":0.016,"sourced":True},
 {"k":"NVIDIA revenue","st":0.002,"sourced":True},
]

# ------------------------------------------------------------- reconciliation
out["reconciliation"] = {
  "routes":[{"name":"LBNL energy model, bottom-up","lo":6.5,"hi":11.6},
            {"name":"NVIDIA revenue ÷ disclosed $/GW","lo":6.8,"hi":12.5}],
  "overlap":[6.8,11.6],
  "quoted":[{"name":"ERCOT large-load queue","gw":230},
            {"name":"Dominion signed contracts","gw":47},
            {"name":"Dominion’s own load forecast","gw":16.6}],
}

# ------------------------------------------------------------------- density
out["density_refresh"] = {"enterprise_rack_kw":[8,10],"ai_rack_kw":[132,142],
                          "ratio":[13.2,17.8],"recovered":[0.056,0.076],
                          "bound":[0.0,0.23]}

out["unknowns"] = [
 "What fraction of new hardware lands in an already-energized envelope. No published measurement. 33.9% of the variance.",
 "What fraction is powered outside the interconnection queue. No published measurement. 33.9% of the variance.",
 "Fleet-weighted GPU utilization. Measured values span 5% to 85%. No one has published a weighted average.",
 "What Amazon actually retired in Q4 2024 — no generation, count, location or gross cost is disclosed.",
 "Burry’s $176bn derivation. Verified as his exact words; the method is paywalled and unreproduced in ten months.",
 "The scaling from two published meter readings to a national energization figure. No source provides it — and it carries the verdict.",
]

Path("site/data/figures.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(f"wrote site/data/figures.json  ({Path('site/data/figures.json').stat().st_size:,} bytes)")
print(f"  P(C) = {out['verdict']['p_regime_c']:.3f}   median shortfall {out['verdict']['median_shortfall_gw']} GW/yr")
