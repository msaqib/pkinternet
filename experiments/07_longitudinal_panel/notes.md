# Experiment 07 — The PKIX-underuse longitudinal panel (flagship)

**Author:** Rayan Atif · **Status:** 🟢 LIVE — launched **2026-07-11**, auto-stops **2026-07-18 ~16:55 PKT** (two-account split running on `ispl02`)

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
  across the multiple probes we have per ISP (Cybernet ×3, Nayatel ×2, PTCL ×3). Add normalization across cities for the same ISP
  
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

## Cost & limits (7 days, ~15 probes, 100 websites)

Per-result cost: traceroute 30 credits, ping 3 credits.

| Our account quota | Full-panel usage | OK? |
|---|---|---|
| Daily credit spend **10,000,000/day** | trace 15·100·24·30 = 1.08M + ping 15·100·48·3 = 0.22M ≈ **1.3M/day** | ✅ far under |
| Daily result flow **1,000,000/day** | 36k trace + 72k ping ≈ **108k/day** | ✅ far under |
| **Parallel measurements 100** | 100 sites × (trace + ping) = **200** | ❌ **the one blocker** |
| Probes/measurement 1000 | 15 | ✅ |
| Measurements/target 25 | 2 | ✅ |

7-day total ≈ **9M credits**. The daily credit and result-flow caps are 10× bigger than needed —
**the only binding limit is the 100 parallel-measurement cap** (200 needed). A limit increase has
been **requested from RIPE**; once granted (≥200) the full both-together panel runs as designed.

**Until the increase lands**, run the caps-fitting fallback: **traceroute-only** (halves to 100
measurements) at any cadence — set `TRACE_ONLY = True` in the CONFIG block. Traceroute still yields
path + destination RTT, so it keeps both signals. (No need to reduce cadence for credits/results —
those caps are not binding.)

## Outputs (local only — never pushed)

A per-round **panel** row: `(ts_utc, ts_pkt, probe_id, probe, isp, target, class, rtt_min,
hop_count, loss, tromboned, exit_cc, transit)`.
- `results/<instance>/measurements.json` — the periodic measurement IDs (the **index** — back up).
- `results/<instance>/panel_<ts>.csv` — **distilled** long-format series (`rtt_min`, `loss`,
  `hop_count`, `tromboned`, `exit_cc`, `transit`); rewritten each fetch but cumulative (each fetch
  re-pulls all results since launch).
- `results/<instance>/routes_<ts>.txt` — readable traces (standing rule).
- `results/<instance>/raw_<ts>.json.gz` — **raw untouched RIPE JSON**, produced by `dump_raw.py`
  (run once after the 7-day window — see §3c). Not written during the run; recoverable any time from
  the measurement IDs, no credits.
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

### 3. Pick a mode (only the 100 parallel-measurement cap matters — see *Cost & limits* above)
The default 100 sites × (traceroute + ping) = **200 measurements**, over the **100** parallel cap.
Credits (~1.3M/day) and results (~108k/day) are far under our 10M and 1M daily quotas, so cadence
is *not* a concern. Two modes:
- **Full panel (once the limit increase lands)** — leave the CONFIG defaults (`TRACE_ONLY = False`,
  60 min / 30 min). Both ping + traceroute, all 100 sites, 7 days, 200 measurements.
- **Fallback until then** — set `TRACE_ONLY = True` in the CONFIG block → 100 measurements
  (traceroute only, which still gives path + destination RTT). Keep the hourly cadence; no need to
  slow it down.
- Other levers (same CONFIG block): `DURATION_DAYS`, `TRACEROUTE_EVERY_MIN`, `PING_EVERY_MIN`.

### 3b. Two-account launch — THE ACTUAL DEPLOYED PLAN (fits the 100 cap, keeps BOTH signals)
Since the parallel-measurement cap (100) is **per account**, we split by measurement *type* across two
credit-sharing accounts: **account A (Saqib's key, in `.env`) runs all 100 traceroutes, account B
(Rayan's key, in `~/panel_ripe_key`) runs all 100 pings** → 100 measurements each (at the cap), the
same `targets.csv`, and the merged result is identical to the full single-account panel.
`PANEL_INSTANCE` namespaces outputs to `results/a/` and `results/b/` so both run on the one host.
Credits are **per-account** (RIPE has no shared pool — "sharing" is a manual transfer; B was topped
up to 2M by transfer from A).

**Step 1 — schedule both (run once each; creates the server-side periodic measurements):**
```bash
cd ~/pkinternet && source .venv/bin/activate

# Account A — 100 traceroutes (key comes from .env)
PANEL_TRACE_ONLY=1 PANEL_INSTANCE=a PANEL_PARALLEL_CAP=100 \
  python experiments/07_longitudinal_panel/panel_monitor.py schedule

# Account B — 100 pings (key from ~/panel_ripe_key via PANEL_RIPE_KEY)
PANEL_RIPE_KEY="$(cat ~/panel_ripe_key)" PANEL_PING_ONLY=1 PANEL_INSTANCE=b PANEL_PARALLEL_CAP=100 \
  python experiments/07_longitudinal_panel/panel_monitor.py schedule
```
Each prints its plan (`100 targets × 1 type(s) = 100 measurements`), then a line per site, then
`scheduled 100 periodic measurements … saved results/{a,b}/measurements.json`. *(Cosmetic: the
`scheduling … (trace+ping)` log line is a stale label — single-type mode really creates only the one
type, as the `1 type(s)` count and per-line `trace`/`ping` prefix confirm. The Python-3.8
`CryptographyDeprecationWarning` is harmless.)*

**Step 2 — start the two watchers in tmux (so they survive SSH disconnect):**
```bash
# Traceroute watcher
tmux new -s watch_a
#   inside tmux:
cd ~/pkinternet && source .venv/bin/activate
PANEL_TRACE_ONLY=1 PANEL_INSTANCE=a PANEL_PARALLEL_CAP=100 \
  python experiments/07_longitudinal_panel/panel_monitor.py watch
#   detach (leaves it running):  Ctrl-b  then  d       <-- a KEY COMBO, not text to type

# Ping watcher
tmux new -s watch_b
#   inside tmux:
cd ~/pkinternet && source .venv/bin/activate
PANEL_RIPE_KEY="$(cat ~/panel_ripe_key)" PANEL_PING_ONLY=1 PANEL_INSTANCE=b PANEL_PARALLEL_CAP=100 \
  python experiments/07_longitudinal_panel/panel_monitor.py watch
#   detach:  Ctrl-b  then  d
```

**Managing / watching on the server (any time, from a fresh SSH session):**
```bash
tmux ls                          # should list watch_a and watch_b -> both alive
tmux attach -t watch_a           # peek at live output; detach again with Ctrl-b then d
ls -lt experiments/07_longitudinal_panel/results/a/   # traceroute CSV + routes.txt piling up
ls -lt experiments/07_longitudinal_panel/results/b/   # ping CSV
```
**Golden rule:** to *leave a watcher running*, detach with **`Ctrl-b` then `d`** — never `Ctrl-C`
(that kills it). If a watcher dies, the RIPE measurements keep running server-side; only the local
CSV harvesting pauses until you restart that watcher.

Outputs land in `results/a/` (traceroutes) and `results/b/` (pings); **merge them at analysis**
(join on probe + target + timestamp). Both accounts discover the same live PK probes, so the data
is consistent. (`PANEL_RIPE_KEY` overrides the `.env` key per account; `TARGETS_FILE` can point at
a different list if you'd rather split by site instead of by type.)

### 3c. ⏰ REMINDER — pull the raw results after the run (2026-07-18)
The `watch`/`fetch` CSVs are **distilled** (per-round `rtt_min`, `loss`, `hop_count`, `tromboned`,
`exit_cc`, `transit`) and are **overwritten each cycle** — but each fetch re-pulls *all* results
since launch, so the single latest `panel_*.csv` is cumulative/complete. The **raw RIPE JSON is not
archived to disk**; it lives permanently on RIPE's servers, keyed by the measurement IDs saved in
`results/a/measurements.json` + `results/b/measurements.json`. It is re-fetchable any time, **no
credits spent, no expiry.**

**After the window closes (on/after 2026-07-18), do one raw pull** — this is the archival dataset:
```bash
cd ~/pkinternet && source .venv/bin/activate
python experiments/07_longitudinal_panel/dump_raw.py        # -> results/{a,b}/raw_*.json.gz
```
`dump_raw.py` reads both `measurements.json` files and writes gzipped raw JSON for all 200
measurements — the untouched RIPE output, independent of RIPE staying reachable.
**Do not lose the two `measurements.json` files** — they are the index of measurement IDs; back them
up somewhere off-server as a safeguard.

### 4. Schedule the run (single-account, if the cap gets raised)
```bash
# after RIPE raises the parallel cap to >=200:
export PANEL_PARALLEL_CAP=200
python experiments/07_longitudinal_panel/panel_monitor.py schedule
```
Discovers all live PK probes, reads `targets.csv`, and creates the server-side periodic
measurements for the 7-day window (writes `results/measurements.json`, printing each measurement
id). **Run this once.**

**Preflight guard:** `schedule` first prints the plan (`N targets × K types = M measurements`,
current running count, cap) and **aborts without creating anything** if `M` would exceed the cap
(default 100, override with `PANEL_PARALLEL_CAP`). So running it *before* the limit increase is
safe — it just reports and stops. To proceed: raise `PANEL_PARALLEL_CAP` once RIPE bumps the limit,
or set `TRACE_ONLY = True` (100 measurements), or `PANEL_FORCE=1` to bypass the check. *(Verified:
one-off 15-probe test to `airblue.com` returned all 15 probes' traceroute + ping in ~90 s; and the
guard correctly aborts the 200-measurement plan under the 100 cap, creating nothing.)*

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

### Config (edit the CONFIG block at the top of `panel_monitor.py`; env vars override)
| setting / env var | default | meaning |
|---|---|---|
| `RIPE_API_KEY` (env / `.env`) | — | RIPE Atlas key |
| `DURATION_DAYS` | 7 | run length in days |
| `TRACEROUTE_EVERY_MIN` | 60 | minutes between traceroutes |
| `PING_EVERY_MIN` | 30 | minutes between pings |
| `WATCH_EVERY_MIN` | 30 | minutes between `watch` fetches |
| `TRACE_ONLY` / `PANEL_TRACE_ONLY` | False / 0 | skip pings (100 measurements, fits the cap) |
| `PING_ONLY` / `PANEL_PING_ONLY` | False / 0 | only pings (100 measurements; account B) |
| `PANEL_PARALLEL_CAP` (env) | 100 | preflight abort threshold; set to your raised RIPE cap |
| `PANEL_FORCE` (env) | 0 | 1 = bypass the preflight guard |
| `PANEL_INSTANCE` (env) | — | namespaces outputs to `results/<instance>/` (multi-account) |
| `PANEL_RIPE_KEY` (env) | (from `.env`) | per-account key override (multi-account) |
| `TARGETS_FILE` (env) | `targets.csv` | use a different target list (e.g. a site-split half) |

## Status

**🟢 LIVE — launched 2026-07-11 on `ispl02`; auto-stops 2026-07-18 ~16:55 PKT.** Deployed as the
two-account split (§3b): **account A = 100 traceroutes** (`results/a/`), **account B = 100 pings**
(`results/b/`), both under the per-account 100-parallel cap, both scheduled and confirmed
(`measurements.json` written for each; msm ids 189032884…189033055 traceroutes, 189033057…189033220
pings). Both watchers run in tmux (`watch_a`, `watch_b`) harvesting distilled CSVs every 30 min.
`targets.csv` is the **final 100-site stratified sample** (40 Pakistan / 40 CDN / 20 Abroad,
sector-proportional; source `data/pk_100_final_v2.csv`). Credit (~1.3M/day vs 10M) and result-flow
(~108k vs 1M) quotas are comfortable; B was funded to 2M by transfer from A.

**⏰ Next action (on/after 2026-07-18):** run `dump_raw.py` for the archival raw JSON pull (§3c),
then merge `results/a` + `results/b` and start analysis (per-ISP KPI CDFs, diurnal/weekly, trombone
intermittency, and — if a cable fault landed in the window — event-vs-baseline).


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
