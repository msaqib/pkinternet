# 15.1 — data plane — findings

**Status:** detector written and validated against the 4.1 archive. No measurements run.
**Last updated:** 2026-09-07.

## Detector corrections, validated before any measurement

`detector.py` implements the Exp 04 rules plus two corrections found by re-analysing
`run_20260627_192918`. `validate_against_41.py` checks them against that frozen census, read-only,
no network, no credits. All checks pass:

| Check | Result |
|---|---|
| RTT arithmetic reproduces the frozen `max_rtt` | **18,260 of 18,260 rows** |
| `DOMESTIC_OBSERVED` admits the three known squatters | `182.45.51.22`, `70.70.71.137`, `149.40.227.134` |
| and rejects the known non-squatters | C-root, L-root, Equinix Singapore `27.111.230.170` |
| rate-limit guard fires only on same-address adjacent jumps | **71 of 1,191** RTT-evidence detours |
| no correction ever creates a verdict | confirmed |

**Effect on the 4.1 baseline:**

| | before | after |
|---|---|---|
| foreign hop seen | 811 (4.4%) | **422 (2.3%)** |
| RTT backstop | 1,191 (6.5%) | **1,140 (6.2%)** |
| local | 15,451 (84.6%) | **15,742 (86.2%)** |
| inconclusive | 807 (4.4%) | **956 (5.2%)** |
| **all detours** | **2,002 (11.0%)** | **1,562 (8.6%)** |

Per vantage: PTCL Karachi **38.4% to 15.1%**, Cybernet Haripur 46.3% to 42.9%, Orbit 6.6% to 5.4%.
Nayatel is unchanged at 4.0%.

**Coverage limit of the domestic rule.** It needs 3 or more readings of an address from one vantage.
That holds for **92 of the 141 addresses ever used as an exit hop (65%), covering 97% of exit-hop
observations**. The remaining 3% are addresses seen once or twice, where the rule cannot fire.
Whether the census design supplies enough repeats is the open question for Phase 1.

Fill this in **while the experiment runs**, not only at the end. A finding recorded late is a
finding half-remembered.

---

## Headline

_One paragraph, written last. What does this sub-experiment now let us say that we could not say
before?_

## Results

_Tables and numbers as they land. Every figure carries the file it came from._

| Finding | Value | Source file |
|---|---|---|
| | | |

## Surprises and things that broke

_Anything that did not match the manual's expectation. This section is usually where the real
result is — the June run's 8× coverage imbalance and the last-hop rate-limiting false positives
were both found here, not in the plan._

## Open questions

_Carried into the next sub-experiment or the next round._

## Verification

- [ ] Every number traced back to a file in `results/`
- [ ] `routes_*.txt` spot-checked against the computed verdicts
- [ ] Exit criteria in `MANUAL.md` met, or the gap stated explicitly
