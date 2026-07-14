# Experiment 4.3 — Path-Tromboning Analaysis from Cybernet Haripur to various selected IPs

**Author:** Adnan Iqbal

## Objective

**A complete, systematic census of how much of each small Pakistani ISP's address
space is reachable only by hairpinning out of the country** — measured from real
in-country vantages, across the whole small-ISP population at once.

Concretely: for **every announced block** of **every FLL (small/local) ISP**, from
**several source ISPs**, decide whether a packet to that block **stays in Pakistan or
trombones abroad** — and if abroad, **via which transit (PTCL / Transworld) and which
foreign exchange (Equinix-SG, DE-CIX, …)**. This turns the single Worldcall result
(Exp 04) into a **national, per-ISP, per-transit map of PKIX underuse** — the headline
this project exists to produce: *how much "Pakistani" traffic needlessly leaves the
country, ISP by ISP, and who is responsible for sending it there.*

- **Q1 (primary):** per-ISP trombone rate + the **source × destination × transit
  matrix** — who hairpins whom, through whom, to where.
- **Q2 (same pass):** the **population-weighted** version — `Σ (trombone?) × (block
  density)` — using live-host density collected while probing. Q1 is the scaffold;
  Q2 re-weights the identical dataset (see *Q1 → Q2*).

## Scope & the block universe (Phase 0 — done, free)

**Destinations:** FLL licensees (`data/pk_isp_fll_list.csv`) with a usable ASN that
announce prefixes — the project's small/local-ISP roster (the Set-1 population).
Enumerated from **RIPEstat** announced-prefixes (no key, no credits).

**Real numbers (2026-06-27):**

| | |
|---|---|
| FLL ISPs with a usable ASN | 66 |
| …that actually announce prefixes | **48** (18 announce nothing — defunct / sub-allocated) |
| **announced blocks (prefixes)** | **747** |
| /24-equivalents | 807 |
| total addresses | 206,592 |

Full lists: `results/blocks_all.csv` (one row per block) and `results/isp_summary.csv`.

**"Complete" = every announced block**, no block subsampling. It is **not** every IP:
an exhaustive per-IP sweep is infeasible (millions of probes, RIPE credit/rate limits,
throttling) **and pointless** — all IPs in an announced prefix share one BGP route, so
a few IPs per block is routing-complete (and is exactly what TASS argues).

**Caveat — FLL ≠ strictly small.** A few roster members are large or are LDIs
(Connect 166 /24-eq, CMPak LDI 98, Optix 88, Broadband Vision 78, Multinet 26, TES
29). Kept for completeness; **flagged in analysis** so the "small ISP" headline isn't
skewed by them.

## Sources (vantages)

Tromboning depends on the **source's transit**, so we measure from a spread of source
ISPs and let the data show the transit pattern rather than assuming it. **All 7
path-visible connected probes** (status as of 2026-06-27):

| Probe | ISP (ASN) | City | Transit / role |
|---|---|---|---|
| 1016126 | PTCL (AS17557) | Karachi | PTCL itself |
| 1015679 | Nova/TPCPL (AS136174) | Lahore | Transworld-transit |
| 7613 | Z-Com (AS152605) | Lahore | Transworld-transit |
| 1016036 | Cybernet (AS9541) | Haripur | Cybernet |
| 1016154 | Cybernet (AS9541) | Karachi | Cybernet (RQ2: 2nd Cybernet) |
| 60223 | Nayatel (AS23674) | Islamabad | independent (multi-homed) |
| 64535 | Orbit (AS151983) | Faisalabad | small ISP |

**ICMP-filtered** (path invisible — handled separately via ping, not in the traceroute
census): 62224 (Transworld backbone, AS38193), 7764 (PTCL anchor). **Recently offline:**
1016153 (TES, AS135407), 1016143 (Cybernet-Khi) — re-add if they reconnect.

## Method (strict)

Per **source probe × block**:

1. **Phase 0 — Enumerate** *(done)*: RIPEstat → 747 blocks (`blocks_all.csv`).
2. **Phase 1 — Probe**: **TCP/80 Paris traceroute** (`protocol=TCP, port=80, paris=16,
   packets=3`) to **K = 8 spread IPs per block** (evenly spaced, e.g. `.16 .48 .80
   .112 .144 .176 .208 .240`). Eight traceroutes per block yield, in one shot:
   - a **routing verdict per IP** → **intra-block consistency** (do all 4 agree? — the
     open question from Exp 04), and
   - a **density** per block (responders / 4) → the population proxy for Q2.
3. **Phase 2 — Detect** (Exp 04 RTT-physics detector, geo-IP-proof):
   - **trombone** if any responding hop is foreign with RTT ≥ 40 ms, **or** a ≥ 60 ms
     RTT jump between hops, **or** any hop RTT ≥ 70 ms;
   - **local** if max RTT stays < 45 ms;
   - **ignore** RTTs > 500 ms (queuing / ICMP-error-generation artifact — use ping
     min-of-N on ICMP-filtered probes);
   - **exclude** artifact ASNs (Shaw AS6327; Cogent AS174 PoP is in-PK at ~2 ms).
4. **Phase 3 — Aggregate**: per-(source, block, IP) verdict → per-block (consistency)
   → per-ISP trombone rate → **source × destination matrix**; carry density per block.
5. **Phase 4 — Longitudinal**: repeat over **R rounds spaced over days** (catch
   intermittency; also refines the density estimate). One round = a full census pass.
6. **Pacing (good-citizen)**: launch in batches under RIPE's **100-concurrent cap**,
   randomized inter-launch delay, spread over hours/days. Minimises throttling.

## Cost

Complete pass = `747 blocks × 8 IPs × 7 sources = 41,832 traceroutes ≈ ~837k credits`
(at ~20 credits/traceroute). Balance is **~54M credits**, so a pass is **~1.5%** —
multiple longitudinal rounds are trivially affordable. Must still be **paced** under
RIPE's 100-concurrent cap (runs in batches over hours), which also keeps us polite and
dodges throttling. Levers if ever needed: fewer IPs/block, fewer sources, subset of ISPs.

## Outputs

`results/run_<ts>/`:
- `census_<ts>.csv` — one row per **(source, block, target_ip)**: verdict, evidence,
  exit country/IXP, transit ASN, max_rtt, plus per-block density.
- `routes_<ts>.txt`, `raw_<ts>.json` (Exp 04 conventions).
- `matrix.csv` — source-ISP × destination-ISP trombone %.
- `isp_tromboning.csv` — per destination ISP: block-% trombone (Q1) **and**
  density-weighted % (Q2).

## Q1 → Q2 (why one pass answers both)

`Q2 = Σ_blocks (trombone? from Q1) × (density of block)`. The density weights come
**free** from the 4-IP probing in Phase 1, so Q2 is a weighting of the same dataset —
no separate rating phase. **Honest ceiling:** Q2 is **active-address-weighted**, a
proxy for users, **not** traffic volume (RIPE Atlas can't see bytes; NAT and dynamic
IPs distort the live-IP count). Report Q2 as "% of **active address space**," not "% of
traffic."

## Caveats

- **Density = active-address proxy**, not byte/traffic weight (above).
- **Source-transit clustering** is an assumption (3 sources represent the diversity) —
  validate by occasionally running all probes on a subset of ISPs.
- **TCP/80, not ICMP** for responsiveness — ICMP undercounts badly (Exp 04: 12/52).
- **Intermittency** — a single round is a snapshot; verdicts flip minute-to-minute, so
  the per-ISP rate needs R rounds and should be quoted as a range / fraction-of-rounds.
- **FLL roster** includes a few non-small / LDI members — flagged, not dropped.
- **18 FLL ISPs announce no prefixes** — excluded (nothing to measure).
- **Target IP (aimed-at) ≠ last responding hop.** Each block is probed at 8 *spread*
  addresses (`.16, .48, …`), which are the traceroute **targets** (`dst_addr`, the
  `-> IP` in the routes header) — **not** necessarily live hosts. Small-ISP /24s are
  sparse, so most targets are dead/unassigned or ICMP-filtered and never reply: the
  trace then ends in `* * *` and the **last responding hop is an upstream/transit
  router, not the target**. They coincide **only when `reached=True`** (target
  answered). The `routes_tromboning_*.txt` blocks carry a **`reached=`** label so this
  is explicit. This does **not** affect tromboning detection — the foreign hop appears
  *mid-path, before* the target, so the hairpin is seen even when the target address
  is empty/silent (we measure the **route toward the block**, not one host's liveness).

## Status

**Phase 0 done** (747 blocks enumerated, cost priced). **Next:** build
`census_sweep.py` (multi-source, multi-IP per block; imports the Exp 04 detector +
cousteau/sagan), **pilot on a handful of ISPs** to validate before the full ~179k-credit
run, then run the complete census + the longitudinal rounds.
