# Experiment 09 — AS Hegemony: quantifying the PTCL/Transworld duopoly from global BGP data

**Author:** Rayan Atif · **Status:** ✅ RQ1 + RQ2 complete (first pull 2026-07-17). RQ3 (SMW5
time series) **moved to its own experiment: Exp 6.1** (`experiments/06.1_submarine_hegemony/`)

## Results (pull of 2026-07-17)

**RQ1 — the duopoly, quantified.** Of **455** ASNs registered to Pakistan, **291** announce
prefixes visibly in global BGP. Among those:
- **261/291 = 89.7%** have PTCL or Transworld hegemony **≥ 0.5** (the majority of their AS paths
  traverse one of the two operators);
- **268/291 = 92.1%** at the ≥ 0.1 (material-dependency) threshold;
- **median hegemony across PK origins: Transworld 0.50, PTCL 0.17** — notably, *Transworld* is
  the majority-dependency operator for more networks than PTCL (consistent with Exp 4.1, where
  TWA ≈ PTCL in hand-offs abroad).
- Output: `results/pk_hegemony_rollup.csv` (per-AS: hege_ptcl, hege_twa, top dependency).

Paper-ready sentence: *"Control-plane analysis using AS Hegemony shows that ~90% of Pakistani
origin networks visible in global BGP depend on AS17557 or AS38193 for the majority of their AS
paths (median hegemony 0.17 and 0.50) — the duopoly is a measured property of global routing, not
only of our vantage points."*

**RQ2 — cross-validation against our probes.** Global BGP agrees with our traceroute findings
per-ISP (`results/probe_isp_deps.csv`):

| ISP (probe) | Hegemony (global BGP) | Our data-plane finding |
|---|---|---|
| **Orbit** | **TWA = 1.00** (total dependency) | worst domestic performer (ratio 11.9×) |
| Nayatel | PTCL 0.68, TWA 0.32, **Cogent 0.17** | most independent; uses the in-PK Cogent PoP |
| NTC | PTCL 0.69, TWA 0.31, Omantel 0.21 | (state operator; dual-homed) |
| Fasttel | PTCL 0.71, TWA 0.29 | fully dependent |
| PTCL / TWA | only small foreign upstreams (Cogent, Level3, Omantel) | top of the hierarchy |

Two independent datasets (our 16 probes' data plane vs. the world's BGP control plane) tell the
same story — the validation RQ2 sought.

**Notes / caveats recorded:** hegemony counts *paths*, not traffic; IPv4 only; 164 registered
ASNs are BGP-invisible (unused registrations — excluded, stated); unannounced private links are
invisible to BGP, so scores are a *lower bound* on dependency. API quirk for reproducibility:
the IHR endpoint requires **both** `timebin__gte` and `timebin__lte`, and rejects a `format`
param.

## Why this experiment

Our central structural claim — *"PTCL (AS17557) and Transworld (AS38193) are the gatekeepers of
Pakistan's Internet; nearly every other network depends on them for transit"* — currently rests on
three legs:

1. **Licensing facts** (only two international gateway licences) — institutional, not measured.
2. **Our own traceroutes** (Exp 01/03/07: downstream ISPs route ~100% of paths via an LDI operator;
   Nayatel ~40%) — measured, but from **our** 16 vantage points only; a reviewer can ask whether
   the picture generalises beyond the probes we happen to have.
3. **The AINTEC 2024 paper's BGP graph** (Opalinski, Uzmi, Douzet) — global BGP data, but their
   centrality metric is **betweenness**, which the authors themselves caveat as unreliable at
   scale, and their graph is a single January-2023 snapshot.

**AS Hegemony closes the gap.** It is a peer-reviewed centrality metric (Fontugne, Shah, Aben —
IIJ, SIGCOMM Posters 2017; the same reference [12] the AINTEC paper cites) that is:
- computed from **global BGP data** (RouteViews + RIPE RIS, hundreds of collectors) — independent
  of our probes entirely;
- **robust by design** — it trims biased viewpoints before averaging, fixing exactly the
  known weakness of betweenness on BGP data;
- **continuously computed and archived** by IIJ's Internet Health Report (IHR), so we get both
  current values and **history** (including the SMW5 outage window) via a free public API.

One sentence this experiment buys for the paper:
> *"Across all Pakistani origin ASes, X% depend on AS17557 or AS38193 for the majority of their
> BGP paths (median hegemony Y) — a globally-observed confirmation of the transit duopoly."*

## What AS Hegemony is (the metric, precisely)

For an origin network *O* and a candidate middleman *T*, the **local hegemony** of *T* over *O* is
the (viewpoint-trimmed) average fraction of AS paths toward *O* that traverse *T*:

- **1.0** — every path to *O* crosses *T*: total dependency, a chokepoint.
- **0.0** — no path crosses *T*: irrelevant to *O*.
- The origin's own score over itself is 1 by definition (excluded from analysis).

Two views are used here:
- **Per-origin ("local") hegemony:** for one Pakistani AS, the ranked list of the transit networks
  it depends on, with scores. This is the unit of measurement.
- **Country roll-up:** aggregate the per-origin results over *all* Pakistani ASes → what fraction
  of the country's networks have PTCL/TWA above a dependency threshold. (IHR also publishes a
  precomputed per-country hegemony; we record it as a cross-check but compute our own roll-up so
  the thresholding is explicit.)

## Research questions

- **RQ1 (the duopoly, quantified):** What fraction of Pakistani origin ASes have hegemony ≥ 0.5
  (majority of paths) — and ≥ 0.1 (material dependency) — for AS17557 or AS38193? What is the
  median hegemony of each operator across PK origins?
- **RQ2 (cross-validation of our probe ISPs):** Do the hegemony scores of our nine probe ISPs
  match the transit-dependency ranking we measured by traceroute (Nayatel most independent;
  Z-Com/Nova ~fully dependent)? Agreement = independent validation of both datasets.
- **RQ3 (dynamics, ties into Exp 06):** did dependencies shift during the SMW5 fault?
  **→ Spun out as Experiment 6.1** (`experiments/06.1_submarine_hegemony/`), which extends Exp 06
  with this control-plane time series.

## How (method)

**Data source:** IHR public API (`https://ihr.iijlab.net/ihr/api/`), endpoint `hegemony/` with
`originasn=<AS>`, `af=4`, and a recent `timebin` range; we take the latest available bin per
origin. No API key; free; results cached to disk so re-runs cost nothing.

**Enumerate Pakistani origin ASes:** RIPEstat `country-resource-list` for `PK` (~220+ ASNs, the
same universe as the AINTEC paper's 223).

**Pipeline (all in `hegemony.py`):**
1. `deps <asn…>` — per-origin dependency table for named ASes (default: our nine probe ISPs +
   the two operators). Output: ranked transit list with hegemony scores per origin.
2. `rollup` — loop over every PK origin AS; record each origin's hegemony for AS17557, AS38193,
   and its top foreign dependency. Output: `results/pk_hegemony_rollup.csv` + printed summary
   (the RQ1 percentages, at both thresholds, plus medians).
3. *(RQ3 time series → now Exp 6.1's `hegemony_timeseries.py`.)*

**Interpretation rules (stated up front):**
- Hegemony measures **BGP path traversal**, not traffic volume — a score of 0.6 means 60% of
  *paths*, not bytes. We say "paths" in every claim.
- Scores are per-AF; we use **IPv4** (`af=4`) to match all our measurements.
- A PK origin with low PTCL/TWA hegemony is not necessarily "independent" — it may simply be
  served via a foreign parent (e.g., a multinational's PK ASN). The rollup CSV keeps each
  origin's top dependency so these cases are visible, not hidden.
- IHR data is computed from public BGP; private/unannounced backbone links (e.g. Transworld's
  unannounced 110.93.x infrastructure, Exp 04) are invisible to it — hegemony therefore gives a
  **lower bound** on dependency, which strengthens rather than weakens the claim when scores are
  high anyway.

## Outputs

- `results/probe_isp_deps.csv` — per-origin ranked dependencies for our probe ISPs (RQ2).
- `results/pk_hegemony_rollup.csv` — one row per PK origin AS: hegemony(17557), hegemony(38193),
  top dependency ASN/name/score (RQ1).
- Summary numbers printed + copied into `findings/` when the pull completes.
- *(RQ3 outputs live in Exp 6.1.)*

## Relationship to other experiments

- **Validates Exp 01/03's transit-dependency finding** from an independent, global dataset (RQ2).
- **Feeds the paper's Introduction/Background** — replaces the qualitative "route server absent /
  duopoly" claims with a robust, citable number (Fontugne et al. metric, IHR data).
- **Extends Exp 06** — RQ3 asks whether the cable fault moved logical dependencies at all
  (our data showed physical-path load-balancing but no transit change; hegemony can confirm this
  at the BGP level).
- **Complements Exp 07** — Exp 07 measures the *performance cost* of the structure; Exp 09
  measures the *structure itself*, from outside our own vantage points.

## How to run

```bash
cd experiments/09_as_hegemony
python hegemony.py deps            # our probe ISPs + the two operators (fast, ~a dozen queries)
python hegemony.py rollup          # all PK origin ASes (~220 queries, cached; a few minutes)
```
Both commands are resumable (per-AS cache in `.cache_hegemony.json`); re-running only fetches
what is missing.
