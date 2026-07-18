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

## Takeaways for the paper

1. Domestic routing to PK sites is **dynamic** (81% of paths change over a week) — strengthens the
   "instability/load-balancing" framing over "static misconfiguration."
2. The **gate choice itself flips** (PTCL↔TWA on the same pair) — the duopoly routing is not
   deterministic.
3. The hairpin RTT cost is **bimodal**: cheap for load-balanced flips, expensive for structural
   hairpins — cite the *within-pair* +0.7 ms median and the structural ~100 ms separately; do not
   quote the conflated 24.5→104 ms as a causal penalty.
4. Instability is **ISP-driven** (PTCL/Fasttel volatile; Nayatel/TWA stable) — supports RQ1
   (ISP choice affects experience).
