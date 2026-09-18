-------------------------------- MODULE Energization --------------------------------
(***************************************************************************)
(* The energization gap as a state machine.                                *)
(*                                                                         *)
(* The article asserts a dichotomy: when shipments outrun energized power,  *)
(* the excess hardware must either sit stranded or displace working gear at *)
(* an accounting cost, and "both carry specific financial penalties".       *)
(*                                                                         *)
(* An assertion of that shape is exactly what a model checker settles. TLC  *)
(* explores EVERY operator strategy -- every schedule of deploying,         *)
(* warehousing and cannibalizing -- so if no behaviour reaches the horizon  *)
(* with both stocks clean, the dichotomy is forced by the structure rather  *)
(* than by a badly chosen policy. That is a strictly stronger claim than    *)
(* the article makes, and it is the claim worth checking.                   *)
(*                                                                         *)
(* Units: one "unit" is a fixed block of IT megawatts. Dollars are integers *)
(* with UnitCost = Life, so a write-off at age a is exactly (Life - a).     *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS
    MaxTime,        \* horizon, in periods
    ShipRate,       \* new units arriving from the vendor each period
    EnergizeRate,   \* new energized units arriving each period (see I3 note)
    InitEnergized,  \* energized units at t = 0
    InitOld,        \* previous-generation units already racked at t = 0
    Life,           \* accounting useful life, in periods
    Cap             \* state-space bound on any single stock

VARIABLES
    t,              \* clock
    warehoused,     \* shipped, not energized, earning nothing
    newDeployed,    \* current-generation units racked and drawing power
    oldDeployed,    \* previous-generation units racked and drawing power
    oldAge,         \* periods of depreciation already taken on the old cohort
    retired,        \* units pulled from service
    energized,      \* energized capacity available to IT load
    shipped,        \* cumulative units shipped by the vendor
    impaired        \* cumulative dollars written off ahead of schedule

vars == << t, warehoused, newDeployed, oldDeployed, oldAge,
           retired, energized, shipped, impaired >>

(***************************************************************************)
(* I3 is represented by EnergizeRate being a CONSTANT rather than an        *)
(* action. That is the modelling claim, and it is the honest one: within    *)
(* the transformer-and-interconnection lead time, the arrival schedule of   *)
(* energized megawatts was fixed by commitments made before t = 0. No       *)
(* action in this spec can raise it, because no decision taken inside the   *)
(* horizon can raise it in the world either.                                *)
(***************************************************************************)

Deployed == newDeployed + oldDeployed
Headroom == energized - Deployed

TypeOK ==
    /\ t \in 0..MaxTime
    /\ warehoused \in 0..Cap
    /\ newDeployed \in 0..Cap
    /\ oldDeployed \in 0..Cap
    /\ oldAge \in 0..(Life + MaxTime)
    /\ retired \in 0..Cap
    /\ energized \in 0..Cap
    /\ shipped \in 0..Cap
    /\ impaired \in 0..(Cap * Life)

Init ==
    /\ t = 0
    /\ warehoused = 0
    /\ newDeployed = 0
    /\ oldDeployed = InitOld
    /\ oldAge = 0
    /\ retired = 0
    /\ energized = InitEnergized
    /\ shipped = 0
    /\ impaired = 0

(***************************************************************************)
(* Actions                                                                 *)
(***************************************************************************)

\* The vendor ships. The operator does not control this; it has been ordered.
Ship ==
    /\ t < MaxTime
    /\ shipped + ShipRate <= Cap
    /\ warehoused' = warehoused + ShipRate
    /\ shipped' = shipped + ShipRate
    /\ UNCHANGED << t, newDeployed, oldDeployed, oldAge, retired, energized, impaired >>

\* Path zero: rack new hardware into genuine headroom. Costless, and the only
\* action here that is. It is available exactly as far as Headroom allows.
Deploy ==
    /\ warehoused > 0
    /\ Headroom > 0
    /\ warehoused' = warehoused - 1
    /\ newDeployed' = newDeployed + 1
    /\ UNCHANGED << t, oldDeployed, oldAge, retired, energized, shipped, impaired >>

\* Path two: pull a working previous-generation unit to free its power envelope
\* and rack a new one in its place. The envelope is conserved; the book value
\* is not. Retiring at age a < Life recognises (Life - a) of unamortised cost.
Cannibalize ==
    /\ warehoused > 0
    /\ oldDeployed > 0
    /\ retired + 1 <= Cap
    /\ oldDeployed' = oldDeployed - 1
    /\ newDeployed' = newDeployed + 1
    /\ warehoused' = warehoused - 1
    /\ retired' = retired + 1
    /\ impaired' = impaired + (IF oldAge < Life THEN Life - oldAge ELSE 0)
    /\ UNCHANGED << t, oldAge, energized, shipped >>

\* Retire an old unit without backfilling it. Same write-down, no compute gain.
\* Present so that TLC cannot be accused of having been denied an escape route.
RetireOnly ==
    /\ oldDeployed > 0
    /\ retired + 1 <= Cap
    /\ oldDeployed' = oldDeployed - 1
    /\ retired' = retired + 1
    /\ impaired' = impaired + (IF oldAge < Life THEN Life - oldAge ELSE 0)
    /\ UNCHANGED << t, warehoused, newDeployed, oldAge, energized, shipped >>

\* Time passes: the old cohort ages and the grid delivers what was committed.
Tick ==
    /\ t < MaxTime
    /\ energized + EnergizeRate <= Cap
    /\ t' = t + 1
    /\ oldAge' = oldAge + 1
    /\ energized' = energized + EnergizeRate
    /\ UNCHANGED << warehoused, newDeployed, oldDeployed, retired, shipped, impaired >>

Next == Ship \/ Deploy \/ Cannibalize \/ RetireOnly \/ Tick

Spec == Init /\ [][Next]_vars

(***************************************************************************)
(* Invariants                                                              *)
(***************************************************************************)

\* I1. Nothing shipped vanishes, and every retirement came out of the old
\* cohort. Units racked at t=0 were never shipped inside the horizon, so the
\* two generations are conserved separately.
I1_Conservation ==
    /\ shipped = warehoused + newDeployed
    /\ retired = InitOld - oldDeployed

\* I2. You cannot draw power you have not been given.
I2_Envelope == Deployed <= energized

\* I4. Every dollar written off corresponds to a unit actually pulled early.
I4_BookConservation == impaired <= retired * Life

(***************************************************************************)
(* The result under test.                                                  *)
(*                                                                         *)
(* Absorbed: every unit the vendor shipped is racked and earning.          *)
(* Clean:    no unamortised book value was written off to get there.       *)
(*                                                                         *)
(* NoFreeAbsorption asserts the two cannot both hold at the horizon after a *)
(* full shipment programme. TLC violating it produces a WITNESS -- an       *)
(* explicit schedule that absorbs everything at no accounting cost. TLC     *)
(* exhausting the state space without violating it proves no such schedule  *)
(* exists, for any operator strategy whatsoever.                            *)
(***************************************************************************)

Absorbed == warehoused = 0
Clean == impaired = 0
ProgrammeComplete == /\ t = MaxTime
                     /\ shipped = MaxTime * ShipRate

NoFreeAbsorption == ~(ProgrammeComplete /\ Absorbed /\ Clean)

(***************************************************************************)
(* Reachability probes. NoFreeAbsorption holding is only interesting if the *)
(* operator could have cleared the warehouse at all. These separate the two *)
(* reasons it can hold, and they turn the article's dichotomy into a        *)
(* trichotomy with a computable boundary.                                   *)
(*                                                                          *)
(*   Let S = units shipped over the horizon, E = final energized capacity,  *)
(*       B = installed base already occupying the envelope at t = 0.        *)
(*                                                                          *)
(*   S <= E - B   regime A  absorption is free                              *)
(*   E - B < S <= E  regime B  absorption is reachable, but only by pulling *)
(*                             working gear: the write-down is forced       *)
(*   S > E        regime C  absorption is unreachable by any strategy:      *)
(*                             stranding is forced, and cannibalizing buys  *)
(*                             a write-down without curing it               *)
(*                                                                          *)
(* The article presents A-or-B as the whole choice. C is the case where     *)
(* both penalties land at once, and it is the case the data has to be       *)
(* checked against.                                                         *)
(***************************************************************************)

Probe_NeverAbsorbed == ~(ProgrammeComplete /\ Absorbed)
Probe_NeverClean == ~(ProgrammeComplete /\ Clean)

(***************************************************************************)
(* Canaries. An invariant that cannot fail proves nothing, and a harness    *)
(* that cannot report a failure proves less. Each of these MUST be violated *)
(* when checked; a run in which one passes means the harness is not looking.*)
(***************************************************************************)

Canary_ReachesHorizon == t < MaxTime          \* must fail: the clock advances
Canary_NeverShips == shipped = 0              \* must fail: Ship is enabled
Canary_NeverStrands == warehoused = 0         \* must fail under a binding grid

=============================================================================
