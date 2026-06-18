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
| **Probes** | **8 PK probes** across 6 ISPs (full list in `targets.md`): Nayatel, Transworld, Z-Com (anchor), **Cybernet ×2**, **PTCL ×2** (7764 anchor + 1016126), TPCPL/Nova. All connected PK probes except the Endangered one (1014872). | One measurement per site runs from **all 8 at once** (RIPE multi-probe), so every output is **per (site, probe)** and ISPs are directly comparable. Each result carries its `prb_id` and its **live-measured egress ASN** (two probes share AS9541, two share AS17557). Note: some probes (Docker / ICMP-filtering) show `* * *` mid-path and can't reveal a *path* change — Nayatel is the most route-visible. Earlier runs used fewer probes (`run_20260610_2h` = 1, `run_20260611_24h` = 5). |
| **Targets** | **10 sites**, spread by behaviour (see `targets.md`) | 2 PK-hosted controls, 2 local-Cloudflare, 2 international-Cloudflare, 1 ecommerce abroad, 2 banks abroad, 1 GeoDNS/anycast gov. The mix maximises the chance of *seeing* PoP flips / diurnal change while keeping stable baselines. |
| **Traceroute type** | **ICMP, Paris (`paris=16`)**, `max_hops=32`, `size=48`, `dont_fragment`, **3 packets/hop** (RIPE default) | Identical to Exp 01 so results are directly comparable, and Paris kills load-balancer false positives (above). |
| **Interval** | **15 min** (900 s) → 96 rounds/target/day | Matches the paper-2 cadence band (10 min), round number, low credit cost, fine enough to resolve the diurnal RTT curve and any path change lasting more than ~30 min. |
| **Duration** | **≥ 48–72 h, ideally including a weekend** | Must cover **full 24 h diurnal cycles** (peak-evening congestion vs early-morning) and ≥1 weekend/weekday contrast. 48 h is one CAIDA-Ark cycle; 72 h is safer. |
| **Scheduling** | RIPE Atlas **periodic measurement** (`is_oneoff=False`, `interval=900`, `start`/`stop`), **not** a local loop of one-offs | RIPE's own infrastructure fires every 15 min on time, survives our script/laptop dying, and is one measurement ID per target (10 trace + 10 ping = 20) instead of thousands of one-offs. Results persist on RIPE and are fetched later (matches CLAUDE.md's interrupted-run recovery philosophy). |
| **RTT recorded** | **min (best-of-3) reply** to the destination per round | Exp 01 stored the *first* reply (noisy — a documented caveat). For a time series we take the **min of the hop's replies**, which removes per-round queuing jitter and makes the diurnal trend cleaner. |

### Packets per traceroute (and what "a round" costs)

Each traceroute probes by **incrementing TTL** (1, 2, 3, …); the router that many
hops away replies. At **each hop (each TTL) RIPE sends 3 packets** — this is the
RIPE default and we don't override it. So:
- Each hop gets up to **3 RTT samples**, and we record the **min (best-of-3)** —
  see the *RTT recorded* row; the other two still cost packets but aren't stored.
- A traceroute **stops when it reaches the destination**, not at `max_hops`. So a
  path that reaches the target in 12 hops sends ≈ **12 × 3 = 36 packets** out (plus
  replies), not 32 × 3. Timed-out hops (`* * *`) still cost their 3 packets.
- A **"round"** in the `watch` log = one *whole* traceroute (one probe → one target
  at one 15-min mark), **not** a packet. Each 15-min cycle adds up to
  `sites × probes` rounds (25 here). This `~hops × 3 packets/round` is exactly the
  assumption behind the wire-traffic figure in `stats` (~32 MB for the full run).

To send fewer packets (cheaper, slightly noisier RTT) add `"packets": 1` to the
traceroute payload in `create_periodic` — but 3 is the sensible default.

### What counts as "a change"

For each target we track, per 15-min round:
1. the **AS-path** string (`asns_in_path`, e.g. `23674 > 38193 > 13335`),
2. the **serving location** (`dest_location` — handoff metro for anycast),
3. the **destination RTT** (min reply), and **reachability** (did it answer).

A **path change** = the `asns_in_path` (or serving metro) differs from the previous
round. `fact_trace` carries `asns_in_path` + `dest_location` per round, so the
analysis notebook derives, per (site, probe), every distinct path seen, the
transitions between them, and RTT min/mean/max + **jitter (stdev)** + reachability %
(see `findings/03_*_48h.ipynb` §10, the path-change + ASN tables).

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

## Output files  (a normalized star schema + a readable routes report)

`experiments/03_longitudinal_routing/results/{RUN_NAME}/` (committed to git):

| File | Contents |
|------|----------|
| `normalized/dim_probe.csv` | One row per probe: `probe_id` (key), `label` (`isp.city (ASN)`), `isp`, `city`, `city_code`, `asn_registered`, `probe_ip`. |
| `normalized/dim_site.csv` | One row per target: `site_id` (key), `target_label`, `target_hostname`, `target_category`. |
| `normalized/fact_trace.csv` | One row **per (probe, site, round)**: `trace_id` (key), `trace_time`, `probe_id`, `site_id`, `probe_asn_measured`, `dest_rtt_ms` (min reply), `total_hops`, `asns_in_path`, `countries_in_path`, `dest_location`, `destination_responded`, `measurement_id`. The **time series** you plot. |
| `normalized/fact_hop.csv` | One row **per hop**, linked to its round by `trace_id`: `hop`, `hop_ip`, `rtt_ms`, `hop_asn`, `hop_prefix`, `hop_country`, `hop_asn_name`, `is_private`, `is_timeout`. |
| `normalized/fact_ping.csv` | *(ping companion)* one row **per ping**: `ping_id`, `ping_time`, `probe_id`, `site_id`, `sent`, `rcvd`, `loss_pct`, `rtt_min/avg/max`. |
| `routes_TIMESTAMP.txt` | Readable **hop-by-hop traceroute**, one block per (site, round) — SOURCE/TIME/DEST header then the full path. The time-domain analogue of Exp 01's `routes_*.txt`. |
| `measurements.json` | The periodic measurement IDs (trace + ping per target) + probe/target metadata, written at schedule time and read at fetch time. |

This is a **star schema**: the facts reference the dimensions by numeric id and
repeat no descriptive text, so the data is ~40 % of the old flat-CSV size with no
loss (verified row-for-row). It is written with pure stdlib (no pandas) so the
server needs nothing beyond `requests`/`dnspython`. Re-join it for analysis with a
read + merge on `probe_id`/`site_id`/`trace_id` (see `findings/03_*_48h.ipynb`,
which loads it in three lines).

`watch` mode does **not** write these every cycle. Each cycle it refreshes a
**local-only Prometheus textfile** `live/{RUN_NAME}/exp03_live.prom` — the latest
RTT/loss per (probe, site) + probe liveness as gauges (`exp03_dest_rtt_ms`,
`exp03_ping_rtt_ms`, `exp03_ping_loss_pct`, `exp03_probe_up`). It lives **outside**
`results/`, so it is never committed or zipped; node_exporter's textfile collector
scrapes it → Prometheus → Grafana for a live on-server dashboard. The committed
normalized snapshot + routes file are written once when the window closes (or on
Ctrl-C). Results are committed to git, one subfolder per run.

---

## How to run

```bash
export RIPE_API_KEY="your-key-here"          # or .env at repo root

# 0) estimate data volume / storage / credits before spending anything
python experiments/03_longitudinal_routing/trace_monitor.py stats

# 1) schedule: 1 traceroute/15min per site, + (if PING_COMPANION) 1 ping/min per site
python experiments/03_longitudinal_routing/trace_monitor.py schedule

# 2a) one-shot: pull results so far + write the normalized snapshot + routes file
python experiments/03_longitudinal_routing/trace_monitor.py fetch

# 2b) OR refresh the local-only live/<run>/exp03_live.prom every INTERVAL_SEC for
#     Grafana/Prometheus; when the window closes, write the committed normalized
#     snapshot + routes and (if AUTO_PUSH) commit + push the results folder. Run
#     inside tmux/VNC so it survives SSH disconnects on a long run.
python experiments/03_longitudinal_routing/trace_monitor.py watch

# optional: stop the measurements early
python experiments/03_longitudinal_routing/trace_monitor.py stop
```

Edit `RUN_NAME`, the probe set (`PROBE_META` + `PROBE_IDS`, which build the clean
`isp.city (ASN)` labels), `TARGETS`, `INTERVAL_SEC`, `DURATION_HOURS`, and the
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

**Credit cost** scales with `targets × rounds × probes` (+ ping). Run `stats` for the
exact figure; e.g. the 48 h × 8-probe × 10-site run with **1 ping/5 min** is
**~445k credits**. The 1/min ping would have been ~1M — the ping cadence is the main
cost lever (`PING_INTERVAL_SEC`). Check your balance with the RIPE credits API first.

---

## Dynamic probe ASN (multi-ISP / campus probes)

Each probe's ASN is **measured every round**, not taken from what we registered in
`PROBES`. A probe at a multi-homed site (e.g. a university campus with PERN/HEC +
a commercial ISP) can egress via **different ISPs round to round**, so its true
origin ASN is a moving quantity — the registered value is just a point-in-time guess.

**How** (RIPE-compatible): we can't shell into a RIPE Atlas probe to run the
`whois $(curl -s ifconfig.me)` one-liner. But every RIPE result already carries the
probe's **public egress IP** in the `from` field, so `_probe_live_asn()` runs that
through the same Team Cymru lookup we use everywhere else — the data-plane
equivalent of the `whois` command, derived per round. (If we ever deploy our **own**
measurement nodes on campus servers we control, that exact `curl/whois` one-liner is
what we'd embed instead, writing the same columns.)

**What gets recorded** (`probe_asn_measured`/`probe_ip` per round in `fact_trace` and
`fact_ping`; the registered ASN once in `dim_probe`):
- `probe_id` — the RIPE probe (stable; the foreign key into `dim_probe`).
- `probe_asn_measured` — ASN **measured this round** from the egress IP (source of truth).
- `asn_registered` (`dim_probe`) — the ASN we registered in `PROBE_META` (for comparison).
- `probe_ip` — the public egress IP the ASN was derived from.

**An ASN changes when:** the site is multi-homed and load-balances/policy-routes
across ISPs; an ISP link fails over to a backup; a dynamic public IP rotates or the
host changes provider (registered ASN now stale); a prefix is re-homed (different
origin ASN in BGP); or the probe is physically moved.

The notebook's ASN table (§10) flags this: it lists each probe's **measured** egress
ASN(s) vs its **registered** ASN and marks any probe whose egress ASN varies across
rounds (multi-homed) or differs from registration. (Across all runs so far every
probe was stable on its registered network.)

---

## Results & findings

This file is the **methodology**; per-run results live in `findings/` (Exp 01
convention). Written up so far:

| Run | Findings doc | What it shows |
|-----|--------------|---------------|
| `run_20260610_2h` (1 probe, 5 sites, 2 h) | [`findings/03_longitudinal_routing_analysis.md`](../../findings/03_longitudinal_routing_analysis.md) | Baseline + pipeline validation: clean local-vs-offshore latency snapshot. |
| `run_20260611_24h` (5 probes, 5 sites, 24 h) | [`findings/03_longitudinal_routing_24h.md`](../../findings/03_longitudinal_routing_24h.md) | The full per-ISP day, **incl. the overnight thunderstorm outage**. |
| `run_20260612_48h` (8 probes, 10 sites, 48 h) | *pending* (will be `…_48h.md`) | Two diurnal cycles; CDN-PoP-flip + PTCL-vantage run. |

Charts: [`findings/03_longitudinal_routing.ipynb`](../../findings/03_longitudinal_routing.ipynb)
(per-probe + per-site ping-fluctuation graphs, PKT).

**24 h headline:** a Pakistani user reaches **local** government/news in **2–40 ms**
(wildly ISP-dependent — same site is 1.6 ms on Z-Com vs 42 ms on Cybernet) but their
**banks in 127–211 ms regardless of ISP, because both banks are hosted offshore**
(MCB→Singapore, HBL→New Jersey). Over the full day there was **no diurnal congestion
cycle and no route flapping** — so for these sites the inefficiency is a
**hosting/peering** problem (the PKIX story), not a time-of-day capacity problem. The
only real event was a **~5.7 h ISP outage** (TPCPL/Nova) during an overnight
thunderstorm, which the method captured cleanly as a gap across all targets.

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
