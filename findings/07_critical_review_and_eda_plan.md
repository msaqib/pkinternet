# Exp 07 — Critical Review & EDA Plan for the 7-Day Data

Written 2026-07-15 (panel live, ends 2026-07-18). Part 1 is a referee-style pass over the project:
weaknesses, silent assumptions, and fixes — the criticisms a reviewer *will* make, raised now while
they are still cheap to address. Part 2 is the concrete EDA menu for the full 7-day dataset.

---

## Part 1 — Research-critical review

### 1. The sample's hosting strata are contaminated (highest priority)
The 40/40/20 (PK/CDN/Abroad) stratification was assigned at *selection time* using DNS + geo-IP.
Our own physics arbiter has since **proven that classification wrong for a material fraction**:
≥4 "Pakistan"-class sites are actually offshore (`phf.gop.pk` 233 ms/US, `toptop.net`, `youth.cn`,
`efulife.com`), and 34/40 CDN geo-IPs were fictitious ("Toronto"). Consequences:
- Any per-class statistic quoted on the *original* strata mixes classes (the PK class's heavy ratio
  tail is partly offshore sites mislabelled PK).
- The **post-stratification weights (58/26/14)** inherit the same classification method, so
  population-level claims carry the same error.
- **Fix:** re-classify hosting *post hoc* from the measured evidence (RTT physics + traceroute +
  reverse-DNS), report results on **both** the design strata and the corrected strata, and state
  the misclassification rate as a finding (it *is* one: "official" sites masquerade as local).
- Selection hygiene: `youth.cn` (a `.cn` domain) inside a "Pakistani web" sample needs an
  explanation or removal; Tranco ranks in the sample span ~13k–950k, so call it "the Pakistani web
  presence," not "top Pakistani websites."

### 2. Vantage-point validity — what 16 probes can and cannot claim
- **No mobile networks.** Jazz/Zong/Telenor/Ufone carry the majority of Pakistani users; every
  probe is fixed-line. The paper must scope claims to fixed-line access or this is a fatal
  generalization gap.
- **n=1 per small ISP.** Fasttel, Orbit, Nova, Transworld, Z-Com(≈2) are single vantages — Exp 4.1
  itself proved routing is **per-PoP, not per-ISP** (Cybernet: 46% vs 10% trombone by city). So
  per-ISP claims from one probe are really per-PoP claims; say so, or hedge the ISP ranking.
- **Geographic skew:** Lahore ×7 of 16. Any "national" statement is Lahore-weighted; consider
  city-stratified summaries.
- **Metadata cannot be trusted uncritically:** the panel's own `measurements.json` mislabelled
  probe 1015491 ("AS13335" → really Z-Com), and 1016036 carries a placeholder coordinate. We
  caught both, but the lesson generalizes: **re-verify probe ASN/coordinates from the RIPE API at
  analysis time, every time.**

### 3. Measurement-method gaps
- **ICMP survivorship bias (important, quantified):** 22/40 PK-class sites block ping, so the ping
  panel's "Pakistan" statistics describe only the 18 that answer — plausibly the better-run hosts.
  The TCP/80 traceroute half (results/a) reaches web servers that drop ICMP; **use it to fill the
  missing 22 and test whether the ping-only subset is biased** (compare trace-RTT distributions of
  responders vs non-responders).
- **Network edge ≠ content:** a 3 ms Cloudflare edge can still serve the page from Singapore
  (`colo=SIN`, the shaukatkhanum case). The CDN locality score measures *network* access, not
  content delivery. The **Cloudflare `colo` check from a PK host** is still pending — do it once
  from ispl02; it upgrades the CDN claims from "reaches the edge locally" to "served locally."
- **Ratio instability at tiny floors:** intra-city pairs have ~0.1 ms floors, so the ratio explodes
  (a 20 ms path over 8 km reads 250×). Report **excess-ms alongside the ratio** (interpretable +
  bounded) and/or floor the theoretical at a minimum distance; never quote intra-city ratios raw.
- **Detector thresholds are single-sourced:** 40/60/70/45 ms were calibrated on one ISP (Worldcall,
  Exp 04). Run a **sensitivity sweep** (±10 ms on each threshold) on the panel traces and show the
  trombone rate is stable; a reviewer will ask.
- **Asymmetric routing:** RTT sums forward+return; the traceroute sees forward only. A clean
  forward path with an inflated RTT may be a return-path trombone — flag such pairs (low hop
  inflation, high RTT inflation) rather than force-classifying them.
- **Central DNS resolution:** one server-side lookup per site (GeoDNS misses ~8% of sites per
  Exp 1.1). Acceptable, but must be stated in Methodology; `resolve_on_probe` is the future option.

### 4. Statistical hygiene for the 7-day analysis
- **Rounds are not independent.** ~160 rounds per (probe,site) are a repeated-measures cluster;
  treating them as independent gives absurd significance. Aggregate to (probe,site) first, or use
  cluster-robust/bootstrap-over-sites intervals.
- **The right model exists now:** with Cybernet×3, PTCL×3, Nayatel×2, TES×2, Z-Com×2, a nested
  variance decomposition (`KPI ~ class + (1|ISP/probe) + (1|site)`) *is* RQ2 — how much variance is
  ISP vs probe-within-ISP vs site. Report the ICC, not just anecdotes.
- **Effect sizes, medians, IQRs** — with n~10⁵ everything is "significant"; heavy tails make means
  misleading. Quote median differences with bootstrap CIs.
- **Multiple comparisons:** scanning 100 sites × 16 probes for anomalies will produce false
  discoveries; use FDR control or report only pre-registered comparisons as confirmatory.
- **Quote ranges, not snapshots:** the census's own lesson (verdicts flip). Trombone rates and
  ratios should be week-ranges (e.g. "9–13% across days"), not single numbers.

### 5. Reproducibility / paper-consistency debts
- **Probe count drift in drafts:** `aintec_panel.tex` intro says 14 probes; the panel scheduled 17,
  16 reported. Reconcile everywhere (16 is the honest number for RTT analyses).
- **Site-selection provenance:** the AINTEC draft describes seed-42 proportional sampling; the
  actual `targets.csv` came via the team CSV with manual gap-fills (2 ranks via apex, 1 ISP
  corrected). Document the true procedure or regenerate reproducibly — reviewers check.
- **Post-run raw archive:** run `dump_raw.py` once after 2026-07-18 (both accounts) and back up
  `results/{a,b}/measurements.json` off-server — they are the only index of measurement IDs.
- **Two-account merge check:** trace (A) and ping (B) halves must be joined on (probe, target,
  round); verify per-pair round counts match ~2:1 (ping 30 min vs trace 60 min) before analysis.

### 6. Framing risks (be careful what the data can support)
- **CDN locality ≠ PKIX usage.** Nayatel's 85% comes from *direct CDN peering*, not necessarily the
  PKIX route server (which remains absent from BGP). The result supports "local peering pays," a
  necessary-but-broader claim than "use PKIX." Keep the attribution precise or a knowledgeable
  reviewer will split it.
- **Forex (deliverable #1)** remains unmeasurable without volume data — keep it explicitly scoped
  out; a per-packet "wasted distance" figure is evocative but is not an economic estimate.

---

## Part 2 — EDA plan for the full 7-day dataset

Ordered; each step names the technique and the question it answers. Inputs: merged
`results/a` (traces) + `results/b` (pings) + raw dump; tools extend `analysis/geo.py`.

### Stage 0 — Data-quality audit (before any statistic)
- **Completeness matrix:** heatmap of rounds received per (probe × site × hour) for each half —
  finds probe outages, site deaths, harvest gaps. Expected: ~336 ping rounds, ~168 trace rounds per
  pair.
- **Missingness typology:** classify gaps as probe-wide (outage), site-wide (block/ICMP), or
  sporadic (loss) — determines which analyses each pair can join.
- **Artifact filter:** drop RTT > 500 ms (ICMP-error artifact), negative/zero, duplicate rounds;
  count what was dropped (report, never silently).
- **A/B join integrity:** per pair, ping:trace round ratio ≈ 2:1; flag pairs where halves disagree
  wildly (e.g. ping dead but trace alive = ICMP block, expected for ~22 PK sites).

### Stage 1 — Distributions (the cross-sectional picture)
- Per-class and per-ISP **CDFs** of: min-RTT, latency ratio, excess-ms, jitter, loss, hop count.
  (CDF = this genre's native figure; medians + IQR in a companion table.)
- **Box/violin by ISP × class** with access-floor-corrected variants side by side.
- **Corrected-strata versions** of everything (post-hoc hosting classes from §1 of the review).

### Stage 2 — Temporal structure (what 7 days buys us)
- **Diurnal profiles:** median KPI per hour-of-day (PKT) per class/ISP; peak-vs-offpeak delta with
  bootstrap CI. Flat ⇒ structural penalty (the "not a bandwidth problem" argument); peaked ⇒
  congestion component and *when*.
- **Weekday/weekend contrast** (the week covers both): same profiles split Fri/Sat/Sun vs work
  days.
- **Jitter over time:** rolling per-hour IQR/std per pair; identifies chronic-unstable pairs vs
  event-driven spikes.
- **Change-point detection** on per-(probe,site) RTT series (PELT or CUSUM): candidate reroutes →
  cross-check each against the traceroute path at the same timestamp (did the AS path actually
  change?). This pairs the ping sensitivity with the trace ground truth.
- **Autocorrelation/persistence:** does a bad hour predict the next (congestion memory), or are
  spikes memoryless (random loss)?

### Stage 3 — Path analysis (the trace half)
- **Per-pair path-change rate:** # distinct AS-level paths per (probe,site) over 168 rounds;
  distribution by ISP (who flaps?).
- **Trombone stability:** per-pair fraction of rounds tromboned → three families:
  persistently-local / persistently-hairpinned / **flapping** — closes Exp 4.1's single-snapshot
  caveat and turns the rate into a range.
- **Transit dependency over time:** share of paths through PTCL vs Transworld per ISP per day
  (does the 4.1 "source dominates" result hold longitudinally?).
- **Sensitivity sweep of the detector thresholds** (±10 ms) → stability table for the trombone
  rate.
- **ICMP-survivorship check:** trace-derived dest RTT for the 22 ping-blocked PK sites vs the 18
  responders — is the ping panel biased?
- **PKIX/PIE peering-LAN scan (extends Sameera's Exp 08 to panel scale):** search every hop of all
  ~160k panel traceroutes for the exchanges' peering-LAN prefixes — **PIE Karachi
  `58.181.127.0/24`, PKIX Lahore `100.128.0.0/24`** (add other PKIX sites' LANs if identified). A
  hop in those ranges is a physical fingerprint that the packet crossed the exchange fabric; Exp 08
  found zero in ~a dozen targeted traces, and this scan answers the same question over a week ×
  16 probes × 100 sites. Also add these LANs as flagged annotations in `geo.py annotate`. Expected
  result (either way, quotable): "N of 160k traces traversed an exchange."

### Stage 4 — The inferential comparisons (RQ1/RQ2 proper)
- **RQ1 table:** per-ISP median (CI) of each KPI to each class — the uniform four-indicator
  comparison the earlier experiments couldn't make. Cluster bootstrap over *sites*.
- **RQ2 variance decomposition:** nested model `KPI ~ class + (1|ISP/probe) + (1|site)`; report
  ICC per level. Multiple probes per ISP (Cybernet×3, PTCL×3, Nayatel×2, TES×2, Z-Com×2) make this
  identifiable for the first time.
- **CDN locality score, longitudinal:** per-ISP % local, per *day* (is Nayatel's 85% stable?);
  split by CDN provider (Cloudflare vs Sucuri vs Google behave differently by design).

### Stage 5 — Relationships & anomaly scan (exploratory)
- **Ratio vs Tranco rank** (do popular sites buy better hosting?); **ratio vs CISA sector**
  (which sectors pay the offshore penalty?).
- **Loss–RTT joint distribution** (is the offshore penalty latency-only, or lossy too?).
- **Event scan:** per-hour cross-probe correlated spikes (national events) vs single-probe
  (local); FDR-controlled. If any submarine/routing event landed in the window, quantify vs the
  within-window baseline (the Exp 06 method, now with a real pre-event reference).
- **Clustering (optional, exploratory):** k-means/hierarchical on per-pair feature vectors
  (median, IQR, diurnal amplitude, trombone fraction, loss) to *discover* behavioural families
  rather than impose them; PCA to see the dominant axes.

### Stage 6 — Robustness appendix
One table: headline numbers (PK/Abroad ratio medians, trombone rate, CDN scores, ISP ranking)
recomputed under: (a) detector thresholds ±10 ms, (b) with/without access-floor subtraction,
(c) excluding high-floor probes (1016126, 1016393, 64535), (d) design vs corrected strata,
(e) ping-only vs ping+trace RTT. Stable = credible.

### Deliverables checklist (post-18th, in order)
1. `dump_raw.py` both accounts; back up `measurements.json`; scp the final panel CSVs.
2. Stage 0 audit notebook → data-quality note.
3. Re-run `geo.py distances/relocate/ratio/cdn` on full data (numbers should barely move).
4. Post-hoc hosting re-classification → corrected strata.
5. Stages 1–4 (the paper's Results section feeds directly from these).
6. Stage 6 robustness table + updated `aintec_panel.tex` (fill the `\pending` slots).
