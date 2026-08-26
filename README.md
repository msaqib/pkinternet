# Assessing Local Interconnectivity Resilience in Pakistan

A network measurement research project studying Pakistani internet infrastructure
using RIPE Atlas probes. 

The study uses traceroutes launched from Pakistani RIPE Atlas probes to determine:
- Where Pakistani websites are physically hosted (in-country vs abroad)
- How traffic is routed across Pakistani ISPs
- Whether traffic transits Pakistan's internet exchange point (PKIX) or exits the country unnecessarily

## Repository structure — where to find what

**Start here if you want the results:** `extra/FINDINGS.md` → `extra/EVIDENCE.tsv` → the
experiment's `notes.md`. See [Claims to evidence](#claims-to-evidence) below.

**Start here if you want to run something:** `scripts/measurement/pk_multi_probe.py` (the main
measurement script) or a specific `experiments/NN_*/` folder — each has its own `notes.md` runbook.

**Start here for standing context** (conventions, ASNs, known measurement artifacts, what's
already been established): [`experiments/01_website_destinations/METHODOLOGY.md`](experiments/01_website_destinations/METHODOLOGY.md).
Other docs in this repo cite it rather than restating it.

```
extra/                 FINDINGS.md, EVIDENCE.tsv, CV-BULLETS.md — the claims-to-evidence trail
findings/              Per-experiment analysis writeups + the charts notebook
experiments/           One subfolder per experiment: notes.md, scripts, results/
scripts/measurement/   Core measurement scripts (pk_multi_probe, geo_utils, format_routes)
data/                  Canonical input files: website list, ISP/FLL list, CDN targets, etc.
site_collection/       Tranco-based site sampling that produced the Exp 07/paper candidate pool
  pipeline/               The live scripts + their outputs (still read by other code)
  archive/                Superseded/abandoned/one-off scripts, kept for the record only
paper/                  The paper: running_draft.tex, references.bib, figures/, scripts/
tools/probe_status/     Flask dashboard for probe roster vs live RIPE Atlas status
Related work/           Reference papers (PDFs) informing the related-work section
```

Every directory below `experiments/` and `site_collection/pipeline/` is load-bearing — something
else in the repo reads from it. Everything under `*/archive/` is historical only; nothing imports
or reads from it.

## The paper

The write-up lives in `paper/`.

| File | What it is |
|---|---|
| **`paper/running_draft.tex`** | **The live paper.** Single source of truth. `acmart`, `sigconf`, anonymous. |
| `paper/references.bib` | Bibliography. Must stay directly in `paper/` — `\bibliography{references}` resolves relative to the `.tex` file. |
| `paper/figures/` | Every figure the paper includes. |
| `paper/scripts/make_*.py` | The scripts that regenerate those figures from the experiment outputs. Nothing in `figures/` is hand-drawn. |
| `paper/tab_sample.tex` | Generated sample table, produced by `scripts/make_sample_table.py`. |
| `paper/paper_draft.tex` | Earlier standalone draft. Not the live paper, kept for reference. |
| `paper/supplementary/` | Supplementary notes referenced by the paper (probe data quality, cable-cut background). |
| `paper/archive/` | Superseded drafts and working notes. Local-only, **not** tracked (see `.gitignore`). |

### Claims to evidence

Every reported number is traceable without re-running a measurement:

- **`extra/FINDINGS.md`** — the findings, grouped by theme, each with its key numbers, the
  experiment that produced them, and its caveats and failure modes.
- **`extra/EVIDENCE.tsv`** — one row per claim, resolving to the analysis file or paper section
  that backs it.
- **`extra/CV-BULLETS.md`** — the same findings condensed into CV/resume bullets, each one
  citing back to `EVIDENCE.tsv`.

Start at `extra/FINDINGS.md`, follow the experiment reference into `experiments/NN_*/`, and the
per-experiment `notes.md` explains what was run and what came out.

## Reproducing

```bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scriptsctivate
pip install -r requirements.txt
```

Python 3.10+. Measurement scripts need a RIPE Atlas API key in `.env` as `ATLAS_API_KEY`
(`.env` is gitignored — never commit it). Analysis and figure regeneration need no key;
the experiment outputs are committed.

`pybgpstream` is **not** installed by default: it needs the `libbgpstream` C library and
will not build from pip alone. Only the BGP experiments (05, 09) import it.

Large regenerable artefacts — raw RIPE archives, geolocation caches — are deliberately
gitignored and re-fetchable; see `.gitignore` for what and why.

## Experiments

- [01 — Website Destinations](experiments/01_website_destinations/notes.md):
  Traceroutes to Pakistani websites to determine hosting location and routing.
  Per-run outputs (grouped/summary CSV + readable routes), a full
  [batch inventory](experiments/01_website_destinations/batch_inventory.md), and a
  [website list](experiments/01_website_destinations/website_list.md).
- [1.1 — DNS Resolution](experiments/01.1_dns_resolution/notes.md):
  Per-ISP DNS lookups to find sites that resolve differently per ISP (GeoDNS).
  ~8% of sites differ; refines Exp 01's central-resolution shortcut.
- [1.2 — CDN Presence](experiments/01.2_cdn_presence/notes.md):
  Pings major content services (Netflix, Google, Meta, ...) per ISP to detect
  caches served from inside Pakistan.
- [1.4 — PK100 Website Hosting Census](experiments/01.4_pk100_hosting/notes.md):
  Classifies the top-100 Pakistani sites as CDN / Abroad / Pakistan (with the hosting
  ISP), and traceroutes from Transworld to check where PK-hosted sites hairpin.
- [02 — ISP Classification](experiments/02_isp_classification/notes.md):
  Classifying ISPs into PKIX Sets 1/2/3, with the roster, probe coverage, and the
  ~21-probe deployment plan (in progress).
- [03 — Longitudinal Routing](experiments/03_longitudinal_routing/notes.md):
  Re-traces the same sites every 15 min over days to add the time axis (path/RTT
  change, diurnal cycle, outages).
- [04 — Path Tromboning](experiments/04_path_tromboning/notes.md):
  Systematically detecting domestic traffic that hairpins abroad across an ISP's
  whole address space, via prefix-based target selection (TASS-adapted) and paced
  `tcptraceroute` (planning).
- [4.1 — Small-ISP Tromboning Census](experiments/04.1_small_isp_tromboning/notes.md):
  Scales Exp 04 to the whole small-ISP population — a complete block-level census of
  every FLL ISP (747 announced /24s, 8 IPs each, 7 vantages). **Done: 18,260 traces.**
- [05 — BGP Validation](findings/05_BGProuting.md):
  Cross-checks traceroute-observed AS paths against RIPEstat BGP data and bgp.he.net
  peer tables — **78/80 unique ISP-site paths consistent** with public peering.
- [06 — Submarine-Cable Outage](experiments/06_submarine_outage/notes.md):
  Monitors routes during the SMW5 submarine-cable fault (Jul 2026) — ping + traceroute
  every 15 min for 12 h from all 14 PK probes to a CDN/Abroad/PK sample, with a
  time-series notebook (UTC→PKT). **Done.**
- [6.1 — SMW5 in the Control Plane](experiments/06.1_submarine_hegemony/notes.md):
  Daily AS-hegemony time series across the fault window — did any *logical* (BGP)
  dependencies move when the cable broke, or did networks endure congestion on the same
  paths? Extends Exp 06 with global routing data.
- [6.1.1 — SMW5 Robustness](experiments/06.1.1_smw5_robustness/notes.md) **(done)**:
  Systematically closed 6.1's caveats. Headline results: a placebo test (4 control
  operators, incl. two with zero SMW5 exposure) forced the retraction of the
  churn-*magnitude* claim as a global artifact, but confirmed a Hurricane-Electric
  swing 2–8× larger in SMW5-exposed operators; **99.63%** of Pakistan's ~42M
  estimated internet users (APNIC-weighted) were on networks whose gate never
  moved; and RIPE Atlas's own worldwide anchor mesh **independently confirms**
  the fault predated the PTA announcement (a 78σ RTT/loss spike from 1 Jul
  17:00 PKT).
- [07 — Longitudinal Panel (flagship)](experiments/07_longitudinal_panel/notes.md):
  7-day uniform panel from all connected PK probes to a frozen 100-site stratified
  sample (40 PK / 40 CDN / 20 Abroad): TCP/80 Paris traceroute hourly + ping every
  30 min, run as server-side periodic measurements split across two accounts. Analysis
  methodology (speed-of-light latency ratio, physics-verified locations, per-ISP CDN
  treatment) in [analysis/METHODOLOGY.md](experiments/07_longitudinal_panel/analysis/METHODOLOGY.md).
- [08 — CDN Peering at PIE Karachi](experiments/08_CDN/findings.md) *(Sameera)*:
  Does traffic between IXP members actually cross the exchange fabric? Peering-LAN
  fingerprinting shows PIE Karachi and PKIX Lahore are **bypassed by their own members**
  (private bilateral links instead), and ACE CDN RTT varies 23→255 ms across ISPs.
- [09 — AS Hegemony](experiments/09_as_hegemony/notes.md):
  The PTCL/Transworld duopoly quantified from **global BGP data** (IIJ IHR): **90% of
  the 291 BGP-visible Pakistani networks depend on PTCL or TWA for the majority of
  their routes**; per-ISP scores independently confirm our traceroute findings.

## Findings

- [01 — Hosting & Routing Analysis](findings/01_hosting_and_routing_analysis.md)
  with the [charts notebook](findings/01_hosting_and_routing.ipynb)
  (re-run after new batches to refresh every figure).
- [1.1 — Per-ISP DNS Resolution](findings/01.1_dns_resolution_analysis.md):
  which sites resolve differently per ISP, and how much it matters.
- [1.2 — CDN Presence in Pakistan](findings/01.2_cdn_presence_analysis.md):
  whether Netflix/Google/Meta/etc. are served from caches inside Pakistan.
- [1.3 — Nayatel Routing](findings/01.3_nayatel_routes.md):
  per-destination breakdown of what Nayatel transits (LDI vs direct peering).
- [03 — Longitudinal Routing (48 h)](findings/03_longitudinal_routing_48h.md):
  path/RTT change over time from the 48-hour run (see also the
  [24 h](findings/03_longitudinal_routing_24h.md) and
  [initial](findings/03_longitudinal_routing_analysis.md) write-ups).
- [3.1 — PTCL RTT Jumps & PTCL↔Transworld Peering](findings/03.1_ptcl_rtt_jumps.md):
  where PTCL paths jump RTT (access floor vs international exit) and that PTCL peers
  with Transworld domestically (100%) but never for abroad traffic (0%).
- [1.4 — PK100 Website Hosting](findings/01.4_pk100_hosting.md):
  where the top-100 sites are hosted (CDN/Abroad/Pakistan) by sector and ISP, plus the
  gov sites that still hairpin ~200 ms from Transworld.
- [04 — Path Tromboning across Worldcall](findings/04_path_tromboning_worldcall.md):
  31% of Worldcall's sampled /24s hairpin through Transworld → Equinix Singapore,
  while PTCL reaches the same IPs locally — so Transworld chooses the hairpin.
  Destination-dependent and time-variable (intra-/24 consistency not yet verified).
- [4.1 — Small-ISP Tromboning Census](findings/04.1_small_isp_tromboning.md):
  the complete census — **11% of small-ISP traces hairpin abroad**; the source ISP
  dominates (Cybernet-Haripur 46%, PTCL-Karachi 38% vs 4–10% for others); Transworld
  and PTCL split the hairpins; exits are China/US/Singapore.
- [06 — SMW5 Submarine-Cable Outage](findings/06_submarine_outage.md):
  a latency degradation (not a blackout) that eased over the window (shophive via PTCL
  646→278 ms); quantified as **+31% jitter / +2% mean RTT / flat path length** on
  international paths, with **local/PK-hosted traffic unaffected** — the resilience case for PKIX.
  Independently confirmed (Exp 6.1.1): RIPE Atlas's own external anchor mesh supplies the missing
  pre-fault baseline, pins the true onset to **32 h before this experiment's window even opened**,
  and corroborates the "congestion easing, not cable repair" recovery read from a second method.
- [6.1 — SMW5 in the Control Plane](findings/06.1_submarine_hegemony.md):
  the same fault in global BGP — downstream dependencies **frozen** (one 2-day exception),
  while the operators re-carriered **~21%/13.5%** of their world paths for ~48 h (Hurricane
  surge, Cogent collapse): the duopoly absorbed the fault upstream.
- [SMW5 — the complete story](findings/smw5_fault_complete_story.md):
  every experiment on the fault (06, 6.1, 6.1.1, cross-checked against 07 and 09), assembled
  into one sourced, day-by-day timeline — onset 32 h before the announcement, ~42M users'
  exposure by gateway, the reroute-not-repair recovery, and the placebo test that retracted
  one claim and strengthened another.
- [07 — Longitudinal Panel (full week)](findings/07_longitudinal_panel.md):
  the flagship's complete results — international paths never exceed 10× the physics floor while
  **24% of domestic paths do**; **15.1% steady-state tromboning** (49% of pairs genuinely
  re-route at AS level within the week); **banking is the worst-routed sector** (79% trombone, 103 ms domestic); CDN locality is
  an ISP lottery (Nayatel 85% → PTCL 0%); TWA's backbone (125/143 routers) invisible to BGP.
- [09 — AS Hegemony](findings/09_as_hegemony.md):
  the duopoly from global BGP: **90% of BGP-visible Pakistani networks depend on PTCL or
  Transworld for the majority of their paths** (medians: TWA 0.50, PTCL 0.17); per-ISP
  dependencies independently confirm the traceroute findings.

## Probe Setup

Instructions for deploying a RIPE Atlas software probe on Raspberry Pi hardware:

- [Raspberry Pi 2](tools/probe_status/pi2.md) (32-bit, build from source)
- [Raspberry Pi 3 and later](tools/probe_status/pi3.md) (64-bit, official Debian package)
