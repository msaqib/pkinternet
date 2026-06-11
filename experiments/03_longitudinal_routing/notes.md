# Experiment 03 — Longitudinal Routing (5 probes → 5 sites, every 15 min)

**Author:** Rayan Atif

## Objective

Experiments 01/01.1/01.2 take a **single snapshot** of where Pakistani sites live
and how each ISP reaches them. This experiment adds the **time axis**: from **5 PK
probes** (one per ISP), repeatedly traceroute the **same 5 destinations every 15
minutes** over a day, and record whether the **path** and the **RTT** change over
time — **per (site, probe)**, so ISPs can be compared. (The first run,
`run_20260610_2h`, used a single Nayatel probe as a baseline.)

The question it answers for PKIX work:

> For a real Pakistani user on a given ISP, is the route to a site **stable**, or
> does it flip between a local path and a foreign hairpin (different CDN PoP, different
> transit) depending on the time of day? How much does RTT swing across the
> diurnal (day/night) cycle?

A one-off measurement can't see this — a site that traces to Karachi at 18 ms now
might trace to Singapore at 100 ms at peak evening load. Catching that flip is the
whole point.

---

## What the two source papers tell us about *how* to measure

| Source | Relevant finding | What we take from it |
|---|---|---|
| **Di Bartolomeo et al., "Is It Really Worth to Peer at IXPs?"** (RIPE Atlas, ISCC 2015) | EXPERIMENT CIS: *"5 traceroutes … at intervals of 10 minutes … We intentionally performed few traceroutes … reducing the probability of measuring noise due to routing changes."* | A **~10–15 min traceroute spacing** is an established, sane cadence for RIPE-Atlas routing observation. We use 15 min. |
| same | EXPERIMENT SBA: *"one ping per minute and one traceroute every 10 minutes."* | **Path** is sampled at ~10–15 min; **RTT/loss** wants finer sampling (ping/min). Traceroute every 15 min captures path + coarse RTT; a 1/min ping companion (optional, §"Future") captures fine RTT/jitter/loss. |
| same | *"The great majority of the intervals were located during the **daytime hours, to avoid any time-of-day effect** on the measures [23]."* (ref [23] = Gill & Mahanti, RTT observations) | They **suppressed** the diurnal effect because it was a confound for them. Our goal is the **opposite** — we *want* to observe it — so we must sample **around the clock**, not daytime-only. |
| same | jitter = **stdev of rtt values**; packet loss = unanswered/sent ratio. | We compute the **same metrics longitudinally**: jitter = stdev of the destination RTT across rounds; "loss"/reachability = fraction of rounds the destination did not answer. |
| **Sanchez et al., "Inter-Domain Traffic Estimation for the Outsider"** (Network Syntax, IMC 2014) | CAIDA Ark probes in **~48-hour cycles**; two **30-day** campaigns **two years apart** to study evolution. | Natural observation windows: a **couple of days** is a complete short cycle; longer/repeat windows show evolution. We run **≥48–72 h**. |
| same | Vantage-point bias: *"an edge is much more likely to be visible if it is close to the vantage point."* | A single probe gives a **vantage-biased** view. That is exactly what we want here (this ISP's lived experience), but findings describe **this ISP**, not the global Internet. |
| same | §7.2 IP-to-AS pitfalls / false AS links from longest-prefix matching. | Keep Exp 01's correction stack: **Team Cymru + RDAP fallback** for hop ASNs, so a path "change" is real and not a mis-mapping artifact. |

### The single most important methodological point: **Paris traceroute**

A plain traceroute varies the flow tuple each run, so per-flow **load balancers**
send successive probes down **different physical paths** — the route looks like it
"changed" every 15 minutes when nothing actually changed. For a change-detection
experiment that is fatal. We use **ICMP Paris traceroute (`paris=16`)**, exactly
as Exp 01 does, so the flow identifier is held constant and an observed path
change reflects a **real routing/BGP change**, not multipath noise. (Paper 1's
robustness section is entirely about not letting measurement artifacts look like
real structure; this is the time-domain version of that warning.)

---

## Chosen methodology

| Decision | Value | Why |
|---|---|---|
| **Probes** | **5 PK probes** — 60223 Nayatel (AS23674), 62224 Transworld (AS38193), 7613 Z COM Networks (AS152605), 1016036 Cybernet (AS9541), 1015679 LocalInternetProj01 (AS136174) | One measurement per site runs from **all 5 at once** (RIPE multi-probe), so every output is **per (site, probe)** and ISPs are directly comparable. Each result carries its `prb_id`. Note: some probes (Docker / ICMP-filtering) may show `* * *` mid-path and can't reveal a *path* change — Nayatel remains the most route-visible. Earlier single-probe runs (e.g. `run_20260610_2h`) used only Nayatel. |
| **Targets** | **5 sites**, deliberately spread by behaviour (see `targets.md`) | One stable PK server (control), two Cloudflare anycast sites that were already seen to flip PoP (Karachi vs Hong Kong/Singapore) across ISPs, one US-hairpinning gov site, one foreign real server. The mix maximises the chance of *seeing* change and contrast. |
| **Traceroute type** | **ICMP, Paris (`paris=16`)**, `max_hops=32`, `size=48`, `dont_fragment` | Identical to Exp 01 so results are directly comparable, and Paris kills load-balancer false positives (above). |
| **Interval** | **15 min** (900 s) → 96 rounds/target/day | Matches the paper-2 cadence band (10 min), round number, low credit cost, fine enough to resolve the diurnal RTT curve and any path change lasting more than ~30 min. |
| **Duration** | **≥ 48–72 h, ideally including a weekend** | Must cover **full 24 h diurnal cycles** (peak-evening congestion vs early-morning) and ≥1 weekend/weekday contrast. 48 h is one CAIDA-Ark cycle; 72 h is safer. |
| **Scheduling** | RIPE Atlas **periodic measurement** (`is_oneoff=False`, `interval=900`, `start`/`stop`), **not** a local loop of one-offs | RIPE's own infrastructure fires every 15 min on time, survives our script/laptop dying, and is one measurement ID per target (5 total) instead of thousands of one-offs. Results persist on RIPE and are fetched later (matches CLAUDE.md's interrupted-run recovery philosophy). |
| **RTT recorded** | **min (best-of-3) reply** to the destination per round | Exp 01 stored the *first* reply (noisy — a documented caveat). For a time series we take the **min of the hop's replies**, which removes per-round queuing jitter and makes the diurnal trend cleaner. |

### What counts as "a change"

For each target we track, per 15-min round:
1. the **AS-path** string (`asns_in_path`, e.g. `23674 > 38193 > 13335`),
2. the **serving location** (`dest_location` — handoff metro for anycast),
3. the **destination RTT** (min reply), and **reachability** (did it answer).

A **path change** = the `asns_in_path` (or serving metro) differs from the previous
round. The readable `path_changes_*.txt` lists, per target, every distinct path
seen, the time windows it held, the transitions between them, and RTT
min/median/max + **jitter (stdev)** + reachability %. That report is the
longitudinal analogue of Exp 01's `routes_*.txt`.

### Why 15 min, and how it relates to "noticing changes"

- **Path (BGP) changes** persist from minutes to hours; 15-min sampling reliably
  catches anything lasting ≳ 30 min and bounds the timing of a flip to a 15-min
  window. Paper 2 used 10 min for the same kind of observation.
- **RTT / congestion** is a continuous diurnal curve; 96 samples/day resolves it
  well. To also catch **sub-15-min** congestion spikes and compute true jitter you
  would add a **1-ping/min** companion measurement (paper 2's SBA design) — cheap,
  and noted under Future work rather than run now.
- Going **faster than ~10 min adds noise, not signal** (paper 2's explicit reason
  for "few traceroutes"); going **slower than ~30 min** risks aliasing the diurnal
  cycle and missing short-lived reroutes. 15 min sits in the sweet spot.

---

## Output files per fetch  (mirrors Exp 01, plus a `trace_time` axis)

`experiments/03_longitudinal_routing/results/{RUN_NAME}/`:

| File | Contents |
|------|----------|
| `trace_grouped_TIMESTAMP.csv` | One row **per hop, per round** — same columns as Exp 01's `pk_grouped` plus `trace_time` (the round's actual UTC time). |
| `trace_summary_TIMESTAMP.csv` | One row **per target, per round**: `trace_time`, `dest_rtt_ms` (min reply), `total_hops`, `asns_in_path`, `countries_in_path`, `dest_location`, `destination_responded`. This is the **time series** you plot. |
| `ping_series_TIMESTAMP.csv` | *(ping companion)* one row **per ping (1/min)**: `ping_time`, `sent`, `rcvd`, `loss_pct`, `rtt_min/avg/max`. The fine-grained RTT/loss series. |
| `routes_TIMESTAMP.txt` | Readable **hop-by-hop traceroute**, one block per (site, 15-min round) — SOURCE/TIME/DEST header then the full path. The time-domain analogue of Exp 01's `routes_*.txt`. |
| `path_changes_TIMESTAMP.txt` | Readable per-target report: distinct AS-paths over time + transitions + RTT min/median/max + jitter + reachability %, **plus the ping companion's loss% / rtt / jitter** when it ran. |
| `measurements.json` | The periodic measurement IDs (trace + ping per target) + probe/target metadata, written at schedule time and read at fetch time. |

`watch` mode writes the same files with a `_live` suffix (overwritten each cycle)
instead of a timestamp, so there's always one current dataset mid-run; it also
writes a final timestamped snapshot when the window closes.

Results CSVs should be committed to git, one subfolder per run — same convention
as Exp 01.

---

## How to run

```bash
export RIPE_API_KEY="your-key-here"          # or .env at repo root

# 0) estimate data volume / storage / credits before spending anything
python experiments/03_longitudinal_routing/trace_monitor.py stats

# 1) schedule: 1 traceroute/15min per site, + (if PING_COMPANION) 1 ping/min per site
python experiments/03_longitudinal_routing/trace_monitor.py schedule

# 2a) one-shot: pull results so far + build timestamped CSVs
python experiments/03_longitudinal_routing/trace_monitor.py fetch

# 2b) OR auto-refresh the local data every INTERVAL_SEC until the window closes,
#     then (if AUTO_PUSH) auto-commit + push the results folder. Run inside
#     tmux/VNC so it survives SSH disconnects on a 24h run.
python experiments/03_longitudinal_routing/trace_monitor.py watch

# optional: stop the measurements early
python experiments/03_longitudinal_routing/trace_monitor.py stop
```

Edit `RUN_NAME`, `PROBES`, `TARGETS`, `INTERVAL_SEC`, `DURATION_HOURS`, and the
`PING_COMPANION` / `PING_INTERVAL_SEC` / `PING_PACKETS` / `AUTO_PUSH` knobs at the
top of `trace_monitor.py` before scheduling.

**Multi-probe credit cost.** One measurement per site fans out to all probes, so
cost scales with `targets × rounds × probes`. A 24 h, 5-probe, 5-site run is
**~156k credits** — and **~108k of that is the 1/min ping companion**. To cut it:
set `PING_INTERVAL_SEC = 300` (1/5 min → ~22k for pings), or `PING_COMPANION =
False`. `schedule` prints the estimate and asks for confirmation when run
interactively.

**Auto-push** (`AUTO_PUSH = True`) makes `watch` commit the run's results folder
and `git push` when the window closes. It needs working git auth on the machine
(SSH deploy key or cached HTTPS token); on failure it reports and leaves the files
in place (they're also safe on RIPE).

**Credit cost:** 5 targets × 96 rounds/day × ~20 credits ≈ **9.6k credits/day**
(~29k for a 72 h run) — well within budget.

---

## Caveats

- **Single vantage = vantage-biased** (paper 1): this is *Nayatel-from-Islamabad's*
  experience, not a global truth. Repeat on a second ISP to generalise (ties to
  Exp 02's probe deployment).
- **Anycast serving location is the handoff metro, not the HTTP `colo`** — same
  ICMP-vs-HTTP caveat as Exp 01 (`shaukatkhanum.org.pk` traced ~4 ms but served
  from Singapore). A change in handoff metro is still a genuine, meaningful routing
  change to record.
- **DNS resolved once at schedule time.** If a target is GeoDNS and its IP rotates
  mid-window, the periodic measurement keeps hitting the original IP. Exp 1.1
  showed only ~8 % of sites are GeoDNS; the 5 chosen here are not among them, but
  note it. (The script also records each round's actual `dst_addr` so a silent
  re-resolution would be visible.)
- **Paris fixes multipath, not all noise.** A genuine BGP path change and a
  load-balancer artifact are now distinguishable, but transient ICMP rate-limiting
  on a hop can still blank a mid-path hop; we key "change" on the **AS-path**, not
  raw IPs, to stay robust to that.
