#!/usr/bin/env python
"""How much new hardware can land in an already-energized envelope?

One of the two factors carrying 66% of the model's variance. It has no direct
published measurement, but it can be BOUNDED from two directions, and the
bound turns out to be much tighter than the plausible range I started with.
"""
import sys; sys.path.insert(0, "src")
from chipgrid.exact import Interval as I
from chipgrid.load import load

r = load("data/parameters.yaml")
H = lambda s: print(f"\n{'='*78}\n{s}\n{'='*78}")

H("Bounding share_refresh")
print("""
  There are only two ways a new accelerator can occupy power that already
  exists: displace a conventional server, or displace an older accelerator.
  They behave completely differently and must be bounded separately.
""")

H("Route 1 — conventional server displaced by an AI server: nearly worthless")
ent = r["rack_kw_enterprise_mean"]
ai_rack = r["gb300_nvl72_rack_kw"]
ratio = ai_rack / ent
print(f"  enterprise mean rack draw (Uptime, measured)   {ent.fmt(1):>16} kW")
print(f"  GB300 NVL72 rack draw (OEM)                    {ai_rack.fmt(0):>16} kW")
print(f"  density ratio                                  {ratio.fmt(1):>16} x")
recovered = ent / ai_rack
print(f"  => power recovered per rack slot converted      {recovered.fmt(3):>16}")
print(f"""
  Converting an enterprise rack to an AI rack recovers only {(recovered*I.of(100)).fmt(1)}% of what
  the AI rack needs. The other {((I.of(1)-recovered)*I.of(100)).fmt(1)}% has to come from somewhere new.

  And the headline turnover number is misleading here. US server retirements
  ran at {r['us_server_retirement_share_2024'].fmt(2)} of shipments in 2024 -- 10-13% annual fleet turnover --
  which sounds like a large reuse pool. It is not, because in LBNL's own model
  CONVENTIONAL SERVER ENERGY IS ESSENTIALLY FLAT from 2024 to 2030: efficiency
  gains absorb workload growth, and the retiring slots are refilled with
  conventional servers rather than released. Flat energy means no net
  megawatts freed, whatever the unit turnover.
""")

H("Route 2 — older accelerator displaced by a newer one: MW-neutral, but small")
ai_ret = r["ai_server_retirement_share_2024"]
print(f"  AI-server retirements as a share of AI shipments, 2024  {ai_ret.fmt(2):>10}")
print(f"""
  This route IS megawatt-neutral: retire 132 kW of Hopper, install 132 kW of
  Blackwell, the envelope is unchanged. But it is bounded by how much AI
  hardware is old enough to retire, and a fleet compounding at ~42%/yr has
  very little of that. LBNL's inputs put AI retirements at {(ai_ret*I.of(100)).fmt(0)}% of AI
  shipments in 2024; they do not become material until roughly 2029.

  Note this also contradicts the article's cannibalization premise in a
  second way. The article pictures operators pulling two-year-old Hopper to
  make room. The observed retirement rate says almost nobody is doing it --
  consistent with Oracle renewing four-year-old GPUs at a 20% premium and AWS
  stating it has never retired an A100.
""")

H("Route 3 — the constraint the model did not carry")
print("""
  Both routes above account only for AGGREGATE megawatts at the site. Dean Lee
  raised a third limit in reply to this audit, and it is a real one:

    "you can clear out fourteen legacy server bays and still lack the power
     infrastructure to light up a single AI rack. Legacy data center retrofits
     run into feeder and substation limits almost immediately."

  A hall's feeders, busway and local substation are sized for the density the
  hall was built at. Freeing 140 kW of contracted capacity across fourteen
  cabinets does not put 140 kW at one cabinet, and the distribution equipment
  between them is its own multi-month procurement. So even the megawatt-neutral
  route 2 swap is not automatically executable in place.

  There is no published figure for how much retrofit in-building distribution
  actually permits. That was searched alongside the decommissioned-MW question
  and returned the same confirmed negative, which makes it a THIRD unsourced
  quantity sitting on top of the two the sensitivity analysis already found.

  Its effect on the model is directional and one-sided: it cannot raise the
  reuse ceiling, only keep it from being reached. The bound below is therefore
  a ceiling, not an estimate.
""")

H("Bound")
hi_iv = ai_ret + (I.of(1) - ai_ret) * recovered
hi = hi_iv.hi
print(f"  Route 1 contribution   ~0 (conventional energy is flat)")
print(f"  Route 2 contribution   <= {ai_ret.fmt(2)}")
print(f"  => share_refresh bounded at                    [0.00, {float(hi):.2f}]")
print(f"""
  I began this model allowing share_refresh anywhere in [0.10, 0.45]. The
  physical and fleet-composition evidence caps it at {float(hi):.2f}, and route 3 means
  even that is a ceiling rather than a level.
  That is a real tightening of one of the two dominant factors, and it moves
  the answer TOWARD the article's conclusion: less of the new hardware can
  hide in existing power than a casual reading of "10-13% fleet turnover"
  would suggest.

  This is the strongest single piece of support the article's thesis gets
  from this exercise, and it comes from a number the article never cites.
""")
