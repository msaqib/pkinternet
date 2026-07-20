# Experiment 6.1 — Did the SMW5 fault move Pakistan's logical dependencies? (AS-hegemony time series)

**Author:** Rayan Atif · **Status:** ✅ pull complete 2026-07-17 (window 15 Jun–10 Jul, 10 origins,
~131k bins → 1,712 daily points)
**Extends:** Exp 06 (SMW5 outage, data plane) · **Uses:** Exp 09's method (AS Hegemony via IHR)

## Results (see `results/fig_hegemony_smw5.png`, fault date 2 Jul marked)

**Verdict: two-level. Downstream dependencies stayed rigid; the operators shuffled their own
foreign upstreams. The re-routing happened *above* the duopoly, not below it.**

1. **Downstream Pakistan did not move (with one exception).** Orbit stayed pinned at TWA = 1.00
   through the entire fault; Nova ~0.88, Cybernet ~0.12, Nayatel ~0.72/0.28, NTC ~0.68/0.31 — all
   flat across 2 Jul. Whatever customers experienced (Exp 06's congestion), their *logical*
   dependency on the two operators never changed: there was nowhere else to go. This is the
   control-plane half of the resilience claim, now measured.
2. **The exception — Fasttel (exact dailies):** steady ~0.73 PTCL / 0.27 TWA through 30 Jun;
   **1 Jul: 0.54/0.46; 2 Jul (report day): 0.46/0.54 — crossed; 3 Jul: back to 0.67/0.33** and
   stable after. One downstream ISP re-balanced across the duopoly for ~2 days and reverted. The
   move begins **one day before the 2 Jul PTA announcement** — consistent with the fault being
   physically operative before it was publicly reported (Exp 06 also inferred this), *not*
   evidence of foreknowledge; unrelated maintenance cannot be excluded.
3. **The operators' upstream shift — VERIFIED UNFILTERED (confidence-graded).** The first pull
   dropped readings < 0.02, which can fake "appearances"; PTCL/TWA were re-pulled with no
   threshold for 28 Jun–4 Jul. What survives:
   - **CONFIRMED — TWA's emergency swing on 2 Jul:** Hurricane 0.022 → **0.205** → 0.023 (3 Jul),
     with simultaneous Cogent collapse 0.157 → 0.040 → 0.159 and Sparkle dip 0.086 → 0.047 →
     0.074. Continuous unfiltered series, large amplitudes: real.
   - **CONFIRMED — PTCL leaned on Hurricane the same days:** unfiltered shows Hurricane ≈ 0.000
     on 28 Jun, **0.142 on 1–2 Jul**, absent again after. The both-operators-same-carrier-same-days
     synchronization stands.
   - **RETRACTED — "a new PTCL→Cogent dependency appears 4 Jul":** unfiltered data shows the
     Cogent link existed all along at 0.001–0.015 and merely rose to 0.040 — the "appearance" was
     an artifact of the 0.02 filter.
   - **DOWNGRADED — "Level3 fades" / "Arelion appears":** Level3's decline (0.062 → 0.001) began
     *before* the fault and involves tiny values; Arelion was already present on 30 Jun. Both are
     plausible routine variation; not claimed as fault effects.
   - **NEW CAVEAT — IHR itself has data gaps on the fault days:** bins per day run 96 normally but
     **69 on 29 Jun, 45 on 2 Jul, 23 on 3 Jul**. Daily "means" on those dates cover partial days
     (47% and 24% of bins on 2–3 Jul). The large TWA/Fasttel swings dwarf this, but small
     day-level effects on 2–3 Jul should not be over-read — and operator-level analysis should
     always use the unfiltered pull.

### The two-leg view (the clearest presentation of the event)

Pakistan's routing has two legs: **local ISPs → the two gates** (domestic) and **the gates → the
world's carriers** (international). The fault played out almost entirely on leg 2.

**Leg 1 — local ISPs → PTCL/TWA** (*"of all routes reaching this ISP, what share comes through
each gate?"*; baseline 26–30 Jun → fault day 2 Jul):

| Local ISP | via PTCL | via TWA | changed? |
|---|---|---|---|
| Orbit | — | 1.00 → 1.00 | no |
| Z-Com | — | 1.00 → 1.00 | no |
| TES | — | 1.00 → 1.00 | no |
| Nova | 0.12 → 0.12 | 0.88 → 0.88 | no |
| Nayatel | 0.72 → 0.73 | 0.28 → 0.27 | no |
| NTC | 0.72 → 0.67 | 0.28 → 0.33 | barely |
| **Fasttel** | **0.74 → 0.46** | **0.26 → 0.54** | **YES — swapped gates for ~2 days** |

**Leg-1 verdict: frozen** (1 of 8 changed, transiently).

**Leg 2 — TWA → the world** (*"of all the world's routes reaching Transworld, what share arrives
through each foreign carrier?"*; unfiltered data):

| TWA's foreign carriers | before (28–30 Jun) | **fault day (2 Jul)** | after (3 Jul) |
|---|--:|--:|--:|
| Level3 | 21% | 17% | 17% |
| **Cogent** | **16%** | **4%** ⬇ | 16% |
| Sparkle (Telecom Italia) | 8.5% | 4.7% ⬇ | 7.4% |
| Omantel | 4.4% | 3.9% | 4.6% |
| **Hurricane Electric** | **2%** | **20.5%** ⬆⬆ | 2.3% |

**Leg 2 — PTCL → the world** (unfiltered; note the much smaller magnitudes — PTCL reaches most of
the world by *peering*, so no single carrier holds a large share of paths to it; its dependency is
diffuse):

| PTCL's foreign carriers | before (28–30 Jun) | 1 Jul | **2 Jul (fault)** | 3 Jul |
|---|--:|--:|--:|--:|
| **Hurricane Electric** | **0%** | **14.2%** ⬆ | **14.2%** ⬆ | 0% |
| Etisalat | 2.1% | 7.4% ⬆ | 5.8% | 1.6% |
| Arelion | 2.5% | 1.1% | 7.1% ⬆ | 0% |
| Level3 | 4.3% | 2.3% | 1.0% | 0.3% |
| Cogent | 0.8% | 0.1% | 0.9% | 0.3% |

The robust PTCL signal is the **Hurricane appearance (0 → 14.2%) on exactly the two fault days**,
mirroring TWA; Etisalat's rise into the fault and Arelion's 2 Jul spike are supporting but small;
Level3's slide began *before* the fault and is not attributed to it. Both operators' carrier mixes
are plotted side-by-side in `results/fig_operators_upstreams.png`.

The **churn percentages below are these tables compressed to one number** — the total movement
between carriers: on 2 Jul, ~21 of every 100 world-routes to TWA (and ~13.5 to PTCL) arrived via
a different carrier than the week before.

### Quantified route changes — how much, when, where, who

**Metric:** per origin and day, *route churn* = ½ · Σ |Δhegemony| across all transits vs the
pre-fault baseline (28–30 Jun) — i.e. **the fraction of the world's paths to that origin that
changed intermediary**. Computed from the **unfiltered** operator pull
(`results/operators_unfiltered.csv`).

| Origin | 1 Jul | **2 Jul (fault)** | 3 Jul | 4 Jul |
|---|--:|--:|--:|--:|
| **Transworld** | 2.1% | **20.9%** | 3.5% | 6.4% |
| **PTCL** | 11.9% | **13.5%** | 3.9% | 5.6% |

- **How much:** on the fault day, **~21% of all paths to Transworld and ~13.5% of paths to PTCL
  changed carrier**, dominated by the swing onto Hurricane Electric (TWA: +18.3 pp) and away from
  Cogent (−11.7 pp) and Sparkle (−3.9 pp). **Robustness (Exp 6.1.1, W3a+W3b): the churn-magnitude
  claim is retracted.** A placebo test against four control operators — including two (Nepal,
  Vietnam) with zero SMW5 exposure — showed the same elevated-churn ranking on 1–3 Jul for
  *everyone tested*, even after correcting for a global IHR data gap on those days. The elevation
  is a worldwide phenomenon our method cannot attribute to Pakistan or SMW5, so no claim is made
  on churn size or ranking. What the placebo test *does* confirm, specifically: the size of the
  **swing onto Hurricane Electric** — TWA +9.1 pp, PTCL +7.1 pp, and SLT (itself an SMW5 landing
  country) +13.2 pp — is 2–8× larger than the two confirmed non-SMW5 controls (NTC-Nepal +1.5 pp,
  VNPT +3.8 pp), a placebo-tested, carrier-specific fingerprint rather than a magnitude argument.
  Full detail in `06.1.1_smw5_robustness/notes.md` (W3b).
- **When:** PTCL's churn was already elevated on **1 Jul** (11.9%) — again suggesting the fault
  predates the 2 Jul announcement; both operators normalized by **3 Jul**.
- **Where:** at the operators' interconnects with foreign carriers — physically the
  Karachi-gateway edge and the far-end carrier PoPs; logically in their BGP announcements.
  Nothing changed *inside* Pakistan's domestic mesh.
- **Who it affects — downstream (26–30 Jun baseline → 2 Jul):** **1 of 8** probe ISPs changed
  materially (**Fasttel**, PTCL 0.74 → 0.46, TWA 0.26 → 0.54, i.e. ~28 pp of its paths switched
  gate); the other **7 of 8 moved ≤ 5 pp** (Orbit/TES/Z-Com pinned at TWA = 1.00; Nova 0.88 flat;
  Nayatel 0.72 → 0.73; Cybernet 0.12 flat; NTC 0.72 → 0.67 modest). **At national scale (Exp 6.1.1): 98.5%
  of 273 gate-dependent PK networks held their majority gate; 4 switched; ~4% re-balanced.** And
  *indirectly*, everyone riding the operators was affected: per Exp 09, TWA is the majority
  dependency for most Pakistani networks (median 0.50), so **the 21% carrier churn silently
  re-routed part of the international path of most of the country's networks** — their own
  dependencies unchanged, the roads beyond the gate swapped under them.

### Are these physical cables? (mechanism, stated carefully)

**No — the routes hegemony sees are logical (BGP): which *companies* hand traffic to each other.**
The metric cannot see cables. The connection to the physical fault is mechanistic, one level down:
each carrier relationship (TWA↔Cogent, TWA↔Hurricane, …) rides leased capacity on **specific
physical submarine systems** out of Karachi (SMW5, AAE-1, IMEWE, PEACE, TW1) to the carriers'
PoPs abroad. When SMW5 lost capacity, the physical lanes under *some* of those interconnects
degraded or died → the BGP sessions/announcements over them were withdrawn or depreferenced →
the world's routers re-selected paths via the interconnects that remained (Hurricane's) → the
hegemony shares moved. **The 2 Jul churn spike is the BGP shadow of a physical failure.**
Honest limits: there is no public mapping of which carrier rides which cable, so we cannot name
the cable behind each shifted interconnect — the attribution rests on the placebo-tested
Hurricane-swing fingerprint (both operators onto the same substitute carrier, at a magnitude
2–8× larger than confirmed non-SMW5 controls, on the same two days) plus the known mechanism,
not on churn magnitude (retracted, Exp 6.1.1 W3b) or on direct observation of the fibre.

**What is public vs. what we'd need (the cable-mapping question):**
- *Public (coarse):* cable → Pakistani operator. The AINTEC'24 paper states Karachi's 6 submarine
  cables land at stations owned by PTCL and TWA; consortium membership via TeleGeography gives
  roughly PTCL: SMW4, IMEWE, AAE-1; Transworld: SMW5, TW1; PEACE also lands Karachi.
- *Not public (the missing layer):* **which foreign-carrier interconnect rides which cable** —
  e.g. "TWA↔Cogent = 2×100G on SMW5 (Karachi→Marseille)". Lease-level; lives inside the operators.
- *If obtained, it buys four things:* (1) upgrades this experiment's inference to verification
  (Cogent's 16%→4% collapse directly explained if its interconnect rides SMW5); (2) a quantified
  single-point-of-failure map — "breaking cable X removes interconnects carrying Y% of Pakistan's
  international paths"; (3) with terrestrial fibre lengths, the what-if latency arithmetic
  (WorldCall-peers-at-PKIX counterfactual); (4) a built-in validation test — any claimed mapping
  must predict which carriers dipped on 2 Jul.
- *Route to get it:* Nowmay's interviews were with the PTCL/TWA IP-gateway engineers who operate
  exactly this layer — the email to him should include this as a third ask.

**Interpretation for the paper:** during a national submarine-cable fault, *all* observed
adaptation occurred at the two licensed operators' interface with their foreign upstreams
(~21%/13.5% of their world paths re-carriered for ~48 h); domestic networks' dependencies were
essentially frozen (1 of 8 changed, transiently). Combined with Exp 06 (data plane: congestion,
no transit change), the event is now characterised in both planes: **users rode out the fault on
unchanged routes while the duopoly absorbed it upstream.**

*Caveats:* daily means of sub-daily bins; hegemony counts paths, not traffic; TWA's upstream mix
is volatile all month, so operator-level shifts are "coincident with", not proven caused by, the
fault; Fasttel's swap is a single-ISP observation.

## Why this experiment

Exp 06 measured the SMW5 submarine-cable fault (reported 2 Jul 2026) in the **data plane**: RTT
and jitter degraded on international paths, but path changes were only **load-balancing within the
same transit** — we saw no reroute onto a different operator or exit. That was measured from our
probes over 12 hours.

This experiment asks the same question in the **control plane, globally, over weeks**: when the
cable broke, did anyone's *BGP dependencies* actually change? IIJ's Internet Health Report
archives AS-hegemony scores continuously, so we can replay June–July 2026 day by day and watch
whether the dependency structure moved.

Two possible outcomes, both valuable:
- **Flat curves through the fault** → nobody re-routed; networks endured congestion on the same
  logical paths. This confirms Exp 06 at the global-BGP level and sharpens the resilience claim:
  *the duopoly is so rigid that even a cable fault moved no dependencies — there was nowhere else
  to go.*
- **Shifted curves** (e.g. TWA-dependent origins briefly gaining PTCL/Omantel/China paths, or the
  operators' own upstream mix changing) → the fault *did* redraw the logical map — a new finding
  that Exp 06's 12-hour data-plane window could not see.

## What we measure

Daily AS-hegemony series over the window **2026-06-15 → 2026-07-10** (bracketing the 2 Jul fault):

1. **Downstream dependencies:** for each of our probe ISPs (Nayatel, Z-Com, Cybernet, Nova,
   Fasttel, Orbit, NTC, TES), the hegemony of **PTCL (AS17557)** and **TWA (AS38193)** over them,
   per day. A reroute would appear as one operator's curve dipping while the other's rises.
2. **The operators' own upstreams:** for origins PTCL and TWA themselves, the hegemony of their
   foreign upstreams (Cogent, Level3, Omantel, Sparkle, Telstra, …) per day. **This is where a
   cable fault should show first** — SMW5 capacity loss changing which upstreams carry TWA's
   routes.

Interpretation rules carry over from Exp 09: hegemony counts **paths, not traffic** (so congestion
with unchanged routing is *invisible* here — exactly why a flat result complements Exp 06's
congestion finding rather than contradicting it); IPv4; BGP-visible links only.

## How

`hegemony_timeseries.py` — same IHR API as Exp 09 (`hegemony/` endpoint, both `timebin` bounds
required, **and each query's range must be < 7 days** — the window is fetched in 6-day chunks;
a longer range returns HTTP 400 "timebin range too large"). Paged, cached per-origin, resumable;
failed pulls are never cached. Bins are sub-daily; we keep all bins ≥ 0.02 hegemony and
**downsample to daily means**.

```bash
cd experiments/06.1_submarine_hegemony
python hegemony_timeseries.py            # pull + CSV + figure
```

## Outputs

- `results/hegemony_timeseries.csv` — (date, origin, transit, hegemony) daily.
- `results/fig_hegemony_smw5.png` — per-origin curves, fault date marked; top panel = probe ISPs'
  PTCL/TWA dependency, bottom = the operators' upstream mix.
- Verdict paragraph here + cross-links into `findings/06_submarine_outage.md`.

## Robustness programme → Experiment 6.1.1

The caveats above are being closed systematically in **Exp 6.1.1**
(`../06.1.1_smw5_robustness/`): churn-anomaly baseline (15 May–10 Jul), population-scale
downstream scan (all PK origins), placebo operators, independent fault-onset clocks (PK anchor
builtins, IODA, Cloudflare Radar), and APNIC user-weighting. Its results replace the
corresponding caveats here as they land.

## Future work — enabled by the physical-layer mapping (with the exact asks)

The four analyses below all hinge on data we must request (route: Nowmay Opalinski — his
AINTEC'24 interviews were with the PTCL/TWA IP-gateway engineers who operate this exact layer —
cc Dr Saqib + Dr Zartash).

### The EXACT asks (email checklist)

1. **Router/node coordinates** of the fibre map in the AINTEC'24 paper (Appendix A): lat/long per
   node, any format (CSV/KML/shapefile/GeoJSON — even the plotting script's input file).
2. **Fibre segment geometries or lengths** for the same map: per segment, endpoints + route
   geometry or at least km length.
3. **Their submarine cable-cut compilation 2002–2022** (footnote 1 of the paper: compiled from
   PTA/PTCL/TWA public declarations) — dates, cable, duration if recorded.
4. **Carrier-interconnect → cable mapping** (the missing layer; even partial/coarse/anonymised
   helps): for each of PTCL's and TWA's major international interconnects — carrier name, far-end
   PoP city, which cable system(s) the capacity rides, and (if shareable) approximate capacity.
   Format example we'd ask for:
   `TWA <-> Cogent | far end: Marseille | rides: SMW5 | ~2x100G`
   If lease-level detail is not shareable, a coarse version ("TWA's Cogent and Sparkle capacity
   is predominantly on SMW5; Hurricane via TW1/Fujairah") already unlocks analyses 1–2 below.

### The four analyses the mapping unlocks

1. **Fault attribution: inference → verification (upgrades this experiment).** Join the mapping
   to the Leg-2 table: if the interconnects that collapsed on 2 Jul (Cogent 16%→4%, Sparkle
   8.5%→4.7%) are the ones riding SMW5, and the one that surged (Hurricane 2%→20.5%) rides other
   capacity, the causal story is verified, not inferred. Method: one join + a per-carrier
   consistency check.
2. **A quantified single-point-of-failure map of Pakistan's international connectivity.** For
   each cable system: sum the hegemony shares of all interconnects riding it → *"a fault on cable
   X strands interconnects carrying Y% of the world's paths to Pakistan"*. Combine with the
   Exp 09 rollup (who depends on which operator) to get per-ISP and country-level exposure. This
   is the resilience deliverable in its strongest, most citable form — and directly extends the
   AINTEC'24 paper's qualitative vulnerability argument with numbers.
3. **What-if latency arithmetic (deliverable #2).** With segment lengths: compute the physical
   fibre km of counterfactual paths — e.g. WorldCall → PKIX Lahore → Nayatel → local CDN PoP —
   and convert to ms (km ÷ 102 each way). Compare against our measured detour RTTs from
   Exp 04/07: *"peering at PKIX would cut this path from measured X ms to computed Y ms"*. Turns
   the peering recommendation into engineering arithmetic.
4. **A falsifiable validation loop.** Any claimed mapping must *predict* which carriers dipped on
   2 Jul (our Leg-2 shifts are the test set it didn't see). Passing that test validates the
   mapping; the validated mapping then makes analysis 2's predictions trustworthy — and every
   future cable fault becomes a fresh test.

**Graceful degradation:** if only asks 1–2 are answered, analysis 3 proceeds (terrestrial
what-ifs) and 1–2 wait; if only coarse ask 4, analyses 1–2 proceed at cable granularity. Nothing
is blocked entirely by a partial response.

## Relationship to other experiments

- **Exp 06:** supplies the missing control-plane view of the same event; whatever the outcome, it
  goes into the outage finding as "logical dependencies did/did not move."
- **Exp 09:** same metric and API; 09 is the *static* structure (who depends on whom), 6.1 is its
  *dynamics under stress*. (This was RQ3 in Exp 09's notes; it now lives here.)
- **Exp 07:** the panel's window (11–18 Jul) is after the fault; if hegemony shows any residual
  shift into that window, it informs the panel's baseline interpretation.
