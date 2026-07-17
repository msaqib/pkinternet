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
| `scripts/measurement/pk_multi_probe.py` | Main measurement + analysis script (Exp 01) |
| `data/pk_websites_list.csv` | Input: 100 Pakistani websites across 10 categories |
| `data/pk_isp_fll_list.csv` | PTA FLL licensee list (77 unique ISPs, deduped) |
| `data/pk_cdn_targets.csv` | Input: CDN/content services to test for in-PK caches (Exp 1.2) |
| `experiments/01_website_destinations/` | Exp 01: website hosting/routing (notes, results, inventory, site list) |
| `experiments/01.1_dns_resolution/` | Exp 1.1: per-ISP DNS resolution (`dns_check.py`) |
| `experiments/01.2_cdn_presence/` | Exp 1.2: CDN/cache presence in PK (`cdn_check.py`) |
| `experiments/02_isp_classification/` | Exp 02: 20-probe deployment plan (PKIX set classification). Also holds the PTCL↔Transworld peering probe (`ptcl_peering.py`, modes `peering`/`hosted`) backing finding 3.1. |
| `experiments/04_path_tromboning/` | Exp 04: systematic path-tromboning detection across an ISP's whole address space. Pipeline: `enumerate_prefixes.py <ASN>` (RIPEstat announced prefixes) → `responsiveness_sweep.py` (find live IPs/prefix) → `tromboning_sweep.py` (TCP/80 Paris traceroute + 3-signal RTT-robust detector). `trace_from_probes.py` = ad-hoc traceroute to one target from named probes (RQ4). Built on **ripe-atlas-cousteau + sagan**. |
| `experiments/03_longitudinal_routing/` | Exp 03: 8 probes → 10 sites, traceroute every 15 min + ping companion over days; path/RTT change over time (`trace_monitor.py`). Committed output is a normalized star schema (`results/<run>/normalized/dim_*`+`fact_*` CSVs) + a `routes_*.txt`; `watch` also writes a local-only Prometheus textfile (`live/<run>/exp03_live.prom`) for Grafana. Probe identity lives in one `PROBE_META` map (labels `isp.city (ASN)`). |
| `experiments/04.1_small_isp_tromboning/` | Exp 4.1: complete block-level tromboning census of every FLL small ISP (`census_sweep.py`; 747 /24s × 8 IPs × 7 probes = 18,260 traces). Canonical output `results/run_*/census_*.csv` + `isp_tromboning.csv`; derived tables (`make_ip_status_table.py`) and route files (`render_{tromboning,filtered,all}_routes.py`) read the **census CSV as the frozen verdict** (re-classifying raw drifts, and raw has ~190 resume-duplicates). |
| `experiments/05_BGProuting/` | Exp 05: BGP validation of traceroute AS paths (`bgp_validate.py`, `bgp_cross_reference.py`) vs RIPEstat bgp-state + bgp.he.net peer tables. **78/80 unique ISP-site paths consistent** with public peering after multi-level checks; 2 benign anomalies. See `findings/05_BGProuting.md`. |
| `experiments/06_submarine_outage/` | Exp 06: SMW5 outage monitor (`outage_monitor.py` — server-side periodic ping+traceroute, 15 min × 12 h, 14 probes → CDN/Abroad/PK sample). `build_timeseries.py` → `results/timeseries.csv`; `rtt_timeseries.ipynb` plots RTT-over-time per site/probe (UTC→PKT). |
| `experiments/06.1_submarine_hegemony/` | Exp 6.1: **SMW5 fault in the control plane** — daily AS-hegemony time series (IHR API, Exp 09's method) for 2026-06-15→07-10 bracketing the 2 Jul fault: probe ISPs' PTCL/TWA dependency + the operators' own upstream mix. Tests whether any *logical* dependencies moved (Exp 06 saw only same-transit load-balancing in the data plane). `hegemony_timeseries.py` → `results/hegemony_timeseries.csv` + `fig_hegemony_smw5.png`. |
| `experiments/07_longitudinal_panel/` | **Exp 07 (FLAGSHIP, LIVE): 7-day uniform panel** — all connected PK probes → frozen 100-site stratified sample (`targets.csv`: 40 PK / 40 CDN / 20 Abroad, CISA-sector proportional). TCP/80 Paris traceroute hourly + ping every 30 min, **server-side periodic measurements split across two accounts by type** (A=100 traces → `results/a/`, B=100 pings → `results/b/`; per-account 100-parallel cap). Launched 2026-07-11, auto-stops 2026-07-18; watchers in tmux on `ispl02`. **After the run: `dump_raw.py` once** for the archival raw JSON (re-fetchable anytime, no credits). `panel_monitor.py` = schedule/watch/fetch/stop; `notes.md` = full design + runbook. |
| `experiments/07_longitudinal_panel/analysis/` | Exp 07 analysis: **`METHODOLOGY.md`** (vantage roster §0 → distance §1 → km→ms §2 → dimensionless latency ratio §3 → geo-IP caveats §4 → reading the plots §8 → **CDN per-ISP treatment §9** + Appendix A geolocation methods, Appendix B multilateration spec) and **`geo.py`** (subcommands `distances` / `locate` / `relocate` / `ratio` / `cdn`). Key methods: Haversine distance, speed-of-light floor (fibre ≈ d/100 ms), **physics arbiter** (ping < vacuum floor ⇒ geo-IP proven wrong — caught 37/78 sites incl. 34 CDNs "in Toronto"), per-ISP CDN locality score. |
| `experiments/08_CDN/` | Exp 08 (Sameera): ACE CDN RTT from all probes (`ACE_CDN_run_all.py`) + targeted IXP checks — 08.1/08.2 PIE Karachi (PTCL+Nayatel → ACE CDN / Connect Communications), 08.3 PKIX Lahore (Z-Com+Nayatel → Transworld). |
| `experiments/09_as_hegemony/` | Exp 09: **AS Hegemony** (Fontugne et al. metric via IIJ IHR public API) — quantifies the PTCL/TWA duopoly from **global BGP data**, independent of our probes. `hegemony.py deps` (per-origin dependencies, validates our traceroute transit findings — e.g. Orbit hege(TWA)=1.0, Nayatel PTCL 0.68/TWA 0.32/Cogent 0.17) + `rollup` (all ~220 PK ASes → % depending on the duopoly). API quirk: requires BOTH `timebin__gte` and `timebin__lte`; no `format` param. See `notes.md`. |
| `paper/` | Paper drafts: `paper.tex` (IEEEtran, full multi-experiment story), `aintec_panel.tex` (**ACM/AINTEC '26, Exp 07 standalone**, results scaffolded `\pending`), `exp07_panel.tex` (IEEE variant), `draft.md`, style/structure notes (`style_notes_ixp.md` = Di Bartolomeo ISCC'15 template, `style_notes_p1.md` = IMC register, `paper_structure.md`, `experiment_consistency.md`), `make_figures.py`. |
| `site_collection/` | Tranco tooling: `get_tranco.py`, `.pk` filtering, DNS/ASN resolution + hosting classification (`classify_pk_hosting.py`) — produced the Exp 07 candidate pool (`site_candidates.csv`, 1,781 sites). |
| `scripts/processtraces/`, `scripts/processtraces2/` | Team-member ad-hoc notebooks (ping/trace EDA on Exp 03 data: hop timeseries, anomaly spikes, heatmaps). Not part of the canonical pipeline. |
| `tools/probe_status/` | Flask dashboard: Google-Sheet probe roster vs live RIPE Atlas status, two sections (**Our Probes** / Existing), pulls each probe's RIPE label+tags on refresh. |
| `findings/` | Analysis writeups (01, 01.1, 01.2, **1.4 PK100 hosting**, 03, **3.1 PTCL↔Transworld**, **04 Worldcall tromboning**, **4.1 small-ISP census**, **06 SMW5 outage**) + charts notebook |

---

## Spin-off experiments 1.1 and 1.2

Both reuse Exp 01's probe list / helpers by **importing** from `pk_multi_probe.py`
(read-only — they do not modify it), and skip offline probes via an
`OFFLINE_PROBES` set (PTCL 1015210, TPCPL 1015679 were down during these runs).

- **Exp 1.1 - per-ISP DNS** (`experiments/01.1_dns_resolution/dns_check.py`):
  RIPE Atlas DNS A-record lookups with `use_probe_resolver=True`, so each probe
  resolves via its own ISP. Addresses the Exp 01 limitation of resolving DNS
  centrally. **Result: only 8 of 103 sites (~8%) returned different IPs per ISP
  (GeoDNS); ~92% identical.** Most of the 8 are just different edges of the same
  CDN; two are notable (`lums.edu.pk` split-DNS private IP on Transworld;
  `nayatel.com` foreign IP on Z-Com). So Exp 01's central resolution was fine for
  the vast majority. See `findings/01.1_dns_resolution_analysis.md`.

- **Exp 1.2 - CDN/cache presence** (`experiments/01.2_cdn_presence/cdn_check.py`):
  PINGs major content services (Netflix, Google, Meta, Akamai, Cloudflare, ...)
  from each probe with `resolve_on_probe=True`; the resolved IP + RTT reveal a
  local cache. Verdict per (service, probe): PK-local (<15 ms) / regional
  (<50 ms) / abroad. **Early result (3 probes): most big content is reached
  "regional" (~20-50 ms, Gulf/region), not from inside Pakistan; only Cloudflare
  and X were PK-local, and only via Nayatel.** Caveat: the ISPs that reportedly
  host embedded caches (Optix, StormFiber, Telenor, ...) are not among our probes,
  so this undercounts - ties into Exp 02.

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
    (1015679, 136174, "Pakistan", "LocalInternetProj01 (TPCPL/Nova, transits Transworld)"),
    (1015210,  17557, "Pakistan", "AS17557 (PTCL)"),
    (  62224,  38193, "Pakistan", "Zartash-Office (Transworld)"),
    (  60223,  23674, "Pakistan", "PK_Inara (Nayatel)"),
    (   7613, 152605, "Pakistan", "Z COM Networks"),
]
```

**Probe roster (name ↔ ID ↔ ASN, connected as of 2026-06-22).** RIPE's API does
**not** expose our custom "LocalInternetProjNN" names, so keep this table current by
hand. Proj-number ≠ probe-ID order.

| Probe ID | ProjNN | ASN | ISP | City | Notes |
|---|---|---|---|---|---|
| 1015679 | Proj01 | AS136174 | TPCPL/Nova | Lahore | transits Transworld; hop-2 Shaw (AS6327) artifact |
| 1016036 | Proj02 | AS9541 | Cybernet | Haripur | |
| 1016143 | Proj04 | AS9541 | Cybernet | Karachi | |
| 1016126 | Proj05 | AS17557 | PTCL | Karachi | route-visible; ~25 ms access floor |
| 1016153 | **Proj14** | **AS135407** | TES-PL (Transworld retail/home) | Karachi | **unfiltered** — best Transworld-family vantage |
| 1016154 | ? | AS9541 | Cybernet | Karachi | unidentified Proj# |
| 64535 | ? | AS151983 | Orbit | Faisalabad | unidentified Proj# |
| 7764 | — | AS17557 | PTCL (anchor, LUMS) | Lahore | **ICMP-filtered** (only hop1/2/dest) |
| 62224 | — | AS38193 | Transworld (Zartash office) | Lahore | **ICMP-filtered**; use ping for RTT |
| 60223 | — | AS23674 | Nayatel | Islamabad | most route-independent |
| 7613 | — | AS152605 | Z-Com | Lahore | anchor |

Disconnected (can't measure): AS38264 Wateen ×4, AS45773 PERN ×2, others.
**ICMP-filtered probes** (62224, 7764) hide their path and report bogus
1000 ms+ dest RTTs (ICMP-error-generation delay) — **use ping (min-of-N) for a real
RTT**, and the unfiltered TES probe (1016153) to *see* a Transworld path.

**Exp 07 panel roster (17 scheduled 2026-07-11; authoritative table in
`experiments/07_longitudinal_panel/analysis/METHODOLOGY.md §0`).** New IDs beyond the table above:
64078 (TES, Lahore), 64722 (TES, Karachi), 65892 (Nayatel, Lahore), 1014872 (Fasttel, Islamabad),
1015491, 1016393 (PTCL, N. Punjab), 1016431 (NTC, Karachi). **Three corrections (verified against
the RIPE probe API):**
- **1015491 is mislabelled "AS13335"** in measurements.json — real ASN **AS152605 (Z-Com)**; never
  treat it as a Cloudflare vantage (fixed via `LABEL_FIX` in `analysis/geo.py`).
- **1016036 (Cybernet) has a placeholder coordinate (30.0, 70.0)** and a 22 ms access floor, so it
  can't be re-located by latency → **excluded from all distance analysis**
  (`EXCLUDE_FROM_DISTANCE`). Earlier docs called it "Haripur" — unverified.
- **1016431 (NTC) returned no data** during the panel (offline).
Per-probe **access floors** (min RTT to any PK site) range 0.2–25.6 ms; subtract before per-ISP
ratio comparisons (1016126 ≈ 25.6 ms, 1016036 ≈ 22 ms, 64535 ≈ 18.3 ms, 1016393 ≈ 14.8 ms).

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
| AS135407| TES-PL / Transworld Enterprise | Transworld's retail/home arm; probe 1016153 (Proj14) |
| AS38710 | Worldcall | ISP; Exp 04 first target (52 announced /24s) |
| AS32787 | Prolexic/Akamai | DDoS mitigation (US) — appears in govt site paths |
| AS174   | Cogent | **Runs a PoP physically IN Pakistan** (~2 ms) used as a domestic interconnect fabric — geo-IP mislabels it "US". Don't treat AS174 hops as foreign without checking RTT. |
| AS6327  | Shaw/Rogers | "Canadian" ISP, but hop 2 of probe 1015679 is **physically in PK** (~1.5 ms) — measurement artifact, exclude from country analysis |
| — | Equinix Singapore (`27.111.228.83`) | Transworld's int'l egress where Worldcall traffic trombones (Exp 04). Unannounced in BGP — only RDAP/hostname (`*.equinix.com`) identifies it. |

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
  operator (PTCL or Transworld) — Z-Com 91/91, TPCPL 65/65 — whereas **Nayatel is
  ~40%** (37/91), the most independent. **Detect by ASN + RDAP registry name:**
  Transworld's backbone is not announced in BGP, so an ASN-only check undercounts
  Nayatel as 6%; the RDAP operator label (already in the data) catches it - no
  hardcoded IP range. Nayatel reaches CDNs/other PK ISPs by direct peering and only
  uses Transworld for foreign-hosted destinations.
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

### Path tromboning — Exp 04 (Worldcall, 2026-06-22)

See `findings/04_path_tromboning_worldcall.md`. From the Nova probe to **Worldcall
(AS38710)**: **16 of 52 announced /24s (31%) trombone to Equinix Singapore** and
back; 36 stay local; **all hairpins handed off by Transworld via `110.93.252.136`**.
Local paths stay in-PK via a **Cogent PoP inside Pakistan** (`149.40.227.134`).

- **RQ4 isolates Transworld as the culprit (a domestic route exists):** the *same*
  Worldcall IP `115.186.61.254` is **LOCAL ~46 ms from PTCL** (path never touches
  Transworld) but **TROMBONE ~134 ms from Transworld** / 117 ms TES / 124 ms Nova.
  Worldcall IP `117.102.19.1` is local from *everyone* (3–20 ms). So Transworld
  routes some Worldcall destinations domestically and hairpins others — a routing
  choice, not a connectivity limit. Strongest form of the PKIX argument.
- **Detector methodology (reusable):** geo-IP lies (Shaw/Cogent register abroad but
  sit in PK at ~2 ms), so tromboning is decided by **RTT physics**, not hop country:
  (a) a responding foreign hop with RTT ≥40 ms, (b) a ≥60 ms RTT jump, or (c) any hop
  ≥70 ms = left PK; a path whose RTT stays <45 ms = local. Ignore RTTs >~500 ms
  (queuing / ICMP-error-generation artifact, esp. on filtered probes — use **ping
  min-of-N** there). This took the result from 53/53 false positives → 16/52 clean.
- **Open caveat:** "per-prefix" is so far an *inference* — only one IP/­/24 was tested;
  intra-/24 consistency is unverified, and per-flow/time variance is real (an IP
  flipped local↔abroad minutes apart). The intra-block test (many IPs in one /24) is
  the next step.

### Small-ISP tromboning census — Exp 4.1 (complete, 2026-07-03)

See `findings/04.1_small_isp_tromboning.md`. Scaled Exp 04 to every FLL small ISP
(747 /24s × 8 IPs × 7 probes = **18,260 traces**).
- **~11% hairpin abroad, ~85% local** (2,002 trombone / 15,451 local / 807 inconclusive).
- **The source ISP dominates:** trombone rate is driven by *where you measure from* —
  **Cybernet-Haripur 46%, PTCL-Karachi 38%** vs **4–10%** for Nova/Z-Com/Orbit/Cybernet-Khi
  and **Nayatel 4%** (cleanest). Same Cybernet ISP = 46% from Haripur but 10% from Karachi →
  per-PoP, not just per-ISP.
- **Transwo­rld (589) ≈ PTCL (566)** split the attributable hand-offs abroad; exits are
  **China (347) > US (259) > Singapore (107)**.
- **Intra-block consistency 82%** (of source×block pairs uniform across their 8 IPs) — a /24
  is a usable routing atom ~4/5 of the time (answers the Exp 04 open question).
- **Consistency note:** the census CSV is canonical; the raw checkpoint holds ~190
  resume-duplicate measurements and `hop_geo` re-classification drifts (live lookups), so all
  derived tables/routes are keyed off the frozen census CSV verdict.

### Submarine-cable outage — Exp 06 (SMW5, Jul 2026)

See `findings/06_submarine_outage.md`. 14 probes → CDN/Abroad/PK sample, 15 min × 12 h.
- **A latency degradation, not a blackout** — international RTT ran 2–6× and erratic;
  median stayed ~baseline because monitoring began *after* the outage was active.
- **It eased over the window** (first-vs-last is the right lens): worst paths recovered
  sharply (shophive via PTCL **646→278 ms**), improving even into peak hours.
- **Quantified (peak vs recovered, international): +2% mean RTT, +31% jitter, flat path
  length** — hit as *instability*, not a latency step; concentrated on PTCL (RTT +12%,
  jitter +50%), local unaffected. See `experiments/06_submarine_outage/outage_impact.py`.
- **No cable-restore reroute** — path changes were load-balancing within the same transit
  (same exit country); the SMW5-era detour's congestion cleared (a splice takes days).
- **Local/PK-hosted traffic was unaffected** — the resilience argument for PKIX. One local
  anomaly: `pbs.gov.pk` spiked chaotically ~08:00–10:00 PKT across all probes (separate event).

### BGP validation — Exp 05 (48-h window, Jun 2026)

See `findings/05_BGProuting.md`. Traceroute-observed AS paths cross-checked against RIPEstat
bgp-state + bgp.he.net peer tables (multi-level: direct peer, or peer-of-peer within 3 hops):
**78/80 unique ISP-site paths fully consistent** with public peering. Most RIPEstat matches are
"partial" (private peering isn't re-advertised globally) — expected, not anomalous. Two benign
exceptions: Cybernet→MCB via undocumented AS20773 (stable across 90 rounds — a private Arelion
downstream), and one transient Nayatel→MCB round via GoDaddy (1/191 rounds). Validates the
traceroute data's integrity; also confirms Nayatel reaches CDNs via Transworld's direct
Cloudflare peering.

### Exp 07 preliminary analysis (partial 3-day ping data; re-run after 2026-07-18)

From `experiments/07_longitudinal_panel/analysis/` (methods in `METHODOLOGY.md`, code `geo.py`):
- **Latency ratio** (measured RTT ÷ speed-of-light theoretical, dimensionless; unicast only):
  **Pakistan median 6.5× with a tail to ~100×; Abroad median 2.6×, tight.** Domestic routing is
  relatively *further* from physics than international. (Caveats: tiny PK floors inflate the
  ratio; some "PK" sites are actually offshore.)
- **Physics arbiter:** measured ping < vacuum-light floor to the geo-IP location ⇒ location proven
  wrong. **37/78 sites failed** (34/40 CDN "in Toronto/Ottawa", + 3 PK intra-country) — all
  actually local. `phf.gop.pk` (Punjab govt, tagged PITB) confirmed genuinely US-hosted
  (~233 ms from every probe, consistent with geo-IP Coral Springs); `toptop.net`, `youth.cn`,
  `efulife.com` also offshore despite "Pakistan" class.
- **CDN per-ISP locality score** (anycast has no single location — each ISP reaches its own PoP;
  score = % of CDN sites reached <15 ms): **Nayatel 85% local (median 3 ms) → Cybernet 41% → TES
  20% → everyone else 0% — PTCL worst (median 136 ms)**. Same content ~40× slower by ISP choice;
  independent of ISP size — it's local peering (the Set-2/3 story, now quantified per ISP).
- **22 of 40 PK-class sites block ICMP ping** (mostly .gov.pk/.edu.pk) — no RTT in the ping panel;
  fill from the TCP/80 traceroute half (results/a) at analysis.

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
- **Quotas learned during Exp 07 (actual account dashboard):** the caps are
  **100 simultaneous measurements PER ACCOUNT** (the only binding limit),
  10M credits/day spend, 1M results/day, 1000 probes/measurement, 25
  periodic + 25 one-off per target. Cost per result: ping 3 cr, traceroute
  30 cr. **Credits are per-account — there is NO shared pool**; "sharing" is a
  manual transfer between accounts (tested: a create from a 0-balance account
  fails even when a linked account holds millions).
- **Two-account pattern (Exp 07):** to run >100 concurrent measurements, split
  **by measurement type** across two accounts (A = all traceroutes, B = all
  pings) against the same target list; namespace outputs (`PANEL_INSTANCE`) and
  merge at analysis on (probe, target, timestamp) — identical to an uncapped
  single account.
- **Server-side periodic measurements** (`is_oneoff=False`, start/stop window)
  run on RIPE's infrastructure regardless of the local host; a `watch`/fetch
  loop can die and restart freely with no data loss. Raw JSON is retrievable
  per msm-id forever, at zero credit cost.
- CSV files are written `encoding="utf-8"` — geolocation city names contain
  non-ASCII characters (e.g. `ā`) that crash the default Windows cp1252 codec.

---

## Dependencies

```bash
pip install requests dnspython python-dotenv          # Exp 01/03 (hand-rolled API)
pip install ripe.atlas.cousteau ripe.atlas.sagan      # Exp 04 (official RIPE libs)
```

Exp 01/03 hand-roll the RIPE Atlas REST API with `requests`. **Exp 04 onward uses the
official libraries**: `ripe.atlas.cousteau` to create/fetch measurements
(`Traceroute(protocol="TCP", port=80, paris=16)`, `AtlasSource`, `AtlasCreateRequest`,
`AtlasResultsRequest`) and `ripe.atlas.sagan` (`TracerouteResult`) to parse results.
Use `.last_median_rtt` (not the deprecated `.last_rtt`). `RIPE_API_KEY` still comes
from `.env` via `pk_multi_probe` (Exp 04 scripts import its ASN/RDAP helpers).