# Experiment 15 — National block-routing census (single round)

**Root for all block-level experiments.** Experiment 16 is this same design run longitudinally.
**Owner:** Rayan Atif. **Status:** designed, unrun. Detector written and validated
against the 4.1 archive (`15.1_data_plane/validate_against_41.py`).
**Created:** 2026-09-02. **Last updated:** 2026-09-07.

---

## 0. Terminology, fixed

These three were used interchangeably in earlier drafts and it made the coverage tables unreadable.

| Term | Means | Never means |
|---|---|---|
| **probe** | a deployed RIPE Atlas device, i.e. a vantage point. RIPE's own usage. | a measurement, a packet, or a target |
| **trace** | one traceroute from one probe to one target | the device |
| **target** | one destination IP address sampled from a block | anything we measure *from* |
| **check** | one liveness test of one address (up to three methods tried in sequence) | a packet, a probe, or a trace |
| **draw** | one batch of 8 addresses selected from a block by the adaptive sampler | the addresses themselves |

So 4.1 was **18,260 traces from 7 probes to 6,456 targets**, not "18,260 probes".

And the liveness scan performs **checks**, not probes: 508,616 checks across 19,267 blocks. A
check may send up to three packets (ICMP, then TCP/80, then TCP/443) and still counts as one.

## 1. The question

For **every announced block of every small Pakistani ISP**, measured from several in-country
vantage points: does a packet sent toward that block stay in Pakistan, or hairpin abroad and
come back? And when it leaves — through whose transit, and via which foreign exchange?

Exp 04 (`../04_path_tromboning/`) answered this for one ISP.
Exp 4.1 designed the population-scale version and ran it once. **This is the corrected re-run.**

## 2. How it is split

**Measurement and interpretation are separate, and interpretation carries no BGP.**

| | Does | Evidence |
|---|---|---|
| **15.1 Data plane** | Runs the measurement, emits a snapshot with per-trace quality. No verdicts. | Active traceroute from RIPE Atlas |
| **15.2 Post-processing** | Selects the panel for 16.1, and benches competing tromboning detectors over that snapshot. | 15.1's output, local only |
| **15.3 Comparison** | **Retired.** See `15.3_comparison/RETIRED.md`. | |

15.1 and 15.2 are split because 4.1 baked its detector into collection, so when the detector proved
wrong the whole run had to be reinterpreted from raw JSON. Now a detector change never forces a
re-measurement.

**Why 15.3 is gone.** Of 3,352 collector sessions worldwide exactly one is Pakistani, and every
Pakistani vantage AS appears in **0 of 364** collector paths to a Pakistani target block. Public BGP
has no record of how one Pakistani network reaches another, so there is nothing to compare against.
A control-plane rule applied anyway returns "domestic" by default, because it never meets a foreign
AS: it reports *fine* where the honest answer is *no data*.

**BGP survives as an input, not an arm.** `announced-prefixes` enumerates the block universe in
15.1 Phase A. That is enumeration, not inference.

## 2b. What 15.1 must fix, measured

| | 4.1 result |
|---|---|
| Targets that answered | 11.0% |
| Blocks with zero reachable targets | 76% |
| Blocks with 8 clear targets | 6 of 696 |
| Vantages contributing almost no clear traces | 2 of 7 (Nayatel, Cybernet Khi: 7 clear from 5,288 traces) |

4.1 sampled 8 addresses per /24 with no liveness check, which at an 11% response rate yields 0.9
responders per block. **15.1 adds a responsiveness sweep before the census.** Full numbers in
`15.1_data_plane/analysis/trace_quality_20260908.txt`.

## 3. The shared design

Full detail lives in two documents at this level, which **both 10.x and 11.x inherit**:

- **`SAMPLING_METHOD.md`** — the block universe and how every number in it was derived, the
  sampling rule, detection rules with their literature, and the limits.
- **`EXP41_CENSUS_PLAN.md`** — vantage points with per-probe justification, run sizing, and the
  phase-by-phase execution plan.
- **`make_slides.py`** → `slides.html` + `slides.pptx` — the deck explaining all of it.

Summary of what those fix, so this manual stands alone:

| | |
|---|---|
| Destination universe | **747 announced blocks** across **48 small ISPs** (PTA FLL licensees) = **807 /24-equivalents**, 206,592 addresses |
| Source of the universe | RIPEstat announced-prefixes API, backed by RIPE NCC RIS. IPv4 only. Snapshot 2026-06-27 — **re-enumerate before running** |
| Sampling | **One target per 32 addresses** at every block size → K=8 on a /24, 16 on a /23, 32 on a /22, 256 on the single /19. **6,456 targets** |
| Vantage points | **6–7 RIPE Atlas probes**, one per distinct upstream transit, plus two deliberate same-transit duplicates as controls |
| Probe type | TCP/80 Paris traceroute, `paris=16, packets=3` |
| Detection | Geolocation **gated by RTT**: foreign hop ≥40 ms, or ≥60 ms inter-hop jump, or any hop ≥70 ms; local if max RTT <45 ms |
| One round | 6,456 targets × 6 vantages = **38,736 traceroutes** |

## 4. Baseline to beat

Exp 4.1's June 2026 run is the baseline, and its flaw is the reason this exists:

- **11.0%** of traces detoured (2,002 of 18,260)
- Destination ISPs ranged **0.6% → 64.5%**; vantage points ranged **4.0% → 46.3%**
- **20.0%** of blocks were internally split
- **But coverage was unbalanced 8×** across probes (562 to 4,609 traces), so no cross-vantage
  number from it is quotable

**Equal coverage per vantage is the hard requirement of the re-run.** A round is not complete until
every vantage has probed every target.

## 5. Non-negotiables

- Every run emits a human-readable `routes_*.txt` beside the CSV. No verdict ships without the
  paths to check it against.
- Report **per-ISP** rates as the headline; block-level averages are dominated by the five ISPs
  holding 58% of blocks.
- Aggregate in **/24-equivalents (807)**, not blocks (747), or the single /19 counts the same as
  somebody's lone /24.
- `inconclusive` is reported, never folded into `local`.
- Separate genuine detours from **last-hop rate limiting**, which produces the same RTT-jump
  signature (`SAMPLING_METHOD.md` §3.4).

## 6. Layout

```
15_national_block_routing_census/
├─ MANUAL.md              this file
├─ FINDINGS.md            filled during and after the run
├─ SAMPLING_METHOD.md     shared design — universe, sampling, detection
├─ EXP41_CENSUS_PLAN.md   shared plan — vantages, sizing, phases
├─ make_slides.py → slides.html / slides.pptx
├─ papers/
├─ 15.1_data_plane/
├─ 15.2_control_plane/
└─ 15.3_comparison/
```
