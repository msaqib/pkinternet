# 15.3 — retired 2026-09-08

This sub-experiment was to join 15.1's data-plane observations against 15.2's control-plane
predictions and characterise where they disagree. **It is retired because the control plane holds
no observation to compare against for the question this project asks.**

## The evidence

| | measured |
|---|---|
| Collector sessions worldwide | 1,434 RIS + 1,918 RouteViews = **3,352** |
| Pakistani peers among them | **1** — PTCL at rrc26, feeding only its own cone |
| Pakistani vantage ASes in collector paths to a PK target block | **0 of 364** |

Checked on `103.154.196.0/23` via `bgplay` initial_state at 2026-07-10 and 2026-08-20, searching
every AS_PATH for each vantage ASN. AS136174 (Nova), AS38193 (Transworld) and AS17557 (PTCL) appear
in none.

**BGP records how the world reaches a Pakistani network, not how Pakistan does.** All 363 live
collector paths to that prefix are foreign networks routing inward.

## Why a comparison would have been worse than nothing

15.2 would have modelled paths from CAIDA relationships under Gao-Rexford rather than reading them
from a collector. With no observed path for any PK vantage, its output is extrapolation from
relationship data that is itself thinnest for small Pakistani ASes. A detour rule of the usual form
("foreign if any AS on the path is registered abroad") never encounters a non-PK AS, because there
is no path to inspect, so it returns **domestic by default**. A control-plane study does not report
*unknown* here; it reports *fine*.

## What survives

BGP remains an **input** to 15.1 Phase A: `announced-prefixes` is how the block universe is
enumerated. That is enumeration, not inference, and it is not affected by the above.

The worked case is `04_efu_life_routing_change.md` (working notes, outside this repository): a 4 to 7 times latency change
on a Pakistani route, with no trace in public BGP before or after.
