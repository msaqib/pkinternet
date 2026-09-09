# 15.1 — Data plane — the measurement

**Asks:** for every announced block of every small Pakistani ISP, from several in-country vantage
points, what path does a packet actually take?

**Produces a data snapshot and nothing else.** No verdicts, no detour rate, no interpretation.
Every judgement happens in 10.2. This split exists because the 4.1 run baked its detector into the
collection, and when the detector turned out to be wrong the collection had to be reinterpreted
from raw JSON. Separating them means a detector change never requires a re-measurement.

**Status:** designed, unrun. **Last updated:** 2026-09-08.

---

## 1. What the 4.1 archive tells us before we start

Every number below is measured, from `analysis/trace_quality.py` over
`run_20260627_192918`. They are the reason this experiment is shaped the way it is.

| | |
|---|---|
| Targets that answered at all | **11.0%** (2,007 of 18,260) |
| Blocks with zero reachable targets | **527 of 696 (76%)** |
| Median hop response rate inside a trace | **50%** |
| Traces that are CLEAR | **4.6%** |
| Blocks with 8 clear targets | **6 of 696 (0.9%)** |
| ISPs with zero clear traces | **28 of 45** |

**CLEAR** means: the trace reached the destination ISP's AS, at least 80% of its hops replied, and
no more than half the replying hops were RFC1918.

**The vantage asymmetry is the most consequential finding.** Two of the seven probes contribute
almost nothing:

| probe (vantage) | traces | reached | clear | clear % |
|---|---|---|---|---|
| zcom.lhe | 4,609 | 12.5% | 319 | 6.9% |
| nova.lhe | 4,264 | 12.9% | 309 | 7.2% |
| orbit.fsd | 2,012 | 15.0% | 159 | 7.9% |
| cybernet.hrp | 562 | 15.8% | 29 | 5.2% |
| ptcl.khi | 1,525 | 12.9% | 24 | 1.6% |
| **nayatel.isb** | 3,204 | 4.6% | **4** | **0.1%** |
| **cybernet.khi** | 2,084 | 7.1% | **3** | **0.1%** |

Nayatel and Cybernet Karachi produced 7 usable traces between them out of 5,288 traces. Phase 1
must establish whether that is ICMP filtering, private-address transit, or probe placement, because
as it stands two of seven vantages contribute no path visibility at all.

## 2. Phases

### Phase A — Re-enumerate *(free)*
The 747-block universe is a **2026-06-27 RIPEstat snapshot and is now three months stale.** Re-pull
`announced-prefixes` for the 48 FLL licensees. Cross-check against RouteViews: a locally-scoped
prefix may never reach a RIS collector, and a discrepancy is itself a finding.

**BGP is an input here and nowhere else.** It supplies the block universe. It is not an analysis
arm; see `../15.3_comparison/RETIRED.md`.

### Phase B — Responsiveness sweep *(new, and the reason 4.1 failed)*
4.1 sampled 8 addresses per /24 with no liveness check. At an 11% response rate that yields **0.9
responders per block**, which is why 76% of blocks came back empty. To find 8 live hosts you must
probe roughly 73.

Sweep wide and cheap first, then traceroute only what answered. Output `live_<asn>.csv`.
The `--live` path already exists in `tromboning_sweep.py:targets_for()` but was never implemented
for 4.1 and no `live_AS*.csv` has ever been produced.

**Open decision:** sweep depth per block, and probe type. See §4.

### Phase C — Census traceroute
Live targets only, every vantage, **equal coverage is a hard requirement**. 4.1's coverage was
unbalanced 8× across vantages (562 to 4,609 traces), which is what made its cross-vantage numbers
unquotable.

### Phase D — Emit
Raw JSON, `routes_*.txt`, and a per-trace **quality record**: hops attempted, hops answered,
private-hop fraction, reached flag. **No verdict column.** 15.2 adds those.

## 3. Non-negotiables

- Every run emits a human-readable `routes_*.txt` beside the CSV.
- Keep **repeat observations of each hop address**. The domestic-address rule needs a median over
  3 or more samples from one vantage, and collapsing repeats destroys it.
- Report `inconclusive` separately, never folded into `local`.
- Aggregate in /24-equivalents, not blocks.

## 4. Decisions still open

1. **Sweep depth.** How many addresses per block in Phase B. Drives cost directly.
2. **Probe type.** Median hop response is 50%. ICMP vs TCP/80 vs UDP is untested and a liveness
   sweep does not fix router silence. Settling it needs a small paid pilot.
3. **The two dark vantages.** Keep, replace, or diagnose.
