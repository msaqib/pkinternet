# Exp 07 — Latency-vs-Distance Methodology

**What this produces:** for **every probe × every website**, a single **dimensionless number** —
the *measured* RTT divided by the *theoretical minimum* RTT that the physical distance allows. This
"latency ratio" (latency inflation / stretch) is the metric the reference paper uses; it is unitless,
so it plots cleanly as a CDF or box-and-whisker and can be sliced by site type (local / abroad / CDN).

The pipeline is three stages:

```
(1) locate endpoints  →  distance in km        [Haversine, great-circle]
(2) km → ms           →  theoretical min RTT   [speed of light in fibre, round trip]
(3) measured ÷ theoretical  →  latency ratio   [dimensionless; keep site type for slicing]
```

**The pipeline forks by site type.** Stages 1–3 apply to **unicast** sites (one real server:
Pakistan + Abroad). **Anycast CDN sites have no single location** — each ISP is served from a
different PoP — so for them "where is it?" is not a well-posed question and the distance/ratio is
skipped; they get the **per-ISP near/far treatment** of §9 instead (`geo.py cdn`).

**Contents:** §0 Vantage points · §1 Locating + distance · §2 km→ms theoretical RTT · §3 latency
ratio · **§3b the three site types at a glance (location · formula · reading)** · §4 how coordinates
are found · §5 scale · §6 assumptions · §7 output · §8 reading the ratio plots · §9 CDN sites: the
per-ISP treatment · Appendix A geolocation methods · Appendix B multilateration spec.

**Files in this folder (deliberately minimal).** One script, three data files, the figures:
- **`geo.py`** — the whole pipeline as subcommands. Standard order:
  `correct` (physics-check + fix site locations/classes → `targets_corrected.csv`) →
  `ratio` (auto-runs `correct` if needed; distances + ratios → `ratio_corrected.csv` + the official
  figures) → `cdn` (per-ISP CDN treatment + `ratio_vs_best` → `cdn.csv`).
  Diagnostics on demand (print/inspect; any files they write are regenerable and disposable):
  `distances`, `locate <sites…>`, `relocate`.
  **`annotate [routes.txt] [max_blocks]`** — offline route annotator: re-renders a `routes_*.txt`
  with per-hop `ASN | operator | geo-cc` (RIPEstat, with an RDAP `[registry]` fallback for
  unannounced hops such as the Transworld backbone and the Equinix egress). Run **once on frozen
  post-run data** — never live during collection (the Exp 4.1 no-drift rule); output lands next to
  the input as `*_annotated.txt`. Geo-cc is a label only; verdicts stay RTT-physics.
- **`targets_corrected.csv`** — per-site verified location/class (the §4/§3b corrections record).
- **`ratio_corrected.csv`** — per (probe, site): distance, theoretical, measured, ratio, intercity.
- **`cdn.csv`** — per (probe, CDN site): min RTT, PoP class, `ratio_vs_best`.
- **`figures/`** — deliverables (`ratio_cdf_all3`, `ratio_box`, `cdn_heatmap` + supporting/teaching
  figures). Hidden `.cache_*.json` files avoid re-fetching lookups; safe to delete.

---

## 0. Vantage points (the probes we measure from)

Distance and RTT are always **from a probe**, so the probe set is part of the methodology. We use the
RIPE Atlas probes that were **connected in Pakistan when the panel launched** (discovered live via the
API, not a hardcoded list): **17 scheduled, 16 returning data** (NTC `1016431` produced no results).
Coordinates are the probe hosts' declared positions (RIPE); ASN and status from the RIPE probe API;
the access floor is each probe's fastest ping to any Pakistani site (a proxy for its last-mile
overhead).

| Probe | ISP | ASN | City | Coordinates (lat, lon) | Access floor | Notes |
|---|---|---|---|---|--:|---|
| 7613 | Z-Com | 152605 | Lahore | 31.509, 74.338 | 0.2 ms | cleanest vantage (co-located hosting) |
| 1015491 | *(labelled "AS13335")* | **152605 (Z-Com)** | Lahore | 31.558, 74.362 | 3.5 ms | **label wrong** — real ASN is Z-Com |
| 65892 | Nayatel | 23674 | Lahore | 31.518, 74.362 | 4.1 ms | |
| 1015679 | Nova / TPCPL | 136174 | Lahore | 31.462, 74.430 | 1.9 ms | traceroute hop-2 "Shaw" artifact (path only) |
| 7764 | PTCL | 17557 | Lahore | 31.470, 74.410 | 5.0 ms | **ICMP-filtered** (path hidden; ping RTT valid) |
| 64078 | TES (Transworld Home) | 135407 | Lahore | 31.521, 74.361 | 4.5 ms | |
| 62224 | Transworld | 38193 | Lahore | 31.470, 74.409 | 3.7 ms | **ICMP-filtered**; the LDI backbone vantage |
| 1016143 | Cybernet | 9541 | Karachi | 24.858, 66.999 | 4.5 ms | |
| 1016154 | Cybernet | 9541 | Karachi | 24.860, 66.999 | 3.6 ms | |
| 1016126 | PTCL | 17557 | Karachi | 24.860, 66.999 | 25.6 ms | high last-mile floor (container/access anomaly) |
| 64722 | TES (Transworld Home) | 135407 | Karachi | 24.799, 67.079 | 2.8 ms | |
| 1016431 | NTC | 23888 | Karachi | 24.788, 66.969 | — | **no data returned** (offline during run) |
| 60223 | Nayatel | 23674 | Islamabad/Rawalpindi | 33.699, 72.989 | 2.8 ms | most route-independent |
| 1014872 | Fasttel | 150683 | Islamabad/Rawalpindi | 33.608, 72.990 | 5.0 ms | |
| 64535 | Orbit | 151983 | Faisalabad | 31.399, 73.118 | 18.3 ms | |
| 1016393 | PTCL | 17557 | N. Punjab (Mianwali area) | 32.569, 71.531 | 14.8 ms | |
| 1016036 | Cybernet | 9541 | *(unknown)* | 30.000, 70.000 | 22.0 ms | **placeholder coordinate** — **excluded from distance pipeline** (caveat 3) |

**Coverage (why this set):**
- **Both licensed international operators** — PTCL (AS17557 ×3) and Transworld (AS38193 ×1), plus
  Transworld's retail arm **TES** (AS135407 ×2).
- **Seven downstream ISPs:** Cybernet (AS9541 ×3), Nayatel (AS23674 ×2), Z-Com (AS152605 ×2),
  Nova/TPCPL (AS136174), Fasttel (AS150683), Orbit (AS151983), NTC (AS23888, offline).
- **Multiple probes per major ISP and per city** — to compare *within* an ISP and across ISPs from
  one city. Cities: Lahore ×7, Karachi ×5, Islamabad/Rawalpindi ×2, Faisalabad ×1, + 2 Punjab probes.

**Documentation caveats (carry these into any per-probe claim):**
1. **`1015491` was mislabelled "AS13335"** — its real ASN is **152605 (Z-Com)**. **Resolved:** the
   pipeline (`geo.py` `LABEL_FIX`) relabels it `zcom`; no phantom "AS13335" ISP.
2. **`1016431` (NTC) returned no data** — excluded from RTT-based results (its distance is still valid).
3. **`1016036` (Cybernet) coordinate `30.0, 70.0` is a placeholder.** It **cannot be re-located by
   latency** — its fastest ping to any site is 22 ms (self-radius ~2,246 km, larger than Pakistan),
   because that 22 ms is last-mile overhead, not distance. **Resolved:** **excluded from the distance
   pipeline** (`geo.py` `EXCLUDE_FROM_DISTANCE`); its RTTs may still feed non-distance analyses.
4. **ICMP-filtered probes (`7764`, `62224`)** hide their traceroute path but give **valid ping RTT**.
5. **High access floors** (`1016126` 25.6 ms, `1016393` 14.8 ms, `64535` 18.3 ms) inflate the *ratio*
   on short distances — remove them via the per-probe access floor before comparing ISPs.

---

## 1. Locating the endpoints and computing distance

### 1.1 The probe's latitude/longitude
From the RIPE Atlas probe API `GET /api/v2/probes/{id}/`, field `geometry = [lon, lat]` — the host's
declared coordinates. Public request, no key, zero credits. City-accurate (sometimes ~1 km rounded).

### 1.2 The website's latitude/longitude  *(see §4)*
1. **Resolve the hostname to a server IP** — the exact IP the panel measured, from
   `results/{a,b}/measurements.json`, so location matches the host the RTTs were taken against.
2. **Geolocate that IP** with **ip-api.com** (`lat,lon,city,countryCode`), cached to disk.

ip-api returns a **city and its centroid**, not the exact building — a website's lat/long is "the
centroid of the city ip-api assigns its IP" (see §4 for what this costs).

### 1.3 Coordinate system
WGS-84 decimal degrees (what both APIs return), converted to radians (`rad = deg · π/180`).

### 1.4 Distance — the Haversine (great-circle) formula
Shortest path between two points over the surface of a sphere. For `(φ₁,λ₁)`, `(φ₂,λ₂)` in radians:

```
Δφ = φ₂ − φ₁                                            R = 6371 km  (mean Earth radius)
Δλ = λ₂ − λ₁
a  = sin²(Δφ/2) + cos φ₁ · cos φ₂ · sin²(Δλ/2)
c  = 2 · atan2(√a, √(1−a))          # central angle (rad)
d  = R · c                          # great-circle distance (km)
```
`atan2` (≡ `2·asin√a`) is numerically stable from a few km to half the globe.

---

## 2. Converting km → ms (the theoretical minimum RTT)

A signal in fibre travels at ~2/3 of light-in-vacuum:
```
v_fibre = c / n = 299 792.458 / 1.468 ≈ 204 218 km/s ≈ 204.2 km per ms
```
A packet travels the distance **there and back**, so the theoretical *round-trip* minimum is:
```
theoretical_RTT_ms = 2 · distance_km / v_fibre  ≈  distance_km / 102.1   (~1 ms per ~102 km one-way)
```
This is the fastest the round trip could physically be; no measurement can beat it. We also record the
vacuum value (`2·d/c`) as an absolute hard floor for sanity checks; the ratio uses the **fibre**
theoretical, since real paths run on fibre.

---

## 3. The dimensionless latency ratio (the headline metric)

For each (probe, website) pair with a measured RTT:
```
latency_ratio = measured_RTT_min_ms / theoretical_RTT_ms          (dimensionless)
```
- `measured_RTT_min_ms` = the **minimum ping** over the run (min-of-N: noise only adds delay, so the
  minimum is the cleanest estimate of true path latency).
- **1.0** = at the physical limit; **3.0** = three times slower than physics allows; **< 1.0** is
  impossible and flags a wrong location (§4 / Appendix B).

Being unitless, the ratio is comparable across near and far sites — the right quantity for a **CDF**,
**box-and-whisker**, or per-ISP summaries. **We keep the site `class` ∈ {Pakistan, Abroad, CDN}** as a
column so every plot can be sliced by hosting type (and by probe/ISP).

### 3b. The three site types at a glance — location, formula, reading

One reference block per class: how its location was determined, the exact ratio formula, and how to
read the number.

| | **Pakistan** (local server) | **Abroad** (foreign server) | **CDN** (anycast) |
|---|---|---|---|
| what it is | one real machine in PK | one real machine overseas | same IP served from many PoPs |
| location method | geo-IP, physics-verified | geo-IP, corroborated | **none exists** — per-ISP PoP instead |
| theoretical min | straight fibre over distance | straight fibre over distance | **best RTT any PK probe achieves** |
| full-week median (14-probe roster) | 2.88× | 2.46× | 8.43× |

**Pakistan-class sites**
- **Location:** hostname → the measured server IP (`measurements.json`) → **ip-api geo-IP** (city
  centroid). Then **physics-checked**: if any probe's ping beats the vacuum-light round trip to that
  city, the city is impossible — 3 such sites were **re-located by multilateration** (the
  RTT-weighted centroid of the probes' distance circles, Appendix B), and 3 sites that were FAR from
  *every* probe (nearest ping > 20 ms) were **re-classed to Abroad**.
- **Formula:** `d = Haversine(probe, site)`; `theoretical = 2·d / v_fibre (≈ d/102 ms)`;
  `ratio = measured_min ÷ theoretical`. Only for pairs **≥ 30 km** apart — same-city pairs are
  reported in plain ms (theoretical ≈ 0 makes the division degenerate).
- **How to read:** 1× = a dead-straight private fibre. Median **2.88×** (full week) = the typical
  domestic connection takes ~3× the physics time (normal Internet overhead). The **10–30× tail**
  (24% of pairs above 10×) = routes taking real detours (hairpins/poor peering) — the finding.

**Abroad-class sites**
- **Location:** same method — measured IP → ip-api. A slow ping can never *disprove* a far location
  (slowness is always possible), so physics can't catch errors here the way it does for PK claims;
  corroboration comes from **reverse-DNS hosting names** (e.g. `…spaceship.host`) and from the RTT
  being *consistent* with the distance. Includes the 3 re-classed ex-"PK" sites at their geo-IP
  locations.
- **Formula:** identical to Pakistan (distance-based straight-fibre floor, ≥ 30 km trivially true).
- **How to read:** this class is the **control group**. Median **2.46×** (full week), everything
  within ~7× — what routing looks like when it works. Any class doing worse than this is underperforming
  ordinary international transit.

**CDN-class sites**
- **Location:** **deliberately not determined** — an anycast IP has no single location. Geo-IP
  returns the registration city (proven physically impossible for 34/40 of them: pings beat light to
  "Toronto"). What we *can* bound: the fastest probe's RTT proves **a serving PoP exists within
  `RTT/2 × v_fibre` km of that probe** (e.g. within ~255 km of Islamabad). Which PoP each ISP
  reaches is a property of the **ISP's peering**, shown in the heatmap.
- **Formula (instructor's definition):**
  `ratio_vs_best = measured_min(probe → site) ÷ min over ALL probes of measured_min(· → site)`.
  The denominator is a real, attained path — any ISP could peer with the best-performing ISP and
  match it — so it is a legitimate, measured floor. No distance, no geo-IP anywhere in it.
- **How to read:** **1× = this ISP rides the best path available in Pakistan** (it defines the
  frontier). **52× (PTCL)** = its customers wait 52× longer for the same content than the
  best-peered ISP's customers — a gap closable by peering, not bandwidth. Sites that are far for
  *everyone* (US-WAF-fronted) score ≈1 for all ISPs — correctly, since no peering could improve
  them (the heatmap's solid-red columns identify these).

---

## 4. How website coordinates are obtained, and the city-only cases

**Method (state this in the paper):** each site's apex hostname → the measured IP → ip-api, which
returns a **city and the city's centroid coordinates**. We do **not** get building/rack coordinates.

**Can we only determine the city? In effect, yes — the city is the finest resolution we get:**
- **0 of 100** sites fell back to country-level only — every site returned at least a city.
- The coordinates are **city centroids, not distinct server points**: the 100 sites resolve to only
  **44 distinct lat/long points** — e.g. **24** CDN sites at Toronto's centroid, 9 at Ottawa, 6 at
  Lahore, 6 at Islamabad, 4 at Helsinki, 4 at Singapore.

**Consequences:**
- **Inter-city / intercontinental** distances: centroid error (~10–50 km) is **< 1 %** — negligible.
- **Intra-city** pairs: "same city ≈ a few km," correct in spirit but not building-precise.
- **Anycast CDNs:** the returned city (Toronto) is the **registration** city, not where it serves —
  those coordinates are *wrong*, flagged `geo_method = cdn_dstip`; the ratio < 1 test (Appendix B)
  catches them automatically.

### 4.1 Alternative location methods considered (and why geo-IP at this step)
Truly *exact* (building-level) location is generally unobtainable without inside access. Options
best-to-worst for our purpose:

| Method | How it works | Accuracy | Fit here |
|---|---|---|---|
| **Database geo-IP** (ip-api, MaxMind) | registration + crowd DB | city-level; **wrong for anycast** | **used now** — simple, good enough for the km distances that dominate |
| **Reverse-DNS hints** | airport/city codes in the PTR | precise *if present* | some hosts only; better for router hops |
| **Active latency geolocation** (CBG/Octant, RIPE IPmap) | RTT from known-position landmarks (multilateration) | metro / tens of km; **geo-IP-independent** | **the principled upgrade** — we already have 17 probes + their RTTs |
| **Application truth** (Cloudflare `/cdn-cgi/trace` → `colo`) | the CDN reports its serving PoP | authoritative *for CDN* | needs an HTTP vantage (RIPE probes can't) |

**Why geo-IP for this step:** no extra infra, city-accurate (< 1 % error on the distances that
dominate); its one failure (anycast CDNs) is *auto-detected* by physics (a ratio < 1 is impossible).
**Next step:** re-locate the failing sites by **latency multilateration** (Appendix B), cross-check
with **RIPE IPmap**, and get **Cloudflare `colo`** for CDNs. `geo.py locate` prototypes all of these.

---

## 5. Scale and units
- **Distance:** kilometres, to 0.1 km. Range ~0.1 km → ~13,500 km (≈ 4 orders of magnitude → distance
  plots use a **log** scale).
- **Theoretical & measured RTT:** milliseconds. **Latency ratio:** dimensionless (~1–100; log axis
  suits its CDF).

## 6. Assumptions
1. **Spherical Earth, R = 6371 km** (< 1 % distance error).
2. **A site's location = the city-centroid geolocation of its measured IP** — city-reliable for
   unicast; **not** for anycast CDNs (flagged).
3. **One IP per site** (measured apex IP); GeoDNS/multiple A-records ignored.
4. **Probe coordinates as declared to RIPE** (may be ~1 km rounded; placeholders excluded — §0).
5. **Great-circle = straight line;** real fibre is longer, so the theoretical RTT is a *lower bound*
   and the ratio is a conservative (slightly high) efficiency estimate.
6. **min-of-N** removes transient queuing.
7. **Static snapshot:** one fixed location per endpoint.

## 7. Output — the DataFrame / listing
One row per (probe, website) pair:
```
probe_id, probe_isp, probe_lat, probe_lon,
target, class, ip, target_lat, target_lon, target_city, target_cc, geo_method,
distance_km, theoretical_rtt_ms, measured_rtt_min_ms, latency_ratio
```
`class` is retained for slicing; `geo_method` marks CDN rows provisional. Pairs with no measured RTT
(e.g. ICMP-blocked sites) keep distance/theoretical and a blank ratio, counted separately.

---

## 8. Reading the ratio plots (`geo.py ratio`)

> **Final-figure decisions (2026-07-15).** (1) Deliverable axes are **linear** — our ratios span
> only ~1–50, and log axes confused readers; log is reserved for the internal distance plots that
> genuinely span orders of magnitude. (2) The deliverable set is: `ratio_cdf_all3.png` (CDF, all
> three site types — PK/Abroad on the fibre floor, CDN on the best-observed floor of §9.3b),
> `ratio_box.png` (same three classes), and the **CDN heatmap** `cdn_heatmap.png` (rows = ISP
> peering ranking; solid-red columns = site-property, not ISP-property). (3) Same-city pairs
> (<30 km) are excluded from ratios and reported in plain ms (median 6.1 ms); ping-blocked sites
> (22 of 40 PK) are filled from the TCP/80 traceroute half after the full run. (4) The ratio is
> **raw** (no access-floor subtraction) to match the reference paper; the decomposition is quoted
> in text: PK path-only median is 1.9× after subtracting the per-probe last-mile floor.

Both plots use the **latency ratio** (measured RTT ÷ theoretical minimum). It is unitless, and drawn
on a **log axis** because it spans ~1–100×. **1× = the physical floor** (dashed line): a real point
can never be below it. The plots use only the trustworthy **unicast** sites (Pakistan + Abroad); CDN
is held out (its geo-IP distance is wrong — correct it via `geo.py relocate` first).

**`figures/ratio_cdf.png` — cumulative distribution.**
- X = latency ratio (log); Y = cumulative fraction of probe–site pairs.
- Read a point as: *"this fraction (Y) of pairs have a ratio at or below X."* The **median** is where
  a curve crosses **Y = 0.5** (Pakistan ≈ 6.5×, Abroad ≈ 2.6×).
- **Steeper curve = tighter/more consistent**; a **long shallow tail = highly variable**. A curve
  **further right = worse** (more inflation). The horizontal **gap between the two curves** at a given
  Y is how much more inflated one class is than the other.

**`figures/ratio_box.png` — box-and-whisker by hosting type.**
- One box per class: the **box = the middle 50%** (25th–75th percentile), the **thick line = median**,
  the **whiskers = the spread** (outliers hidden). Log Y; dashed line = 1× floor.
- **A tall box = high variability; a short box = consistent.** Compare median lines for the typical
  inflation and box heights for the spread.

**What they show (this run):** Abroad routing is **efficient and uniform** (median 2.6×, tight),
while Pakistani routing is **more inflated and far more variable** (median 6.5×, tail to ~100×).

**Read with two caveats (see §6):** (a) PK physical floors are tiny (a few ms), so ordinary last-mile
overhead inflates the *ratio* even without a detour — remove the per-probe access floor before
comparing ISPs; (b) some "PK" sites are actually offshore/tromboning, which lengthens the tail. These
figures are on the **partial 3-day data**; min-of-N is stable, so they will barely move on the full run.

---

## 9. CDN sites: the per-ISP treatment (`geo.py cdn`) — and why not multilateration

### 9.1 Why the question changes for a CDN
For a unicast site there is one server, so *"where is it?"* has an answer, and stages 1–3 apply. An
**anycast CDN announces the same IP from many PoPs**: our own data shows the identical IP answering
Nayatel in **2.5 ms** and PTCL in **~136 ms** — different probes are served by **different physical
buildings**. The difference is in **routing (BGP), not DNS**: every probe measured the *same*
centrally-resolved IP (panel IPs were resolved once, on the measurement server), yet reached
different PoPs. So for a CDN, *"where is it?"* has **no single answer**, and we replace it with a
question that does: **"from each ISP, is this CDN reached NEAR or FAR?"** — which the RTT answers
directly, no location needed.

*(Aside: GeoDNS — different resolvers receiving different IPs — is a separate, smaller effect
(~8 % of sites in Exp 1.1). Central resolution misses it; anycast routing, above, is the dominant
effect for our CDN class and is unaffected by where the name was resolved.)*

### 9.2 Why multilateration is NOT the tool for CDN location
Multilateration's core premise (Appendix B, Step 3) is that **all probes' circles contain the same
point**, so intersecting them narrows down one server. **For anycast that premise is false:**
Nayatel's 2.5 ms circle contains *Nayatel's* PoP (Islamabad); PTCL's 136 ms circle contains
*PTCL's* PoP (elsewhere). The circles bound **different objects**, so their intersection — and the
weighted-centroid point estimate — is **meaningless for a CDN**. Two pieces of the method survive,
reinterpreted:
1. **The physics arbiter (B.6) stays valid** — if any probe beats light to the geo-IP point, that
   claimed location is proven wrong (this is what disproved "Toronto").
2. **The nearest-probe bound (B.5 Step 2) stays valid but means less** — it proves *"at least one
   PoP exists within `R_nearest` of that probe"* (existence of a local PoP), **not** "the server is
   there."

**Division of labour:** multilateration = locating **unicast** servers + impossibility proofs;
the per-ISP scoring below = the correct treatment for **anycast**.

### 9.3 The per-ISP CDN treatment (the method)
For every (probe, CDN-site) pair, classify by the measured min-RTT — thresholds follow Exp 1.2:

```
local     RTT < 15 ms      (served from a PoP inside Pakistan for this ISP)
regional  15–50 ms         (a nearby-region PoP, e.g. Gulf)
distant   > 50 ms          (a far/foreign PoP)
```

*Relation to Appendix B:* the classification uses the **measured RTT only** — but each threshold is
a **per-probe distance bound in disguise**, i.e. multilateration **Step 1** (one circle per probe,
radius `= RTT/2 · v_fibre`) applied per probe **without** the cross-probe intersection that Rule 8
invalidates for anycast: 15 ms ⇒ the serving PoP lies within ~1,530 km of *that probe*; 50 ms ⇒
within ~5,100 km. So the CDN treatment is the valid per-probe remnant of the latency method — no
geo-IP anywhere in it.

Then the **per-ISP CDN-locality score** = the share of CDN sites that ISP reaches **locally**. This
is a *service-quality* metric, not a location: it ranks ISPs by how well they are peered with the
CDNs (RQ1), which is exactly what the PoP differences reflect. Output: `cdn.csv` (per-pair) and
`figures/cdn_by_isp.png` (a 100 %-stacked bar per ISP: green = local, amber = regional,
red = distant; annotated with % local and median RTT).

### 9.3b The CDN latency ratio (instructor's definition) — CDN joins the main CDF
A distance-based theoretical minimum fails for CDNs (no true location; nearest-PoP distance ≈ 0).
The working definition: **a CDN site's theoretical minimum = the best RTT any Pakistani probe
actually achieves to it.** That number is attainable by construction — *any ISP could peer with the
best-performing ISP (e.g. at PKIX) and match it* — so it is a legitimate floor, and it is measured,
not modelled.

```
ratio_vs_best(probe, site) = min_RTT(probe → site) ÷ min over all probes of min_RTT(· → site)
```

- **1.0 = at the frontier** (this ISP defines or matches the best path); large = what the ISP loses
  by not peering. It is dimensionless, so **CDN joins the PK/Abroad curves on one CDF**
  (`figures/ratio_cdf_all3.png`), with the caption noting the two floor definitions.
- Full week (14-probe roster): pooled CDN median **8.43×**; per-ISP medians = a
  **peering-inefficiency score**: Nayatel 1.1 → Cybernet 2.0 → mid-pack 7.1–9.8
  (Zcom/Nova/Orbit/TWA/TES) → Fasttel 10.8, PTCL 12.7. The CDF's shape is bimodal (~27 % at
  ≲1.5×, a long plateau, ~23 % beyond 40×): peering is effectively binary.
- Caveats: the benchmark includes the best probe's own last-mile (conservative); for sites that are
  far for *everyone* (US-WAF/Sucuri), the best is itself ~100 ms, so all ISPs score ≈1 — correct
  under this definition (no peering could improve those; the heatmap's red columns catch them).
- Computed in `geo.py cdn` (`ratio_vs_best` column of `cdn.csv`).

### 9.4 How to read the chart + this run's result
Greener bar = better CDN access. This run (partial 3-day data): **Nayatel reaches 85 % of CDN sites
locally (median 3 ms); Cybernet 41 %; TES 20 %; every other ISP 0 % — PTCL worst at median 136 ms.**
Same content, ~40× slower, depending only on the ISP — and it is not about size (PTCL is the
largest). It is **local peering**, the Set-2/Set-3 distinction PKIX exists to fix. Caveat: the CDN
class is heterogeneous — a Cloudflare-style anycast site shows the bimodal local/distant split,
while a US-WAF-fronted site (e.g. Sucuri) is uniformly distant for everyone; the score absorbs both
(a uniformly-distant site simply counts as "distant" for every ISP).

---

# Appendix A — Geolocation Methods Compared

A plain-language guide to the ways we can locate a website's server. Prototyped in `geo.py locate`.

## A.1 The five methods (what · how · gap · trust · best-for)

**1. Geo-IP database (ip-api, our default)** — an online IP→city lookup from registration/crowd data.
Fills: *a* location for every site instantly. Trust: country almost always right, city roughly right,
**anycast CDN wrong** (coordinates are the city centre). Best for ordinary single-server sites.

**2. Reverse DNS (the server's own hostname / PTR)** — sometimes carries airport/city codes or the
hosting company. Fills: a free, independent hint (it exposed `tallymarksapp.com` and `…spaceship.host`
in our test). Trust: useful when present, often absent. Best for identifying the **hosting provider**.

**3. RIPE IPmap (active-measurement geolocation)** — RIPE pings IPs from known locations and infers
position. Fills: a database-free second opinion. Trust: accurate where covered, **but mostly covers
routers, not web servers** (empty for 3 of our 4 test sites). Best for **routers/hops**.

**4. Cloudflare "colo" (`/cdn-cgi/trace`)** — Cloudflare reports which data centre served you
(`HKG`, `KHI`…). Fills: the **authoritative** CDN serving location. Trust: authoritative, but reports
the PoP for **the requester's** machine — must be run **from a PK host** to reflect PK users. Best for
**CDN sites** from a PK vantage.

**5. Latency multilateration (our probes)** — location from ping times using probes of known position;
a ping can't beat light, so a small RTT means the server is close. Fills: **geo-IP-independent** — it
**fixes the CDN case** and decides local-vs-far. Trust: strong when a probe is near (tens–hundreds of
km); **cannot pinpoint servers far from every probe** (only says "far"). Best for **CDNs** and any
"is it local?" question. **Full spec: Appendix B.**

## A.2 Evidence (four sites, `geo.py locate`)

| site | type | geo-IP | reverse-DNS | IPmap | CF colo | **latency (ours)** |
|---|---|---|---|---|---|---|
| zcomnetworks.com.pk | local | Lahore ✓ | its own name ✓ | Lahore ✓ | — | **within 20 km of Lahore** ✓ |
| phf.gop.pk | gov | Coral Springs, US | **tallymarksapp.com** | — | — | **far, not local** |
| paknavy.gov.pk | CDN | **Toronto ✗** | — | — | HKG | **within 255 km of Islamabad ✓** |
| 588wingames.pk | abroad | Los Angeles, US | **…spaceship.host** | — | — | **far, not local** |

## A.3 Which method for which site type

| Category | Best method | Backup | Avoid |
|---|---|---|---|
| **Local (PK server)** | geo-IP | latency confirms; reverse-DNS | — |
| **Abroad (real foreign server)** | geo-IP + reverse-DNS | latency confirms "far" | latency for exact city |
| **CDN (anycast)** | **latency (ours)** | Cloudflare `colo` from a PK host | **geo-IP**, IPmap |

One-line rule: **use geo-IP by default; for CDNs trust the latency method (and colo from Pakistan),
never the geo-IP city.**

## A.4 Accuracy / trust summary

| Method | Accuracy | Trust | Coverage (our sites) |
|---|---|---|---|
| Geo-IP | city-level | high for unicast, **zero for CDN** | 100 % (40 CDNs wrong) |
| Reverse-DNS | provider-level hint | high **when present** | ~half have a useful PTR |
| RIPE IPmap | metro (measured) | high **where covered** | ~1 of 4 (web servers not covered) |
| Cloudflare colo | exact serving PoP | authoritative, **requester-relative** | CDN only |
| Latency (ours) | tens–hundreds of km near a probe | high for "local vs far" | 100 % of sites that answer ping |

## A.5 Next steps
1. **Scale the latency method to all sites** and **auto-correct CDN locations** (removes geo-IP's one
   failure). 2. **Run Cloudflare `colo` from the PK server** for CDN ground truth. 3. Add
   **reverse-DNS/provider** as a column. 4. **Fold corrected locations back** into the ratio pipeline.

---

# Appendix B — Latency Multilateration: Full Specification

The geo-IP-independent way we locate a server (and decide whether geo-IP is wrong). Every step, rule,
constant, and threshold, matching `geo.py` (`locate` / `relocate`).

## B.1 What it determines
Given a target and its RTTs from probes of **known location**: a **hard bound** ("within *R* km of
probe *X*"), a **point estimate** (when localizable), and a **ruling** on whether geo-IP is possible.
It never trusts geo-IP; only measured time and known probe positions.

## B.2 Physical principle
A signal cannot travel faster than light (~2/3 c in fibre). A round-trip ping time is a **hard ceiling
on distance**. Measured time → maximum distance. That is the entire basis.

## B.3 Constants
| Symbol | Value | Meaning |
|---|---|---|
| `c` | 299.792 km/ms | speed of light in vacuum |
| `n` | 1.468 | fibre refractive index |
| `v_fibre` | `c/n` ≈ **204.218 km/ms** | fibre signal speed (realistic bounds) |
| `R⊕` | 6371 km | Earth radius (Haversine) |
| `T_local` | **20 ms** | RTT threshold to accept a point estimate (Rule 5.5) |
| `ε` | 0.5 ms | divide-by-zero guard in the weighting (Rule 5.4) |

## B.4 Inputs — which vantages
- **Every probe that returned a ping RTT to this target** is a candidate. Probes with no reply
  contribute nothing.
- Each supplies its **coordinates** (RIPE, §0 roster) and its **`min_RTT`** (min-of-N).
- **Rule 4.0 — a vantage is only usable if its coordinate is trustworthy.** In this run this applies
  to `1016036` (placeholder `30.0, 70.0`): it cannot be re-located (fastest ping 22 ms ⇒ self-radius
  ~2,246 km) and is excluded — see §0.

## B.5 The algorithm, step by step
**Step 1 — one distance constraint per vantage.** `R_i = (t_i / 2) · v_fibre` km (Rule 5.1). Why
`t_i/2`: RTT is round-trip. Why min-of-N: minimum ≈ true propagation. Meaning: the server is inside a
**circle of radius `R_i` centred on vantage *i***.

**Step 2 — the binding bound = the nearest vantage.** `nearest = argmin RTT`; `Bound = R_nearest`
(Rule 5.2). The server is inside **every** circle, so inside the **smallest** one. We report this as
the location bound (e.g. "within 255 km of Islamabad"). Far probes only widen it.

**Step 3 — true location = intersection of all circles**, dominated by the nearest few; approximated
by the centroid in Step 4.

**Step 4 — RTT-weighted centroid point estimate.** `w_i = 1/(t_i + ε)²`;
`lat* = Σ w_i·lat_i / Σ w_i`, `lon*` similarly (Rule 5.4). `1/t²` makes near vantages dominate; `ε`
avoids infinite weight at ~0 ms.

**Step 5 — localize-vs-far rule.** If `RTT_nearest ≤ T_local (20 ms)`: report **LOCALIZED** (bound +
estimate); else **FAR** (bound only, do not pinpoint) — Rule 5.5. A point estimate is meaningful only
if some vantage is close; 20 ms ↔ ~2,043 km radius.

## B.6 The physics arbiter — is geo-IP WRONG?
```
for each vantage i:
    d_i     = Haversine(vantage_i, geoip_point)     # km to the geo-IP claim
    floor_i = 2 · d_i / v_fibre                      # ms, FIBRE round-trip minimum
    if t_i < floor_i:  geo-IP is IMPOSSIBLE          (Rule 6)
```
**Rule 6 — use *fibre* speed here, the same floor as B.5** (changed 2026-07-22 from an earlier
vacuum-based version, for consistency with the ratio in §3): if a ping beats even the realistic
fibre-speed time to the geo-IP spot, the claimed location is not credible given how real signals
travel — flagged as **impossible**. This is a *practical* impossibility check, not an absolute
physical one (an unusually direct real path could in principle beat the fibre estimate without
geo-IP being wrong) — the vacuum floor (`V_VAC`, still defined in `geo.py` but unused here) is
the strictly unbeatable bound if a harder proof is ever needed. On the panel data, switching from
vacuum to fibre adds 2 CDN sites to the flagged set (both geo-IP-registered to "Menifee, US" —
the same registration-artifact pattern as the other 34) and changes no unicast-site verdicts:
37/78 sites impossible under vacuum vs. **39/78 under fibre** (36 CDN + 3 Pakistan). Verdict: any
impossible vantage → **geo-IP wrong, latency wins**; else **consistent**. Record
`worst_impossible_gap = min_i(t_i − floor_i)`; negative = the proof.

## B.7 Worked example — `paknavy.gov.pk` (a CDN geo-IP put in "Toronto")

| Vantage | City | RTT | Circle radius `R_i` |
|---|---|--:|--:|
| Nayatel | Islamabad | **2.5 ms** | **255 km** ← binding |
| TES | Karachi | 3.1 ms | 317 km |
| Nayatel | Lahore | 3.2 ms | 327 km |
| … | … | … | … |
| PTCL | Karachi | 25.4 ms | 2,594 km |

Step 2: nearest = Nayatel/Islamabad → **within 255 km of Islamabad** (inside PK). Step 5: 2.5 ≤ 20 →
LOCALIZED. Step 6: geo-IP Toronto (vacuum floor ≥ 75 ms) but ping 2.5 ms → `2.5 − 75 < 0` →
**impossible** → geo-IP wrong by ~11,300 km; latency correct. *(Note: this site is a CDN, so per
Rule 8 the valid conclusions are exactly these two — the existence bound and the impossibility
proof; the RTT spread across probes (2.5→25 ms) is the per-PoP effect handled in §9, and the
centroid point estimate is not meaningful here.)*

## B.8 Anycast / CDN rule — the intersection premise FAILS
A CDN answers each probe from a **different** PoP (2.5 ms from Islamabad, 16–25 ms from
Lahore/Karachi — same IP). **Rule 8:** for anycast, Step 3's premise is false — the probes' circles
bound **different physical PoPs**, so intersecting them (and the Step-4 centroid) is **invalid**, not
merely unreported. Only two outputs remain valid for a CDN: (a) the **physics arbiter** (B.6) —
geo-IP impossibility is still a proof; (b) the **nearest-probe bound**, reinterpreted as *"at least
one serving PoP exists within `R_nearest` of `nearest.city`"* — an existence claim, not a location.
The correct full treatment for CDN sites is the **per-ISP near/far scoring of §9**, which reads each
probe's RTT as its own answer instead of forcing one point.

## B.9 Dependencies & failure modes
- **Anchored to probe coordinates** — a wrong coordinate on the *nearest* probe corrupts the bound
  (Rule 4.0); a wrong coordinate on a *far* probe is harmless.
- **Needs a nearby vantage to pinpoint** — distant servers can only be bounded as "far."
- **Round-trip only** — asymmetric routing is not separable from ping.
- **Requires a ping reply** — ICMP-blocked sites yield no constraint (use TCP-traceroute RTT later).

## B.10 Result of scaling to all sites (`geo.py relocate`)
Of 78 sites with both geo-IP and a ping, **geo-IP is flagged wrong for 39** (36 CDN + 3 PK, fibre
floor — see B.6), all actually **local**; the other 39 are **consistent** (geo-IP not ruled out
and agreeing with latency). The physics arbiter decides every case: geo-IP is either flagged
impossible (latency wins) or consistent (no conflict).
