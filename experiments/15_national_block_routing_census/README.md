# Experiment 15 — national block-routing census

**Question.** For every announced block of every Pakistani ISP, measured from several in-country
vantage points: does a packet sent toward that block stay in Pakistan, or leave and come back?

**Status.** Universe enumerated, liveness mapped, route sweep complete and annotated, detector
built and validated, per-ISP results published. Atlas census pending.

**Scope is now all of Pakistan**, not the 48 small ISPs it started as. 5,774,336 addresses across
22,556 /24 blocks and 352 networks. Headline results are in
[`15.1_data_plane/ISP_SUMMARY.md`](15.1_data_plane/ISP_SUMMARY.md). New to this work? Read
[`15.1_data_plane/EXPLAINER.md`](15.1_data_plane/EXPLAINER.md) first: methods, sampling, worked
examples of real traces, and what the study cannot tell you.

---

## Layout, in run order

```
15_national_block_routing_census/
├─ README.md              this file — start here
├─ MANUAL.md              design and rationale
├─ SAMPLING_METHOD.md     shared design: universe, sampling, detection rules
├─ TOOLS.md               tool register: what each source answers, and what it does not
├─ FINDINGS.md            results index
├─ docs_EXP41_CENSUS_PLAN.md   vantage points, phases, sizing
├─ slides/                make_slides.py → slides.html / slides.pptx
├─ papers/                literature
│
├─ 15.1_data_plane/       THE MEASUREMENT. Produces a snapshot, no verdicts.
│  ├─ MANUAL.md               what 15.1 does and why
│  ├─ SWEEP_FINDINGS.md       method and results of the liveness sweep
│  ├─ EXPLAINER.md            START HERE — what it does and why, no context assumed
│  ├─ ISP_SUMMARY.md          RESULTS BY ISP — the presentable rollup
│  ├─ RULES.md                per-vantage detection rules, as testable statements
│  ├─ FINDINGS.md             detector validation results
│  ├─ 1_universe/             block universe, plus block -> ASN -> operator ownership
│  ├─ 2_liveness/             scan every address for liveness (local, free)
│  ├─ 3_routes/               traceroute every live host (local, free)
│  ├─ 4_atlas/                RIPE Atlas: probe-type pilot, and the census
│  ├─ 5_detector/             detector.py, its validation, and RULES.md
│  └─ 6_analysis/             per-ISP rollup, trace quality, vantage fingerprints
│
├─ 15.2_postprocessing/   INTERPRETATION. Panel selection and the detector bench. No BGP.
└─ _retired/              superseded work, kept for the record
```

Each stage directory holds its script **and** its output, so a stage is self-contained.

---

## How to run it

Every step is free unless marked otherwise.

```
# 1. refresh the block universe (RIPEstat, free)
python 15.1_data_plane/1_universe/reenumerate.py

# 2. map ownership: every /24 -> the ASN that announces it -> operator name (free)
python 15.1_data_plane/1_universe/build_block_owners.py
python 15.1_data_plane/1_universe/resolve_unowned.py

# 3. find which addresses are alive (local, free)
#    all-Pakistan adaptive sweep, ~7 h; then top up thin blocks from a second vantage
python 15.1_data_plane/2_liveness/scan_all_pk.py --threads 100
python 15.1_data_plane/2_liveness/topup_scan.py  --threads 50

# 4. traceroute every live host, then select and annotate the usable traces (local, free)
python 15.1_data_plane/3_routes/local_trace.py --threads 120

# 5. roll the whole sweep up per ISP and render the summary (free, read-only)
python 15.1_data_plane/6_analysis/build_isp_summary.py
python 15.1_data_plane/6_analysis/write_isp_summary.py

# 6. RIPE Atlas — COSTS CREDITS. Dry run first; --fire actually spends.
python 15.1_data_plane/4_atlas/fire_probe_type_pilot.py          # dry run, prints cost
python 15.1_data_plane/4_atlas/fire_probe_type_pilot.py --fire
python 15.1_data_plane/4_atlas/fetch_pilot.py
python 15.1_data_plane/4_atlas/analyse_pilot.py

# 7. detector, validated against the frozen 4.1 census (free, read-only)
python 15.1_data_plane/5_detector/validate_against_41.py

# 8. analysis over the 4.1 archive (free, read-only)
python 15.1_data_plane/6_analysis/trace_quality.py
python 15.1_data_plane/6_analysis/vantage_fingerprint.py
python 15.1_data_plane/6_analysis/probe_rules.py
```

---

## Non-negotiables

- **Every run emits a human-readable route file beside the CSV.** No verdict ships without the
  paths to check it against.
- **Keep repeat observations of each hop address.** The domestic-address rule needs a median over
  three or more samples from one vantage; collapsing repeats destroys it.
- **Report `inconclusive` separately**, never folded into `local`.
- **Nothing on RIPE Atlas fires without the cost being stated first.**
- **Earlier experiments are read-only.** This experiment reads from 04.1 and 07; it never writes to them.

---

## Scope

The universe was inherited from Exp 4.1 as **the 48 PTA FLL licensees**, small ISPs only. PTCL,
Transworld and the other large operators were excluded and appeared in the data as transit, never
as destinations.

**That scope has been widened to every Pakistani network, and the sweep is done.** The universe is
now the union of the registry view and the routing view: **5,774,336 addresses, 22,556 /24 blocks,
352 networks with announced space**. See
[`1_universe/UNIVERSE_FINDING.md`](15.1_data_plane/1_universe/UNIVERSE_FINDING.md) for why neither
view alone is sufficient, and why the older 5,521,664 figure was the registry view only.

The widening changed the shape of the study, not just its size. PTCL alone holds 65% of the blocks
and 68% of the live hosts found, so **any country-level statistic that is not weighted by network
is a statistic about PTCL**. That was not true of the small-ISP universe.
