# Experiment 07 — The PKIX-underuse longitudinal panel (flagship)

**Author:** Rayan Atif · **Status:** planned (not yet launched)

The **canonical, uniform** experiment. Every earlier experiment drifted on vantages, protocol,
RTT definition, and metric set (see `paper/experiment_consistency.md`); Exp 07 fixes all of them
by running **one framework** — all available PK probes, same TCP/80 Paris traceroute + ping
(min-of-N), same four indicators, same RTT-physics detector — continuously for **7 days**. It is
designed to be the paper's backbone: the per-ISP KPI distributions, the diurnal/weekly stability,
the intermittency of tromboning, and a **normal-day baseline** that captures the next cable fault
with a true before/during/after.

## Why this experiment (what it fixes)

| Prior drift | Exp 07 fix |
|---|---|
| Vantage set changed every run (5→3→8→1→7→14) | **All connected PK probes**, queried live at schedule time |
| ICMP (01/03/06) vs TCP/80 (04/4.1) | **TCP/80 Paris** for path (ping for RTT) — one protocol |
| RTT defined 3 ways (single-packet / avg / max-hop) | **ping min-of-N** for the level; stddev for jitter |
| Only Exp 06 carried jitter + loss | **All four KPIs** (RTT, hop count, jitter, loss) everywhere |
| Single snapshots (fragile to intermittency) | **7-day** continuous series |
| Curated, non-reproducible site lists | **Documented, frozen website list** (Tranco → filter `.pk` → resolve → CISA) |

## Objective & research questions

Produce the definitive longitudinal dataset that answers, uniformly and per-ISP:
- **RQ1 (Set-3 vs Set-1/2):** is the user experience (RTT, hops, jitter, loss) of ISPs that
  peer at PKIX better than those that don't? → per-ISP KPI distributions to local vs offshore vs
  CDN targets.
- **RQ2 (same-ISP consistency):** do customers of the *same* ISP get similar service? → variance
  across the multiple probes we have per ISP (Cybernet ×3, Nayatel ×2, PTCL ×3).
- **Tromboning intermittency:** how stable is a trombone verdict over 7 days (per-host vs
  time-flipping — the open Exp 04 question); complements Exp 4.2.
- **Diurnal / weekly structure:** does the offshore penalty have a time-of-day or weekday cycle?
- **Resilience:** if a cable fault occurs in the window, we have a **true pre-event baseline**
  (the gap Exp 06 could not fill).

## Design

| | |
|---|---|
| **Probes** | **All connected Pakistani probes**, discovered at schedule time via the RIPE API (`country_code=PK, status=1`) — currently ~14, but the set is taken live, not hardcoded |
| **Cadence** | **1 traceroute / hour** (TCP/80 Paris, `packets=3`, `paris=16`) + **1 ping / 30 min** (`packets=3`) |
| **Duration** | **7 days** |
| **Mechanism** | server-side RIPE **periodic** measurements: one periodic traceroute (interval 3600 s) + one periodic ping (interval 1800 s) per target, fanning to all PK probes, 7-day start/stop window → **runs on RIPE regardless of our host** |

### Targets — final 100-site stratified sample (`targets.csv`)

**This panel measures websites only — no canaries, no IP blocks.** The final target set is a
**fixed 100-website stratified sample** (`targets.csv`; columns `class,target,cisa_sector,
isp_cdn,tranco_rank`, `class ∈ {Pakistan, CDN, Abroad}`), selected on **two axes at once**:

**Axis 1 — genre (CISA critical-infrastructure sector): proportional.** The sample mirrors the
real `.pk`-web population's sector mix:

| CISA sector | sites | | CISA sector | sites |
|---|--:|---|---|--:|
| Commercial Facilities | 60 | | Financial Services | 4 |
| Government Services & Facilities | 11 | | Energy | 3 |
| Education | 10 | | Healthcare & Public Health | 3 |
| Communications | 7 | | Transportation Systems | 2 |

**Axis 2 — hosting class: a deliberate fixed 40 / 40 / 20 split** — **40 Pakistani, 40 CDN,
20 Abroad** — held *within* each sector as far as counts allow (Commercial 24/24/12, Government
4/4/3, Education 4/4/2, …).

**How they were selected.** Candidate pool = Tranco top-1M filtered to `.pk` (plus curated
critical-infrastructure sectors), each site's hosting resolved (DNS → ASN/geo → CDN / Pakistani /
Abroad) and CISA-sectored; then a **stratified draw** that keeps the sector marginal *proportional*
and forces the hosting marginal to *40/40/20*. Frozen in `targets.csv` (site, sector, hosting,
host, Tranco rank) so the panel is reproducible and auditable. (7 sites carry no Tranco rank —
included as sector representatives though outside the top-1M.)

**Why this design makes sense probabilistically.**
- **Proportional across genres → representativeness.** Drawing sectors in proportion to their true
  prevalence means any *pooled/weighted* statistic generalises to "the Pakistani web" without
  post-hoc correction; each sector's influence matches its real footprint (Commercial dominates
  `.pk`, so it dominates the sample — as it should).
- **Balanced across hosting classes → statistical power.** RQ1 compares *between* hosting classes
  (local vs CDN vs abroad). The population is heavily CDN/abroad-skewed (~58% CDN, ~26% Abroad,
  ~14% PK in the 1,781-site pool), so a purely proportional draw would leave only ~14 Pakistani
  sites — too few to estimate that class or detect class differences. Over-sampling the thin
  classes to **40/40/20 equalises the per-class sample sizes**, and the variance of a difference of
  means is minimised when the groups are balanced — i.e. equal allocation **maximises the power** to
  compare classes. We trade a representative *hosting* marginal for that power.
- **2-D stratification (sector × hosting) → both comparisons, unconfounded.** Holding 40/40/20
  *within* each sector lets us compare hosting classes *inside* a sector (e.g. government hosted
  abroad vs locally) without a sector's own mix confounding the hosting effect.
- **Population estimates via post-stratification.** Because the hosting marginal is deliberately
  non-representative, any *population-level* figure (e.g. the average `.pk` site's RTT) must be
  **re-weighted** by the true stratum shares (~58/26/14). So the one sample serves both:
  unweighted for powerful *between-class* comparisons, reweighted for representative *population*
  estimates.

Tromboning is still recorded (the `tromboned` flag per trace) — some PK-hosted sites hairpin — but
the dedicated tromboning-intermittency census over IP blocks is **Exp 4.2**, not this panel.

## Operations (how it runs)

Runs on an **external server** (SSH in; the operator manages it — this is **not** committed and is
**never** git-pushed by the tool). Three modes, all reusing the Exp 06 periodic-measurement
machinery:

- **`schedule`** — discover PK probes, read `targets.csv`, resolve, create the periodic
  traceroute+ping measurements (7-day window), write `results/measurements.json`.
- **`watch`** — a **background** loop that periodically (e.g. every 30 min) fetches new results,
  appends to the panel CSV, and re-renders `routes_*.txt` — a local, self-contained monitor like
  the Exp 03 `trace_monitor` watch, **but with no git / no push**. Meant to be left running under
  `nohup`/`tmux`/systemd on the server.
- **`fetch`** — a one-off pull of everything so far → panel CSV + routes txt.
- **`stop`** — stop the measurements early.

Because the measurements are server-side periodic, the collection continues on RIPE even if the
watch process is restarted; `watch`/`fetch` only gather results. Nothing leaves the server.

## Cost estimate (7 days, ~15 probes, 100 websites)

100 websites × 15 probes: traceroute = 15 × 100 × 168 rounds ≈ **252k traceroutes**; ping =
15 × 100 × 336 ≈ **504k pings**. Credits ≈ ~6.3M (traceroute) + ~2.5M (ping) ≈ **~8.8M (~16%)** of
the ~54M balance. Scales linearly with the live probe count. **Monitor the burn**; levers: fewer
sites, ping-only for the ICMP-filtered probes (7764, 62224).

**⚠ Concurrency limit.** 100 targets × (trace + ping) = **200 periodic measurements**, which
exceeds RIPE Atlas's default **100 concurrent-measurement** cap. Mitigations, in order of
preference: (a) request a limit increase for the account; (b) schedule in **two waves** (e.g. all
traceroutes first, pings second — or split the target list); (c) drop the separate ping and take
RTT from the traceroute's destination reply; (d) reduce to ≤50 targets. `schedule` should check the
account's running-measurement count and warn before creating measurements.

## Outputs (local only — never pushed)

A per-round **panel** row: `(ts_utc, ts_pkt, probe_id, probe, isp, target, class, rtt_min,
hop_count, loss, tromboned, exit_cc, transit)`.
- `results/measurements.json` — the periodic measurement IDs.
- `results/panel_<ts>.csv` — the long-format series (appended by `watch`, or built by `fetch`).
- `results/routes_<ts>.txt` — readable traces (standing rule).
- Derived later: per-ISP KPI CDFs, diurnal/weekly decompositions, per-(probe,target)
  trombone-fraction over time.

## Analysis plan

1. **Per-ISP KPI CDFs** — RTT / hops / jitter / loss to local vs CDN vs offshore, one panel per
   ISP → the uniform table the earlier snapshots cannot support (RQ1).
2. **Same-ISP variance** — spread across the multiple probes per ISP (RQ2).
3. **Tromboning of PK-hosted sites over time** — for any PK website that hairpins, the
   fraction-of-rounds it trombones (stable vs flapping). The dedicated block-level
   intermittency census is Exp 4.2, not this panel.
4. **Temporal structure** — diurnal + weekday cycles in the offshore penalty and trombone rate.
5. **Event capture** — quantify any cable fault against the pre-event baseline (Exp 06 method).

## Framework consistency (the point of this experiment)

- **Protocol:** TCP/80 Paris traceroute (ICMP undercounts — Exp 04: 12/52) + ICMP ping for RTT.
- **RTT:** ping **min-of-N** for the level; **jitter** = round-to-round stddev; loss = sent−received.
- **Detector:** the Exp 04 RTT-physics rules (foreign hop ≥40 ms, or ≥60 ms jump, or hop ≥70 ms
  = left PK; <45 ms = local; ignore >500 ms; exclude Shaw/Cogent artefact ASNs).
- **Hop-count caveat:** exclude ICMP-filtered (7764, 62224) and Docker-opaque (1015210) probes
  from path-length metrics.

## Design rationale (justification for each choice)

Every parameter is a deliberate choice; here is why each is what it is.

- **7-day duration.** Long enough to cover two full **diurnal cycles** and a complete
  **weekday/weekend** cycle (so we can separate time-of-day and day-of-week effects from
  structural ones), and to observe **routing intermittency** (verdicts flip over hours);
  short enough to iterate and keep credits modest (~5% of balance). It also has a realistic
  chance of catching a routing/cable event with a clean pre-event baseline.
- **All connected PK probes (discovered live).** Prior experiments each used a different,
  partly-hardcoded probe set, which broke cross-experiment comparison. Taking *every*
  connected PK probe at schedule time (a) maximises per-ISP and per-PoP coverage, (b) gives
  **multiple probes per ISP** (Cybernet ×3, Nayatel ×2, PTCL ×3) needed for RQ2 (same-ISP
  consistency), and (c) avoids a stale hardcoded list as probes come and go.
- **Websites only (no canaries, no IP blocks).** The panel's question is *user-facing*
  quality and *where real content lives* — websites are what users actually load. Canaries
  add no QoS signal the website set doesn't already give, and dedicated IP-block tromboning
  intermittency is **Exp 4.2's** job — separating concerns keeps each experiment answering
  one thing cleanly.
- **TCP/80 Paris traceroute (not ICMP).** ICMP is heavily filtered in Pakistani networks and
  undercounts badly (Exp 04: only **12/52** targets answered ICMP). TCP/80 reaches web
  servers and dodges ICMP rate-limiting; **Paris** holds the flow tuple constant so an
  observed path change is a *real* reroute, not load-balancer noise.
- **Ping min-of-N for the RTT level.** Network noise is one-directional (queuing only ever
  *adds* delay), so the **minimum** of N packets is the cleanest estimate of the true path
  latency. Legacy single-packet RTT (Exp 01) was noisy and biased upward.
- **Four KPIs: RTT, hop count, jitter, loss.** The standard IXP-comparison metric set from
  our template paper (Di Bartolomeo, ISCC 2015). RTT alone misses **stability**; jitter and
  loss capture the quality a user actually experiences, and only Exp 07 carries all four
  uniformly across all vantages.
- **Cadence: 1 traceroute/hour + 1 ping/30 min.** Traceroute is the heavier measurement, so
  hourly path sampling catches diurnal reroutes without hammering the network or the credit
  budget; ping is cheap, so 30-min sampling gives finer RTT/jitter/loss resolution. The split
  balances temporal resolution against cost and good-citizen pacing.
- **Server-side periodic measurements.** Registered once with a fixed window, they run on
  RIPE's infrastructure — **host-independent**, low create-rate (polite), and the local
  `watch`/`fetch` process can restart freely without losing data.
- **Target pool = curated categories + all Tranco `.pk`.** **Tranco** is the reproducible,
  popularity-ranked research standard (aggregates Alexa/Majestic/Umbrella/Quantcast), so the
  pool is defensible and re-derivable; the PDF's **curated sectors** (banks, government,
  energy/DISCOs, courts, telco) add critical-infrastructure coverage that raw popularity
  under-weights. Resolving hosting *first* lets us pick a final subset **balanced across
  CDN / Pakistani / Abroad** and across sectors.
- **Categorisation (sectors + `.pk` sub-TLD).** *Which sectors stay in-country vs go
  offshore* is a headline finding axis (government is mostly PK; e-commerce is mostly CDN).
  Manual sectors suit the curated set; the `.pk` **sub-TLD** (`gov/edu/com/net/org`) is the
  only feasible automatic category for the ~1.5k bulk Tranco domains.
- **RTT-physics detector (not geo-IP).** Registration country lies exactly where it matters —
  Shaw (AS6327) and Cogent (AS174) sit *in Pakistan* at ~2 ms, while foreign IXP egress hops
  are often unannounced. RTT is the ground truth for "did the packet leave the country."
- **Hop-count exclusions (probes 7764, 62224, 1015210).** Two are ICMP-filtered and one is a
  Docker container exposing only two hops, so their hop counts are meaningless — excluded from
  path-length metrics only (their RTT is still valid).

## Relationship to other experiments

- **Supersedes/extends Exp 03** (longitudinal) with all PK probes, TCP/80, all four KPIs, and
  trombone-IP targets — quote the final offshore-penalty numbers from here, keep 03 as the pilot.
- **Supplies the baseline Exp 06** lacked (a normal-day reference for the next cable fault).
- **Absorbs / runs alongside Exp 4.2** (repeat census) for tromboning intermittency.

## How to run (server runbook)

Everything runs on the **external server** (SSH in yourself). The tool never touches git and
never pushes; results stay in `results/` (git-ignored).

### 1. One-time setup
```bash
ssh <you>@<server>
cd <repo>/pkinternet
python3 -m venv .venv && source .venv/bin/activate          # optional but recommended
pip install ripe.atlas.cousteau ripe.atlas.sagan requests python-dotenv
printf 'RIPE_API_KEY=%s\n' "<your-key>" >> .env             # loaded automatically; never committed
```

### 2. Confirm the target list
`experiments/07_longitudinal_panel/targets.csv` is the final 100-site list. Sanity-check it loads:
```bash
python - <<'PY'
import importlib.util, collections
s=importlib.util.spec_from_file_location('pm','experiments/07_longitudinal_panel/panel_monitor.py')
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(len(m.discover_probes()),'probes |', collections.Counter(c for c,_,_ in m.load_targets()))
PY
```

### 3. Pick a mode that fits the RIPE caps (see *Cost estimate* above)
The default 100 sites × (traceroute + ping) at 1 h / 30 min = **200 measurements, ~1.3M
credits/day, 108k results/day**, which breaks the 100-measurement, 1M-credit/day and
100k-result/day caps. Choose one:
- **Full panel** — first email `atlas@ripe.net` to raise the caps, then run as-is.
- **Fits-the-caps (no request)** — traceroute-only, every 2 h. Edit the **CONFIG block at the
  top of `panel_monitor.py`**: set `TRACEROUTE_EVERY_MIN = 120` and `TRACE_ONLY = True`
  (or `export TRACEROUTE_EVERY_MIN=120 PANEL_TRACE_ONLY=1`). → 100 measurements,
  ~540k credits/day, 18k results/day.
- Other levers (same CONFIG block): `DURATION_DAYS`, `PING_EVERY_MIN`, or fewer probes/sites.

### 4. Schedule the run
```bash
python experiments/07_longitudinal_panel/panel_monitor.py schedule
```
Discovers all live PK probes, reads `targets.csv`, creates the server-side periodic
measurements for the 7-day window, and writes `results/measurements.json`. It prints each
measurement id as it is created. **Run this once.** (Verified with a one-off 15-probe test to
`airblue.com`: first results in ~20 s, **all 15 probes reported both traceroute and ping within
~90 s**; the ICMP-filtered PTCL anchor 7764 lost its ping and stalled at 2 hops, as expected.)

### 5. Start the background collector
```bash
nohup python experiments/07_longitudinal_panel/panel_monitor.py watch > results/watch.log 2>&1 &
echo $! > results/watch.pid            # remember the PID
tail -f results/watch.log              # Ctrl-C just stops tailing, not the run
```
`watch` fetches every 30 min → rewrites `results/panel_<ts>.csv` + `results/routes_<ts>.txt`.
Because the measurements run on RIPE, you can kill and restart `watch` freely without losing data.

### 6. Check progress any time
```bash
python experiments/07_longitudinal_panel/panel_monitor.py fetch   # one-off pull -> panel CSV + routes
ls -la results/                                                    # panel_*.csv, routes_*.txt, watch.log
```

### 7. Stop
```bash
python experiments/07_longitudinal_panel/panel_monitor.py stop     # stop the RIPE measurements early
kill "$(cat results/watch.pid)"                                    # stop the background watcher
```
The run also **auto-stops after 7 days**; you can then do a final `fetch`.

### Environment variables
| var | default | meaning |
|---|---|---|
| `RIPE_API_KEY` | (from `.env`) | RIPE Atlas key |
| `DURATION_DAYS` | 7 | run length |
| `TRACE_INTERVAL` | 3600 | seconds between traceroutes |
| `PING_INTERVAL` | 1800 | seconds between pings |
| `WATCH_EVERY` | 1800 | seconds between `watch` fetches |

## Status

**Planned — target set finalised.** `panel_monitor.py` is **built** (`schedule`/`watch`/`fetch`/
`stop`, live PK-probe discovery, TCP/80 traceroute + ping, four-KPI fetch, no git). `targets.csv`
is the **final 100-site stratified sample** (40 Pakistan / 40 CDN / 20 Abroad, sector-proportional
— see *Targets* above; source `data/pk_100_final_v2.csv`). The 1,781-site candidate pool
(`site_candidates.csv`) is retained as context. **Next:** resolve the **200-measurement vs
100-concurrent-cap** issue (request a limit increase, or schedule in two waves), then `schedule` +
`watch` on the external server to start the 7-day clock. Priority: start soon so it can catch the
next outage with a real baseline.


## Candidate website list

All **1781 candidate websites** from `site_candidates.csv` (curated categories + all Tranco `.pk`), summarised by category. **In Tranco** = how many of a category's sites carry a Tranco rank (the `Tranco .pk:` categories are 100% by construction; the curated categories from the PDF are the ones where this matters). Full per-site detail (hosting, ISP/CDN, rank) is in `site_candidates.csv`.

| Category | Sites | In Tranco | CDN | Abroad | Pakistani | Unresolved |
|---|--:|--:|--:|--:|--:|--:|
| Telco | 6 | 6 | 2 | 0 | 4 | 0 |
| ISPs | 19 | 10 | 2 | 7 | 8 | 2 |
| Energy (DISCO) | 11 | 6 | 1 | 2 | 8 | 0 |
| News | 75 | 40 | 45 | 26 | 4 | 0 |
| E-commerce | 74 | 74 | 67 | 7 | 0 | 0 |
| Airlines | 5 | 4 | 3 | 2 | 0 | 0 |
| Bus / Public Transport | 5 | 2 | 0 | 4 | 1 | 0 |
| Insurance | 13 | 5 | 5 | 5 | 3 | 0 |
| Courts | 5 | 4 | 2 | 2 | 1 | 0 |
| Banks | 32 | 21 | 21 | 5 | 3 | 3 |
| Chinese/HK (PK-hosted infra via S.B Link Network) | 4 | 4 | 0 | 0 | 4 | 0 |
| Government / Education (PK-hosted, ISP noted in source) | 4 | 4 | 0 | 0 | 4 | 0 |
| Tranco .pk: Government | 124 | 124 | 31 | 9 | 83 | 1 |
| Tranco .pk: Education | 178 | 178 | 78 | 55 | 44 | 1 |
| Tranco .pk: Commercial | 348 | 348 | 200 | 114 | 27 | 7 |
| Tranco .pk: Network/ISP | 57 | 57 | 20 | 18 | 13 | 6 |
| Tranco .pk: Organization | 51 | 51 | 21 | 24 | 6 | 0 |
| Tranco .pk: .pk (direct) | 770 | 770 | 531 | 190 | 33 | 16 |
| **Total** | **1781** | **1708** | **1029** | **470** | **246** | **36** |
