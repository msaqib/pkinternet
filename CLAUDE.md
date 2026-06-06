# Project Context for Claude Code

## What this project does

RIPE Atlas traceroutes from Pakistani probes to Pakistani websites to determine
where those websites are hosted (in-country vs abroad) and how traffic is routed.
Funded by APNIC Foundation; supervised by Dr Saqib Ilyas at LUMS.

**Experiment 01 (website hosting & routing) — author: Rayan Atif.**

The broader research question is: **how effective is Pakistan's Internet Exchange
Point (PKIX)?** We investigate whether domestic Pakistani traffic routes locally
or hairpins internationally, and whether ISP choice affects the quality of
content delivery to Pakistani users.

---

## Research goals, questions & definitions

**Three concrete deliverables** (what "PKIX effectiveness" must produce in numbers):
1. **Forex saved** if the IXP were actually used (less international transit bought).
2. How much better users' experience would be **under normal conditions**.
3. How much better it would be **during a submarine-cable fault**.

**Transit structure (why hairpinning happens):** only **PTCL (AS17557)** and
**Transworld (AS38193)** are licensed to sell international transit in Pakistan;
every other ISP buys upstream from them (and they also compete with those ISPs).
So two domestic ISPs with no peering relationship typically reach each other
*through* PTCL/Transworld — and domestic traffic frequently hairpins abroad
(e.g. via Europe) and back even when both endpoints are in the same city. An IXP
fixes this; PKIX exists but most members are physically present without
exchanging routes.

**Three-set ISP framework** (core classification — see also "PKIX status"):
- **Set 1** — ignored the PTA mandate; not at any IXP node.
- **Set 2** — physically present at the IXP but NOT exchanging BGP routes/traffic.
- **Set 3** — present AND actively exchanging traffic.

**Research questions:**
- **RQ1** — Is the user experience of Set-3 ISP customers better than Set-1/2?
- **RQ2** — Do all customers of the *same* ISP receive similar service?

**"User experience" is operationalised as:** RTT and hop count to/from key
locally-hosted servers; path tromboning / hairpinning; and behaviour under
submarine-cable cuts.

---

## Key files

| Path | Purpose |
|------|---------|
| `scripts/measurement/pk_multi_probe.py` | Main measurement + analysis script |
| `data/pk_websites_list.csv` | Input: 100 Pakistani websites across 10 categories |
| `data/pk_isp_fll_list.csv` | PTA FLL licensee list (77 unique ISPs, deduped) |
| `experiments/01_website_destinations/notes.md` | Experiment log |
| `experiments/01_website_destinations/results/` | Output CSVs, one subfolder per run |

---

## Run workflow

1. Set `RUN_NAME` at the top of `pk_multi_probe.py` (format: `run_YYYYMMDD_description`)
2. Set env var: `export RIPE_API_KEY="your-key-here"`
3. Run from repo root: `python scripts/measurement/pk_multi_probe.py`
4. Script creates `results/{RUN_NAME}/` automatically
5. Commit the results folder to git

---

## Output files per run

- `pk_grouped_TIMESTAMP.csv` — per-hop rows sorted website → probe → hop,
  with RTT, ASN, country, org name on every row. Destination info repeated
  on every row for self-contained analysis.
- `pk_summary_TIMESTAMP.csv` — one row per measurement with headline numbers:
  total hops, max RTT, ASN path, country path, plus **`dest_location`** (the
  actual serving city/country — see "Serving location") and **`location_via`**
  (how it was derived: `handoff <ip>`, `server IP`, or blank if undetermined).
- `routes_TIMESTAMP.txt` — human-readable route report; one block per
  traceroute with SOURCE/DEST header and hop-by-hop path underneath.
  Generated automatically at step `[6b]`.

Results CSVs **should be committed to git**. Each run gets its own subfolder.

### Grouped CSV column order

```
target_hostname | target_label | target_category |
probe_id | probe_asn | probe_city |
hop | hop_ip | rtt_ms | hop_asn | hop_prefix | hop_country | hop_asn_name |
is_private | is_timeout |
target_ip | target_asn | target_asn_name | target_country | destination_responded |
measurement_id | timestamp
```

---

## Scripts

- `scripts/measurement/pk_multi_probe.py` — runs traceroutes, ASN resolution
  (Team Cymru + RDAP fallback), serving-location classification, writes grouped +
  summary + `routes_*.txt`. Single invocation produces everything.
- `scripts/measurement/geo_utils.py` — shared geolocation + anycast handoff
  logic, on-disk cache (`.geo_cache.json`). Imported by other scripts.
- `scripts/measurement/format_routes.py` — renders `routes_*.txt`; called
  automatically at step `[6b]`, also runnable standalone to rebuild route files.

---

## Probe configuration

Probes are manually specified in the `PROBES` list at the top of
`pk_multi_probe.py`. Format: `(probe_id, asn, city, description)`.

Current probes:
```python
PROBES = [
    (1015679, 136174, "Pakistan", "LocalInternetProj01 (TPCPL/Nova/Transworld)"),
    (1015210,  17557, "Pakistan", "AS17557 (PTCL)"),
    (  62224,  38193, "Pakistan", "Zartash-Office (Transworld)"),
    (  60223,  23674, "Pakistan", "PK_Inara (Nayatel)"),
    (   7613, 152605, "Pakistan", "Z COM Networks"),
]
```

**Geography:** RIPE Atlas reports 5 connected probes for this account in Pakistan
— 4 in Lahore, 1 in Islamabad (the Nayatel / 60223 probe), one of the Lahore
probes being a RIPE Atlas *Anchor*. The RTT table below assumes a Lahore vantage.
Note: only Transworld is double-covered (two probes, 1015679 and 62224); every
other ISP has a single probe — which limits RQ2 (intra-ISP consistency) until
more probes are deployed.

**Batching:** With 5 probes × 100 sites = 500 measurements, RIPE Atlas hits its
100-concurrent-measurement limit. Current settings: `BATCH_WAIT = 30` (seconds
between probes), `BATCH_SIZE = 10`, `RESULT_TIMEOUT = 3600`.

---

## API key

Never hardcode. Read from environment:
```bash
export RIPE_API_KEY="your-key-here"
```
Or use a `.env` file with `python-dotenv` (`pip install python-dotenv`).

---

## RTT interpretation (from Lahore)

| RTT | Interpretation |
|-----|---------------|
| < 10 ms | Same city or co-located |
| < 50 ms | Traffic likely stayed in Pakistan |
| 50–100 ms | Possibly exited to nearby region (Gulf, India) |
| > 100 ms | Traffic almost certainly exited Pakistan |
| > 150 ms | Europe or North America |
| > 200 ms | US East Coast or beyond |

---

## ASN lookup

Destination and hop ASNs resolved via Team Cymru DNS (no API key, no rate limits).

**RDAP fallback for unannounced hops.** Some hops return nothing from Cymru
because their prefix isn't in global BGP tables — typically ISP internal backbone
interfaces (e.g. Transworld's `110.93.252–254.x`). When Cymru returns nothing,
the script falls back to RDAP registry allocation via `rdap.org` for an
operator/country hint. Such hops keep an empty `hop_asn` but get `hop_asn_name`
and `hop_country` filled. The readable report tags these `[registry]`. This
surfaces foreign IXP hops (Equinix-SG, DE-CIX-FRA, EMIX-UAE) that were
previously unknown.

---

## Serving location (where the destination ACTUALLY is)

`target_country` is the ASN's *registration* country and is misleading for
anycast CDNs (Cloudflare reads "US" even when it serves from Karachi). The
pipeline computes a real serving location per measurement
(`geo_utils.serving_location`), written to `dest_location` / `location_via` in the
summary and shown in `routes_*.txt` as **`SERVED`** for real (unicast) servers
and **`ENTERS`** for anycast CDNs — `ENTERS` marks where the probe enters the
CDN's network (the handoff), *not* a confirmed HTTP serving location:

- **Unicast (real server):** geolocate the destination IP (ip-api.com). Stable
  regardless of vantage — reliable.
- **Anycast CDN** (AS13335 Cloudflare, AS20940 Akamai, AS19551 Incapsula,
  AS30148 Sucuri, …): geolocate the **handoff hop** — the last real router before
  traffic enters the CDN's ASN — i.e. where this probe hands off to the CDN. RTT
  corroborates distance. ip-api results cached in `.geo_cache.json`.

**Reliability ranking (best → worst):** `colo` (Cloudflare `/cdn-cgi/trace`, the
HTTP truth) > traceroute handoff + RTT > IP geolocation of an anycast IP (worst —
returns the registration city, e.g. a Cloudflare IP geolocating to "Toronto").

**CRITICAL caveat — ICMP path ≠ HTTP serving location.** A traceroute can
terminate at a *local* Cloudflare node at very low RTT while the actual HTTPS
request for that zone is served from a distant PoP. Real case:
`shaukatkhanum.org.pk` traced to a Cloudflare IP at ~4ms from Lahore (looks
local) but `/cdn-cgi/trace` returned `colo=SIN` — actually served from Singapore.
Happens for free/basic-plan zones and ISPs without full local Cloudflare HTTP
peering. RIPE Atlas probes can't run HTTP, so the probe-side method can report
"reaches Cloudflare locally" when the site is really served abroad. The honest
probe-side claim is **"reaches the CDN's network locally," not "served
locally."** Only `colo` (from a machine that can run HTTP) is authoritative.

**Apex-only blind spot.** We measure each site's apex hostname only. For a
CDN-fronted site that hides the real origin *and* the organisation's other
servers. Example: shaukatkhanum.org.pk's apex is Cloudflare, but its
certificate-transparency subdomains (via `crt.sh`) revealed its actual hospital
systems (`hmis`, `mhmis`) hosted **in Pakistan** on PTCL, plus servers on Hetzner
(DE/FI), netcup (SG), etc. A CT-log + subdomain sweep turns "it's on Cloudflare"
into a real per-org infrastructure map — worth doing for important targets
(banks, government, hospitals).

---

## Known measurement artifacts

**Shaw Communications hop (probe 1015679 only)**
Hop 2 always shows `70.70.209.16` (Shaw Communications, AS6327, Canada) at ~1.7ms.
This IP is physically in Pakistan. Confirmed by:
- PTR record `S01061c1b689fabd3.vn.shawcable.net` on the adjacent hop `70.70.148.252`
  — legitimate Shaw Cable infrastructure hostname confirming Shaw's managed equipment
- RTT of 1.7ms — physically impossible for Canada from Pakistan
- HE traceroute confirms the IPs route through Shaw's backbone from North America

**Explanation:** TPCPL (The Professional Communications Pvt Ltd, AS136174) has a
commercial transit agreement with Shaw Communications. Shaw has deployed physical
CPE at TPCPL's facility in Pakistan using their own Canadian IP space. Outgoing
traffic exits through Shaw's router before reaching Transworld's backbone. Return
traffic skips Shaw entirely via direct BGP routing to TPCPL through Transworld.

Transworld has no documented North American presence (PeeringDB shows only
Asia Pacific, Middle East, and Europe). The Shaw arrangement is therefore at
the TPCPL/Nova layer, not the Transworld layer.

**Exclude this hop from any country-of-hosting analysis.**

**Probe 1015210 (PTCL) path anomaly**
This probe shows `172.17.0.1` at hop 1 (Docker bridge gateway) then reaches
destinations in 1-2 hops. It is running inside a Docker container or VM.
Destination RTTs are valid but the intermediate path is opaque.
It also goes **offline intermittently** — batch8 returned "No suitable probes"
for all 10 of its measurements (handled gracefully now; see RIPE Atlas limits).

**Probe 62224 (Transworld/Zartash) path anomaly**
Shows only 2 RFC1918 hops then all `* * *` until hop 255. Aggressive ICMP
filtering throughout. Destination-level data usable; no routing path visible.

---

## Key Pakistani ASNs

| ASN | Operator | Notes |
|-----|---------|-------|
| AS38193 | Transworld Associates | LDI operator, backbone |
| AS17557 | PTCL | LDI operator, IXP operator, largest ISP |
| AS45595 | PTCL Broadband | PTCL subsidiary |
| AS9541  | Cybernet / StormFiber | Major ISP |
| AS38264 | Wateen Telecom | ISP |
| AS9260  | Multinet Pakistan | ISP |
| AS45773 | PERN | Pakistan Education & Research Network |
| AS23888 | NTC | National Telecom Corp (government) |
| AS23674 | Nayatel | Islamabad-focused ISP |
| AS136174| TPCPL | The Professional Communications Pvt Ltd (Nova) |
| AS152605| Z COM Networks | Small ISP |
| AS59323 | PITB | Punjab Information Technology Board |
| AS138424| FBR | Federal Board of Revenue (own ASN) |
| AS7590  | COMSATS | Commission on Science & Technology |
| AS153561| PITC | Pakistan IT Company |
| AS32787 | Prolexic/Akamai | DDoS mitigation (US) — appears in govt site paths |
| AS174   | Cogent | US backbone — appears in PITC paths |
| AS6327  | Shaw/Rogers | Canadian ISP — appears at hop 2 of probe 1015679 |

---

## Key findings so far

### Website hosting (government batch)

| Site | Hosted by | ASN | Routing |
|------|-----------|-----|---------|
| bisp.gov.pk | Cloudflare | AS13335 US | Local delivery ~3-21ms |
| nlc.com.pk | Cloudflare | AS13335 US | Local delivery ~3-24ms |
| pbs.gov.pk | NTC | AS23888 PK | Genuinely local, 41-75ms |
| pid.gov.pk | COMSATS | AS7590 PK | Genuinely local, 3-49ms |
| pseb.org.pk | Multinet | AS9260 PK | Genuinely local, ~40ms |
| pitc.com.pk | PITC | AS153561 PK | Routes via Cogent locally |
| moitt.gov.pk | Cybernet+Prolexic | AS9541 PK | Hairpins to US, 107-194ms |
| railways.gov.pk | Cybernet+Prolexic | AS9541 PK | Same IP as moitt, hairpins US |

moitt.gov.pk and railways.gov.pk share the same destination IP (203.101.184.86)
and route through Akamai Prolexic in the US despite being hosted on Cybernet (PK).

### Cloudflare anycast findings

Cloudflare resolves to US ASN (AS13335) but delivers locally at 3-21ms.
Nayatel probe hits Cloudflare at 3ms — confirming a Cloudflare PoP directly
peered with Nayatel in Islamabad. Wateen (laptop) routes to Hong Kong (colo=HKG)
at 25ms for the same sites. Same website, same city, different ISP = different
Cloudflare PoP. Demonstrates CDN peering inequality between Pakistani ISPs.

ASN country code alone cannot determine physical hosting location when CDN
anycast is involved. RTT must be used alongside ASN data.

**Caveat (important):** a low ICMP/traceroute RTT proves the *network edge* is
local — NOT that the HTTP content is served locally. See "Serving location": for
`shaukatkhanum.org.pk` the trace was ~4ms (local edge) but `colo=SIN` (served
from Singapore). Read "delivers locally at Xms" as "reaches Cloudflare's edge
locally," and confirm true serving PoP with `/cdn-cgi/trace` where possible.

### Measured transit dependency & hairpinning (batches 2-11, data-plane)

Robust, RTT-independent results from the traceroutes (Shaw AS6327 artifact excluded):
- **Transit dependency:** downstream ISPs route ~100% of paths through an LDI
  operator (PTCL AS17557 or Transworld AS38193) — Z-Com 91/91, TPCPL 65/65 —
  whereas **Nayatel is ~6%**. Confirms PTCL/Transworld as the chokepoint and
  Nayatel as largely independent (good local peering).
- **Hairpinning is concentrated:** of 23 PK-hosted sites, only 5 are reached via a
  foreign hop (pakistan.gov.pk, moitt.gov.pk, railways.gov.pk, pitc.com.pk,
  goto.com.pk), and only by downstream ISPs — never PTCL/Transworld.
- **Hosting census (91 sites):** 23 real PK servers (25%), 26 foreign servers (29%),
  42 anycast CDN (46%, mostly Cloudflare). Government mostly in-country; news /
  banking / e-commerce overwhelmingly offshore. See `findings/01_*`.

**Data caveat:** stored `rtt_ms` is a single packet (first reply), not min-of-N, so
RTT is noisy; and per-ISP RTT averages are confounded because the responding-
destination set differs per probe. Quote medians; prefer path-based metrics.

### BGP path analysis findings

- PKIX route server (AS140307) appears in **zero** BGP paths to any Pakistani
  destination — IXP is effectively unused
- All Pakistani networks reachable only via Transworld (AS38193) or PTCL (AS17557)
- Transworld performs AS path prepending (up to 7x) on paths to single-homed
  customers to steer inbound traffic toward PTCL
- PTCL and Transworld have a private bilateral routing arrangement
- Neither PTCL nor Transworld are at PKIX (Transworld has zero North American
  presence; PKIX is in Pakistan)

### PKIX status

Source: PTA presentation by Ahmed Bakht Baloch (Director Cybersecurity PTA),
May 2026, titled "Pakistan Peering Roadshow."

**PKIX has four locations (not one as previously believed):**

| Location | Established | Managed by |
|---|---|---|
| Islamabad (HEC/PERN) | Jan 2017 | HEC |
| Karachi (HEC/PERN) | Feb 2019 | HEC |
| Lahore (PITB) | Aug 2023 | PITB/Nexlinx |
| PIE Karachi (PTCL datacenter) | Jan 2024 | DE-CIX/PTCL |
| Multan | 2025 | In pipeline |

**ISPs at each location (from PTA slide):**

Islamabad: COMSATS, Cybernet, Gerry's, Jazz, Mobilink, Multinet, Nayatel, NTC,
PERN, PTCL, Qubee, Telenor, Transworld Enterprise, Ufone, Virtury, Warid,
Wateen, Wi-Tribe, Worldcall, Zong (21 ISPs)

Karachi: Connect, CubeX, Cybernet, Faria, Fiberbeam, GCS, Gerrys, Multinet,
PERN, Redtone, SATCOMM, Telenor, TES/Transworld Home, Wateen (14 ISPs)

Lahore: Brain Net, Connectel, Cybernet, Gerrys, Jazz PMCL, KK Network,
M-Root Server (WIDE/Japan), Multinet, Nayatel, Nexlinx, PITB, Sigin, Smartline,
TES/Transworld Home, Wateen, WellNet, Ylinx, ZCom (18 ISPs)

**Transworld IS connected to PKIX** — "Transworld (TWA)" listed at Islamabad
and Lahore. "TES (Transworld Home)" at Karachi and Lahore. This corrects our
earlier PeeringDB-based conclusion that Transworld was absent.

**Latency comparison from PTA data (Slide 9):**

| Route | International | Through IXP |
|---|---|---|
| Cybernet → Nayatel | 104ms | 1ms |
| PTCL → Wateen | 103ms | 5ms |
| Multinet → Cybernet | 130ms | 2ms |
| Wateen → all others | 144ms | 15-31ms |

IXP reduces inter-ISP latency from 100-144ms to 1-31ms. Wateen is the worst
performer even through the IXP (15-31ms vs 1-6ms for others).

**Fee structure:** Joining fee Rs. 100,000 (1G) / Rs. 200,000 (10G).
Monthly Rs. 60,000 (1G) / Rs. 125,000 (10G). No fees charged since 2016.

**2022 floods:** Internet disruption confirmed. More redundant routes adopted
after the event — real-world validation of the cable fault resilience argument.

**Supporting organisations:** JPRS, NSRC, ISOC, APNIC (confirms APNIC funding).

**Way forward (PTA):** Regulatory compliance, cost sharing, CDN deployment,
upgrade to IXP Manager, connect to PeeringDB.

**Slide 7 interpretation:** Both slide 6 and slide 7 are titled "Current IXPs
in Pakistan (Non Commercial)" — slide 7 lists ISPs that are **currently physically
connected** as of May 2026, not a historical list. This means the 21/14/18 ISPs
per location are present right now.

**Three-set framework applied to slide 7:**

```
Set 1 — Not physically present at any PKIX node
Set 2 — Physically connected (on slide 7) but not exchanging BGP routes
Set 3 — Physically connected AND actually exchanging traffic
```

The latency table (slide 9) shows some ISPs achieving 1-6ms through the IXP —
those are Set 3. The research question is which of the listed ISPs are Set 2
vs Set 3.

**Why our BGP analysis showed nothing despite 21 ISPs being connected:**
Physical presence ≠ route exchange. ISPs may have plugged in their cable but
never configured BGP sessions, or only peer bilaterally with specific partners
rather than all members. No route server means the exchange is invisible in
global BGP tables.

**Wateen as a confirmed Set 2 example:**
Wateen appears on all three PKIX location lists as currently connected. Yet our
traceroute measurement showed Wateen (laptop) routing to Cloudflare's Hong Kong
PoP at 25ms while Nayatel (also connected at PKIX) reaches Cloudflare at 3ms.
This is direct measurement evidence that Wateen is physically present at PKIX
but not actively peering — a Set 2 ISP confirmed by data.

**Revised conclusion:** PKIX is physically functional at three locations with
dozens of ISPs connected. The research question is not "is PKIX built" but
"which ISPs are actually exchanging routes vs just maintaining a physical
connection." Traceroute RTT comparisons between ISPs that are listed as PKIX
members are the most direct way to answer this.

---

## ISP handoff measurements (from Transworld probe)

Confirmed via MTR and RIPE Atlas cross-validation:

| Handoff | RTT jump | Location | Via PKIX? |
|---------|----------|----------|-----------|
| Transworld → PTCL | 1ms | Local, same facility | Unknown |
| Transworld → Multinet | ~19ms via Cogent PoP | Local, Pakistan | Unknown |
| Transworld → NTC (via PTCL) | 2ms | Karachi region | Unknown |
| Transworld → Cybernet | ~41ms | Local, Pakistan | Unknown |

All handoffs confirmed local. None documented through PKIX.

---

## Network topology (probe 1015679)

```
Probe device
  ↓ 0.4ms
192.168.100.1 (TPCPL internal gateway)
  ↓ 1.3ms
70.70.209.16 (Shaw CPE router, physically in Pakistan) ← ARTIFACT
  ↓ 0.8ms
110.93.212.161 (Transworld AS38193, Lahore)
  ↓ ~18ms
110.93.254/252/253.x (Transworld internal backbone)
  ↓ varies
destination
```

---

## Probe 60223 (Nayatel) topology

```
192.168.18.1 (RFC1918 gateway)
100.89.64.1 (carrier-grade NAT or tunnel)
172.27.0.x / 172.31.5.x (RFC1918 internal hops)
110.93.202.x (Transworld — Nayatel routes via Transworld)
203.175.65.67 (Nayatel backbone AS23674)
  ↓ to destination
```

Nayatel uses Transworld as transit. Despite this, Nayatel reaches Cloudflare and
COMSATS at ~3ms — suggesting direct local peering with these networks in Islamabad.

---

## RIPE Atlas limits

- Max 100 concurrent one-off measurements per account
- 500 measurements (5 probes × 100 sites) will exceed this limit
- BATCH_WAIT = 30 seconds between probes (with BATCH_SIZE = 10) stays under the limit
- RESULT_TIMEOUT = 3600 for large runs
- Paris traceroute (paris=16) used throughout to avoid load-balancer multipath
- **Offline probes:** if a probe is down, RIPE returns status "No suitable
  probes" for its measurements (they never reach "Stopped"). `wait_for_all` now
  treats that and other terminal failure states (id ≥ 4) as finished and skips
  them, instead of hanging until `RESULT_TIMEOUT`. (This was a bug; fixed.)
- **Interrupted-run recovery:** one-off results persist on RIPE. If a run is
  killed mid-poll, results can be re-fetched from the account's recent
  measurements (`GET /measurements/my/`) and the CSVs rebuilt — no re-spending
  credits. Measurement descriptions are `"<probe_id>→<label>"`, which maps each
  result back to its probe and target. (Used to salvage batch8 when PTCL was
  offline.)
- CSV files are written `encoding="utf-8"` — geolocation city names contain
  non-ASCII characters (e.g. `ā`) that crash the default Windows cp1252 codec.

---

## Dependencies

```bash
pip install requests dnspython python-dotenv
```