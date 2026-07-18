# Experiment 6.1.1 — Robustness of the SMW5 control-plane findings (filling 6.1's caveats)

**Author:** Rayan Atif · **Status:** set up 2026-07-18; W3a + W4 running (background)
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
| **W3a** | "coincident, not caused" — no churn baseline | pull the operators' full upstream series **15 May – 10 Jul**; day-over-day churn distribution; report the percentile/z-score of the fault days | **running** |
| **W4** | Fasttel = single-ISP anecdote; "frozen" claim from 8 ISPs | scan **all BGP-visible PK origins** (fault window ± baseline): count who switched majority gate → *"K of N networks moved"* | **running** |
| W3b | same, second leg | placebo controls: same churn metric, same dates, on comparable operators *not* behind SMW5 (e.g. Omantel AS8529, SLT AS9329) — their 2 Jul should be flat | planned (next) |
| W5 | fault-predates-announcement is an inference | independent onset clocks: RIPE Atlas **anchor builtin measurements** from PK anchors (7613, 7764) for 28 Jun–3 Jul; cross-check IODA + Cloudflare Radar PK | planned |
| W1 | hegemony counts paths, not traffic | reweight the frozen-downstream result by **APNIC Labs per-AS user estimates** (aspop) → "networks serving X% of Pakistani *users* saw no change" | planned |
| W2 | IHR archive gaps on 2–3 Jul (45/96, 23/96 bins) | independent hourly recomputation from raw RIPE RIS data (BGPlay/pybgpstream) for the operators' main prefixes | deferred (most engineering, least narrative gain — the observed swings dwarf the gaps) |
| W6 | no carrier↔cable mapping | external — the Nowmay email (asks itemised in Exp 6.1 notes) | blocked on reply |

Residual limits stated up front: W1 can never recover true *traffic* (only operator NetFlow has
bytes), and W3 can reach "statistically anomalous + Pakistan-specific," not laboratory proof —
that is the accepted standard for event attribution in measurement papers.

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

**Verdict — the magnitude claim is downgraded; the pattern claim carries the attribution:**
- ❌ *"3–10× normal churn"* does not survive: churn of fault-day size occurs occasionally
  (late May was larger). Removed from 6.1's claims.
- ✅ What survives and was always stronger: the **fingerprint** — both operators swinging onto the
  *same* substitute carrier (Hurricane) on the *same* two days, Cogent collapsing and recovering
  within 48 h, synchronized with an independently documented physical fault. For TWA the fault day
  is still top-5% of the period (z=+1.8); for PTCL the churn is within its noisy norm, so PTCL-side
  claims rest on the Hurricane appearance (0→14.2%) specifically, not on total churn.
- 6.1's notes and `findings/06.1_submarine_hegemony.md` amended accordingly.

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
```
Both resumable (`.cache_*.json`); non-200 responses fail loudly; nothing partial is cached.

## Outputs feed back into

- Exp 6.1's notes + `findings/06.1_submarine_hegemony.md` (caveats replaced by results),
- the paper's SMW5 subsection (Route-B plan): the frozen-downstream claim at population scale and
  the churn spike with an anomaly statistic.
