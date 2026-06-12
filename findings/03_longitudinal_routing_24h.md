# Findings 03 (24h run) — Longitudinal Routing, 5 ISPs × 5 sites

**Dataset:** `run_20260611_24h` — 5 RIPE probes (one per PK ISP) × 5 sites, ICMP
Paris traceroute every 15 min + 1/min ping, **24 h** (2026-06-11 09:14 → 2026-06-12
09:05 UTC). 2,262 trace rounds, ~34k pings. Charts: `findings/03_longitudinal_routing.ipynb`.

> Probes: Nayatel (AS23674), Transworld (AS38193), Z COM Networks (AS152605),
> Cybernet (AS9541), LocalInternetProj01 (AS136174). Sites: dunyanews.tv, hbl.com,
> mcb.com.pk, ptcl.com.pk, pseb.org.pk.

---

## 1. Median RTT (ms) — site × ISP

| Site (hosting) | Cybernet | LocalIP01 | Nayatel | Transworld | Z-Com |
|---|---:|---:|---:|---:|---:|
| **Dunya News** (PK, Multinet) | 42.0 | 2.9 | 39.3 | 6.8 | **1.6** |
| **PSEB** (PK, Multinet) | 24.5 | 37.8 | **22.8** | 41.2 | 36.2 |
| **MCB Bank** (Sucuri, Singapore) | 138.5 | 131.9 | 128.7 | 136.7 | **126.7** |
| **HBL Bank** (Incapsula, New Jersey) | 211.1 | 211.3 | **199.8** | 202.6 | 201.9 |
| *PTCL* | — ICMP-blocked at host (100% no-reply) — trust the traceroute path | | | | |

## 2. Local sites: a huge, destination-dependent ISP gap

For the *same locally-hosted content*, the ISP you're on changes RTT by up to **~26×**:
- **Dunya News:** Z-Com **1.6 ms**, LocalIP01 2.9, Transworld 6.8 — but Nayatel **39**
  and Cybernet **42**. Same Multinet server, 25× difference.
- **PSEB:** the ranking **flips** — Nayatel **22.8** and Cybernet 24.5 are fastest,
  while Transworld 41 and Z-Com 36 are slowest.

So there is **no universally "fast" ISP** — it depends on each ISP's peering to that
specific destination network. (Z-Com/Transworld peer well for Dunya's prefix;
Nayatel/Cybernet peer better for PSEB's.) This is the per-ISP routing-quality story
from Exp 01, now confirmed stable over a full day.

## 3. Offshore banks: ISP barely matters — distance dominates

For the two banks hosted abroad, all five ISPs converge:
- **HBL (New Jersey):** ~**200–211 ms** on every ISP.
- **MCB (Singapore):** ~**127–139 ms** on every ISP.

The spread across ISPs is a few ms — the ~200/~130 ms is the **cost of leaving the
country**, not an ISP-routing artifact. Compared to the local sites (2–40 ms), that's
the offshore-hosting penalty, **3–9× even on the best local ISP**.

## 4. No meaningful diurnal variation — the penalty is structural

Holding a clean probe fixed (Nayatel) and taking median RTT per hour over 24 h:

| Site | hourly-median RTT range | spread |
|---|---|---|
| HBL Bank | 200–201 ms | **1 ms** |
| PSEB | 23–24 ms | 2 ms |
| Dunya News | 39–44 ms | 5 ms |
| MCB Bank | 128–129 ms, + two isolated spikes (155 @09 UTC, 179 @17 UTC) | — |

There is **no smooth peak-evening congestion curve**. Latency to the offshore banks
was essentially constant all day; the only deviations are two brief MCB spikes (one
mid-morning, one evening UTC ≈ 22:00 PKT). **Conclusion:** the offshore penalty is
**structural** (physical distance + hosting choice), not peak-hour congestion — a
question the 2 h baseline literally couldn't answer, now settled by the 24 h window.

## 5. Routing was stable — ~zero genuine path changes in 24h

Across all 25 (site × ISP) pairs over 96 rounds each, the AS-path was **stable the
whole day**. Two pairs were flagged by the change detector but on inspection are
**last-hop visibility flicker, not route changes**:
- `MCB / LocalIP01`: `…3257 > 30148` vs `…3257` — Sucuri's AS (30148) intermittently
  appearing as the final hop.
- `PTCL / Cybernet`: `9541 > 9557` vs `9541 > 9557 > 17557` — PTCL's AS (17557)
  intermittently replying on the last hop.

Because we use **Paris traceroute**, a stable path string means a genuinely stable
route (not load-balancer aliasing). So: over this day, from these 5 ISPs, the routes
to these sites did not change.

## 6. Outages — overnight thunderstorm (June 12)

A notable thunderstorm overnight knocked out ISP connectivity, and the longitudinal
data **captured it directly**. When a probe's ISP loses internet, the probe produces
**no result to any site** — so an outage shows as a stretch of *missing rounds across
all 5 targets at once*, which is unambiguous in the per-probe round counts:

| Probe (ISP) | Outage window (UTC) | PKT | Duration | Rounds missed |
|---|---|---|---|---|
| **LocalInternetProj01** (AS136174, TPCPL/Nova) | **06-12 01:30 → 07:15** | **06:30 → 12:15** | **~5.7 h** | ~22 (×4 sites ≈ 88 rows) |
| Nayatel, Transworld, Z-Com, Cybernet | — | — | continuous | none > 20 min |

So **one ISP (TPCPL/Nova) lost connectivity for ~5.7 h** during/after the storm; the
other four stayed up the whole 24 h (any sub-15-min drops are below our cadence and
wouldn't register). This is a nice demonstration that the longitudinal method
**detects real-world ISP outages**, not just routing changes — a power outage / link
loss is visible as a clean gap.

## 7. Data-quality notes

- **LocalInternetProj01 (AS136174)** has two distinct issues, now separated:
  1. the **5.7 h storm outage** above (≈88 missing rows — *not* a measurement fault); and
  2. genuine **path flakiness when up** — only **~55% of its online rounds reached the
     destination** (vs ~100% for the other probes), with high RTT jitter (58–90 ms).
  Use its medians with care and exclude the outage window for time-series work.
- **The other four probes are clean:** ~**100% reachability** to the four ICMP-replying
  sites, <1–3% ping loss, low jitter. (Z-Com missed a handful of isolated single
  rounds but never a sustained gap.)
- **PTCL: 100% ICMP loss** — firewalled at the host, **not** down. The traceroute
  reaches PTCL's network (AS17557) in-country; treat the path as the signal, not loss.

## 8. Headline

Over a full day, from 5 Pakistani ISPs: **routes were stable and latency was flat —
the offshore-hosting penalty is structural, not congestion.** A Pakistani user reaches
local government/news in **2–42 ms (wildly ISP-dependent)** but their **banks in
127–211 ms regardless of ISP, because both banks are hosted abroad** (MCB→Singapore,
HBL→New Jersey). There was **no diurnal congestion cycle** and **no route flapping**
across the 24 h. This both validates the longitudinal pipeline and shows that, for
these sites, the inefficiency is a *hosting/peering* problem (the Exp 01 / PKIX
story), not a time-of-day capacity problem. The one real event of the day was a
**~5.7 h outage of TPCPL/Nova** during an overnight thunderstorm — which the method
captured cleanly as a gap across all targets.

## 9. Caveats

- **One 24 h weekday run**, single snapshot in calendar terms — a weekend or
  multi-day run could still surface variation this day didn't.
- **ICMP only**; serving location for the security-CDN banks is edge IP-geolocation,
  not an HTTP `colo`.
- This run used the **pre-dynamic-ASN** code, so each probe is single-ISP as
  registered (the live-egress-ASN feature applies to future multi-homed/campus runs).
