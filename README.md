# chip_spunk_rd — the energization gap, tested

An invariant model and primary-source audit of the claim that AI accelerator
shipments are outrunning the electrical grid.

Target: *"What Happens When Chip Volume Doubles but the Grid Does Not"*
(Dean Lee, dev.to, 2026-09-18).

**Findings: [`reports/FINDINGS.md`](reports/FINDINGS.md)**

## What this is

Three layers, each answering a question the others cannot.

**A formal model** (`spec/Energization.tla`). The article asserts a dichotomy:
stranded hardware or cannibalized installed base. TLC explores *every* operator
strategy and shows the outcome space has three regions, not two, with a
computable boundary. `spec/check.sh` runs 9 configurations, each declaring its
expected outcome before it runs — including three canaries that must fail and
three reachability probes that separate a real result from a vacuous one.

**Exact arithmetic** (`src/chipgrid/exact.py`). Every number that decides
something routes through `agent-calc` as an exact rational or a closed
interval. Floats raise `TypeError` at the boundary rather than entering
silently. Interval predicates have three outcomes and the third is *undecided* —
the honest answer a point estimate cannot give.

**Sourced parameters** (`data/parameters.yaml`). 65 parameters, each carrying a
provenance class (MEASURED / FILED / OFFICIAL / ESTIMATED / VENDOR / ADVOCACY /
DERIVED / ASSUMED). The loader refuses a hard parameter without an as-of date.
Hard evidence is 34 of 65, and that ratio is itself reported rather than hidden.

## Reproduce

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q        # 15 tests
./spec/check.sh                      # 9 TLC runs, expects 9/9
for f in analysis/0*.py; do .venv/bin/python "$f"; done
```

Requires `agent-calc` on PATH and `tla2tools.jar` (override with `TLA_JAR`).

## Layout

```
spec/            TLA+ model, configs with declared expectations, check.sh
src/chipgrid/
  exact.py       agent-calc bridge: exact rationals, closed intervals
  invariants.py  the ten invariants, each tagged by WHY it must hold
  regime.py      the trichotomy classifier (agrees with TLC)
  chain.py       the seven factors between "2x chips" and "MW of new grid"
  accounting.py  depreciation, impairment, the deferral ledger
  economics.py   marginal cost, full-cost recovery, the loss band
  mc.py          Monte Carlo and Saltelli/Sobol
  params.py      provenance-enforcing registry
  load.py        strict YAML loader
data/            parameters.yaml — every number with its source
analysis/        the claim tests, one script per theme
reports/         generated output, and FINDINGS.md
```

## The invariants

An invariant here is a predicate that holds in every state for structural
reasons, so it constrains the outcome even when every input is disputed.

| | statement | why it must hold |
|---|---|---|
| I1 | produced = warehoused + deployed + retired | nothing shipped vanishes |
| I2 | deployed ≤ energized | the article's thesis, as physics |
| I3 | energized(t) ≤ e₀ + commitments made by t−L | near-term supply is read-only |
| I4 | gross = accumulated + book + impaired | depreciation moves cost, never removes it |
| I6 | queue wait = L/λ | Little's Law — a theorem, not an assumption |
| I7 | (1+g_rev) = (1+g_units)(1+g_ASP) | growth composes multiplicatively |
| I8 | tokens bounded by energized watts | closes demand against supply in one unit |
| I9 | ρ* = 1 + unamortised/(revenue × years) | cannibalization as a decidable predicate |
| I10 | vendor revenue = buyers' capex | shipments are bounded by budgets too |

I10 is the one the grid framing skips: establishing that a grid constraint
exists is not the same as establishing that it is the *binding* constraint.
