# Findings 03 — Longitudinal Routing (one probe → 5 sites, every 15 min)

**Dataset:** 5 sites, 1 probe, 8 ICMP-Paris traceroutes/site (15-min interval) +
~315 pings/site (1/min companion), over a single 2-hour window
(2026-06-10 10:22→12:22 UTC).
**Probe:** 60223 — Nayatel (AS23674), Islamabad. **Method:** RIPE Atlas periodic
traceroute (paris=16) + periodic ping; origin network via Team Cymru (+ RDAP
fallback); serving location via ip-api (server IP / CDN handoff). See
`experiments/03_longitudinal_routing`.

> This run is a **baseline + pipeline validation**, not the full study: 2 hours of
> daytime cannot show time-of-day / diurnal effects — that needs the 48–72 h run
> the experiment is designed for. What it *does* give is a clean, stable snapshot
> and a quantified local-vs-offshore comparison.

---

## 1. Per-site results

| Site | Hosting | Reachable | RTT median | Jitter (trace / ping) | Loss | Served from | AS-path |
|------|---------|-----------|-----------|-----------------------|------|-------------|---------|
| **ptcl.com.pk** | PTCL (PK) | ICMP-blocked* | ~4 ms *(into AS17557)* | — | n/a | Islamabad, PK | `17557` |
| **pseb.org.pk** | Multinet (PK) | 8/8 | **22.9 ms** | 0.2 / 1.0 ms | 0% | Karachi, PK | `9260` |
| **dunyanews.tv** | Multinet (PK) | 8/8 | **40.4 ms** | 0.1 / 0.5 ms | 0.6% | Islamabad, PK | `38193 > 9260` |
| **mcb.com.pk** | Sucuri (bank) | 8/8 | **128.9 ms** | 1.1 / 1.2 ms | 0% | **Singapore** | `2914 > 30148` |
| **hbl.com** | Incapsula (bank) | 8/8 | **199.8 ms** | 0.1 / 1.2 ms | 0% | **Secaucus, New Jersey, US** | `174 > 19551` |

\*PTCL's web host firewalls ICMP — see §5.

---

## 2. The offshore-hosting penalty is ~3–9× latency

PK-hosted content sits at **4–40 ms**; the two banks sit at **129 ms (Singapore)**
and **200 ms (US)**. For a Nayatel user in Islamabad, reaching their own bank costs
**5–9× the latency** of reaching a locally-hosted government or news site. This is
the user-experience cost of hosting abroad, measured directly.

## 3. Both Pakistani banks host offshore — on different continents

- **HBL → Incapsula, New Jersey (US)** — exits via Cogent (AS174), 200 ms.
- **MCB → Sucuri, Singapore** — exits via NTT (AS2914), 129 ms.

Both are security-CDN-fronted and **outside Pakistan**: domestic banking front-ends
(and the traffic to them) leave the country, via foreign Tier-1 transit. This is
the per-ISP, data-plane confirmation of the Exp-01 census finding that banking has
largely left the country — here with the latency cost attached.

## 4. The penalty is distance, not instability

Every site was **rock-steady** for the full 2 hours: **0 path changes**, **≤1.2 ms
jitter**, **0–0.6% loss** — including the 200 ms US path (1.2 ms jitter, 0% loss).
So offshore hosting hurts **latency, not reliability** in this window; the local
sites are both fast *and* steady (≤1 ms jitter).

This stability is also the **method working**: because we used **Paris
traceroute**, a flat path means a genuinely stable route, not load-balancer
multipath masquerading as change. Had we seen path flips, they would have been
real BGP/routing changes.

## 5. `ptcl.com.pk` — 100% ping "loss" is firewalling, not downtime

The PTCL site never answers ping or completes the traceroute, yet the trace
**reaches PTCL's network (AS17557) at 3.9 ms** — the most local of all five — and
the host then drops everything. Read as *ICMP-filtered*, not *down*. **Lesson:**
for such hosts, trust the **traceroute path** (it reaches PTCL Islamabad), not the
ping-loss figure. This is the documented ICMP-vs-reachability caveat captured live.

## 6. Nayatel's transit shows through

`dunyanews.tv` routes `Transworld (AS38193) → Multinet (AS9260)`; `pseb.org.pk`
reaches Multinet with no visible upstream AS (the Transworld backbone interfaces
are unannounced in BGP, so only `9260` shows). Consistent with the project finding
that Nayatel leans on Transworld for transit while reaching some domestic networks
quasi-directly.

---

## 7. What this run does and doesn't establish

**Establishes:**
- A clean local-vs-offshore latency baseline from a real PK ISP: **23–40 ms local
  vs 129–200 ms for offshore banks**, stable and structural (hosting choice).
- That the longitudinal pipeline (periodic traceroute + 1/min ping, path-change
  detection, RTT/jitter/loss) works end-to-end.

**Does not establish (needs the longer run):**
- **Time-of-day / diurnal** variation — 2 h of daytime is too short. Peak-evening
  congestion and any route flips require the **48–72 h around-the-clock** window.
- **Generality** — single vantage (Nayatel, Islamabad). A second ISP is needed to
  separate "Nayatel's experience" from "Pakistan's experience" (ties to Exp 02).

## 8. Caveats

- **Single vantage / vantage-biased** — this is Nayatel-from-Islamabad only.
- **Short window** — no diurnal coverage; treat as a snapshot.
- **Serving location for security CDNs** (Incapsula/Sucuri) is IP-geolocation of
  the responding edge, not an HTTP `colo`; the metros (NJ, Singapore) are the
  stable peering/serving points and are reliable here, but it is the network edge,
  not a confirmed HTTP origin.
- **`rtt_ms` is best-of-3** per round (min reply), less noisy than Exp 01's
  first-reply RTT; ping jitter/loss aggregate the 1/min companion.
