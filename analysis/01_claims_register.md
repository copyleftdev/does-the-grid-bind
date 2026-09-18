# Claims register

Every falsifiable assertion in *"What Happens When Chip Volume Doubles but the
Grid Does Not"* (Dean Lee, dev.to, published 2026-09-18), with the test that
decides it.

A claim is only listed if it could in principle be wrong. Rhetorical framing is
not listed. The `TEST` column names the specific check, not a vibe.

| # | Claim (as stated) | Type | Test |
|---|---|---|---|
| C1 | Huang said NVIDIA expects to sell **twice as many chips** next year as this year, across DC GPUs (Blackwell, Rubin), CPUs, NVLink switches, optical networking, robotics modules | attribution | Locate the primary quote; confirm the product basket |
| C2 | NVIDIA outlined **FY2028 revenue ≈ $673B, ~+70% over the prior year** | attribution | Locate the primary source; check whether $673B is revenue guidance, a bookings/visibility figure, or an analyst estimate; check the base |
| C3 | The spread between +100% units and +70% revenue is **thirty percentage points**, implying ASP compression | arithmetic | `I7`: growth composes multiplicatively. Exact: (1+g_rev)/(1+g_units)−1 |
| C4 | Fab and advanced packaging (CoWoS) **can double within several quarters** | empirical | CoWoS wafers/month 2023→2027; observed YoY doubling episodes |
| C5 | HV substation transformers carry **36–48 month** lead times | empirical | Wood Mackenzie / DOE / NERC / utility filings; compare to stated range |
| C6 | PJM, ERCOT, MISO interconnection queues **average four to seven years** | empirical | LBNL *Queued Up*; independently cross-check with `I6` Little's Law on published queue volume ÷ throughput |
| C7 | The grid **cannot double energized MW** to data-center substations in twelve months | physical | `I3`: near-term energization is fixed by prior commitments. Compare achievable ΔE to required ΔE |
| C8 | Excess hardware must take one of **two paths**, both penalised | structural | `Energization.tla`: TLC over all strategies. **Refuted as stated** — it is three regimes, and in regime C both penalties land together |
| C9 | Accelerators **halve in economic competitiveness within 3–4 years** | empirical | Perf/W across A100→H100→B200→GB300; rental price decay of prior generations; are V100/A100 still earning? |
| C10 | Cloud providers extended server depreciation from **3–4 to 5–6 years** over three fiscal years, deferring billions | filed fact | 10-K/10-Q language per company; disclosed dollar impact |
| C11 | Pulling 2-year-old H100s early forces **accelerated depreciation or impairment** | accounting | `I4`: book conservation. Look for an actual disclosed instance — this is the claim most likely to have already happened |
| C12 | Once racked, marginal cost of a token is **largely wholesale electricity**; capacity growth against linear demand growth forces **spot GPU-hour prices down** | economic | Compute marginal cost/GPU-hr from TDP × PUE × $/kWh; compare to observed spot $/GPU-hr trend 2023→2026 |
| C13 | The return distribution **splits**: holders of prior interconnection rights capture rents; hardware buyers without energization absorb carrying cost | distributional | Model the two positions; is the split bimodal or just wide? |

## Claims the article does not make, which the model forces

| # | Claim | Source |
|---|---|---|
| D1 | The two paths are not alternatives at a given moment. Which one is available is decided by a threshold in (S, E, B) | `Energization.tla`, regime trichotomy |
| D2 | In regime C, cannibalization does **not** cure stranding — it adds a write-down to it | `ConstrainedAbsorb.cfg` holds |
| D3 | Extending useful life did not reduce the cost, it created a deferred liability that the cannibalization path calls | `I4` book conservation |
| D4 | Near-term energized supply is a read-only variable; over the lead time it cannot be forecast, only looked up | `I3` lead-time causality |

## Timeframe defect (noted at registration)

C1 is a **next-year unit** claim. C2 is an **FY2028 revenue** claim. C3 divides one
by the other. Unless the two periods coincide, the implied-ASP computation in C3
is not well posed regardless of the arithmetic method, and the product baskets
differ as well (C1's basket includes robotics modules and networking silicon;
revenue is company-wide). This is registered as a defect in the claim, separate
from the arithmetic error tested under C3.
