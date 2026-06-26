# Findings 04 — Path Tromboning across Worldcall's address space

**Author:** Rayan Atif
**Source:** Experiment 04 first run, `run_20260622_064001` (+ live-target run
`run_20260622_072132`), TCP/80 Paris traceroutes from the **Nova probe**
(AS136174, Lahore) to **Worldcall** (AS38710).
**Method:** `experiments/04_path_tromboning/notes.md`. **Reproduce:**
`enumerate_prefixes.py 38710` → `responsiveness_sweep.py 38710` →
`tromboning_sweep.py 38710` (`--live` for responsive targets).

Companion to `findings/03.1_ptcl_rtt_jumps.md` (same RTT-jump technique) and the
Exp 01/03 hairpinning results.

---

## Headline

Of Worldcall's **52 announced /24 prefixes**, **16 (31%) trombone abroad** — the
packet leaves Pakistan to **Equinix Singapore** and comes back to reach a *Pakistani*
ISP. **Every** tromboning path is handed off by **Transworld (AS38193)**. The other
**36 (69%) stay in-country** at 2–40 ms. **0 inconclusive.** Which destinations
trombone is **destination-dependent** (specific /24s hairpin, adjacent ones don't —
**measured one IP per /24**) and **time-variable** (the same IP flips between local
and abroad within minutes; per-flow variance seen within a single destination).
Whether a whole /24 is internally consistent is **not yet verified** (see Caveats).

This is the systematic, non-cherry-picked confirmation of the single tromboning
traceroute that motivated Exp 04.

---

## How a packet stays local vs trombones — the fork is inside Transworld

Both outcomes start identically (Nova → Transworld). They diverge at the **Transworld
backbone hop** (`110.93.252.x`):

**Local** (to `115.186.32.0/24`, max RTT **3.5 ms**):

```
3  110.93.212.161   2.3ms  Transworld (AS38193)
4  110.93.252.191   2.6ms  Transworld backbone
5  149.40.227.134   2.4ms  Cogent (AS174) — local PoP IN Pakistan
7  192.168.12.13    2.9ms  (private interconnect)
9  117.102.7.130    3.5ms  Worldcall (AS38710)  ← in-country
```

**Trombone** (to `115.186.61.254`):

```
3  110.93.212.161   2.3ms  Transworld (AS38193)
5  110.93.252.136  18.3ms  Transworld backbone
6  27.111.228.83  195.0ms  Equinix Singapore   ← LEAVES PK
...
11 115.186.61.254 124.0ms  Worldcall (AS38710) ← back in PK, at 124ms
```

Same probe, same Transworld next-hop. Transworld simply chooses a **domestic egress**
(via a **Cogent PoP physically in Pakistan**, `149.40.227.134`, ~2 ms) for some
destinations and an **international egress** (Equinix Singapore) for others.
That per-destination routing choice **is** the tromboning. The ~120 ms penalty is pure
geography (PK↔Singapore round trip), so it cannot be fixed with more bandwidth —
only by Transworld keeping the route domestic (the PKIX argument).

---

## Detection methodology (the part that makes this defensible)

A naive "any foreign-registered hop = abroad" rule gave **100% false positives** —
two traps had to be removed, and one class of true positives had to be added back:

1. **Geo-IP lies → RTT gate.** `70.70.x` (Shaw, "CA") and `149.40.227.134` (Cogent,
   "US") are physically in Pakistan, answering at **1–3 ms**. A hop only counts as
   abroad if its RTT is **physically plausible for abroad** (≥ 40 ms; PK→Singapore is
   ~60 ms). RTT is physics; registration country is not.
2. **Invisible foreign hops → RTT-jump backstop.** Tromboning is provable from the
   RTT profile even when the foreign hop is a `*` (no reply) or its lookup fails. We
   also flag a path abroad on a **≥ 60 ms jump** between consecutive hops, or **any
   hop ≥ 70 ms**. This caught **6 of the 16** tromboning prefixes that the
   foreign-hop-only rule missed (the foreign hop didn't respond that round).
3. **Three independent signals** → robust to geo-IP error, lookup failure, and
   unresponsive hops: (a) a responding foreign hop, (b) a ≥60 ms RTT jump, (c) max
   hop RTT ≥70 ms. A path whose RTT never exceeds ~45 ms is classified **local** even
   if it didn't reach the final host (it demonstrably never left PK).

Without (1) the result was 53/53 false "abroad"; with only the foreign-hop rule it
was 11/53; the full detector gives **16/52 with 0 inconclusive**.

---

## Results (kept run, `.128` per /24, 2026-06-22)

| Outcome                          | Prefixes           | Evidence                                                |
| -------------------------------- | ------------------ | ------------------------------------------------------- |
| **Trombone → Equinix-SG** | **16 (31%)** | 11 visible Equinix hop + 5 RTT-evidence (invisible hop) |
| **Stayed local**           | 36 (69%)           | 2–40 ms, via Transworld→Cogent-PK→Worldcall          |
| **Inconclusive**           | 0                  |                                                         |

- **Single exit, single culprit:** 100% of tromboning paths exit at **Equinix
  Singapore** (`27.111.228.83`) and are handed off by **Transworld (AS38193)**.
- **Clustered, not random:** the tromboning prefixes bunch up
  (`115.186.59–61, 90, 106–113, 121`, plus `111.88.233`, `25`) — adjacent /24s
  trombone together, consistent with how Worldcall's blocks are grouped/announced.
- **Penalty:** tromboning paths reach Worldcall at **~120 ms** vs **2–40 ms** local —
  a 3–60× latency cost on traffic between two PK networks.

### Live-target run (responsive IPs) — validates the backstop

Re-running the 12 ICMP-responsive prefixes to **live** hosts, all 5 tromboning ones
showed a **visible Equinix-Singapore hop** (181–195 ms) — confirming the kept run's
RTT-evidence flags were genuine tromboning, just with an invisible hop.

### Intermittency (RQ3), observed directly

Between the responsiveness sweep and the traceroute minutes later, two prefixes
**flipped**: `115.186.31.1` (ping **248 ms** → trace **6.7 ms**) and `117.102.18.1`
(ping **279 ms** → trace **3.4 ms**). Same prefix, same probe — abroad one moment,
local the next. This is the "doesn't always happen" load-balancing, captured
quantitatively, and motivates the longitudinal (time-axis) run.

---

## RQ4 — is it Transworld, or Worldcall? (probe-to-probe, 2026-06-22)

To isolate the culprit, the **same Worldcall IPs** were measured from multiple
vantages (ping = clean min-RTT; the AS38193 backbone probe is ICMP-filtered so its
path is invisible, but TES/AS135407 is not):

| Worldcall target | PTCL (AS17557) | Transworld (AS38193) | TES / Proj14 (AS135407) | Nova (AS136174) |
|---|---|---|---|---|
| `115.186.61.254` *(a trombone IP)* | **LOCAL 46 ms** | TROMBONE 134 ms | TROMBONE 117 ms *(visible Equinix-SG)* | TROMBONE 124 ms |
| `117.102.19.1` *(a local IP)* | — | **LOCAL 6 ms** | **LOCAL 20 ms** *(visible)* | **LOCAL 3 ms** |

**1. Transworld is the culprit, and a domestic route demonstrably exists.** PTCL
reaches `115.186.61.254` locally at ~46 ms over a path that **never touches
Transworld**, while every Transworld-family vantage sends the *same IP* to Singapore.
So the hairpin is Transworld's **routing choice**, not missing connectivity — the
strongest form of the PKIX argument.

**2. Transworld routes some Worldcall destinations locally, others abroad.** To
`117.102.19.1` every vantage is local (6–20 ms); to `115.186.61.254` all trombone.
The **TES probe (AS135407, unfiltered)** shows both from one source: a local path
(`TES → Transworld → Cogent-PK 149.40.227.134 → Worldcall`, 20 ms) and a trombone
path (`TES → Transworld 110.93.252.136 → Equinix-SG`, 117 ms) — **same Transworld
egress router, opposite outcomes by destination.** Every Transworld-family probe
trombones via the *same* `110.93.252.136` hop from the original observation.

Caveat: this is **per-destination**, one IP each — whether it is cleanly per-/24 is
the open intra-block test (see Caveats).

---

## Caveats

- **Single-vantage sweep.** The 52-prefix sweep is *Nova's* view; the RQ4 section
  adds spot-checks from PTCL/Transworld/TES, but a full per-prefix sweep from a
  non-Transworld probe (e.g. PTCL) is still pending — it would show how much of the
  31% is Transworld-specific vs Worldcall-wide.
- **ICMP undercounts live hosts.** Only 12/52 prefixes had an ICMP responder; many
  hosts answer TCP/80 but not ICMP. The tromboning verdict does **not** depend on
  reaching a live host (it shows mid-path), but "stayed local" for the 28 low-RTT
  prefixes that died before Worldcall means *never left PK as far as visible*, not a
  confirmed end-to-end local delivery.
- **Extreme RTTs are queuing, not distance.** One prefix (`115.186.98`) showed
  ~1137 ms — a buffering/ICMP-generation spike, not a real 1137 ms path. It still
  left PK (counted as trombone) but the magnitude is noise; quote medians.
- **One IP per /24 — intra-block consistency UNVERIFIED.** We sampled one address
  per announced /24. Routing is *expected* to be per-prefix (longest-prefix match),
  so all IPs in a /24 *should* share a route — but we have **not** measured that.
  The noisy TES ping (19–305 ms to a "local" IP) and the time-flips show per-flow /
  per-time variance exists, so a /24 may not be a clean static label. The open test:
  probe 8–10 IPs across one trombone /24 vs one local /24 and check agreement. Until
  then, read "per-prefix" as "per-destination, one sample each."
- **Exit = Equinix Singapore handoff**, the point where Transworld leaves PK; the ICMP
  path is authoritative for *that*, distinct from any HTTP serving location.

---

## Artifacts & reproduce

- Targets: `experiments/04_path_tromboning/results/targets_AS38710.csv` (52 /24s)
- Live list: `results/live_AS38710.csv`
- Runs: `results/run_20260622_064001/` (full, `.128`) and `results/run_20260622_072132/`
  (live) — each has `tromboning_*.csv`, `routes_*.txt`, `raw_*.json`
- Re-render/re-classify any run without spending credits:
  `tromboning_sweep.py 38710 --reparse <run_dir>`

## Next steps

1. **Other ISPs / Set-1/2 first** — run the same pipeline for more PK ISPs (each is
   one `enumerate_prefixes.py <ASN>` away) to get a per-ISP tromboning rate.
2. **Other probes (RQ4)** — repeat from Nayatel/Cybernet/Z-Com to see if the
   Worldcall blocks trombone from every vantage or only via Transworld transit.
3. **Time axis (RQ3)** — periodic re-runs to quantify how often each prefix flips.
4. **Cross-check with Region Meshes** for the country-level probe-to-probe picture.
