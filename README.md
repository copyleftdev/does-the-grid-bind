# Does the grid bind?

**[Read the report →](https://copyleftdev.github.io/does-the-grid-bind/)**

[![Tip in tokens](https://img.shields.io/badge/tip%20in-tokens-E8853A?style=flat-square)](https://tokentip.to/@copyleftdev)

An invariant model and primary-source audit of the claim that AI accelerator
shipments are outrunning the electrical grid.

Subject: *“What Happens When Chip Volume Doubles but the Grid Does Not”*
(Dean Lee, dev.to, 2026-09-18). Audited the same day.

---

## The result

**The conclusion is probably right — about 80% likely — and most of its stated
reasons are wrong.** That combination is the finding.

```
P(stranding-forced regime)            80.2%
median annual shortfall               +1.66 GW/yr
median stranded share of shipments     20.7%
```

The exact interval classification of the same inputs returns **undecided** — it
is consistent with all three regimes — so the probability is the honest form of
the answer and the interval is the honest form of the uncertainty.

| | |
|---|---|
| Claims tested | 13 |
| Stands | 5 · Partly 3 · **Falsified 5** |
| Parameters | 86, of which **45** are hard evidence |
| TLC runs | 9/9 matched their declared expected outcome |
| Tests | 15 |

## What the audit found

- **The dichotomy is a trichotomy.** TLC over *every* operator strategy shows the
  outcome space has three regions, not two, with a computable boundary in
  shipped / energized / installed-base. The missed case is where both penalties
  land at once.
- **“Thirty percentage points” is an arithmetic error.** Growth composes
  multiplicatively: `(1+0.70)/(1+1.00) − 1 = −15%`, exactly `−3/20`. Property
  testing pinned the general error at `−u(r−u)/(1+u)`, so the shortcut is worst
  precisely where unit growth is largest.
- **The $673bn revenue figure is not the company’s.** It is a news outlet’s
  arithmetic on an analyst consensus. “673” appears zero times in the 8-K, the
  10-Q and the corrected transcript.
- **Prices went the other way.** The H100 index is up 32.5% off its December 2025
  trough, and a 2020-vintage A100 is appreciating. Electricity is 20% of cash
  marginal cost, not “largely” it.
- **Straight-line book depreciates faster than the market.** Linear book against
  exponential resale: the curves cross at ~1.4 years, and beyond that early
  retirement books a *gain*. Every observed resale point sits above six-year
  straight-line book.
- **Two thirds of the remaining variance** sits in quantities with no published
  measurement — and neither appears anywhere in the original argument.

Full write-up: [`reports/FINDINGS.md`](reports/FINDINGS.md).

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q          # 15 tests
./spec/check.sh                        # 9 TLC runs, expects 9/9
for f in analysis/0*.py; do .venv/bin/python "$f"; done
.venv/bin/python analysis/export_figures.py   # regenerates the site's data
```

Requires [`agent-calc`](https://github.com/copyleftdev) on `PATH` and
`tla2tools.jar` (override the location with `TLA_JAR`).

## How it is built

Three layers, each answering something the others cannot.

**A formal model** — [`spec/Energization.tla`](spec/Energization.tla). Every
configuration declares its expected outcome *before* it runs. Three are canaries
that must fail: a model checker that cannot report a violation has proved
nothing. Three are reachability probes that separate a real result from a
vacuous one.

**Exact arithmetic** — [`src/chipgrid/exact.py`](src/chipgrid/exact.py). Every
number that decides something is an exact rational or a closed interval computed
by `agent-calc`. `Interval.of(0.1)` raises `TypeError`; floats cannot enter the
model silently. Interval predicates return three answers, and the third is
*undecided*.

**Provenance** — [`data/parameters.yaml`](data/parameters.yaml). Every parameter
carries a class: MEASURED, FILED, OFFICIAL, ESTIMATED, VENDOR, ADVOCACY, DERIVED
or ASSUMED. The loader refuses a hard parameter without an as-of date, and the
hard-evidence ratio is reported rather than hidden.

The report page reads [`site/data/figures.json`](site/data/figures.json), which
is exported straight from the model — so the published claims cannot drift from
the analysis, and `git diff` on that file is the diff of what the page asserts.

## Layout

```
spec/            TLA+ model, configs with declared expectations, check.sh
src/chipgrid/    exact arithmetic, invariants, regime classifier, Monte Carlo
data/            parameters.yaml — every number with its source
analysis/        the claim tests, one script per theme
reports/         generated output, and FINDINGS.md
site/            the report page (deployed to Pages)
```

## The invariants

| | statement | why it must hold |
|---|---|---|
| I1 | produced = warehoused + deployed + retired | nothing shipped vanishes |
| I2 | deployed ≤ energized | the thesis, as physics |
| I3 | energized(t) ≤ e₀ + commitments made by t−L | near-term supply is read-only |
| I4 | gross = accumulated + book + impaired | depreciation moves cost, never removes it |
| I6 | queue wait = L/λ | Little’s Law — a theorem, not an assumption |
| I7 | (1+g_rev) = (1+g_units)(1+g_ASP) | growth composes multiplicatively |
| I8 | tokens bounded by energized watts | closes demand against supply in one unit |
| I9 | ρ\* = 1 + unamortised/(revenue × years) | cannibalization as a decidable predicate |
| I10 | vendor revenue = buyers’ capex | shipments are bounded by budgets too |

I10 is the one the grid framing skips: establishing that a grid constraint
exists is not the same as establishing that it is the *binding* constraint.

## Honest limits

The single number carrying the verdict — scaling two published utility meter
readings to a national energization figure — has **no source**. It is an
assumption, and if it is wrong the conclusion moves. Other gaps are listed in
the report under *What nobody knows*, because an audit that hides its gaps is an
advertisement.

## Licence

MIT for the code. The analysis cites public primary sources throughout; figures
belong to their publishers and are attributed inline.
