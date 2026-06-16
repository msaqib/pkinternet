# Findings 03 (48h run) - Longitudinal Routing, 8 ISPs x 10 sites

**Dataset:** `run_20260612_48h` - 8 RIPE Atlas probes (6 ISPs; Cybernet and PTCL each
have 2 probes) x 10 sites, ICMP Paris traceroute every 15 min + 1 ping / 5 min, over
**48 hours** (2026-06-14 19:25 -> 2026-06-16 19:16 PKT, i.e. two full days and two
evening peaks). 14,319 trace rounds. Averages are **means**. Charts:
`findings/03_longitudinal_routing_48h.ipynb`.

> This is the first run with the right targets (anycast / GeoDNS sites) and enough
> time to actually catch CDN serving-location flips, plus a PTCL vantage. It both
> delivers new findings and reconfirms the 24 h result that the offshore penalty is
> structural.

Probes: Nayatel (Islamabad), Transworld (Lahore), Z COM Networks (Lahore, anchor),
Cybernet x2 (Haripur, Karachi), PTCL x2 (LUMS anchor, Karachi), TPCPL/Nova (Lahore).
Sites: dunyanews.tv, fbr.gov.pk, dawn.com, geo.tv, express.com.pk, telemart.pk,
daraz.pk, hbl.com, mcb.com.pk, nadra.gov.pk.

---

## 1. CDN serving location flips - the headline

The 24 h run was completely stable. This run, with anycast / GeoDNS targets, caught the
serving location (the metro a CDN hands the request off to) **moving over time and by
ISP**:

- **NADRA (Akamai, GeoDNS) was served from 8 different cities:** Gebze TR (183 ms,
  most common), Istanbul TR (175 ms), "Lahore PK" but at **300 ms** (the Akamai
  Prolexic scrubbing detour - the geo says Lahore, the RTT says abroad), Singapore
  (242 ms), Marseille, Brooklyn, Muscat. The edge changes both across probes and over
  the run.
- **MCB Bank (Sucuri) flips continents:** Singapore and Arizona (US) on Nayatel,
  Cologne and London on others. In the 24 h run it sat steady on Singapore.
- **Cloudflare sites (Dawn, Geo, Telemart)** shift between **Karachi, Lahore, and
  Islamabad** edges - minor (all local) but real edge rebalancing.
- **Some ISPs peer directly with the CDN** (no flip at all): Transworld reaches Akamai
  (NADRA) and Sucuri (MCB) in a **single CDN-AS hop** (`20940` / `30148`), with no
  intermediate handoff to geolocate. In the notebook these show as a grey
  "direct peer" band - itself a sign of efficient routing.

This is exactly what the longitudinal method was built to catch, and what the stable
24 h run could not.

## 2. Per-ISP CDN edge quality: a 45-90x gap for the same content

The same Cloudflare-fronted pages are reached very differently depending on the ISP:

| Site (Cloudflare) | Nayatel | Cybernet (Karachi) | Z-Com | Transworld | **PTCL (anchor)** | **PTCL (Karachi)** |
|---|---:|---:|---:|---:|---:|---:|
| Dawn | **3 ms** | 5 ms | 17 ms | 23 ms | **135 ms** | **282 ms** |
| Express | **3 ms** | 5 ms | 94 ms | 98 ms | **144 ms** | **279 ms** |
| Telemart | **3 ms** | 5 ms | 94 ms | 99 ms | **136 ms** | **275 ms** |

Nayatel and Cybernet hit a **local Cloudflare edge (3-5 ms)**; PTCL, the dominant
national ISP, sends the same requests to a **far edge (135-282 ms)**. For identical
content that is a 45-90x latency difference, driven purely by CDN peering quality.
This is a strong PKIX-relevant result: the biggest ISP peers worst with the CDN that
hosts most Pakistani consumer sites.

## 3. Theoretical vs actual latency (the inflation cost)

For each (probe, site) we compare the **measured** RTT against the **theoretical floor**
- the absolute minimum set by the fibre distance and the speed of light in fibre
(about 2/3 c). The gap above the floor is the real-world overhead (routing detours,
queueing). Biggest overheads:

| Path | Served from | Distance | Theoretical | Measured | Overhead |
|---|---|---:|---:|---:|---:|
| NADRA via PTCL (LUMS) | "Lahore" | 11 km | 0.1 ms | **300 ms** | **300 ms** |
| HBL via PTCL (LUMS) | "Lahore" | 11 km | 0.1 ms | 228 ms | 228 ms |
| NADRA via PTCL (Karachi) | Gebze TR | 3,892 km | 39 ms | 244 ms | 205 ms |
| MCB via PTCL (Karachi) | Singapore | 4,736 km | 47 ms | 208 ms | 161 ms |
| HBL via any ISP | New Jersey | ~11,500 km | ~115 ms | ~220 ms | ~105 ms (~1.9x) |

Two things stand out. First, even the **best offshore path runs ~2x the physical floor**
(HBL ~220 ms vs ~115 ms theoretical) - inherent to going abroad. Second, the worst rows
are **PTCL serving content that is geolocated to "Lahore" yet measured at 300 ms** - the
RTT proves the traffic actually detours abroad while the edge IP mis-geolocates locally.
So the overhead column doubles as a detour detector.

## 4. Same site, same ISP, two cities (the city effect)

Because Cybernet and PTCL each have a probe in two cities, we can hold the ISP fixed and
vary only the **probe's city**. Mean RTT (ms):

| Site | Cybernet Haripur | Cybernet Karachi | | PTCL Lahore/LUMS | PTCL Karachi |
|---|---:|---:|---|---:|---:|
| Daraz | 179 | **81** | | 106 | 117 |
| Express | 24 | **5** | | 144 | 281 |
| Dawn | 31 | **14** | | 136 | 283 |
| MCB Bank | 140 | **111** | | 112 | 208 |
| NADRA | 178 | **159** | | 300 | 244 |

- **Cybernet: the Karachi probe is consistently faster** (Daraz 81 vs 179 ms, ~2.2x;
  Express 5 vs 24 ms) - Karachi is closer to where much content and many CDN edges sit.
  The city matters even on the same ISP.
- **PTCL: the two cities route the same content very differently** (Dawn 136 ms from
  LUMS vs 283 ms from Karachi). PTCL-Karachi is especially bad for Cloudflare. So PTCL's
  poor CDN peering is not uniform - it depends on the egress point too.

## 5. Offshore + bank RTT (responding sites)

- **HBL Bank (New Jersey, US):** ~203-230 ms on every ISP.
- **MCB Bank (Sucuri):** ~111-208 ms, varying because the Sucuri edge itself flips
  (section 1).
- **NADRA (Akamai):** ~154-300 ms, varying with the Akamai edge.
- **Daraz (Singapore):** ~81-180 ms.

## 6. Still no diurnal cycle, over two full days

Holding each clean probe fixed and taking mean RTT by hour (PKT), the offshore paths are
flat across all 24 hours and both evening peaks:

- HBL Bank: **219-222 ms** (about 3 ms spread).
- MCB Bank: **139-141 ms** (about 2 ms spread).
- Dawn (local): 18-24 ms, a faint few-ms dip around mid-day, nothing congestion-sized.

So the 24 h conclusion holds with twice the data: the offshore penalty is **structural
(distance and hosting), not peak-hour congestion**.

## 7. Stability / jitter: which ISPs are steady

Std dev of RTT to HBL Bank (a fixed offshore target, from the 1/5-min ping):

- **Steadiest:** the two Cybernet probes (std **1.1-1.4 ms**), then PTCL-Karachi (5.3),
  Transworld (7.3), Z-Com (8.5).
- **Jittery:** Nayatel (17.7 ms) and especially **TPCPL/Nova (33.5 ms)** - TPCPL is the
  least stable network, consistent with it being the probe that took the thunderstorm
  outage in the 24 h run.

So low latency and low jitter do not always go together: Nayatel is the *fastest* to
local content but has *more* jitter to a fixed offshore target than the steady Cybernet
probes.

## 8. Path changes: real flips vs a visibility artifact

- **Real changes:** NADRA and MCB's serving-metro flips (section 1), and small
  Cloudflare edge shifts between PK cities. These are genuine.
- **Artifact to ignore:** the PTCL anchor (LUMS) shows huge change counts (~90-110) to
  every site, but these are **last-hop visibility flicker**, not reroutes - e.g.
  `17557 > 13335` vs `17557`, where Cloudflare's edge AS (13335) intermittently replies
  on the final hop. We key "change" on the AS-path string, so a flickering last hop
  inflates the count. The path itself is stable. (In the notebook, sort by
  `distinct_metros`, not `path_changes`, to find the real flips.)

## 9. Outage - one probe went dark for 25.5 hours

When a probe's ISP loses connectivity it produces no result to any site, so an outage is
a clean gap across all targets. This run had one big one:

| Probe (ISP, city) | Down (PKT) | Up (PKT) | Duration |
|---|---|---|---|
| **Cybernet, Karachi** (1016143) | 2026-06-15 17:26 | 2026-06-16 18:58 | **~25.5 h** |

That probe produced only ~899 of an expected ~1920 rounds (about 47%). The other seven
probes were essentially complete (1900-1920 rounds each), and no responding *site* went
dark mid-run. Like the 24 h thunderstorm outage, this shows the method cleanly detects
real-world ISP / probe outages, not just routing changes.

## 10. ICMP-blocked hosts

- **Dunya News and FBR returned 0% replies**, but the traceroutes still reach their
  networks (Dunya -> AS9260 Multinet, FBR -> AS38193 / AS17557). So they are
  **firewalling ICMP at the host, not down**. Note: Dunya *answered* in the 24 h run
  (same IP, 202.142.167.148), so its host behaviour changed between June 11 and 14.
- For these, trust the traceroute path, not the loss figure.

## 11. Dynamic egress-ASN check: all 8 probes stable

Every probe's **live-measured** egress ASN equalled its **registered** ASN, with no
variation across the 48 h. So none of these probes is multi-homed / switching ISP. The
check is especially useful here because two probes share AS9541 (Cybernet) and two share
AS17557 (PTCL); the live measurement confirmed each is on its expected network all run.

## 12. Headline

With the right targets and 48 hours, the longitudinal method delivered the change it was
built to detect: **CDN serving locations flip over time and by ISP** (NADRA served from
8 cities, MCB across 4 countries), and **the dominant ISP (PTCL) reaches Cloudflare
content 45-90x slower than Nayatel** because of poor local CDN peering. Even the best
offshore paths run **~2x the physical-distance floor**, and PTCL adds a further detour
(content "served from Lahore" yet 300 ms). The offshore-bank latency stayed **flat
across both days** (no diurnal cycle), reconfirming the penalty is structural, and the
run captured a clean **25.5 h ISP outage**. Together these strengthen the project's core
argument: the inefficiency Pakistani users experience is a hosting-and-peering problem
that PKIX is meant to fix, not a capacity problem.

## 13. Caveats

- **Serving location is the responding edge's IP-geolocation, not an HTTP `colo`.** The
  NADRA "Lahore 300 ms" case shows why: ip-api places the Akamai/Prolexic edge in Lahore
  while the real path detours abroad. The *RTT* is the reliable distance signal.
- **Theoretical RTT assumes a great-circle fibre run at 2/3 c**; real fibre is longer and
  has equipment delay, so a small overhead (a few ms, or ~1.3-1.5x) is normal even for a
  good path. Only the large gaps are inefficiency.
- **One 48 h window** (a weekday-into-weekend span); longer or repeated runs would show
  evolution.
- **ICMP only**; Dunya / FBR (and PTCL in earlier runs) firewall it, so loss is not a
  liveness measure for those - the path is.
- **PTCL-anchor change counts are inflated** by last-hop flicker (section 8); use the
  serving-metro flips, not the raw change count, as the "real change" signal.
