
# Experiment 04 — Path Tromboning (systematic detection across ISP address space)

**Author:** Rayan Atif

## Motivation

A traceroute from the **Nova probe** (AS136174, Lahore) to an IP in **Worldcall**
(AS38710, a Pakistani ISP) was observed leaving the country and coming back:

```
 3  110.93.212.161           2.6 ms   Transworld (AS38193, PK)
 4  110.93.252.48           20.6 ms   Transworld (PK)
 5  110.93.252.136          19.5 ms   Transworld (PK)
 6  17557.sgw.equinix.com  191.5 ms   Equinix Singapore  <-- LEAVES PAKISTAN
 ...
13  wtl.worldcall.net.pk   123.5 ms   Worldcall (AS38710, PK)
14  115.186.61.254 [open]  124.0 ms   Worldcall (AS38710, PK)  <-- DESTINATION
```

Both endpoints are in Pakistan, yet Transworld handed the packet to **Equinix
Singapore** and it trombrned back — a ~120 ms detour for what should be a domestic
path. This is **path tromboning** (a.k.a. hairpinning): inter-/intra-country traffic
that exits the country and returns. It is the central inefficiency this project
argues PKIX should fix (see `findings/01_*`, `findings/03_*`).

**Two facts make this hard to study rigorously:**

1. It is **intermittent.** Re-running minutes later still trombrned, but *other*
   destinations reached via the same Transworld next-hop did **not** show the high
   RTT. So one example proves existence, not prevalence — load-balancing / policy
   routing means the same ISP pair can be local on one path and foreign on another.
2. We can't **cherry-pick.** "How did we arrive at this IP? Why not other IPs in
   Worldcall's space?" We need a principled, reproducible way to choose targets —
   without scanning so aggressively that our probes get ICMP-throttled.

This experiment builds that method.

## Objective & research questions

For each Pakistani ISP, **measure how much of its address space trombrnes abroad**,
from probes on other PK ISPs — systematically, not anecdotally.

- **RQ1 — prevalence:** what fraction of an ISP's announced prefixes are reached via
  a **foreign hop** (vs staying in-country)?
- **RQ2 — where & who:** which foreign exchange does traffic exit through
  (Equinix-SG, DE-CIX-FRA, EMIX-UAE …), and which transit ASN (PTCL / Transworld)
  makes the decision?
- **RQ3 — stability:** is the tromboning **persistent** or **intermittent** (time of
  day, per-flow load-balancing)? — the time axis, shared with Exp 03.
- **RQ4 — asymmetry of ISP pairs:** does ISP-A → ISP-B trombone while B → A stays
  local? (probe-to-probe, the Exp 02 method.)

## Method — adapted from TASS (Klick et al., IMC 2016)

Source: *"Towards Better Internet Citizenship: Reducing the Footprint of
Internet-wide Scans by Topology Aware Prefix Selection"* (Klick, Lau, Wählisch,
Roth — IMC 2016). Their **TASS** scans the whole IPv4 space efficiently by: scan
once, group responders by **BGP prefix**, rank prefixes by host **density**, keep
the densest prefixes covering a target fraction φ of hosts, re-scan only those.

### What we take

| TASS idea                                                                                                                           | How we use it                                                                                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Work at BGP-prefix granularity, not per-IP**                                                                                | Enumerate the**announced prefixes** of the target ISP and treat **each prefix as the sampling unit**. This is the principled answer to "why this IP" — we cover the ISP's prefixes, not hand-picked addresses. |
| **"Scan once, then focus" (two-phase)**                                                                                       | Phase 1: a light, time-spaced**responsiveness sweep** to find a few **live IPs per prefix** (a hitlist). Phase 2: `tcptraceroute` only those. Avoids spending the throttling budget on dead space.            |
| **Prefixes are stable; individual IPs churn** (their hitlist decays to ~80%/month from dynamic IPs; prefix-based ~0.3%/month) | For the**longitudinal** runs, key on the **prefix** and **re-pick a live IP each round** rather than reusing one that may go dark.                                                                        |
| **Coverage knob φ**                                                                                                          | Choose a coverage target (e.g. "95% of Worldcall's live prefixes") to**bound probe volume** and report it — defensible sampling instead of cherry-picking.                                                           |
| **"Good Internet citizen" ethos**                                                                                             | Minimise footprint by**selection + pacing**; this is the paper's whole thesis and matches the throttling concern.                                                                                                     |

### What we deliberately skip / change

- **No full-IPv4 initial scan.** Our universe is **one ISP's announced prefixes**
  (Worldcall ≈ a handful of /22–/24s), not 2.8 billion addresses — the paper's
  expensive bootstrapping does not apply.
- **No host-density ranking.** TASS ranks prefixes to maximise *host hits*. Our unit
  is the **route**, which BGP decides per prefix, so **≥1 live target per prefix** is
  the right granularity (optionally a few per prefix, and weight larger prefixes).
  Because every IP in a prefix usually shares the same path, we need **far sparser**
  sampling than TASS — this is the main simplification their framing buys us.

## Chosen methodology

| Decision                       | Value                                                                                | Why                                                                                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Target unit**          | BGP**announced prefix** of the ISP (from RIPEstat / CAIDA pfx2as / BGP)        | Routing is per-prefix; principled, reproducible target selection.                                                                                    |
| **Targets/prefix**       | **1–3 responsive IPs**                                                        | Robust to per-host load-balancing without dense scanning.                                                                                            |
| **Probe type**           | **`tcptraceroute`, TCP SYN to :80** (as in the source observation)           | Dodges ICMP filtering/throttling; reaches an open port reliably; completes the path so the return-into-PK leg is visible.                            |
| **Flow variation**       | **Paris-style fixed flow** + a few flow IDs per target                         | Distinguishes a real reroute from load-balancer multipath, and*catches* the intermittent tromboning (vary the flow to see if some flows trombone). |
| **Responsiveness sweep** | 1 light probe per candidate,**widely spaced**, to build the per-prefix hitlist | Phase 1 of TASS; concentrates expensive traceroutes on live targets.                                                                                 |
| **Pacing**               | **Randomised delay between traceroutes** (seconds), small batch sizes          | Stay under ICMP/throttling radar; "good citizen".                                                                                                    |
| **Coverage φ**          | e.g. 0.95 of the ISP's live prefixes                                                 | Bounds probe count; reported with results.                                                                                                           |
| **Longitudinal**         | re-measure the prefix set over**days**, re-picking live IPs                    | RQ3 (intermittency / diurnal); reuses Exp 03's cadence thinking.                                                                                     |
| **Vantage**              | start from the**Nova probe** (where it was first seen); extend to all probes   | Cross-ISP view; RQ4 via probe-to-probe pairs.                                                                                                        |

### Detecting "tromboning" (the decision rule)

A path **trombrnes** if, between two PK endpoints, it contains a **hop outside
Pakistan**. Detection reuses the Exp 01 correction stack:

- **Foreign hop by country** (Team Cymru `hop_country` ≠ PK), **and/or**
- **Foreign IXP by registry/hostname** — the exit hops are often *unannounced* in
  BGP (Cymru returns nothing) and only identifiable via **RDAP / PTR hostname**:
  `*.equinix.com`, `*.de-cix.net`, EMIX-UAE, etc. (Confirmed: the Worldcall trace's
  Singapore hop `27.111.228.83` returns **no ASN** from Cymru but resolves to
  `17557.sgw.equinix.com`.) This is exactly the `registry_lookup` fallback already
  in `pk_multi_probe.py`.
- **RTT corroboration:** a jump to >100 ms at the foreign hop (speed-of-light floor:
  PK→Singapore ~60–90 ms, →Europe ~100–130 ms). RTT alone is not sufficient — the
  **foreign hop** is the decisive signal.

Recorded per (target prefix, probe, round): exit country, exit IXP/ASN, the transit
ASN that handed it off (PTCL/Transworld), RTT before/after, and persistence.

## Targets

- **First:** Worldcall (**AS38710**), the ISP where tromboning was observed.
- **Then:** the other PK ISPs, prioritising Set-1/Set-2 ISPs from Exp 02 (those least
  likely to peer locally), and the Exp-01 PK-hosted destinations as a control set
  known to be domestic.

## Implementation & RIPE tooling

Build on official RIPE libraries instead of hand-rolling the API (as Exp 01/03 did):

| Step                                                    | Tool                                                                                 | Notes                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 0 — prefix enumeration**                 | **RIPEstat** `announced-prefixes` API (no key)                               | `enumerate_prefixes.py <ASN>` → `results/targets_AS<asn>.csv`. The principled target universe. **Done for Worldcall** (below).                                                                                                                                                                                               |
| **Phase 1 — responsiveness sweep + traceroutes** | **ripe-atlas-cousteau** (`pip install ripe.atlas.cousteau`)                  | `Traceroute(protocol="TCP", paris=…, target=…)` + `AtlasSource(type="probes", value=…)` + `AtlasCreateRequest(is_oneoff=True)`. Native **TCP traceroute** (matches the `tcptraceroute` source observation), one-off, specific probes.                                                                                  |
| **Result parsing**                                | **ripe-atlas-sagan** (`pip install ripe.atlas.sagan`)                        | `TracerouteResult` → hops, per-hop RTTs, `destination_responded`. We layer our existing Cymru + RDAP + (optionally **ipmap.ripe.net** for router geolocation) on top for foreign-hop tagging.                                                                                                                                |
| **Ad-hoc spot-checks**                            | **ripe-atlas-tools** CLI (`ripe-atlas measure traceroute --protocol TCP …`) | Quick shell re-confirmation of a tromboning path, no code.                                                                                                                                                                                                                                                                              |
| **Macro triage / presentation**                   | **Region Meshes** (hosted), **TraceMON**, **Path Analysis**        | Region Meshes already classifies intra-country probe-to-probe paths and flags**"IXP Out-of-Region"** arcs (= leaving PK to reach an IXP abroad) — use it for the country-level view and to pick which ISP pairs to drill into. It is probe-to-probe only, so it **complements** (does not replace) the prefix-level sweep. |

So Exp 04's own code is just: (1) `enumerate_prefixes.py` (done), (2) a cousteau-based
paced sweep + traceroute runner, (3) sagan-based parsing + our foreign-hop tagger +
the routes-txt renderer. RIPE does the measurement plumbing and the macro visuals.

## Output (planned)

`experiments/04_path_tromboning/results/{RUN_NAME}/` (committed):

- `targets_{ISP}.csv` — the chosen prefixes + responsive IPs (the hitlist), so the
  selection is auditable (answers "why these IPs").
- `tromboning_{TIMESTAMP}.csv` — one row per (prefix, target IP, probe, round):
  trombrnes? exit country, exit IXP/ASN, transit ASN, RTT, hop count.
- `routes_{TIMESTAMP}.txt` — readable hop-by-hop traceroutes (Exp 03 style), with the
  foreign hop flagged.

## Caveats

- **Intermittency is the point, not noise** — vary flow and repeat over time; a
  single "local" result does not disprove tromboning, and vice-versa.
- **`tcptraceroute` ≠ ICMP traceroute** — different probe type than Exp 01/03; paths
  may differ slightly. Keep it consistent within Exp 04 and note when comparing.
- **Throttling** — if a hop starts rate-limiting, RTTs/timeouts corrupt; the pacing
  and small batches are the mitigation, and we watch for sudden `* * *` onset.
- **IP geolocation of an unannounced IXP hop is unreliable** — trust the
  registry/hostname (`equinix.com`) over a geo-IP city for the exit point.
- **Apex/prefix blind spots** — a prefix may be multi-homed or split across POPs;
  1–3 IPs per prefix may miss intra-prefix routing differences (revisit if needed).

## Relation to other experiments

- **Exp 01** established *where* sites are hosted; Exp 04 measures *how the path gets
  there* across an ISP's whole space, not just 100 named sites.
- **Exp 02** classifies ISPs by PKIX use; Exp 04's per-ISP tromboning rate is direct
  evidence for the Set-1/2/3 split and the probe-to-probe matrix (RQ4).
- **Exp 03** added the time axis for 10 sites; Exp 04 adds the **address-space axis**
  (prefix coverage) and reuses the longitudinal cadence for RQ3.
- **Findings 3.1** already showed PTCL↔Transworld interconnect *locally* for the
  paths we sampled — Exp 04 tests how often the **same** transit instead trombrnes,
  at scale.

## Status

**First run done & written up** — see `findings/04_path_tromboning_worldcall.md`.
Worldcall (AS38710): **16/52 prefixes (31%) trombone via Transworld → Equinix
Singapore**, 36 local, 0 inconclusive; validated with a live-target run and an
observed intermittency flip. Pipeline (`enumerate_prefixes` → `responsiveness_sweep`
→ `tromboning_sweep`, 3-signal RTT-robust detector) is complete. Remaining: other
ISPs, other probes (RQ4), time axis (RQ3). Original phase plan kept below.

---

**Phase 0 done; Phase 1 done.**

- **Phase 0 (prefix enumeration) — done.** `enumerate_prefixes.py 38710` →
  `results/targets_AS38710.csv`. **Worldcall (AS38710) announces 52 IPv4 prefixes,
  all /24 (13,312 addresses).** They are 52 *separate* /24s (not aggregated), so
  there are up to 52 distinct routing behaviours to test — vindicating the
  per-prefix sampling frame. Dr. Saqib's `115.186.61.254` is one of them. With only
  ~13k addresses the universe is tiny, so coverage is cheap here; the prefix frame
  matters more for big ISPs.
- **Phase 1 (next):** cousteau-based responsiveness sweep (find 1–3 live IPs per
  /24, time-spaced) → paced TCP `tcptraceroute` from the Nova probe (then all
  probes) → sagan parse → foreign-hop tagging (Cymru/RDAP/ipmap) → `tromboning_*.csv`
  + `routes_*.txt`. Then add the time axis (RQ3) and other ISPs.
- Also: load **Pakistan in Region Meshes** for the macro probe-to-probe hairpin view
  as an independent cross-check before the sweep.
