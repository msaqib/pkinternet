# Finding 07 — The 7-day longitudinal panel: full-week results

**Experiment:** `experiments/07_longitudinal_panel/` · **Window:** 2026-07-11 11:57 → 07-18 11:04
PKT (complete, event-free week) · **Scale:** 16 probes × 100 frozen targets; **222,944 TCP/80
Paris traceroutes** (hourly) + **445,749 pings** (half-hourly), split across two accounts
(A=traces, B=pings). Classes are **physics-corrected** (`analysis/targets_corrected.csv`): 37
Pakistan / 40 CDN / 23 Abroad — the arbiter moved 3 design-time "Pakistan" sites to Abroad
(`youth.cn`, `toptop.net`, `phf.gop.pk`: nearest PK probe 77–206 ms, physically impossible) and
relocated 3 geo-IP-impossible cities. Supersedes `07_longitudinal_panel_preliminary.md`. Headline analysis numbers use the **14-probe
analysis roster** (excludes the mislabelled Z-Com duplicate and the 90%-loss PTCL probe — the
latter's blinded traces default to non-trombone and would understate PTCL); §1's descriptive
table spans all 16 reporting probes.

---

## Verdict semantics (read this before the tables)

The per-trace flag inherited from Exp 4.1 says `TROMBONE` whenever a path **visibly leaves
Pakistan** (foreign hop, or an RTT jump ≥ the off-PK floor). Its meaning depends on the target's
class:

- **Pakistan-hosted target** → a true **trombone**: domestic traffic hairpinning abroad and back.
- **Abroad/CDN target** → simply "**path exits PK**", which is *expected*; the interesting signal
  is its **absence** (a local CDN cache, or a fully ICMP-blind path). The routes file prints the
  raw verdict for every class, which is why Abroad sites show "VERDICT TROMBONE" — a labelling
  carry-over, not a data error. Every rate below applies the class-correct reading.

---

## 1. The three classes, end to end (A + B combined)

| | **Pakistan** (37 sites) | **CDN** (40) | **Abroad** (23) |
|---|--:|--:|--:|
| trace rounds / ping rounds | 82,471 / 164,924 | 89,228 / 178,310 | 51,245 / 102,515 |
| ping answered | **45%** | 91% | 81% |
| ping RTT median / p90 (ms) | **25.6 / 96** | 78.8 / 206 | 163.1 / 286 |
| trace confirms destination | 82% | 79% | 80% |
| median hops | 10 | 10 | 13 |
| path exits PK | **15.1% = trombone** (analysis roster) | 46.6% | 82.6% |
| latency ratio (measured ÷ physics floor) | **2.88× median, p90 14.9×, 24% >10×** | 8.43× vs best-observed | **2.46× median, p90 4.2×, 0% >10×** |

**Abroad (the control).** Foreign sites behave exactly as global routing should: 82.6% of paths
visibly exit (the remainder are ICMP-blind, not local), 13 hops, 163 ms median — and **not one
probe-site pair exceeds 10× the physical floor**. The international system is near-optimal.

**Pakistan.** Domestic sites are 6× closer in milliseconds (25.6 vs 163) but **further from
physics**: median 2.87× and a heavy tail — 24% of pairs above 10×, worst 31×. The tail is the
tromboning: **15.1% of traces to PK-hosted sites leave the country and come back** (exits:
Singapore ≫ US > HK; carried by Transworld 2,773 and PTCL 1,721 of attributed hairpins). The
comparison that matters: *a quarter of domestic paths are worse, relative to distance, than the
worst international path in the entire dataset.*

**CDN.** Bimodal by design: whether "the CDN" is 3 ms or 200 ms away depends almost entirely on
the probe's ISP. 46.6% of CDN fetches leave Pakistan — i.e. **nearly half of "CDN-delivered"
content is not served from Pakistan at all** for our vantages. Per-ISP locality: Nayatel 85%
local (median 3.7 ms, 2 hops) → Cybernet-KHI 41% → everyone else **0% local** (PTCL median
130–275 ms). Exp 10's GGC scan confirms the mechanism: **no on-net cache inside any of 10 ISPs**.

## 2. By CISA sector (the categories from the sampling design)

**Pakistan-hosted — trombone rate by sector** (the sovereignty ranking):

| Sector | sites | ping median (ms) | **trombone %** |
|---|--:|--:|--:|
| **Financial Services** | 2 | **103.1** | **85.6%** |
| **Government Services & Facilities** | 4 | 22.8 | **27.6%** |
| Energy | 1 | (ping-blocked) | 25.8% |
| Transportation | 1 | (ping-blocked) | 9.9% |
| Commercial Facilities | 21 | 24.4 | 10.0% |
| Education | 4 | 33.7 | 6.5% |
| Communications | 3 | 26.4 | 1.8% |
| Healthcare | 1 | 24.9 | 1.9% |

- **Banking is the worst-routed sector in Pakistan.** ZTBL (the state agricultural bank) hairpins
  **86.4%** of the time; EFU Life 72%. Median RTT to PK-hosted financial sites is **103 ms —
  worse than the CDN class** and 4× the domestic norm, for sites that are *in the country*.
- **Government averages 27.6%**, driven by fgeha.gov.pk at **89.2%** (a federal housing authority
  whose domestic visitors route via Singapore). The other gov sites are mostly clean — so this is
  a *fixable, site-level* failure, not a systemic gov property.
- The bulk of the web (Commercial, 21 sites) trombones at 10.0% — real but far lower; and the
  sectors that run their own networks (Communications, Healthcare-PITC) barely trombone at all.
- Hosting correlation: the three worst sites are hosted on **Cybernet (2) and self-hosted EFU** —
  reached from other ISPs via the foreign hairpin, echoing Exp 4.1's Cybernet finding.

**CDN class by sector** — same lottery, different stakes: Financial-sector CDN sites see 174 ms
median and 78.5% foreign fetch (banks buy CDN but get far PoPs), while Commercial CDN sites
(the big consumer CDNs with PK caches) sit at 25.9 ms. **Abroad by sector** is uniform (81–88%
exit everywhere) — the expected control result; sector doesn't matter once you've left.

## 3. Route dynamics over the week (summary of `analysis/route_changes.md`)

- **81% of the 1,600 (probe,target) pairs changed route** during the week by coarse signature;
  hop-level analysis (route_changes.md §Mechanics) refines this honestly: **49% of pairs genuinely
  re-route at AS level** (the rest is ECMP branch-sampling and hop-visibility artifacts), with
  divergence concentrated at **hops 3–5 — the domestic pre-gate layer an IXP would replace**;
  detours breathe on/off (96% oscillation) rather than migrate.
- **43% of ≥50-round PK pairs flap** (48% persistently local, 9% persistently hairpinned) **by
  verdict** — but a flipped RTT-physics verdict alone doesn't prove the route changed. Checking the
  actual AS-path behind every hairpin flag: only **77 of 233 ever-trombone pairs (33%) show a
  confirmed route change**; the other 156 (67%) never show one — every hairpin flag they ever get
  coincides with an unchanged path, consistent with RTT-threshold noise (concentrated on
  Transworld/Z-Com, 0% confirmed each — full detail and worked examples in
  `experiments/07_longitudinal_panel/analysis/evidence_rq3_flapping.md`). Within the confirmed-33%,
  the same pairs are also served locally elsewhere in the week — real route-level evidence of
  choice for that population — including the **gate flips** (PTCL↔TWA, same pair, 23×), which are
  unambiguous since the two carriers are different ASNs.
- Diurnal signal is mild (12.6% trough → 16.0% evening peak): tromboning is **structural, not
  congestion-driven**.
- The *flip itself* is nearly free (within-pair median +0.5 ms, mean +15.3, n=121 on the
  analysis roster); the cost lives in the **40 persistently-hairpinned pairs (~100 ms vs ~25 ms
  local)**.
- Volatility is an ISP property: PTCL/Fasttel flip ~100%/92% of their PK pairs; Nayatel/TWA are
  the most stable — same ISP ranking as CDN locality.

## 4. Data completeness — quantified, and what it does not threaten

Per the analysis-discipline rule (METHODOLOGY.md): gaps are quantified, not gestured at.

| Gap | size | bounded consequence |
|---|---|---|
| Ping silence | 28.3% of ping rows NaN; **PK-hosted worst at 54.8%** (22/100 targets never answer — domestic firewalls filter ICMP far more than foreign hosts) | Ratio/RTT stats for PK describe the **responding 45%**; the trace half still covers the silent sites' *paths*, so trombone rates are unaffected. Direction of bias: silent sites skew government/corporate — if anything the responding set *understates* domestic dysfunction. |
| Destination unconfirmed (hop 255) | 19.6% of traces, uniform across classes (18–21%) | TCP/80 filtering at the target; the path *up to* the exit is still observed, so exit/transit/trombone verdicts remain valid; hop-count stats exclude these rows. |
| Unattributed exits | 7% of exited traces have exit_cc `?` | Exit-country tables are lower bounds per country; the `?` rows are still counted as exits (the RTT physics is unambiguous). |
| Unattributed transit | 45.1% of traces have transit `?` (private/unresponsive boundary hops) | Carrier attribution (TWA vs PTCL shares) uses the attributed half; treat shares as *among attributable paths*. The duopoly conclusion is robust — no third carrier exists to hide in the `?`. |
| Probe skew | cybernet.1016154 joined late (700 rounds); ptcl.7764 90% ping loss; 1 mislabelled probe | The notebook analyses exclude 7764 + the mislabel (14-probe roster); per-ISP numbers weight by rounds. |
| Blind probes | 62224 (TWA) and 1015210 (PTCL-Docker) show few/no mid-path hops | Destination-level data valid; they contribute no path/exit evidence (part of the transit-`?` mass). |

None of these gaps touches the headline results: the 0%-vs-24% tail asymmetry (ping-based, on
responders), the 14.3% trombone rate (trace-based, robust to 255s), the sector ranking (both), or
the per-ISP CDN lottery (ping + trace agree).

## 4b. The IXP null result (panel-scale cross-check of Exp 08)

Scanning all 906 observed routers (and thereby all 222,944 traces) against the exchange
fingerprints from Exp 08 — PKIX Lahore `58.181.127.0/24`, PIE Karachi `100.128.0.0/24`:
**zero traces crossed either exchange's peering fabric, the entire week.** Meanwhile 11,756
traces to PK-hosted sites went out via Singapore/US and back — every one a pair that an exchange
exists to serve. Caveat (per §4): ~45% of traces have blind middle hops, so fabric hops could in
principle hide there; but combined with Exp 08's direct member-path evidence, the convergent
conclusion stands — **the exchanges are bypassed at national scale, not just in spot checks.**

## 5. What Exp 07 (A+B together) establishes

1. **The tail, not the median, is the story**: international routing never exceeds 10× physics;
   a quarter of domestic paths do. PKIX's case is the tail.
2. **Tromboning is real, dynamic, and duopoly-carried**: 15.1% steady-state, flipping hour to
   hour, exiting via Singapore on TWA/PTCL — with the gate itself non-deterministic.
3. **Sector stakes are inverted from importance**: banking and a federal gov site are the worst
   routed; commodity commercial sites the best.
4. **CDN quality is an ISP choice**: Nayatel proves local is possible; PTCL's 0% proves it isn't
   bought; Exp 10 proves no ISP hosts an on-net cache.
5. **A methodological result**: Transworld's domestic backbone (125 of its 143 observed routers)
   is unannounced in BGP — invisible to pure control-plane studies. Data-plane measurement like
   this panel is the only way to see most of Pakistan's transit infrastructure.

**Artifacts:** `analysis/METHODOLOGY.md` (method), `analysis/route_changes.md` (dynamics),
`analysis/ratio_corrected.csv` + `figures/ratio_cdf_all3.png` + `ratio_box.png` (ratio),
`analysis/cdn.csv` + `figures/cdn_by_isp.png` (CDN), `analysis/hop_annotations.csv` (all 906
routers annotated), `results/a|b/` (full-week panels + routes), notebook figures
(`analysis/figures/fig_*.pdf`).
