# 15.2 — Post-processing

**Reframed 2026-09-08.** This was the control-plane arm. It is now post-processing over 15.1's
snapshot, and it contains no BGP. The reason is measured, not preferential: of 3,352 collector
sessions worldwide exactly one is Pakistani (PTCL, carrying only its own cone), and every Pakistani
vantage AS appears in **0 of 364** collector paths to a Pakistani target block. Public BGP has no
record of how one Pakistani network reaches another. See `../15.3_comparison/RETIRED.md`.

**Two jobs.** Neither needs a new measurement.

---

## Part 1 — Trace quality and target selection for 16.1

**16.1 is a longitudinal experiment and needs a stable panel of targets that reliably trace.**
15.1 is the precursor that finds them.

Score every trace: hops attempted, hops answered, private-hop fraction, destination reached. A
target is **clear from a vantage** when it reached, at least 80% of hops answered, and at most half
the answering hops were private. Thresholds live in one place and are reported with every result.

**The binding constraint is cross-vantage clarity, not per-block count.** Measured on 4.1:

| clarity bar | targets | blocks | ISPs |
|---|---|---|---|
| clear from ≥2 vantages | 300 | 115 | 17 |
| **clear from ≥3 vantages** | **154** | **69** | **14** |
| clear from ≥4 vantages | 45 | 20 | 11 |
| clear from ≥5 vantages | 10 | 6 | 4 |

Only **1 target** in the whole archive was clear from 6 of 7 vantages, and **none** from all 7.

**This kills the original "8 clear IPs per block" design.** Only 6 of 696 blocks reach 8 clear
targets, and their best target is visible from at most 4 vantages. A panel selected per block would
be 6 blocks wide.

**Select on cross-vantage clarity instead.** At ≥3 vantages the 4.1 archive alone would seed a
panel of 154 targets over 69 blocks and 14 ISPs, which is a workable longitudinal experiment. After
Phase B's responsiveness sweep the pool should be substantially larger, and the bar can be raised
rather than lowered.

**Output:** `panel_targets.csv` — target, block, ISP, which vantages see it clearly, quality scores.

## Part 2 — Detector bench

Several detectors over the same snapshot, compared on the same traces, all runnable free against
the 4.1 archive where behaviour is already characterised.

| detector | status | note |
|---|---|---|
| Exp 04 rules, global 40/60/70 | baseline | what 4.1 shipped |
| `DOMESTIC_OBSERVED` median rule | **built, validated** | `detector.py`, 6/6 on known cases |
| Rate-limit guard | **built, validated** | 71 of 1,191 RTT-evidence detours |
| Per-vantage baseline + 40 ms physical offset | tested, not built | keeps 99.4% of true, 5.8% of known-false |
| Physics floor vs claimed geolocation | tested, not built | 6/6, works on a single vantage |
| IPmap cross-check | tested | **23% coverage**, 3/3 precision where it answers |
| PCS-style path consistency (Klein 2026) | not built | HMM, needs country-pair priors we would estimate ourselves |

**Combined effect of the two built corrections on the 4.1 baseline: 11.0% to 8.6%**, with the
foreign-hop tier falling from 811 to 422.

**There is no ground truth and there will not be.** No ISP has confirmed anything. The only hard
constraint is physics: an address answering in 0.7 ms is not in Vancouver. Everything above that is
consistency argument, and detectors are compared on agreement and on which known artefacts they
reject, never on "accuracy".

## Reporting rules

- Report the **coverage fraction** of every tool, always. "IPmap agrees" is not a result;
  "IPmap answered for 14 of 60, disagreed on 3, all 3 genuine" is.
- Report each detector's components, never a bare score.
- Anything unverified is labelled hypothesis or assumption inline, with the check that would settle it.
