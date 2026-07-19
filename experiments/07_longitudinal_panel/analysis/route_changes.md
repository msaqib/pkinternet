# Exp 07 — Route-change analysis (which routes change, and how)

**Data:** full-week trace panel (`results/a/panel_20260718_195946.csv`, 222,944 traces,
11–18 Jul 2026, 16 probes × 100 targets) joined to the ping panel for RTT. Classes are the
physics-corrected split (`targets_corrected.csv`). "PK-hosted" = 37 corrected-Pakistan targets.

## Headline: instability is the norm, not the exception

Of the 1,600 (probe, target) pairs, **only 304 (19%) kept a single stable route the whole week.**
The other **1,296 (81%) changed** — different carrier, exit, hop count, or trombone state across
the 7 days. Over the week we see **≥ 5,466 distinct coarse route-signatures** (transit AS │ exit
country │ trombone │ hop-count), a *lower bound* on true path diversity. Routing to Pakistani
destinations is dynamic, not a fixed misconfiguration.

## 1. What changes (share of the 1,600 pairs whose value varies over the week)

| Attribute | pairs that vary | share |
|---|--:|--:|
| **hop count** | 935 | **58%** |
| **trombone on/off** (local ↔ hairpin) | 756 | **47%** |
| **transit AS** (carrier at the exit) | 655 | **41%** |
| **exit country** | 400 | **25%** |

Hop count is the most volatile (paths lengthen/shorten constantly); trombone-state and carrier
flips are close behind. Exit *country* changes least — when a path does leave PK it tends to leave
to the **same** foreign exit (see §4).

## 2. Carrier flips — including the two gates

335 pairs are carried by **more than one** transit AS across the week. The most common flips:

| Flip | pairs | note |
|---|--:|---|
| AS151983 ↔ Cogent (174) | 86 | CDN/abroad upstream churn |
| Cloudflare (13335) ↔ Transworld | 57 | CDN reached direct vs via TWA |
| **PTCL ↔ Transworld** | **26** | **the domestic gate flip** — same pair reaches a PK site via either gate on different rounds |
| AS135407 ↔ Transworld | 21 | |
| Cloudflare ↔ Z-Com ↔ Transworld | 20 | |

The PTCL↔Transworld flips matter most for the thesis: a domestic path's *choice of gate* is not
fixed — the same customer→site pair is handed to different transit providers at different times,
consistent with the load-balancing/instability seen in Exp 06's data plane.

## 3. Over time

**Diurnal (PK-hosted trombone rate by PKT hour):** a mild evening peak.
- Trough ~06:00 = **12.6%**, peak ~21:00–22:00 = **16.0%** → a **3.4 pp** swing.
- Interpretation: modestly more hairpinning during the evening traffic peak (congestion pushing
  paths off the shortest route), but the effect is small — the hairpinning is **mostly structural,
  not diurnal**.

**Day-by-day:** stable at ~13.6–14.7% for 12–18 Jul (11 Jul reads 17.6% but is a partial launch
day). **No change-point** — importantly, no confounding outage or routing shift occurred *during*
the panel window, so the instability we measure is the normal steady-state, not an event artifact.

## 4. By location (exit country)

Exit countries on PK-hosted hairpins: **Singapore 3,771** (Equinix SG dominant), **US 1,802**,
Hong Kong 167, a handful to NL/SE/AE/IT, plus 6,006 unresolved (`?`). Pairs that hairpin almost
never oscillate *between* foreign exits (only a handful do NL/SG, SG/US, …). So the pattern is
**local ↔ one consistent foreign exit**, not a scramble across many exits — when a PK path leaves
the country it has a stable "escape hatch" (usually Singapore), and the variability is whether it
takes that hatch on a given round.

## 5. By hop count

935 pairs vary in hop count; among varying pairs the **median range is 3 hops**, with **131 pairs
swinging ≥ 3** and **96 pairs ≥ 5 hops** between their shortest and longest observed path — i.e.
the same pair sometimes takes a route 5+ routers longer than its shortest, a large path change.

## 6. By RTT — does a route change cost latency? (honest, two readings)

**Cross-sectional (conflated):** median RTT is **24.5 ms when not tromboned vs 104.3 ms when
tromboned**. But this compares *different pairs* — always-hairpinned far sites vs always-local near
sites — so it overstates the causal cost.

**Within-pair (the causal number):** for the **140 pairs that actually flip** and have RTT in both
states, the hairpin's latency penalty on the *same* pair is **heavily skewed**:
- **median +0.7 ms**, 75th pctile **+8.7 ms**, **mean +14.5 ms** (a long tail).

Reading: **most trombone flips are near-free** — the alternate path is a roughly equal-cost
load-balance, so the pair oscillates without users noticing. But a **minority of flips are
expensive** (the tail pulling the mean to +14.5 ms), where the hairpin genuinely adds tens of ms.
The large cross-sectional gap is therefore mostly **selection** (which sites are structurally far),
not the per-flip cost. The expensive hairpins are the **structural** ones (always-tromboned pairs
sitting at ~100 ms), which is where the PKIX case is strongest.

## 7. By ISP — who has the most volatile routing (PK-hosted targets)

| ISP | trombone % | pairs that flip | mean route-signatures/site |
|---|--:|--:|--:|
| PTCL | 17.4 | **100%** | 5.3 |
| Fasttel | 24.6 | 92% | 4.4 |
| Orbit | 12.6 | 73% | 4.0 |
| Cybernet | 22.4 | 70% | 3.0 |
| TES | 10.4 | 46% | 3.1 |
| Nova | 10.5 | 43% | 2.9 |
| **Nayatel** | **9.7** | **41%** | **1.4** |
| **Transworld** | **3.2** | **35%** | **1.4** |
| Z-Com | 11.6 | 35% | 2.1 |

**PTCL and Fasttel are the most unstable** — essentially every PK-target path flips, averaging
5+ distinct routes each. **Nayatel and Transworld are the most stable** (lowest trombone rate,
fewest signatures) — consistent with Nayatel's strong local peering (Exp 07 CDN result: 85% local)
producing short, steady paths, and Transworld being a gate itself (fewer hops to leave). Routing
quality is an **ISP property**, not just a destination property — the same finding as the small-ISP
tromboning census (Exp 4.1), now with the time axis confirming it.

## Mechanics: HOW exactly the paths change (hop-level, from the raw archive)

Everything above used the coarse per-trace signature. This section re-derives the change story
from the **actual hop sequences** of all 222,944 traces (`.paths_series.json`, built from the raw
archive + `hop_annotations.csv`), and defines precisely what we label a "change".

### The labels, and why (three layers, strictest last)

| Layer | definition | consecutive-round change rate |
|---|---|--:|
| **IP-path** | the literal sequence of responding hop IPs | **42.8%** |
| **AS-path** | IP-path mapped to ASNs, consecutive duplicates collapsed | **11.9%** |
| **Genuine AS re-route** | AS-path changed AND the responding IPs are *not* a projection of the other round's (i.e. not explainable by hops merely failing to answer) | **5.5%** |

Why the layering matters — two honesty corrections it forces:
1. **Most IP-level churn is not routing change.** The panel runs Paris traceroute with 16 flow
   IDs; RIPE rotates the ID between rounds, so consecutive rounds deliberately sample *different
   ECMP branches* of the same route. The 42.8% therefore mostly measures **path diversity**
   (parallel load-balanced branches that exist simultaneously), not temporal change.
2. **53% of AS-path changes are visibility artifacts.** ASes "vanish" from a path when their
   routers ICMP-rate-limit (their hops become `*`) and "reappear" when they answer again — no
   packet took a different road. Filtering these (the projection test above) leaves the genuine
   re-route rate: **5.5% of hourly rounds; 782/1600 pairs (49%) genuinely re-routed at AS level
   at least once in the week** — the defensible version of the coarse "81% of pairs changed".

### Where the paths change

First-differing-hop distribution over all IP-path changes: **hops 3–5 carry 78.5%** of all
divergence (hop 3: 26.6%, hop 4: 24.4%, hop 5: 27.5%). Hops 1–2 (access/CPE: 3.3%) and hops ≥8
(the foreign segment: <10%) are stable. **The instability lives almost entirely in the domestic
aggregation/backbone layer and the handoff into transit — the exact layer an IXP would replace.**
Once a path is out of the country, it barely changes; before the gate, it changes constantly.

### What kind of changes (the 12,234 genuine re-routes)

| kind | share | meaning |
|---|--:|---|
| segment reorder/change | 48% | different domestic backbone segment between same endpoints |
| **detour inserted** | **20%** | an extra AS appears mid-path (trombone/interconnect onset) |
| **detour removed** | **20%** | that AS drops out again |
| substitution (A→B) | 12% | a different AS replaces another — incl. the PTCL↔TWA gate flips |

Insertions and removals are near-perfectly symmetric (2,496 vs 2,492) — detours **breathe** on/off
rather than accumulate. Pair-level dynamics confirm it: pairs hold a median of just **2 distinct
AS-paths** for the whole week, **96% of changing pairs return to a previously-seen state**
(oscillation, not migration), and state dwell time is median 1 round / mean 8 h — a two-state
flap, not an evolving route.

### Two live examples (11–12 Jul, from the archive)

**Gate substitution — Fasttel → cxtreme.pk (Cybernet-hosted), one hour apart:**
```
12:00Z ... -> PTCL AS17557 -> PTCL-bb AS9557 -> ... -> CYBERNET AS9541   (via gate 1)
13:00Z ... -> TWA AS38193 -> TWA backbone (unannounced) -> CYBERNET AS9541  (via gate 2)
```
Fasttel multihomes; its egress flips between the duopoly gates hour to hour — same destination,
same probe, different gate. (This is the mechanism behind §2's 26 gate-flip pairs.)

**Detour insertion — Orbit → careers635.com.pk, one hour apart:**
```
01:01Z ... Orbit -> 172.29.244.9 -> TWA backbone -> dest
02:01Z ... Orbit -> 172.29.244.9 -> COGENT AS174 -> TWA backbone -> dest
```
A Cogent hop materializes mid-path — and at domestic RTT: this is **Cogent's Pakistan PoP fabric**
(known from Exp 01/1.3) being toggled into the interconnect, not a trip abroad. A caution the
AS-level view needs: *AS-foreign ≠ geographically foreign*; the RTT-physics verdict, not the hop's
registry, decides country (which is exactly why the trombone detector is RTT-based).

### What the mechanics add to the takeaways

- The volatility is **structural ECMP diversity plus a two-state domestic flap**, concentrated at
  hops 3–5 — the pre-gate layer. International segments are stable; Pakistan's contribution to a
  path is the unstable part.
- The honest headline pair: **49% of pairs genuinely re-route at AS level within a week** (not
  81%, which includes ECMP sampling and visibility artifacts), and **5.5% of hour-pairs** see a
  genuine AS-route change.
- Detour breathing (20%+20%) is the hourly-scale mechanism behind trombone intermittency: the
  same detour toggles in and out, consistent with traffic engineering across gate/interconnect
  fabrics (incl. Cogent's PK PoP) rather than persistent misrouting.

## Takeaways for the paper

1. Domestic routing to PK sites is **dynamic** — 81% of pairs change by coarse signature; the
   artifact-corrected figure to quote: **49% of pairs genuinely re-route at AS level within the
   week** (see Mechanics) — strengthens the "instability/load-balancing" framing over "static
   misconfiguration."
2. The **gate choice itself flips** (PTCL↔TWA on the same pair) — the duopoly routing is not
   deterministic.
3. The hairpin RTT cost is **bimodal**: cheap for load-balanced flips, expensive for structural
   hairpins — cite the *within-pair* +0.7 ms median and the structural ~100 ms separately; do not
   quote the conflated 24.5→104 ms as a causal penalty.
4. Instability is **ISP-driven** (PTCL/Fasttel volatile; Nayatel/TWA stable) — supports RQ1
   (ISP choice affects experience).
