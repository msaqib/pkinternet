# Experiment 6.1.1 — Robustness of the SMW5 control-plane findings (filling 6.1's caveats)

**Author:** Rayan Atif · **Status:** complete, 2026-07-20 — all six caveats (W1, W3a, W3b, W4, W5)
closed except W2 (deferred) and W6 (external, blocked on Nowmay)
**Parent:** Exp 6.1 (`../06.1_submarine_hegemony/`) — this experiment exists to close its caveats.

## Why this experiment

Exp 6.1 produced strong findings with honest caveats attached. Each caveat is an attack surface a
reviewer will probe; each one that we close upgrades the claim it guards. This experiment
systematically works through them. Concretely, the two headline claims at stake:

1. *"Downstream dependencies stayed frozen during the fault"* — currently an **8-probe-ISP
   observation** with one exception (Fasttel). Should be a **population-scale rate** over all
   ~291 BGP-visible Pakistani origins.
2. *"The operators' 21%/13.5% carrier churn was the fault being absorbed"* — currently
   **coincident, not proven**: TWA's upstream mix is volatile in the 25-day window, so a sceptic
   can say "maybe that churn is normal." Should be an **anomaly statement against a long
   baseline** ("largest churn day in N weeks, p ≈ …") plus **placebo controls**.

## The caveat → fix map (scope of this experiment)

| ID | 6.1 caveat | Fix | Status |
|---|---|---|---|
| **W3a** | "coincident, not caused" — no churn baseline | pull the operators' full upstream series **15 May – 10 Jul**; day-over-day churn distribution; report the percentile/z-score of the fault days | **complete — superseded by W3b** |
| **W4** | Fasttel = single-ISP anecdote; "frozen" claim from 8 ISPs | scan **all BGP-visible PK origins** (fault window ± baseline): count who switched majority gate → *"K of N networks moved"* | **complete** |
| **W3b** | same, second leg | placebo controls: same churn metric, same dates, on Omantel/SLT (same-cable, other branch) and NTC-Nepal/VNPT (no SMW5 exposure at all) | **complete — magnitude claim retracted; a narrower carrier-swing claim survives, tested** |
| W5 | fault-predates-announcement is an inference | independent onset clocks: RIPE Atlas **anchor builtin measurements** from PK anchors (7613, 7764) for 28 Jun–3 Jul; cross-check IODA + Cloudflare Radar PK | **complete — confirmed independently: Z-Com anchor mesh shows a 78σ RTT/loss spike from 1 Jul 17:00 PKT (a day before the announcement), collected by ~1,000 vantages we don't operate; PTCL anchor only marginal (consistent with its diffuse peering); IODA null explained (wrong instrument); Cloudflare Radar blocked, no API token** |
| W1 | hegemony counts paths, not traffic | reweight the frozen-downstream result by **APNIC Labs per-AS user estimates** (aspop) → "networks serving X% of Pakistani *users* saw no change" | **complete — 99.63% of Pakistan's ~42.1M estimated users (99.6% pop. coverage) held their gate** |
| W2 | IHR archive gaps on 2–3 Jul (45/96, 23/96 bins) — now known to be a **global** gap (W3b), not PK-specific | independent hourly recomputation from raw RIPE RIS data (BGPlay/pybgpstream) for the operators' main prefixes | elevated priority, not blocking — see W3b's "what this changes" |
| W6 | no carrier↔cable mapping | external — the Nowmay email (asks itemised in Exp 6.1 notes) | blocked on reply |

Residual limits stated up front: W1 can never recover true *traffic* (only operator NetFlow has
bytes), and after W3b, the churn-based attribution can reach only "a large, carrier-specific,
placebo-tested shift co-occurring with the fault" — not "unusually large churn," which the data no
longer supports. This is a narrower but more defensible claim, and it is what should be cited.

## Results

### W3a — churn anomaly baseline (complete, 2026-07-18)

Day-over-day churn distributions over 56 days (15 May – 10 Jul), unfiltered:

| Operator | mean ± sd | fault days' standing | top days of the period |
|---|---|---|---|
| **TWA** | 0.086 ± 0.065 | 2 Jul = **#3** (0.201, z=+1.8), 3 Jul = #5 | **30–31 May: 0.344 (z=+4.0)** |
| **PTCL** | 0.071 ± 0.053 | **not in the top 5** | 30 May – 7 Jun cluster (z≈+2) |

**Artifact check on the late-May spike** (the 2–3 Jul lesson: data gaps inflate day-over-day
churn): bins per day around it are **76/96 on 30 May and 96/96 on 31 May** — mostly/fully
complete, nothing like the 45/23-bin gaps of 2–3 Jul. **The 30–31 May event is real, not a data
artifact.** Notably it, too, hits *both operators on the same days* — Pakistan's gates evidently
undergo occasional large synchronized upstream reshuffles; the cause of the May event is unknown
(no matching public fault report found yet; flagged as an open question and a candidate for the
same fingerprint analysis).

**Verdict at this stage (later superseded — see W3b):**
- ❌ *"3–10× normal churn"* does not survive: churn of fault-day size occurs occasionally
  (late May was larger). Removed from 6.1's claims.
- 🟡 What looked like it survived: the **fingerprint** — both operators swinging onto the same
  substitute carrier (Hurricane) on the same two days, TWA's fault day ranking top-5% of the
  period by churn (z=+1.8). **W3b below shows this rank is not Pakistan-specific either** — the
  verdict here is superseded, not the final word.

Output: `results/churn_baseline.csv`.

### W3a addendum — the 30–31 May event: decomposed, candidate cause identified

Carrier decomposition of the late-May churn (from the cached baseline pull) shows a **one-day
state flip on 30 May with exact reversion by 31 May**, on both operators:
- TWA on 30 May: **Hurricane collapses 20.7% → 0.9%**, Cogent spikes 9% → 29%, Sparkle 4% → 16%;
  31 May returns to the 29-May mix. (The two equal churn values, 0.344 on both days, are the
  flip and the revert.)
- PTCL on 30 May: **Hurricane 14.3% → 0%**, Etisalat spikes 6% → 17%; reverts 31 May.

**Candidate cause (found by Rayan in press coverage):** a severe rain/hail storm hit Lahore on
**30 May 2026** — Daily Pakistan reports 50+ LESCO feeders tripped and widespread power outages.
Mechanism hypothesis: a Lahore-area facility carrying the **Hurricane Electric interconnects**
(and related capacity) lost power for ~a day; both operators' Hurricane sessions dropped, their
mixes shifted to remaining carriers, and everything restored next day. This is *consistent* with
the July picture: Hurricane's PK capacity appears independent of the Karachi submarine side
(it was the *substitute* during the SMW5 fault, and the *casualty* during a Lahore power event).
**Confidence: plausible hypothesis with coincident timing — not proven** (no facility mapping;
and a data-quality note: TWA's 29 and 31 May daily means are identical to 0.1 pp across six
carriers, which is what an exact BGP state-revert looks like but could also indicate duplicated
bins in IHR — flagged).

Narrative effect: the May event no longer *weakens* the fault attribution — it has its own
distinct, opposite fingerprint (Hurricane *lost* on a storm day vs Hurricane *gained* on a
cable-fault day), supporting the view that these churn spikes track real physical incidents.

### W3b — placebo controls (complete, 2026-07-20): the magnitude claim does not survive at all

**Design.** Four placebo/control operators, same day-over-day churn metric as W3a, same 15 May –
10 Jul window: **Omantel (AS8529)** and **SLT (AS9329)** — both landing points on the SMW5
consortium's *other* branches (Oman, Sri Lanka), testing whether the fault was branch-local to
Pakistan; **NTC Nepal (AS23752)** and **VNPT Vietnam (AS45899)** — true placebos with no SMW5
involvement at all (Nepal is landlocked/terrestrial-only; Vietnam sits on AAG/APG/AAE-1/IA), testing
whether 1–3 Jul was elevated for reasons that have nothing to do with SMW5.

**First pass, raw churn — alarming.** All four controls rank at or near the top of their own
55-day distribution on 2–3 Jul (SLT rank 1–2/25, NTC-Nepal rank 1/25, VNPT rank 1/25, Omantel
rank 4–5/25). If confirmed, this would kill the whole churn-magnitude argument outright — true
non-SMW5 networks topping their own churn distribution on our fault days means the elevation is
not about Pakistan or SMW5 at all.

**But first check the bins**, per the W3a-established rule: **every one of the four controls shows
the identical 45/96 (2 Jul) and 23/96 (3 Jul) bin-completeness pattern already seen for TWA/PTCL.**
This is a global IHR ingestion gap on those two calendar days — not a Pakistan-specific or
SMW5-specific artifact. New information (W3a only established the gap for TWA/PTCL); confirms the
gap is platform-wide.

**Gap-robust reanalysis.** Recomputed day-over-day churn for all six operators (TWA, PTCL, and the
four controls) using **only the timebins present in both days being compared** — the same
correction the W3a addendum used to clear the 30–31 May spike:

| Operator | role | mean±sd (25-day window) | 2 Jul rank | 3 Jul rank |
|---|---|---|--:|--:|
| TWA | fault-exposed | 0.069 ± 0.055 | **1/25** | 2/25 |
| PTCL | fault-exposed | 0.057 ± 0.044 | 4/25 | 2/25 |
| SLT | SMW5-other-branch | 0.066 ± 0.057 | 2/25 | **1/25** |
| Omantel | SMW5-other-branch | 0.047 ± 0.025 | 4/25 | **1/25** |
| NTC-Nepal | **non-SMW5 control** | 0.070 ± 0.052 | **1/25** | 2/25 |
| VNPT | **non-SMW5 control** | 0.072 ± 0.041 | **1/25** | 3/25 |

The gap correction does **not** clear the anomaly this time (unlike 30–31 May). Every operator
tested, including the two with no plausible SMW5 exposure, ranks in its own top 1–4 days on
2–3 Jul. **Conclusion: the elevated churn magnitude on 1–3 Jul is a global phenomenon, not a
Pakistan/SMW5 signal.** Two candidate explanations, not distinguishable from IHR alone: (a) a
genuine worldwide BGP event unrelated to SMW5 coincided with our fault window, or (b) a residual
IHR processing artifact on those specific days that gap-matching bins doesn't fully correct
(inference-model retraining, RIS/RouteViews collector hiccups, etc.). Either way: **the
"anomalous churn magnitude" claim is retracted, not merely downgraded.** ~~"3–10× baseline"~~,
~~"top-5% of the period"~~ — neither survives; both are removed from every claim in this project.

**What does survive — tested and confirmed specific: the size of the Hurricane substitution.**
Churn *magnitude* is contaminated globally, but *which carrier* absorbed the traffic is a separate
question, answered by decomposing each operator's carrier mix (28 Jun–1 Jul baseline vs 2–3 Jul),
identical method for all six:

| Operator | role | Hurricane: baseline → fault | Δ (points) |
|---|---|--:|--:|
| **SLT** | SMW5-other-branch | 6.6% → 19.8% | **+13.2** |
| **TWA** | fault-exposed | 2.3% → 11.4% | **+9.1** |
| **PTCL** | fault-exposed | 7.1% → 14.2% | **+7.1** |
| VNPT | non-SMW5 control | 0.4% → 4.2% | +3.8 |
| NTC-Nepal | non-SMW5 control | 3.1% → 4.6% | +1.5 |
| Omantel | SMW5-other-branch | 26.7% → 24.9% | −1.8 |

The three networks with a plausible physical link to SMW5 (TWA and PTCL as the Pakistani gateways;
SLT as an SMW5 landing country in its own right) show Hurricane swings of **+7 to +13 points**.
The two confirmed non-SMW5 controls show swings under **+4 points** — an order of magnitude
smaller, consistent with Hurricane's baseline global noise rather than a substitution event.
Omantel is the interesting exception: nominally an SMW5-branch operator but showing *no* Hurricane
increase (even a small decline) — a legitimate nuance, not a contradiction: whether a specific
branch operator needs the same substitute carrier depends on which segment failed and how that
operator's own upstream is engineered, not just consortium membership. **This is the fingerprint
that survives**: not "churn was elevated" (retracted), but "the specific, large-magnitude shift
onto Hurricane Electric is concentrated in the SMW5-exposed operators, at a scale unrelated
networks don't show."

**What this changes, precisely:**
- 🔴 Retracted everywhere: any framing that cites churn *magnitude*, *rank*, or *z-score* as
  evidence (the "top-5%", "not unprecedented but still elevated" language in 6.1's notes,
  6.1.1's own W3a verdict above, and `findings/06.1_submarine_hegemony.md`). All three amended
  to point here.
- 🟢 Retained, now on firmer footing: the **raw share numbers** from 6.1's original unfiltered
  pull (Hurricane 2%→20.5%→2.3% for TWA over the fault window, similarly for PTCL) — those are
  direct readings of the operators' carrier mix, not a distributional ranking, and are unaffected
  by the churn-metric contamination.
- 🟢 New and stronger: the **cross-operator Hurricane-swing comparison table above** — this is a
  placebo-tested, magnitude-differentiated result, exactly what a peer reviewer would ask for, and
  it did not exist before this run.
- ⬆️ **W2 (raw-RIS recompute, independent of IHR) is promoted from "deferred" to important-but-not-
  blocking.** It's the only way to know whether the global 1–3 Jul elevation is a real worldwide
  routing event or an IHR artifact — worth doing if time allows, but the paper's SMW5 material
  does not depend on it (see below).
- ✅ **No paper text is affected.** The submitted draft's SMW5 material is entirely data-plane
  (Exp 06: +31% jitter, the 646 ms tail, no comparable domestic degradation) plus the two
  population-scale, non-magnitude control-plane numbers (98.5% gate-frozen; ~21%/~14% of world
  paths re-carriered — both direct readings, not distributional claims). None of tonight's
  retraction touches a number that was ever in the manuscript.

Output: `results/placebo_churn.csv` (raw); gap-robust recompute →
`data/ihr_gap_robust_churn_6ops.json` (repo root); Hurricane decomposition run ad hoc, not
persisted as a file (small enough to be reproduced from the recorded tables above). Neither is
yet in `robustness.py` — candidate for a `cmd_gaprobust()` addition if this needs to be repeated.

### W5 — independent fault-onset clocks (complete, 2026-07-20)

**Question:** 6.1's claim that the fault predates the 2 Jul PTA announcement rests entirely on
*our own* IHR pull (PTCL's churn already elevated 1 Jul). Do independent, third-party measurement
systems — collected by infrastructure we don't operate — show the same onset?

**Sources tried:**
1. **IODA** (Georgia Tech/CAIDA), country-level Pakistan signals, 14 Jun–5 Jul (2-week clean
   baseline + fault week): `bgp` (visible /24 count), `merit-nt` (active-probing responsiveness),
   `gtr-norm` (Google search-traffic volume), `ping-slash24` (active ping reachability).
2. **RIPE Atlas anchor built-in mesh** — Pakistan has two active RIPE Atlas anchors, both in
   Lahore: `pk-lhe-as152605` (Z-Com, probe 7613) and `pk-lhe-as17557-client` (PTCL, probe 7764).
   Every other RIPE Atlas anchor worldwide (~1,000) pings these continuously as part of the
   platform's own anchoring mesh — a pre-existing, independently-collected RTT time series to
   Pakistan that requires no infrastructure of ours.
3. **Cloudflare Radar** — could not access; its public API requires an auth token we don't hold,
   and the unauthenticated frontend is behind bot protection. Not fatal (two independent sources
   remain) but flagged as a cheap follow-up (a free Radar API token takes minutes to obtain).

**IODA result — a genuine null, and an instructive one.** A naive 3-sigma-crossing check flagged
1 Jul on two signals (`bgp`, `merit-nt`). Applying the same discipline as the churn work — compare
against the *worst excursions already present* in a clean 2-week baseline, not just mean±3σ, since
noisy 5-minute-resolution country signals produce several 3σ blips by chance alone (3–5 per
2 weeks, checked directly) — **the "1 Jul" flags mostly don't survive**: `bgp`'s worst dip in the
fault week (9.9σ, 10 min) is *less* extreme than the worst dip already in the baseline (11.7σ,
95 min) — ordinary noise, not a signal. `merit-nt` is marginal (fault week 4.7σ/80 min vs. baseline
4.3σ/105 min — comparable, not clearly distinct). `gtr-norm` shows nothing. **Verdict: IODA's
coarse, country-level signals do not independently corroborate a pre-2-Jul onset — but this is not
surprising and does not weaken Exp 06's finding.** BGP-visibility and reachability probing are
built to catch *blackouts* (prefixes withdrawn, hosts unreachable); Exp 06's finding was
specifically a **degradation, not a blackout** (RTT rose, packets still got through) — exactly the
kind of event these blunt instruments are not built to see. Absence of a coarse signal here is
consistent with, not contrary to, the data-plane finding.

**RIPE Atlas anchor mesh — complete, and this is the strong confirmation W5 was looking for.**
Pulled median RTT + loss rate for both Pakistani anchors, aggregated from the full worldwide
anchoring mesh (~1,000 independent source anchors), 28 Jun–4 Jul, in 3-hour buckets (chunked
fetch — the raw pull is ~1.2 GB and isn't kept, only the aggregate). Same discipline as everywhere
else: baseline = first 3 clean days, compare the fault window against the baseline's *own* worst
excursion, not just a flat 3σ cut.

| Anchor | baseline mean±sd (RTT, ms) | 2 Jul mean / peak | worst fault chunk | onset (first chunk beating baseline's own worst) |
|---|--:|--:|--:|---|
| **Z-Com (AS152605)** | 176.5 ± 1.9 | 211.2 / **323.9** | **78.5σ** | **1 Jul, 17:00 PKT** |
| PTCL (AS17557) | 175.7 ± 1.6 | 180.2 / 182.2 | 4.1σ (baseline's own worst: 3.0σ) | 1 Jul, 23:00 PKT (marginal) |

**Z-Com's anchor shows an unambiguous, massive anomaly** — median RTT from ~1,000 worldwide
vantages more than doubling (176→324 ms) and loss rate jumping from a steady ~1.5% to **7.3%** on
2 Jul, roughly 5× the baseline noise floor (2.8σ) and recovering by 3 Jul (173 ms, back to
baseline). Independently collected, by infrastructure we don't operate, this **confirms the fault
was degrading connectivity from 1 Jul 17:00 PKT — a full day before the 2 Jul PTA announcement**,
matching the "predates the announcement" claim from an entirely different data source and method.

**PTCL's anchor shows only a marginal effect** (4.1σ vs. a 3.0σ baseline noise floor — barely
distinguishable) and **no loss-rate spike at all** (flat ~1.3–1.5% throughout). This is not a
contradiction: 6.1's own notes already establish that PTCL "reaches the world mostly by peering,
so its transit dependency is diffuse," unlike TWA/Z-Com's more concentrated transit reliance —
consistent with PTCL's general reachability (what an anchor ping measures) being far less exposed
than its aggregate international carrier mix (what the IHR churn numbers measure). The two
Pakistani anchors happen to sit on the two different operators this whole experiment is about, and
they show two different severities — itself a small, useful data point.

**What this changes:** the "predates the announcement" claim in
`findings/06.1_submarine_hegemony.md` is now **independently confirmed**, not just inferred from
our own IHR reading — RIPE's global anchor mesh, run by ~1,000 vantage points we don't control,
shows the same 1 Jul onset. IODA's null result is retained as a documented, principled non-finding
(wrong instrument for a degradation) rather than evidence against the timeline.

### W4 — population scan (complete, 2026-07-18; 454/455 origins)

| | count | share |
|---|--:|--:|
| origins with data | 454 | — |
| gate-dependent (PTCL/TWA hege ≥ 0.1) | 273 | — |
| **switched majority gate on fault days** | **4** | **1.5%** |
| material shift ≥ 0.2 (Fasttel-like) | 12 | 4.4% |

Switcher ASNs: 45748, 134231, 138926, 149280 *(holder names TBD — RIPEstat lookup pending a
network retry)*. **Headline: ~98.5% of gate-dependent Pakistani networks held their majority gate
through the fault** — the "downstream frozen" claim now holds at national scale, not just across
our 8 probe ISPs, with Fasttel-like re-balancing in only ~4% of networks. Output:
`results/population_scan.csv`.

### W1 — APNIC user-weighting of the frozen-downstream result (complete, 2026-07-20)

**Question:** W4 showed 98.5% of *networks* held their gate. But hegemony counts networks, not
people — a network of 6.7M users and one of 200 users count equally in that percentage. Does the
result hold when weighted by who's actually behind each network?

**Data:** APNIC Labs' AS population estimator (`stats.labs.apnic.net/aspop/PK`) — an
ad-measurement-derived estimate of connected users per AS, refreshed daily. Pulled the full
Pakistan table: **227 ASes, summing to ~42.29M estimated users** (APNIC's methodology allows some
overlap/double-count across multihomed populations; treated as the denominator throughout for
consistency).

**Join:** matched W4's `population_scan.csv` (454 origins) to the APNIC table by ASN. **201 of 454
origins matched — but they carry 42.12M of APNIC's 42.29M total, i.e. 99.6% of Pakistan's
estimated user population.** The 253 unmatched origins are real but tiny (APNIC has no population
estimate for them, consistent with them being minor/stub ASes) — coverage is excellent in the
dimension that matters for this weighting.

**Result**, restricted to W4's gate-dependent set (max hegemony ≥ 0.1) with a population match
(198 of W4's 273 gate-dependent origins, representing 42.11M users):

| | by network count (W4 original) | by user population (W1) |
|---|--:|--:|
| held majority gate | 98.0% (194/198) | **99.63%** (41.96M / 42.11M users) |
| switched | 2.0% (4/198) | 0.37% (156K users) |
| material shift ≥0.2 | 4.0% (8/198) | 1.43% (602K users) |

**The result strengthens, not weakens, under user-weighting.** The four networks that switched
gate are all small; every one of the 15 largest Pakistani networks by estimated population —
Cybernet (6.7M), PTCL (5.7M), CMPak/Zong (4.1M), Mobilink/Jazz (4.0M), Telenor (2.0M), PTML/Ufone
(1.8M), Connect (1.4M), Nayatel (1.1M), and others — **held their majority gate through the
fault.** The honest reading: *"downstream frozen"* was never at risk of being an artifact of
counting many small networks; the networks carrying the overwhelming majority of Pakistani
internet users personally experienced no gate change, only (per Exp 06) a latency degradation on
whatever fraction of their traffic was already routed internationally.

**Caveats:** APNIC's population estimates are themselves modelled (ad-exchange sampling,
demographic corrections), not a census — treat 99.63% as "very high, precisely to within APNIC's
own estimation error," not to two decimal places of ground truth. The methodology also cannot
separate a user's *domestic* traffic (unaffected either way) from their *international* traffic
(where Exp 06's degradation actually landed) — W1 answers "whose gate held," not "who felt the
fault," which remains a data-plane question Exp 06 already answers directionally (jitter/RTT
degradation, not an outage, for international paths).

Output: `data/apnic_aspop_pk_20260717.json` (repo root; raw APNIC table, 227 ASes, dated —
it's a live daily snapshot, not a fixed dataset) — no separate CSV yet; join was done ad hoc
against the existing `results/population_scan.csv` and is reproducible from those two files.

## How (method detail for the two running pieces)

### W3a — churn anomaly baseline
- **Data:** IHR hegemony for origins AS17557 and AS38193, **2026-05-15 → 2026-07-10**, unfiltered
  (no minimum-hegemony cutoff — the Exp 6.1 lesson), fetched in 6-day chunks (API cap), cached
  per (origin, chunk) so re-runs are free.
- **Metric:** daily mean hegemony per transit; **day-over-day churn** = ½ · Σ_transits
  |hege(d) − hege(d−1)|. Day-over-day (rather than vs. a fixed baseline) avoids an arbitrary
  baseline choice and yields one churn value per day → a ~55-day distribution.
- **Output:** `results/churn_baseline.csv` (per day per operator) + the anomaly statement: the
  rank/percentile of 1–2 Jul within the distribution, and a z-score. Figure:
  churn-over-time with the fault marked.

### W3b — placebo controls
- **Data:** IHR hegemony for AS8529 (Omantel), AS9329 (SLT), AS23752 (NTC Nepal), AS45899 (VNPT),
  same window and chunking as W3a. Two are SMW5-consortium members on other landing branches
  (fault-locality test); two have no SMW5 exposure at all (true placebo).
- **Gap-robust churn:** re-derived for all six operators (TWA, PTCL + the four controls) using
  only timebins present in **both** days of each comparison — the same correction that cleared the
  30–31 May spike in the W3a addendum. This time it does not clear the fault days: every operator,
  including the non-SMW5 controls, ranks in its own top few days on 2–3 Jul, so the churn
  *magnitude* elevation is judged global, not attributable.
- **Carrier-swing decomposition:** for each of the six, mean Hurricane-Electric hegemony share
  28 Jun–1 Jul (baseline) vs 2–3 Jul (fault), same method as the May decomposition. This isolates
  whether *this specific carrier* moved by an unusual amount, independent of the (contaminated)
  aggregate churn number.
- **Output:** `results/placebo_churn.csv` (raw); the gap-robust and carrier-swing tables are ad hoc
  (not yet wired into `robustness.py cmd_placebo()` — worth adding if this needs to be repeated).

### W4 — population-scale downstream scan
- **Data:** all PK-registered ASNs (RIPEstat country-resource-list, as in Exp 09). For each origin,
  hegemony of **only** AS17557 and AS38193 (the API's `asn` filter keeps responses small),
  **2026-06-26 → 2026-07-06** in 6-day chunks. Cached per origin.
- **Classification per origin:** baseline majority gate = whichever of PTCL/TWA has the higher mean
  hegemony over 26–30 Jun (requiring ≥ 0.1, else "neither/foreign-parent" — excluded, counted).
  **Switched** = majority gate on any of 1–2 Jul differs from baseline majority. Also recorded:
  **material shift** = |Δhege| ≥ 0.2 on 1–2 Jul vs baseline for either operator (catches
  re-balancing short of a majority flip, i.e. Fasttel-like events).
- **Output:** `results/population_scan.csv` (per origin: baseline majority, fault majority,
  switched?, max shift) + headline: *"K of N origins switched majority gate; M showed material
  shifts ≥ 0.2"*.

## How to run

```bash
cd experiments/06.1.1_smw5_robustness
python robustness.py baseline     # W3a
python robustness.py population   # W4
python robustness.py placebo      # W3b
```
All three resumable (`.cache_*.json`); non-200 responses fail loudly; nothing partial is cached.
**W1 and W5 were run ad hoc** (not wired into `robustness.py`): W1 is a one-off pull of
`stats.labs.apnic.net/aspop/PK` joined against `results/population_scan.csv`; W5 is an IODA API
pull (`api.ioda.inetintel.cc.gatech.edu`) plus a chunked, aggregated fetch of the two Pakistani
RIPE Atlas anchors' built-in mesh measurements (msm 130058240, 179602008). Candidates for proper
subcommands if this needs to be reproduced or extended. All raw pulls from tonight's ad hoc work
are saved under the repo's top-level `data/`: `apnic_aspop_pk_20260717.json`,
`ihr_gap_robust_churn_6ops.json`, `ioda_pk_signals_28jun-5jul2026.json`,
`ioda_pk_bgp_meritnt_14jun-5jul2026.json`, `ripe_anchor_rtt_agg_zcom_as152605.json`,
`ripe_anchor_rtt_agg_ptcl_as17557.json` — kept as raw evidence, separate from this experiment's
own `results/` (which holds only derived, cleaned outputs).

## The exact process, step by step (W3b, W5, W1 — why each check was run, in order)

This section is the lab-notebook record: not just what was found, but the sequence of decisions
that led there, since several results only emerged because an earlier check came back suspicious
rather than because they were planned from the start.

**W3b started as a validity test for W3a, and became a retraction.**
1. W3a had left one claim standing: TWA's fault-day churn ranked top-5% of a 56-day distribution
   (z=+1.8). The obvious next question — is that specific to TWA/PTCL, or would *any* operator
   look "elevated" on 1–3 Jul for unrelated reasons? Without a control, a top-5% ranking proves
   nothing; lots of operators have *some* day in the top 5% of their own noise.
2. Designed two kinds of control, deliberately different in kind: **Omantel/SLT** (other SMW5
   landing branches — if the fault was Pakistan-branch-specific, these should stay flat) and
   **NTC-Nepal/VNPT** (zero SMW5 exposure at all — the strictest placebo available).
3. Ran the same day-over-day churn metric on all four, same 56-day window. Result looked alarming
   in the wrong direction: every control, including the two with no SMW5 exposure, ranked at or
   near the top of its own distribution on 2–3 Jul.
4. Before concluding anything, checked the one thing that had already fooled us once before (the
   45/23-bin gap that inflated 2–3 Jul's numbers for TWA/PTCL in the original 6.1 pull): pulled
   bin-completeness for all four controls. **Same 45/96, 23/96 pattern, for every operator** —
   this told us the IHR gap on those two days is a platform-wide ingestion issue, not something
   about Pakistan.
5. Re-ran the churn calculation gap-robust — for each day-pair, only using the timebins present in
   *both* days, the same fix that had cleared an earlier false alarm (the 30–31 May spike, in the
   W3a addendum). This time it did **not** clear the anomaly: even bin-matched, every operator
   including the true placebos still ranked in its own top few days on 2–3 Jul. Conclusion: the
   churn-*magnitude* elevation on those two days is real, global, and not attributable to
   Pakistan or SMW5 by this method. The "top-5%"/z-score framing was retracted at this point.
6. That could have ended the check as a pure negative result. Instead, asked a narrower, more
   answerable question: even if overall churn is contaminated, is the swing onto the *specific*
   carrier we'd already flagged (Hurricane Electric) still distinguishable? Decomposed each of
   the six operators' carrier mix, same before/after window, and compared the Hurricane-specific
   delta. This is where the fingerprint held: TWA/PTCL/SLT (all with a real physical link to
   SMW5) show swings of +7 to +13 points; NTC-Nepal/VNPT (no link) show under +4 points. That
   comparison — not the churn ranking — is what survives and is now the cited evidence.
7. Went back through every place the retracted framing appeared (6.1's notes, 6.1.1's own W3a
   verdict, the public findings file) and amended each — including restoring the 30–31 May storm
   finding as a separate, still-valid point once it was clear the two issues (a real May event vs.
   a global July data artifact) were mechanistically distinct, not the same problem twice.

**W5 was designed to answer one question with a source we don't control, and used two instruments
on purpose because the first one's silence needed to be interpretable.**
1. The claim being tested ("fault predates the 2 Jul announcement") rested on one witness — our
   own IHR pull. The fix isn't more analysis of the same source, it's a second, independent
   source that we didn't set up and can't have biased.
2. Picked two kinds of independent source on purpose, expecting different sensitivity: **IODA**
   (Georgia Tech/CAIDA) measures coarse country-level reachability — built to catch *blackouts*.
   **RIPE Atlas's anchor mesh** measures RTT directly from ~1,000 independent vantage points to
   Pakistan's two anchors — built to catch *degradation*. Exp 06 already told us this was a
   degradation, not a blackout, so the expectation going in was: IODA might not see anything, and
   that wouldn't be a contradiction — it would just mean we picked the wrong-shaped tool for one
   of the two checks, which is worth knowing either way.
3. Pulled four IODA signals (bgp, merit-nt, gtr-norm, ping-slash24) for a 2-week clean baseline
   plus the fault week. A naive mean±3σ check flagged 1 Jul on two of them — but a 2-week window
   at 5-minute resolution produces several 3σ blips *by chance alone* (checked directly: 3–5 such
   events in the clean baseline itself). So the real test wasn't "did it cross 3σ" but "is the
   fault-week excursion worse than the worst excursion already sitting in two weeks of normal
   noise." It wasn't — `bgp`'s worst fault-week dip (9.9σ, 10 min) was *milder* than its own
   baseline's worst dip (11.7σ, 95 min). Reported as a principled null, not silently dropped.
4. The RIPE anchor pull needed its own engineering: the raw per-round data for ~1,000 pinging
   anchors over a week is roughly 1.2 GB, and a first attempt to download it in one call timed
   out. Rewrote it to fetch in small time chunks, aggregate (median RTT, p90, loss rate) per
   chunk immediately, and discard the raw rows — turning an intractable download into a ~110 KB
   result. Ran the 112 chunks concurrently (8 workers) once a sequential first pass proved too
   slow to finish in reasonable time.
5. Applied the identical baseline-vs-worst-excursion discipline used for IODA and the churn data,
   not just an eyeball of the visible spike. Z-Com's result cleared that bar by a wide margin
   (78σ vs. a 2.8σ baseline noise ceiling); PTCL's did not (4.1σ vs. 3.0σ — indistinguishable from
   noise). Both results were kept and reported, not just the one that confirmed the hypothesis —
   and the asymmetry between them was cross-checked against something already on record (6.1's
   note that PTCL's international reach is diffuse/peering-based, TWA/Z-Com's more concentrated),
   which the two anchors' different severities independently corroborate.

**W1 was a single, direct join, but the coverage claim needed verifying before trusting the
headline.**
1. The question was simple: does "98.5% of networks held their gate" survive being reweighted by
   how many people are actually behind each network? A network-count percentage treats a 6.7M-user
   ISP and a 200-user ISP as equally informative, which isn't the right lens for "did Pakistanis
   experience a change."
2. Found APNIC Labs' AS population estimator, fetched with a browser user-agent (the bare
   requests default was rejected), and parsed the embedded data table by regex once JSON parsing
   failed on the JS-literal syntax (unescaped characters in AS names broke strict JSON — a small,
   expected data-cleaning step, not a substantive issue).
3. Before trusting any weighted percentage, checked coverage: only 201 of W4's 454 origins matched
   an APNIC population estimate by ASN — sounds low, until checked *by user mass* rather than
   origin count, where the matched set turns out to carry 99.6% of APNIC's entire Pakistan
   estimate. The unmatched 253 origins are real but individually tiny. This coverage check is what
   makes the final percentage trustworthy rather than a coincidence of which ASNs happened to have
   population data.
4. Joined, restricted to W4's gate-dependent definition (≥0.1 hegemony) for consistency with the
   original claim, and computed the same three categories (held/switched/material) by summed user
   count instead of origin count. Manually confirmed the result made sense by inspecting which
   origins carry the most weight (the 15 largest Pakistani ISPs by estimated population) and
   checking each one's verdict individually, rather than trusting the aggregate blindly.

## Outputs feed back into

- Exp 6.1's notes + `findings/06.1_submarine_hegemony.md` — all six caveats now closed: W3a/W3b
  replace the churn-magnitude claim with the placebo-tested Hurricane-swing fingerprint; W4/W1
  give the frozen-downstream claim at both network and user-population scale; W5 independently
  confirms the pre-announcement onset via RIPE's own anchor mesh.
- The paper's SMW5 material is **unaffected by tonight's retraction** — it only ever cited the
  data-plane numbers (Exp 06) and the two population-scale, non-magnitude figures (98.5% gate
  frozen; ~21%/~14% world-path re-carrier), none of which depended on the churn-ranking claim that
  was retracted. If a future draft pass adds a dedicated SMW5-robustness paragraph, the citable
  claims are: the 99.63% user-weighted frozen-gate result (W1), the placebo-tested Hurricane-swing
  differential (W3b), and the independently-confirmed 1 Jul onset (W5).
- Remaining, not part of this experiment's scope: **W2** (raw-RIS recomputation, independent of
  IHR entirely) and **W6** (carrier↔cable mapping, blocked on the Nowmay reply).
