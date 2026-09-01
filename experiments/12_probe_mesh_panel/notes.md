# Experiment 12 — Probe-mesh panel (7-day longitudinal version of Exp 11)

## Objective

Exp 11 answered "does inter-ISP handoff quality depend on which pair of probes you
measure between" with a **single pass** (repeated a few times by hand). This experiment
turns that into a proper **7-day panel**: every connected PK probe pings every other
connected PK probe **hourly**, and traceroutes every other probe **twice a day**,
continuously for a week — the same "one framework, all probes, run continuously"
discipline Exp 07 used for websites, applied to probe-to-probe paths.

Feeds the same questions as Exp 11 (RQ2 same-ISP consistency, PKIX Set 1/2/3
classification, route symmetry) but adds the axis Exp 11 couldn't: **is a pair's
verdict stable over a week, or does it flip** (the Exp 04/07 tromboning-intermittency
question, now applied to ISP-to-ISP paths instead of probe-to-website paths).

## First thing: find out who's online

Before anything is scheduled, **always** run the free, no-credit roster check:

```
python experiments/12_probe_mesh_panel/mesh_panel_monitor.py list
```

**Which live source, and why.** Two different live sources exist in this repo and they
disagree in practice:

- **`mesh_sweep.py`'s `KNOWN_IDS`** (Exp 11) — a hardcoded list of 19 IDs, filtered to
  Connected + usable IPv4 at runtime. It's live-filtered but the *candidate* list itself
  is stale — checked against sir's roster sheet, it's missing several currently-online
  probes (`1016467`, `1016468`, `65761`) and includes one (`1014872`, fasttel.isb) that
  isn't even on the current sheet anymore.
- **Sir's Google Sheet, cross-checked live** (`tools/probe_status/app.py`'s method) —
  the actual project roster (40 rows as of 2026-08-28), joined against live RIPE status.
  Most complete and accurate, but depends on an external sheet URL (`SHEET_CSV_URL`) at
  run time, which this offline batch script can't assume is always set.
- **Plain RIPE `country_code=PK, status=1`** (Exp 07's exact method, and what this
  script uses) — ask RIPE directly for every Connected probe self-reporting
  `country_code=PK`. No hardcoded list, no external sheet dependency, same mechanism the
  flagship experiment already relies on. Trade-off, seen live on 2026-08-28: this
  returned **17** probes, of which 2 (`1001359`, `1017098`) are **not** on sir's roster
  at all — they resolve to Falcon Broadband and Leap Digitals, i.e. other operators'
  RIPE Atlas probes that merely happen to also be in Pakistan — and it can miss a real
  roster probe if that probe's `country_code` field is stale or unset. It was chosen
  anyway to match Exp 07's convention exactly and avoid a live external dependency; the
  daily `check` roster section (below) surfaces any such mismatch instead of hiding it.

`list` prints every probe this method finds, flags which ones have a usable public
IPv4 (can be a *target*; probes without one, e.g. behind CGNAT, can still *source*
measurements), and should be re-run right before `schedule` too — the connected set
moves within minutes, not days.

## Why not N·(N-1) directed one-off pairs (Exp 11's approach), server-side and periodic

Exp 11 creates one measurement per **directed pair** (272 one-offs for N=17) because a
one-off is cheap to fire once. Doing that **periodically** for a week would mean 156
ping + 156 traceroute *periodic* measurement definitions all "Ongoing" simultaneously —
544 for N=17, and it only gets worse as the roster grows. That blows straight through
the 100-parallel-measurement cap that was already the binding constraint on Exp 07 (see
Exp 07 notes, "Cost & limits").

The fix: a RIPE Atlas measurement already fans **one target** out to **many source
probes** in a single object (`AtlasSource(type="probes", value="<comma list>")`) — this
is exactly how Exp 07 sends one website to all 14 probes in one measurement. Applying
the same trick here: for each candidate **destination** probe, create *one* periodic
ping measurement and *one* periodic traceroute measurement whose **sources = every
other connected probe**. That still measures every directed pair (each result is
tagged with its own `prb_id`, i.e. the actual source), but collapses the measurement
*count* from `2·N·(N-1)` to **`2·N`** — 34 for N=17, self-scaling headroom to ~50 probes
before the parallel cap becomes a concern again.

## Design

| | |
|---|---|
| **Probes** | All probes RIPE reports as Connected with `country_code=PK` (Exp 07's exact discovery method), discovered live via `list`/`schedule` — never hardcoded. 17 as of 2026-08-28, of which every probe with a usable public IPv4 can be a target |
| **Topology** | Full directed mesh: every probe → every other probe, both directions measured independently (asymmetric routing is itself a finding — Exp 11 precedent) |
| **Cadence** | **1 ping/hour** (ICMP, `packets=3`) + **1 traceroute every 12 h** (TCP/80 Paris, `paris=16`, `packets=3`) per direction — twice a day, as asked |
| **Duration** | 7 days |
| **Mechanism** | Server-side RIPE **periodic** measurements, fan-out design above: per destination probe, one ping measurement + one traceroute measurement with `sources = all other connected probes`. `2·N` measurement objects total, not `2·N·(N-1)` |
| **Target** | Each probe's own public `address_v4` (RIPE has no "probe→probe" measurement type — same workaround as Exp 11) |

ICMP-filtered probes (`transworld.lhe` 62224, `ptcl.lhe` 7764 — see Exp 11) will show
thin/opaque traceroutes whether they're source **or** destination; ping RTT is the
reliable signal for those pairs, same convention as every prior experiment.

## Cost & limits (7 days, N=17 connected probes — recomputed live at `schedule` time)

| Quantity | Formula | Value (N=17) |
|---|---|---|
| Periodic measurements | `2·N` | **34** |
| Ping rounds/destination | 7 days ÷ 1 h | 168 |
| Traceroute rounds/destination | 7 days ÷ 12 h | 14 |
| Ping results (≤) | `N·(N-1)·168` | 45,696 |
| Traceroute results (≤) | `N·(N-1)·14` | 3,808 |
| Credits (ping @3cr + trace @30cr) | | ≤251,328 |
| Result flow | | ≤49,504 total, ~7,072/day |

| RIPE account cap | This run | OK? |
|---|---|---|
| Parallel measurements (100) | 34 | ✅ huge headroom (roster can grow to ~45 before revisiting) |
| Probes/measurement (1000) | N−1 = 16 | ✅ |
| Daily credit spend (10M/day) | ~36k/day avg | ✅ trivial — ~2.8% of Exp 07's total 7-day budget, in total |
| Daily result flow (1M/day) | ~7,072/day | ✅ trivial |

No two-account split needed (unlike Exp 07) — everything fits one account with room to
spare, which is also why the daily-check tooling below can afford to poll every
measurement's live status on every run without worrying about quota.

## Operations

Same three-mode shape as Exp 07/11, plus the health check this experiment adds:

```
python mesh_panel_monitor.py list        # who's online right now (free, run first, and again before schedule)
python mesh_panel_monitor.py schedule    # create the 2·N periodic measurements, 7-day window
nohup python mesh_panel_monitor.py watch &   # background: pulls new results every hour -> panel CSV + routes txt
python mesh_panel_monitor.py check       # <- run this once a day: health report, see below
python mesh_panel_monitor.py fetch       # one-off pull, same as watch's cycle but on demand
python mesh_panel_monitor.py stop        # stop early if needed
```

`schedule` refuses to run twice (won't overwrite `results/measurements.json`), and
aborts before creating anything if the plan would exceed the parallel cap — same
preflight discipline as Exp 07 (`MESH_FORCE=1` to override).

### Daily check — "so I know nothing is going wrong"

Run once a day:

```
python experiments/12_probe_mesh_panel/mesh_panel_monitor.py check
```

Spends **no credits** (only reads measurement status + results, never creates
anything) and writes `results/health_<YYYYMMDD>.md` as well as printing to stdout.
It checks, in order:

1. **Roster drift.** Re-fetches live probe status and diffs it against the roster
   frozen at `schedule` time. A probe that has gone offline mid-week doesn't crash
   anything (the periodic measurements it doesn't source from just silently stop
   getting entries from it) — but it's easy to miss without an explicit flag, so this
   surfaces it by name every day.
2. **Per-measurement liveness.** For each of the `2·N` measurements: RIPE-reported
   status (should stay `Ongoing` until the window ends), time since its last result
   (flags anything silent for >2× its own interval), and actual vs. expected result
   count so far (flags anything under ~70% of what the elapsed time implies — a
   partial-failure signal a simple "is it Ongoing" check would miss).
3. **Loss outliers.** Per directed pair, packet loss over the run so far compared
   against the fleet's own average — flags pairs whose loss is well outside the
   pack (candidate real ISP-handoff problems, not just routine background loss).
4. **Quota.** Current running-measurement count on the account vs. the cap, so a
   collision with some other experiment sharing the account shows up immediately.

The report ends with a one-line verdict (`✅ all clear` or `⚠ N item(s) need
attention`) so a 5-second glance at the terminal is enough on a normal day, and the
saved `health_<date>.md` files form a running audit trail for the write-up ("the panel
ran clean throughout" or "probe X dropped on day 4, see health_20260904.md").

## Outputs

- `results/roster.json` — the probe roster frozen at `schedule` time (id, ISP/city
  label, ASN, IP) — the baseline the daily roster-drift check diffs against.
- `results/measurements.json` — the `2·N` periodic measurement IDs, keyed by
  destination probe. **Back this up** — it's the only index into the RIPE-side data.
- `results/panel_<ts>.csv` — distilled long-format rows: `ts_utc, ts_pkt, kind,
  src_probe_id, src, dst_probe_id, dst, rtt_min, loss, hop_count, tromboned, status,
  exit_cc, transit`. Rewritten each `watch` cycle, cumulative since launch (same
  convention as Exp 07).
- `results/routes_<ts>.txt` — latest traceroute per directed pair, readable.
- `results/health_<date>.md` — one per day `check` is run, the audit trail above.

## Analysis plan

1. **Symmetry table** — for every unordered pair, diff i→j vs j→i verdict/RTT across
   the whole week (Exp 11's single-pass version, now with a full week of samples per
   direction instead of one).
2. **Stability over time** — per-pair trombone-verdict flip rate across the week,
   the direct probe-mesh analogue of Exp 07's website tromboning-intermittency finding.
3. **Set 2 vs Set 3 classification** — same as Exp 11 §3, now backed by a week of
   samples per pair instead of a handful of repeats.
4. **Diurnal structure** — does inter-ISP RTT/loss show the same time-of-day pattern
   Exp 07 found for probe→website paths, or is it flatter once the destination's own
   hosting/CDN choice is removed from the picture?

## Relationship to other experiments

- **Extends Exp 11** from a one-off census (repeated by hand 3-4 times) to a proper
  7-day continuous panel, using the same target-workaround, RTT-physics detector, and
  ICMP-filtered-probe handling.
- **Mirrors Exp 07's operational shape** (server-side periodic measurements, `list →
  schedule → watch → fetch → stop`, host-independent collection) but adds the daily
  `check` health report Exp 07 didn't have — worth back-porting if useful there too.
