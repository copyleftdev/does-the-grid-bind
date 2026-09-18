# The Energization Gap, Tested

An invariant model and primary-source audit of *"What Happens When Chip Volume
Doubles but the Grid Does Not"* (Dean Lee, dev.to, 2026-09-18).

Compiled 2026-09-18. Every number below is reproducible from this repository:
`spec/check.sh` for the formal results, `analysis/*.py` for the empirical ones.
All arithmetic that decides anything runs through `agent-calc` in exact
rational arithmetic; floats are refused at the type boundary.

---

## Verdict

The article's **structure** is sound and its **central accounting claim is
correct and has already been observed in a filing**. Most of its supporting
claims do not survive contact with primary sources, and two of them are
falsified by evidence the article's own mechanism predicts.

| # | Claim | Verdict |
|---|---|---|
| C1 | Huang: 2× chips next year | **True, basket undefined.** Press gaggle, Dumfries House, 2026-09-17. He said "chips". No primary source narrows it to data-center GPUs |
| C2 | NVIDIA outlined FY2028 revenue ≈ $673B | **Misattributed.** Not NVIDIA's number. CNBC's $396B analyst consensus × 1.70. "673" appears **zero times** in the 8-K, the 10-Q and the corrected transcript |
| C3 | 30-point gap ⟹ ASP compression | **Wrong four ways.** Arithmetic (−15%, not −30%); different speakers/dates/periods; undefined basket; and NVIDIA attributed the gap to **supply** on the same call |
| C4 | Fab can double in several quarters | **No longer true.** CoWoS YoY decays +169→+121→+68→+54→+30%. TSMC's CEO: *"two to three years to build a new fab. No shortcuts."* |
| C5 | Transformers 36–48 months | *pending grid research* |
| C6 | Queues average 4–7 years | *pending grid research* |
| C7 | Grid cannot double energized MW in 12 months | *pending grid research* |
| C8 | Two paths, both penalised | **Refined: it is three regimes**, with a computable boundary. TLC-verified |
| C9 | Accelerators halve in competitiveness in 3–4 yr | **Falsified.** A 2020-vintage A100 is *appreciating*: NVIDIA disclosed A100 rental +~15% y/y |
| C10 | Hyperscalers extended 3–4 yr → 5–6 yr, deferring billions | **Confirmed, exactly.** $43.8bn of FY2025 operating income across five companies, 11% of reported |
| C11 | Early decommission forces accelerated depreciation or impairment | **Confirmed — and it happened in 2024.** Amazon's $920M charge. But the conclusion inverts (below) |
| C12 | Marginal cost ≈ electricity; spot must fall | **Falsified twice.** Electricity is 20% of cash cost, not "largely" it. Spot is **up 32.5%** off its trough |
| C13 | Return distribution splits | **Real and computable**, but the market is not currently in the loss band |

---

## 1. The dichotomy is a trichotomy

The article asserts that excess hardware must either sit stranded or displace
working gear. I modelled the pipeline in TLA+ and let TLC explore **every**
operator strategy — every schedule of shipping, warehousing, racking and
cannibalizing. The outcome space has three regions, not two, divided by a
computable boundary in three quantities: S (shipped), E (energized capacity),
B (installed base already occupying the envelope).

| regime | condition | outcome |
|---|---|---|
| **A** | S ≤ E − B | absorption is free |
| **B** | E − B < S ≤ E | absorption reachable, **write-down forced** |
| **C** | S > E | absorption **unreachable by any strategy** |

Regime C is the case the article misses, and it is the one its own premise
implies: there, cannibalizing does not cure stranding, it adds a write-down
to it.

`spec/check.sh` runs 9 TLC configurations, each declaring its expected outcome
before it runs. Three are canaries that **must fail** — a model checker that
cannot report a violation proves nothing. Three are reachability probes that
separate a real result from a vacuous one: without them, "no strategy absorbs
the programme cleanly" would hold trivially in regime C simply because nothing
can be absorbed at all. An independent Python classifier reproduces all three
regimes from separate code.

```
passed=9 failed=0
GATE PASSED
```

**Two corollaries the article does not state.** Near-term energized supply is a
*read-only* variable: within the transformer-and-interconnection lead time it
was fixed by commitments made before the horizon opened, so it can be looked up
rather than forecast. And extending useful life did not reduce cost — it
deferred it, creating a liability that the cannibalization path immediately
calls. Both follow from conservation, not from any parameter.

---

## 2. The arithmetic error, and the three larger errors behind it

Growth composes multiplicatively:

```
(1 + g_rev) = (1 + g_units) × (1 + g_ASP)
g_ASP = 1.70 / 2.00 − 1 = −3/20 = −15.0%   exactly
```

The article's "thirty percentage points" subtracts two multiplicative rates.
The shortcut overstates the ASP decline by **exactly 2×** here, and property
testing pinned the general error: `exact − additive = −u(r−u)/(1+u)`. It is
therefore largest precisely in the high-unit-growth case the article is about.
(Hypothesis rejected my first statement of that property and forced the exact
characterisation — the shortcut is also correct when `r = u`, not only at
`u = 0`.)

But the arithmetic is the smallest of four problems:

1. **Different speakers, dates, periods.** Huang's unit remark: to reporters in
   Scotland, 2026-09-17, about "next year". Kress's 70%: an earnings call,
   2026-08-26, about fiscal 2028 ending January 2028.
2. **The basket was never defined.** CNBC's own reporter flagged it. NVIDIA
   guides Vera CPU revenue to more than double, ships Groq LPX racks holding
   256 LPUs each, and sells five networking chip families per rack-scale
   system. TrendForce independently models **+26%** high-end GPU unit growth.
3. **NVIDIA already explained the gap, and it is not price.** Same call:
   *"Customers' forecasts point to our growth doubling next year. However… we
   expect to grow approximately 70% as we are supply-constrained."*
4. **The direction is wrong.** Revenue per GW went $18B → $25B → $40B; gross
   margin is guided **up** to 72–73% on "executed price increases"; >15% price
   increases were notified to the top five customers.

---

## 3. The strongest claim is right, and its conclusion is backwards

C10 is exact. Every extension is in a 10-K with a dollar figure, and the
five-company FY2025 effect reconstructs to **$43.8bn of operating income, 11%
of the $438.5bn reported**.

C11 is also right, and it is *retrospective*. Amazon's FY2024 10-K:

> "…changing the useful lives of a subset of our servers and networking
> equipment, effective January 1, 2025, **from six years to five years**… In
> 2024, we also determined, primarily in the fourth quarter, **to retire
> early** certain of our servers and networking equipment. We recorded
> approximately **$920 million of accelerated depreciation** and related
> charges… due to **an increased pace of technology development, particularly
> in the area of artificial intelligence and machine learning**."

That is the article's mechanism, in the filing, in the company's words.

**Then the conclusion inverts, for a reason that is pure arithmetic.**
Straight-line depreciation is linear; resale decay is exponential. The curves
cross.

| age (yr) | 6-yr straight-line book | H100 resale @ −17%/yr | outcome |
|---|---|---|---|
| 1 | 0.833 | 0.830 | charge of 0.3 pts |
| 2 | 0.667 | **0.689** | **gain of 2.2 pts** |
| 4 | 0.333 | 0.475 | gain of 14.1 pts |
| 6 | 0.000 | 0.327 | gain of 32.7 pts |

The break-even was computed exactly **before** the resale data was in hand: an
asset pulled at 24 months against a 72-month book must fetch exactly **2/3** of
original cost to avoid a charge. The observed H100 curve puts a two-year-old
part at ~0.69. It clears. And every observed point — H100 at 3.9 years, A100 at
5.8, V100 at 8.5 — sits **above** six-year straight-line book.

Two further facts from the same filings: the $920M charge is **0.53%** of
Amazon's gross fleet, and Amazon netted it out on the same day by extending
heavy equipment 10→13 years (+$0.9bn against the −$0.7bn server hit, in a
different segment).

**And the cleanest evidence in the whole exercise that book life is judgment,
not measurement:** on 1 January 2025, on comparable hardware, citing the same
industry conditions, **Amazon shortened** server life 6→5 while **Meta
extended** it 5→5.5.

*Caveats that travel with the resale result:* n=10 for H100 and n=14 for A100
over 90 days — only V100 (n=122) is a real sample. CCIR's basis is
system-allocated, not chip MSRP; re-basing roughly doubles the residuals, which
strengthens rather than weakens this. And H100 SXM5 prints 48.4% against H100
PCIe's 79.4% at identical age on identical silicon.

---

## 4. The cannibalization trade, priced

The article treats the write-down as a deterrent but never weighs it against
what it buys. With a revenue-per-megawatt figure the comparison is decidable.

Deriving the **retired** asset's own revenue (685 H100 per facility MW at the
observed $2.65/GPU-hr — not a current-generation yield, which overstates the
gain):

```
break-even performance-per-watt ratio ρ*      [1.189, 1.308]
observed, rack-level dense FP8, two gens       1.723   clears widely
observed, rack-level dense FP4, one gen        1.333   clears by ~2%
```

The one-generation swap clears by less than the error on its own inputs. So the
model's prediction is narrower and more falsifiable than the article's:
**operators should cycle every two generations, not every one**, and the
decision should be visibly sensitive to the rental price of the *outgoing*
part. Where the swap clears, the write-down is about **one year** of the
incremental revenue it buys — an earnings-optics event, not an economic
constraint.

Note also that rack-level gains are smaller than die-level gains: GB200→GB300
is 1.33× at the rack against 1.5× at the die, because rack power rose with it.
And dense FP8 per watt *regressed* from B200 (4.50 TF/W) to B300 (3.57 TF/W) —
Blackwell Ultra's entire efficiency story is FP4-only. There is no single
precision across which an A100→GB300 trend can honestly be drawn.

---

## 5. Both sides of the article's asymmetry have changed

The article's premise is that silicon is fast and the grid is slow. Silicon is
no longer fast.

| | YoY CoWoS growth |
|---|---|
| 2023→24 | +169% |
| 2024→25 | +121% |
| 2025→26 | +68% |
| 2026→27 | +54% |
| 2027→28 | +30% |

TSMC's CEO, on three consecutive calls: *"two to three years to build a new
fab. No shortcuts. And it takes another one to two years to ramp it up."* Of
2026 capex: *"the contribution to this year is almost none, and 2027, a little
bit… we are looking for 2028-2029 supply."* No disclosed greenfield project at
TSMC, SK hynix or Micron reaches production in under 22 months. The one
~15-month datapoint is a brownfield conversion of an already-built,
already-powered LCD fab.

Greenfield fab build + ramp is **[3.0, 5.0] years** against the article's own
[3.0, 4.0]-year transformer figure. The two lead times now overlap.

---

## 6. Prices went the other way, and the article's own mechanism predicts it

| | |
|---|---|
| H100 neocloud index, trough 2025-12-09 | $2.00 |
| H100 neocloud index, 2026-09-18 | **$2.65** (+32.5%) |
| A100 neocloud index, 2026-09-18 | $1.58 — *a 2020 part* |

Corroborated by the issuer. NVIDIA, Q1 FY2027 call: *"The price of renting an
H100 has risen 20% year to date, while A100 cloud pricing is up nearly 15%."*
CoreWeave's deck: *"average A100 pricing increased in 2025."* The forward curve
is **backwardated** — 12-month reserve $2.30 against $2.63 spot — which is the
opposite sign from both a scarcity story and a glut story.

**Take the article's power-scarcity mechanism seriously and it predicts this.**
If energized megawatts are the binding constraint, an accelerator already
occupying an energized slot is priced off the scarcity of the *slot*, not its
FLOPS. Which is why a six-year-old A100 appreciates while newer parts ship —
and which removes the premise of the cannibalization path.

### The marginal-cost claim, and an out-of-sample validation

At EIA's June 2026 industrial rate (9.17¢/kWh) and 1,460 W facility draw per
H100, energy costs **$0.134/GPU-hr** against an all-in cash cost of **$0.662**
derived from CoreWeave's disclosed 75% contracted EBITDA margin. Electricity is
**20% of cash marginal cost**, not "largely" it — wrong by a factor of five,
and wrong in the direction that predicts a $0.13 collapse.

Full-cost recovery computed bottom-up from filings, datasheets, EIA and LBNL,
with **no price observation anywhere in the inputs**:

| book life | full-cost recovery |
|---|---|
| 4-year (Nebius) | $1.820/GPU-hr |
| 5-year (Lambda) | $1.588 |
| 6-year (CoreWeave) | $1.434 |

The independently observed market floor is **$1.70–2.15** across two indices.
**The intervals overlap.** That identifies the floor: not electricity, not a
physical limit — the **depreciation schedule**. And it makes the useful-life
argument load-bearing for solvency, not just earnings: the same market price is
above water on a 6-year book and under it on a 4-year book.

Today's $2.65 sits above full-cost recovery on every book length, needing only
**34.9%** utilization to break even on a six-year schedule.

---

## 7. The demand side reconciles; the debate is about the wrong variable

Two methods sharing no inputs:

| route | US AI capacity additions |
|---|---|
| LBNL energy model (649 TWh × AI share ÷ 8760 ÷ measured capacity factor) | [6.5, 11.6] GW/yr |
| NVIDIA revenue ÷ its own disclosed $/GW × US share | [6.8, 12.5] GW/yr |
| **overlap** | **[6.8, 11.6] GW/yr** |

Set that against what the debate quotes: ERCOT's **230 GW** large-load queue
against an 85 GW state peak; Dominion's **47 GW** of signed contracts against
its own **16.6 GW** load forecast *in the same filing* (ratio 0.35); ~94% of
announced GB200/GB300 GPUs not deployed. **The queue is an option book, not an
order book.**

### Where the uncertainty actually lives

Sobol decomposition of required new US grid capacity:

| factor | total-effect index | provenance |
|---|---|---|
| share powered outside the queue | 0.339 | **unsourced** |
| share landing in an energized envelope | 0.339 | **unsourced** |
| NVIDIA revenue per GW | 0.324 | filed |
| US share | 0.016 | estimated |
| NVIDIA revenue | **0.002** | filed |

**66.4% of the variance sits in two factors with no published measurement,
neither of which the article mentions.** NVIDIA's revenue — the thing the
article opens with — contributes 0.2%. Measuring the interconnection queue more
precisely cannot resolve this question, because the queue is not where the
variance lives.

### One assumption worth a third of the answer

LBNL's widely-cited 148 GW of required 2030 US interconnection capacity is
`649 TWh ÷ 8760 ÷ 0.50`, where 0.50 is described in their own report as *"not
well documented but is estimated to be around 50%."* EPRI **measured** 75% at
hyperscale facilities. Substituting it gives **98.8 GW** — a **49.4 GW** swing,
exactly one third, with no change to the energy estimate. The entire published
cross-forecaster spread is 105.7 GW, so this single unmeasured number accounts
for **~47% of the apparent disagreement between institutions**.

---

## 8. What is still not known

Stated plainly, because the sensitivity analysis shows these dominate:

- **What fraction of new hardware lands in an already-energized envelope.** No
  published measurement. 33.9% of the variance.
- **What fraction is powered outside the interconnection queue** — behind-the-
  meter generation, curtailment-enabled flexible load, reuse of contracted
  capacity. No published measurement. 33.9% of the variance.
- **Fleet-weighted GPU utilization.** Measured values span 5% (enterprise
  Kubernetes) to 85% (optimized hyperscale training). No one has published a
  weighted average. LBNL moved inference utilization 40%→20% between editions
  and says *"there continues to be a lack of verifiable data."*
- **What Amazon actually retired** in Q4 2024 — no generation, count, location
  or gross cost. And whether the "$0.6bn in 2025" continuation materialised:
  the FY2025 10-K silently drops the disclosure.
- **Burry's $176bn derivation.** The figures are verified as his exact words;
  the method is paywalled and in ten months nobody has publicly reproduced it.
  Two reconstructions bracket it at $176bn and $212bn — internally coherent,
  but implying a ~4–4.5-year counterfactual life, not the "2–3 yr product
  cycle" the claim invokes.
- **No peer-reviewed work on GPU economic life or accelerator residual value
  exists.** No vendor MTBF, no HBM degradation curve, no measured
  utilization-collapse data for any generation.

---

## Method

- **Formal:** `spec/Energization.tla`, 9 TLC configurations with declared
  expected outcomes, hermetic metadir per run, 3 canaries that must fail and 3
  reachability probes. `spec/check.sh`.
- **Exact:** every deciding number routes through `agent-calc` (exact rationals
  and closed intervals). `Interval.of(0.1)` raises `TypeError` — floats cannot
  enter the model silently. Interval predicates return three answers, and the
  third is *undecided*.
- **Provenance:** 65 parameters in `data/parameters.yaml`, each carrying a
  provenance class; hard evidence (MEASURED / FILED / OFFICIAL) is **34 of 65**.
  The loader refuses a hard parameter without an as-of date.
- **Statistical:** Monte Carlo (n=400,000, seed 20260918) and Saltelli/Sobol
  first-order and total-effect indices.
- **Tests:** 15, including cross-checks that the Python regime classifier
  reproduces all three TLC regimes from independent code.
