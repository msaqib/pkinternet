# Planned experiments

Forward-looking experiments that close the gaps identified in `paper/paper_structure.md`
(single-snapshot census; no normal-day baseline for the outage). Both are **planned**, not
yet run.

---

## Exp 4.2 — Longitudinal small-ISP tromboning census (repeat rounds)

**Why.** Exp 4.1 is a **single snapshot** (11% trombone) and verdicts flip minute-to-minute
(intermittency is pervasive). Turn the point estimate into a **range**, quantify
intermittency, and separate **per-host** from **time-flipping** routing (the open Exp 04
question).

**Method.** Re-run `census_sweep.py` over **R rounds spaced over days** — same universe
(747 blocks × 8 IPs × 7 probes) or a cost-capped subsample. Per `(source, block)`, compute
the **fraction of rounds** it tromboned and label **stable-local / stable-trombone /
flapping**.

- **Cadence:** ~1 full pass/day for **10–14 days** (or fold into the Exp 07 panel below).
- **Cost:** ~837k credits/pass → ~8–12M over the span; pace under the 100-concurrent cap.
  Lever if needed: subsample blocks/IPs, or restrict to the ISPs that hairpinned in 4.1.
- **Outputs:** per-block trombone-fraction table; intermittency stats; the per-ISP rate as
  a **range**, not a point; a diurnal/weekly tromboning pattern.
- **Answers:** stabilises the headline census number for the paper; the intra-block ×
  over-time cross-tab (per-host vs time-flipping).

---

## Exp 07 — The PKIX-underuse longitudinal panel (flagship / main experiment)

**Why.** The definitive longitudinal dataset that unifies hosting-QoS, tromboning, diurnal/
weekly cycles, and resilience from **every vantage** over a proper span. It feeds the
paper's cost figures (the RTT CDFs, per-ISP penalty, stability) and — crucially — provides
the **normal-day baseline Exp 06 lacked**, so if a cable fault happens during the window we
capture it with a real before/during/after.

**Design.**

| | |
|---|---|
| **Probes** | **all 14 connected PK probes** — PTCL ×3, Transworld 62224, TES 64078, Cybernet ×3, Nayatel ×2, Nova, Fasttel, Orbit, Z-Com |
| **Targets (~30, a mix)** | (a) **websites by hosting class** — CDN (from the Exp 1.4 CDN set), Abroad (offshore banks/news/servers), Pakistan (gov/edu/local-ISP hosts); (b) **IPs that trombone** — a selection from the 4.1 tromboning list (Brain `203.128.0.x`, Worldcall trombone /24s, the reached+tromboned live hosts); (c) **canaries** `1.1.1.1`, `8.8.8.8` for clean international RTT |
| **Cadence** | **1 traceroute / hour** + **1 ping / 30 min**, per (probe, target) |
| **Duration** | **20 days** |
| **Mechanism** | server-side RIPE **periodic** measurements (reuse/extend `06_submarine_outage/outage_monitor.py`): one periodic traceroute (interval 3600 s) + one periodic ping (interval 1800 s) per target, fanning to all 14 probes, 20-day start/stop window → **laptop-independent** |

**Scale & cost (estimate).**
- Traceroute: 14 probes × ~30 targets × (24 × 20 = 480 rounds) ≈ **200k traceroutes**.
- Ping: 14 × 30 × (48 × 20 = 960 rounds) ≈ **400k pings**.
- Credits ≈ ~6M (traceroute) + ~2M (ping) ≈ **~8–10M**, i.e. **~15–18%** of the ~54M
  balance. Feasible; **monitor the burn**. Levers: fewer targets, ping-only for the
  ICMP-filtered probes (7764, 62224).
- Only **~60 periodic measurements** created (30 trace + 30 ping) — far under the
  concurrency cap, and low create-rate (good-citizen).

**Outputs.** A per-round **panel**: `(ts, probe, target, class, rtt, hop_count, loss,
tromboned, exit)` → the paper CSVs; diurnal/weekly decomposition; the RTT CDFs (local vs
hairpin vs offshore) per ISP; any outage windows captured live.

**What it answers.**
- **PENALTY / RQ1** — RTT distribution local vs hairpin vs offshore, **per ISP** (are
  Set-3 ISPs' customers better off?).
- **Stability / RQ2** — diurnal/weekly cycles and route changes over time (do same-ISP
  customers get the same service?).
- **Tromboning intermittency** — how stable a trombone verdict is over 20 days (complements
  Exp 4.2; the two can run concurrently or 4.2 folds into this panel).
- **Resilience** — a proper **vs-normal** baseline for any cable fault in the window
  (fixes the Exp 06 gap).

**Relationship to prior experiments.** Supersedes/extends **Exp 03** (longitudinal) with the
full 14-probe set + tromboning targets; supplies the baseline **Exp 06** needed; provides
the repeat rounds **Exp 4.2** needs.

**Good-citizen.** Server-side periodic (low create-rate), paced, credit-burn monitored;
stop/adjust if balance runs low.

---

## Priority

1. **Exp 07** — start soon; the 20-day clock is the critical path for every longitudinal
   figure, and it opportunistically catches the next outage with a baseline.
2. **Exp 4.2** — run concurrently (or fold its repeat-rounds into the Exp 07 panel) to
   range-bound the census headline.
