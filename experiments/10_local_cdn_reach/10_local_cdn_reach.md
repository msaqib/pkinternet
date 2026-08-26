# Findings 10 — CDN Peering Local Reach & Google Global Cache (GGC) Detection

## Google's Three-Tier Infrastructure

Google operates three distinct types of infrastructure relevant to Pakistani ISP connectivity:

**Data Centers** serve as the core compute layer where Gmail, Search, and YouTube processing actually happen. There are very few of these globally and none in Pakistan.

**Edge Points of Presence (PoPs)** are where Google peers with ISPs via BGP. The `216.239.x.x` hops observed in our traceroutes are Google's PoP routers at these peering points. They are physically located in regional hubs such as Dubai or Muscat but their IP addresses are registered to Mountain View, California, a known geo-IP limitation for anycast infrastructure.

**Google Global Cache (GGC)** nodes are small servers that Google installs directly inside ISP networks, serving cached content such as YouTube videos without traffic ever leaving the ISP's own infrastructure. A GGC node would appear as a Pakistani-registered ASN hop immediately before the first Google ASN hop in a traceroute. Our experiment found zero such nodes across all 10 responding probes.

**Source:** Experiment 10, run `run_cdn_peering_20260719_003053` (summary
analysis) + `results/routes_full_20260719_003828.txt` (full hop-by-hop dump via
`fetch.py`, used for this GGC inspection).
**Method:** TCP/80 Paris traceroutes, `resolve_on_probe=True`, from all
currently-connected Pakistani probes to `google.com`, `youtube.com`,
`facebook.com`, `instagram.com`, `akamai.com`. **Reproduce:**
`experiments/10_local_cdn_reach/run.py` (schedule + summarize) →
`experiments/10_local_cdn_reach/fetch.py` (full hop dump for a fixed set of
measurement IDs).

10 of 14 configured probes were connected and returned data: Cybernet
(Haripur, Karachi), Fasttel (Islamabad), Nayatel (Islamabad ×2 probes), Nova
(Lahore/TPCPL), PTCL (Karachi), TES (Rawalpindi, Karachi), Transworld
(Lahore), Zcom (Lahore). **Orbit (Faisalabad, probe 64535) returned no
results — the probe was Disconnected in RIPE Atlas at run time**, not a
routing finding; PTCL-Mianwali and a second Cybernet-Karachi probe were
likewise disconnected and excluded before scheduling (see `run.py`'s
preflight probe-status check).

---

## Headline

- **No embedded Google Global Cache (GGC) — or any on-net CDN cache — was
  found inside any of the 10 responding Pakistani ISPs.** Every Google/Meta/
  Akamai-registered hop is reached only *after* leaving the ISP's own address
  space, at RTTs of 15–277 ms (never the <5 ms an on-net cache would show).
  One genuine, *named* Google Global Cache node did appear in the data
  (`93.123.23.251`, RDAP netname `"Google Global Cache for NetIX"`) — but it
  sits at **NetIX, a European IXP in Sofia, Bulgaria**, ~4,300 km from
  Pakistan, not inside any domestic network.
- **Meta (Facebook/Instagram) traffic from most ISPs lands on a real, confirmed
  regional PoP in Oman** (`157.240.81.186` → Muscat; `157.240.227.35` →
  Seeb) — verified two independent ways: `ip-api.com` geolocation *and* the
  RTT is physically consistent with a real Pakistan↔Oman round trip
  (15–46 ms), unlike a genuine US round trip. This is a real, corroborated
  finding, not a registration-country artifact.
- **Google's true serving location cannot be confirmed by this method.**
  Every Google-registered hop reached (`216.239.41.x`, `72.14.212.x`,
  `142.250.x`) geolocates to **"Mountain View, US" in both Cymru and
  ip-api** — physically impossible at the observed 15–45 ms RTTs (a real PK↔US
  round trip is >300 ms; see the project's physics-arbiter method in
  `experiments/07_longitudinal_panel/analysis/METHODOLOGY.md`). The real PoP
  is almost certainly regional (plausibly Gulf, consistent with the Meta
  result), but **cannot be pinned to a specific city from traceroute + geo-IP
  alone** — this needs an HTTP-capable vantage, which RIPE Atlas traceroute
  can't provide.
- **Akamai is the worst-served of the three CDNs and never lands regionally.**
  Every probe that reached Akamai landed on either **Singapore**
  (`104.74.135.x`, `23.54.79.x`; 78–120 ms, physically consistent with a real
  PK↔Singapore path) or **Frankfurt** (`184.86.251.13`; 155–277 ms, consistent
  with PK↔Europe). No Gulf-region Akamai PoP was reached by any of the 10
  probes.

---

## The IP-ownership blind spot: why "no embedded cache found" isn't "no cache exists"

The GGC detection method above works by checking who **owns** the IP address of each hop: if a hop
right before the Google/Meta ASN belonged to a Pakistani ISP's own address space, that would be the
traceroute signature of an embedded cache. We found zero such hops — that's the basis of the
headline claim above.

But IP ownership and physical location are two separate things. A cache box can be physically
installed inside an ISP's building while still using an IP address registered to Google/Meta's own
address space, not the ISP's — a common real-world CDN deployment pattern. From outside, that setup
is *indistinguishable* from a genuine international hop: the ASN reads Google/Meta either way. So
"zero Pakistani-owned hops in front of Google/Meta" proves **no cache numbered out of the ISP's own
address space** — it does not prove **no physical cache in Pakistan at all**.

**The RTT evidence doesn't resolve this ambiguity, but it doesn't rule the possibility out either —
worth being precise about, since it's the strongest lead for an operator conversation:**

| Target | Lowest RTT observed | Probe | Consistent with in-PK presence? |
|---|---|---|---|
| google.com | **14.9 ms** | TES (Karachi) | Yes — well under the 50 ms "stayed in PK" threshold (METHODOLOGY.md RTT table), but too high to prove same-building co-location (<5 ms) |
| youtube.com | 19.3 ms | TES (Karachi) / Cybernet (Karachi) | Yes, same reasoning |
| facebook.com | 17.2 ms | TES (Karachi) | Yes, same reasoning |
| instagram.com | 17.0 ms | TES (Karachi) | Yes, same reasoning |
| akamai.com | 78.5 ms | TES (Karachi) | **No** — squarely in "left Pakistan" territory by the same threshold, no ambiguity |

Google's and Meta's Karachi RTTs (15–20 ms) are fast enough to be consistent with genuine
in-country presence by this project's own RTT-interpretation table, but not fast enough to prove
co-location inside the specific probing ISP's building. That gap, a regional-but-just-outside-PK
vantage vs. a physically-in-PK-but-vendor-numbered box — is exactly what traceroute + geo-IP cannot
resolve on its own. Akamai shows no such ambiguity: its RTT floor (78 ms+) is unambiguously abroad.

**What to find out:**  "is there a Google/Meta caching appliance physically
installed in your network, regardless of what IP range it uses?"** That's the one thing only they
can answer; see Next Steps below.

---

## Per-ISP handoff

| ISP (probe) | Handoff to CDN | Evidence |
|---|---|---|
| **Cybernet** (Haripur, Karachi) | **Own backbone (AS9541 / CYBERNET-PK) — no Transworld or PTCL hop visible for any of the 5 targets.** | All non-private hops before the CDN ASN resolve (via Cymru *and* RIPEstat RDAP) to `CYBERNET-PK`, e.g. `202.163.97.213`, `202.163.100.236`. |
| **Fasttel** (Islamabad) | **Dual-transit, split by destination.** Google/YouTube hop 4 = `117.20.23.46` → **AS38193 Transworld**. Facebook/Instagram/Akamai hop 4 = `59.103.181.90` → **AS17557 PTCL**. | Same probe, same hop position, different upstream depending on target — Fasttel is multihomed and appears to route by destination AS. |
| **Nayatel** (Islamabad, 2 probes) | Mostly **opaque** — ICMP-filtered past hop 2 for Google/YouTube/Instagram/Akamai (destination-only reply). Facebook is the exception: surfaces Nayatel's own backbone edge `203.175.65.67` (**AS23674**, matches the topology already documented in METHODOLOGY.md) before the Meta hop. | Akamai trace additionally **dead-ends** at a Japan-registered `202.12.27.33` (AS7500, WIDE/NSPIXP-2) without ever reaching an Akamai-registered hop — a measurement gap, not a routing conclusion. |
| **Nova** (Lahore / TPCPL, AS136174) | **Transworld (AS38193)** at `110.93.212.161`, all 5 targets. | Consistent with the already-documented TPCPL→Transworld transit finding (Shaw/AS6327 hop-2 artifact also present, as expected). |
| **PTCL** (Karachi) | **Own edge (AS17557)** at `39.39.0.1` direct to the CDN, all 5 targets — no other domestic ISP in the path. | Expected: PTCL is an LDI operator, not a Transworld customer. |
| **TES** (Rawalpindi, Karachi; AS135407) | Own edge, then explicit **Transworld (AS38193)** hop (`110.93.200.204` / `110.93.192.x`), all 5 targets. | Matches TES-PL's documented role as Transworld's retail/home arm. |
| **Transworld** (Lahore, probe 62224) | Path **invisible** (ICMP-filtered) — 2 private hops then straight to the CDN-registered IP. | The ~1000–1013 ms "4th hop" RTT for every target is the known ICMP-error-generation-delay artifact for this probe (documented elsewhere in this repo), **not real latency** — do not cite it as a real RTT. |
| **Zcom** (Lahore, AS152605) | Own edge, then explicit **Transworld (AS38193)** hop (`110.93.205.184`), all 5 targets. | |

---

## CDN PoP grounding (traceroute ASN + `ip-api.com` geolocation + RTT physics)

| CDN | Typical PoP IP(s) seen | RIR / geo-IP city | RTT range | Physically plausible? |
|---|---|---|---|---|
| **Google** | `216.239.41.x`, `72.14.212.x`, `142.250.x` | Mountain View, US (both Cymru and ip-api) | 15–45 ms | **No** — real US round trip needs >300 ms. City unconfirmed; real PoP is regional but unidentified by this method. |
| **Meta** (final edge) | `157.240.81.186`, `157.240.227.35` | **Muscat / Seeb, Oman** (ip-api) | 15–46 ms | **Yes** — consistent with a genuine PK↔Oman path. Corroborated finding. |
| **Meta** (backbone hop, `163.77.x.x`) | `163.77.241.90` etc. | Dublin, Ireland (RIR *and* ip-api agree) | 20–65 ms | No — likely Meta's internal address numbering for that link, not its physical location; same registration ≠ location caveat, just agreeing sources this time. |
| **Akamai** | `104.74.135.x`, `23.54.79.x` | Singapore | 78–120 ms | Yes, consistent with PK↔Singapore. |
| **Akamai** | `184.86.251.13` | Frankfurt, Germany | 155–277 ms | Yes, consistent with PK↔Europe. |

This is the same "ASN registration ≠ physical location" trap already
documented for Cloudflare/Toronto in METHODOLOGY.md — it applies identically to
Google and Meta's backbone numbering here. Where geolocation *and* RTT physics
agree (Meta's `157.240.81.186`/`.227.35`), treat the location as real; where
only registration says a location and physics rules it out (Google;
`163.77.x.x`), treat it as unconfirmed.

---

## Caveats

- **Transworld probe (62224) RTTs are an artifact.** Its ICMP filtering means
  every "destination RTT" of ~1000 ms in this run is the known
  ICMP-error-generation delay, not real latency — exclude from any RTT-based
  comparison (same caveat as elsewhere in this repo).
- **Single-packet RTT noise.** `rtt_ms` here is first-reply, not min-of-N.
  Nova's brief 330 ms spike to Google (vs. 37–46 ms on its other 4 targets)
  and PTCL's 107–133 ms mid-path readings on the YouTube trace (vs. 44–45 ms
  on the same run's Google trace, same destination IP) look like transient
  jitter, not a real routing difference — don't read single anomalous
  readings as a routing conclusion without repetition.
- **Coverage gap.** This run covers only the 10 currently-connected probes.
  ISPs the CDN-cache literature and Exp 1.2 flag as most likely to host
  embedded infrastructure (StormFiber/Optix, Telenor) are not in the current
  probe roster — the "no GGC found" conclusion is bounded by that, same
  undercounting caveat Exp 1.2 already documents.
- **`ip-api.com` geolocation is corroborating, not authoritative** — same
  reliability ranking as the rest of this project (HTTP `colo`/trace >
  traceroute handoff + RTT > bare IP geolocation). Used here only where RTT
  physics independently agrees.

---

## Artifacts

- Scheduling + summary: `experiments/10_local_cdn_reach/run.py` →
  `results/run_cdn_peering_20260719_003053/` (`cdn_peering_*.csv`,
  `cdn_pop_comparison_*.csv`, per-target CDN PoP-diversity summary).
- Full hop-by-hop dump used for this GGC analysis:
  `experiments/10_local_cdn_reach/fetch.py` →
  `results/routes_full_20260719_003828.txt`.
