# Are our experiments uniformly designed? (a strict review)

Honest assessment of how consistently we ran things, so the paper's Method section can be
*one* framework rather than ten ad-hoc setups. Companion to `paper_structure.md`.

## The design matrix (what actually varied)

| Exp | Vantages | Targets / selection | Stack + protocol | RTT def. | Metrics | Cadence | Classifier |
|---|---|---|---|---|---|---|---|
| **01** hosting | 5 probes | 100 **curated** websites | requests, **ICMP** Paris | single-packet 1st reply (noisy) | hops, RTT, ASN path, serving-loc | snapshot | geo-IP + serving-location |
| **1.1** DNS | 5 | 103 curated | requests, DNS (probe resolver) | — | resolved IP/ISP | snapshot | GeoDNS diff |
| **1.2** CDN | **3** | content services | requests, ping | ping | RTT tier | snapshot | RTT threshold |
| **1.4** hosting | Pass A central + Pass B **1 probe** (64078) | **PK100** (diff. curation) | cousteau, traceroute | — | hosting class + hairpin | snapshot | ASN/geo + RTT |
| **03** longitudinal | **8** | 10 fixed sites | requests, **ICMP** Paris + ping | ping min-of-N | RTT, path-change, loss | **15 min / 24–48 h** | path-change |
| **3.1** peering | PTCL probe → probes | targeted | ptcl\_peering.py | RTT | peering y/n | snapshot | path inspection |
| **04** Worldcall | 1 (Nova) +RQ4 4 | Worldcall IPs, **RIPEstat** prefixes → live-IP sweep | cousteau/sagan, **TCP/80** Paris | max-hop RTT | trombone verdict | snapshot | **RTT-physics** |
| **4.1** census | **7** | 747 blocks × 8 IPs, **RIPEstat** + spread | cousteau/sagan, **TCP/80** Paris | max-hop RTT | trombone verdict | snapshot | RTT-physics |
| **06** outage | **14** | 18 websites (6/6/6), liveness-checked | cousteau/sagan, **ICMP** Paris + ping, periodic | ping avg | **RTT, jitter, hops, loss** | 15 min / 12 h | RTT-physics + impact |
| *07 (planned)* | 14 | ~30 mixed + trombone IPs | cousteau, trace+ping periodic | ping + hop | RTT, jitter, hops, loss | 1 trace/h + 1 ping/30 min / **20 d** | RTT-physics |

## What drifts (and whether it's fixable or inherent)

**Fixable — these hurt cross-experiment comparison and should be standardised:**
1. **Vantage set changes every time** (5 → 3 → 8 → 1 → 7 → 14, never the same). Partly forced
   (probes go offline), but not *planned*. → Fix: declare one **canonical roster** (the 14),
   report per-experiment availability, and prefer the full set.
2. **Traceroute protocol is inconsistent** — ICMP (01, 03, 06) vs TCP/80 (04, 4.1). We *proved*
   ICMP undercounts (Exp 04: 12/52 responded on ICMP) yet Exp 06 used ICMP again. → Fix:
   standardise on **TCP/80 Paris** for path/reachability (ping for clean end-to-end RTT).
3. **RTT is defined three different ways** — single-packet first reply (01, noisy), ping
   average/min-of-N (03, 06), max-hop RTT (04, 4.1). These are not comparable. → Fix: one
   definition — **ping min-of-N for end-to-end RTT**, max-hop RTT only as the detector's input.
4. **The metric set is inconsistent** — only Exp 06 carries the full **RTT / hop-count / jitter
   / loss** set (the IXP-paper KPIs); 01/03/4.1 lack jitter and loss. → Fix: carry all four
   everywhere (Exp 07 does).
5. **Website selection is not reproducible** — hand-curated in 01/1.4/03 (two *different* 100s).
   Only the IP-space selection (RIPEstat + 8-spread, TASS-justified) is principled. → Fix:
   a reproducible website pipeline (Tranco → filter .pk → resolve → Team Cymru), which is
   exactly what the team member drafted.
6. **Hosting uses a weaker classifier than tromboning** — geo-IP + serving-location (01/1.4) vs
   RTT-physics (04+). → Acceptable *if* labelled, but note hosting is DNS/geo, not RTT-proven.

**Inherent / acceptable — don't over-correct:**
- **Hosting is a snapshot property** (where a domain resolves) — a one-time DNS+geo census is fine.
- **The census's value is completeness** (every /24) — a single pass is defensible; Exp 4.2 adds
  repeat rounds for intermittency.
- Some **probe drift is forced** by availability.

## The root cause (state it plainly)

The experiments were **built incrementally as the method matured**: we started hand-rolling the
RIPE REST API with ICMP traceroute, single-packet RTT, and geo-IP classification (01–03), then
moved to cousteau/sagan + TCP/80 Paris + the RTT-physics detector (04 onward). That is a normal
research trajectory, **but the paper must not present it as one uniform campaign.** Present the
*mature* framework and the results measured under it; use the early experiments as
method-development and preliminary evidence.

## How to structure the paper given this

1. **One canonical Method section** that fixes: the 14-probe roster (with availability windows),
   **two** reproducible target-selection methods (website-population via Tranco+CISA;
   address-space via RIPEstat + 8-spread), **TCP/80 Paris + ping**, the **four KPIs**, and the
   **RTT-physics detector**. Everything else is an instance of this.
2. **Reposition each experiment by role**, not chronology:
   - **Method / validation:** Exp 04 (detector on Worldcall, 53/53→16/52) — folds into Method.
   - **Primary results:** **Exp 4.1** (complete census — unique value is coverage) and **Exp 07**
     (the only *uniform* longitudinal dataset — per-ISP KPI distributions, diurnal/weekly).
   - **Hosting:** Exp 01 + 1.4 as a snapshot census (adopt the Tranco pipeline for reproducibility).
   - **Preliminary → superseded:** Exp 03's penalty result is the **pilot** that Exp 07 confirms
     and extends at scale; present it as motivation, quote final numbers from Exp 07.
   - **Event study:** Exp 06 (the SMW5 outage) — keep; note the baseline gap Exp 07 closes.
   - **Support:** 1.1, 1.2, 1.3, 3.1 as paragraphs.
3. **Lean on Exp 07 for the KPI table** (RTT/hops/jitter/loss per ISP) because it is the only
   experiment that carries all four uniformly across all 14 vantages — the earlier snapshots
   corroborate but don't need re-running.

## Action items
- [ ] Standardise the Method framework as above; write it once.
- [ ] Adopt the reproducible **Tranco** website pipeline (replaces two curated 100s).
- [ ] Make **Exp 07** carry the full four-KPI set from all 14 probes (it is designed to).
- [ ] Re-quote Exp 03's penalty from Exp 07's uniform data once it runs; keep 03 as the pilot.
- [ ] In every results section, label which framework version produced it (legacy ICMP/geo-IP
      vs mature TCP/RTT-physics) so numbers are not silently compared across methods.
