# Exp 07 — EDA exploration log (routing map build + route deep-dives)

Session notes from building the geographic routing map (`routing_map.py` +
`annotate_hops.py`) and digging through `results/a/routes_20260718_195946.txt`
(the latest-trace-per-pair snapshot) for outliers. These are exploration
findings, not yet folded into the paper's headline numbers — flagged here so
they don't get lost, with enough evidence to act on each one.

---

## 1. Probe 1016393 (PTCL-Mianwali) may have inflated trombone numbers

**Finding:** in the snapshot file, `ptcl.1016393` is TROMBONE on **89/100**
traces vs. `ptcl.1016126` (PTCL-Karachi) at **57/100** — same ISP, a 32-point
gap. Some of that could be real (a genuinely worse-connected PoP — itself a
finding for RQ2). But the RTT evidence behind it looks partly like noise:

- Median TROMBONE `maxRTT` for 1016393 is **458.8ms**.
- **16 of its traces sit in a suspiciously tight 490–500ms band**
  (490.7, 491.2, 492.1, 492.7, 493.7, 494.1, 494.4, 495.5, 496.9, 497.5,
  498.0, 498.5, 498.9, 499.5, 499.8 — a near-linear progression right up
  against a ceiling).
- METHODOLOGY.md already treats RTT >~500ms as an ICMP-generation-delay/queuing
  artifact, not real geography. This probe's values creeping right up to
  that line, repeatedly, looks like the same failure mode without quite
  crossing the documented threshold.


---

## 2. Geo-IP lies on intermediate hops too, not just target sites (Sydney → Muscat)

The routing map (built from `ip-api.com` geolocation per hop) initially
showed traceroute paths reaching into Australia. Investigated and fixed —
worth recording the method since it's reusable.

**The claim:** IP `206.148.27.235` (a hop on the PTCL → `efulife.com`
trombone path, owned by GSL Networks / Cogent-leased space) geolocates via
`ip-api.com` to **Sydney, Australia** (`-33.9182, 151.189`).

**Why it wasn't immediately obviously wrong:** the recorded hop RTT (110.8ms)
doesn't clear the physics-arbiter's vacuum-floor test outright — Karachi to
claimed-Sydney is ~11,000km, vacuum round-trip floor ≈73.5ms, so 110.8ms
isn't *provably* impossible the way a Toronto/Mountain-View-style case is.

**What settled it (originally):**
1. **A sibling IP contradicts it.** The same GSL entity's `160.202.164.165`
   geolocates to **Los Angeles** in the same database — one company, two
   wildly different ip-api answers. Consistent with both being an HQ/
   registration-address default rather than the router's real location.
2. **Reverse DNS is authoritative here, but only for the exact IP checked.**
   `dig -x` on `206.148.27.1` and `.2`, two *other* addresses in the same
   `/24`, returns hostnames like `po3.mct-eqxmc1-cr2.globalsecurelayer.com` —
   `mct` = Muscat's IATA code, `eqxmc1` = Equinix Muscat facility 1. A real,
   first-party signal, stronger than any third-party geo-IP database — but a
   confirmation of `.1`/`.2`, not of `206.148.27.235`, the IP that actually
   shows up in this trace.

**Correction, 2026-09-01:** this section originally said `dig -x` on
`206.148.27.235` itself returned the `mct-eqxmc1` hostname and concluded "the
hop is in Muscat, Oman, not Sydney." That was wrong on the specific IP: `.235`
resolves to the generic `peering-edge.globalsecurelayer.com`, no city code,
nothing to disprove Sydney with directly. Re-checked by reverse-DNSing `.235`'s
*actual* neighbors (`.225`-`.239`) instead of `.1`/`.2`: they resolve to
Ashburn, Adelaide, Seattle, and Phoenix, four cities on two continents inside
one `/24`. GSL numbers router interfaces out of shared global pools, not per
physical site, so a `/24` carries no location information for this operator —
`.1`/`.2` being in Muscat says nothing about where `.235` is.

**Revised verdict: `.235` is abroad (not Sydney — that was already established
independently via the sibling-IP contradiction above, and the RTT jump to get
there also rules out Pakistan), but its specific city is unconfirmed.** Not
Muscat, not provably anywhere else either. `206.148.22.141`, a different IP on
the same path, is unaffected by this correction: it decodes to `sg-eqxsg3` =
Equinix Singapore directly on its own hostname (ip-api had called it "New
York"), re-checked live on 2026-09-01 and unchanged.

**Reusable takeaway (revised):** ip-api geolocation on backbone/carrier hops is
often just the company's registration city, and the physics floor alone won't
always disprove it (unlike a consumer/CDN edge IP case). `dig -x <ip>` is the
stronger tool for carrier infrastructure, real airport/facility codes (`mct`,
`sg`, `lax`, etc.) do show up — **but only trust it for the exact IP you dig,
never extend a hit to that IP's neighbors or its whole `/24` without checking
each one individually.** A block can, and here does, span multiple cities and
continents under one operator. See
`edits/2026-09-01_eda_docs_gsl_muscat_correction.md`.

**Second correction, same date, same hop family:** bullet 1 above quotes
`160.202.164.165` geolocating to "Los Angeles" per ip-api, used only to show
ip-api contradicts itself, never claimed as verified, and it wasn't — no PTR
check was ever run on this IP or its neighbors. Run now: `.165` itself has the
generic `unknown.globalsecurelayer.com` hostname, and its real neighbors
(`.158` Brisbane, `.160` Sydney, `.162` Muscat, `.164` Singapore, `.166`
Dallas, `.168` Frankfurt, `.170`/`.172` Phoenix) span six countries in a
12-address span. RDAP confirms `160.202.164.0/24` is one registered block
("KEYSTONE"), not a single site, same story as `206.148.27.0/24`. **`.165` is
abroad, exact city unconfirmed** ("Los Angeles" was never established and
shouldn't be repeated as if it were).

---

## 3. `efulife.com` may be misclassified as "offshore"

`findings/07_critical_review_and_eda_plan.md` and `findings/07_longitudinal_panel.md`
both currently list `efulife.com` as one of the sites the physics arbiter
reclassified from "Pakistan" to "actually offshore." Two checks done here
contradict that:

1. **Registration:** the destination IP (`103.154.196.33`) is RIPEstat-
   registered to `ELAL-PK` / EFU Life Assurance Ltd — a real Pakistani
   insurance company, not a foreign host.
2. **RTT, whole week, three independent probes** (`results/b/panel_*.csv`,
   ping panel, `rtt_min`):

   | Probe | min RTT, whole week |
   |---|--:|
   | cybernet.1016154 | **4.7ms** |
   | cybernet.1016143 | **5.0ms** |
   | cybernet.1016036 | **23.2ms** |
   | everyone else | 78–430ms |

   A 4.7ms RTT is not compatible with an offshore server — this isn't a
   one-off snapshot fluke, it holds across the entire panel week.

**Why it matters if true:** a confirmed-domestic site that 10+ of 16 probes
still hairpin internationally to reach is a *stronger* example for the
thesis than an offshore one — it's exactly the "unnecessary tromboning to a
PK-hosted destination" story, not a sample-contamination issue to explain
away.

---

## 4. Route deep-dives — genuine multi-country hairpins to PK-hosted sites

Scanned all `[Pakistan]`-class TROMBONE traces for ones crossing ≥2 distinct
foreign countries: **60 traces qualify** (out of 640 Pakistan-class traces in
the snapshot). Full hop-by-hop deep-dive done on three:

### `efulife.com` 
```
PTCL edge → PTCL internal
→ GSL Networks/Global Secure Layer (abroad, exact site unconfirmed -- see §2 correction)
→ Zain-Omantel, Muscat, Oman (confirmed via RIPEstat + PTR)
→ Cybernet (PK) → EFU Life's own PK-registered block
```

### `fgeha.gov.pk` + `ztbl.com.pk` (Federal Govt Housing Authority; a state bank)
Consistent across **7–8 different probes/ISPs**, not a one-off:
```
PTCL → Equinix Singapore (27.111.228.x)
→ Akamai Prolexic DDoS scrubbing (2.21.120.x, 72.52.25.142)
→ NTC — Pakistan's own state telecom (175.107.33.22)
→ Cybernet (PK), final host
```
Both destination IPs (`203.101.184.78`, `.80`) sit in the **same /24** as
`moitt.gov.pk`/`railways.gov.pk`, the Prolexic hairpin already documented in
METHODOLOGY.md — this extends that pattern to at least 2 more government/state
sites, confirmed structural (not a single-probe artifact) since it repeats
across most of the panel.

### `networld.pk` (hosted by Fariya Networks, a real PK ISP) — widest geographic swing found
```
PTCL → NTT Singapore
→ Telecom Italia Sparkle, Marseille POP (France)
→ Telecom Italia Sparkle, Italy
→ Transworld backbone → Cogent's in-PK PoP (149.40.227.129, per findings/04)
→ Fariya Networks (PK), final host
```
Pakistan → Singapore → France → Italy → back to Pakistan, to reach a
Pakistan-hosted site.

### Also noted, lower priority
- **`pgf.com.pk`** — `[Abroad]`-class (correctly identified as foreign),
  18-hop path via Transworld → Cologne, Germany → IBM Cloud/SoftLayer
  (`169.45.x`, `169.60.x`, `169.48.x`) at ~280ms. Not a misclassification
  case, just a long real path to a real foreign host.
- **Telecom Italia Sparkle (Seabone) recurs** as an intermediate carrier
  across multiple *different* destination sites (`networld.pk`, `enic.pk`,
  `gbappsup.org.pk`) — a repeated IP (`195.22.192.139`, Seabone's internal
  network) shows up twice within some single traces too, which looked like a
  routing loop but is actually a common MPLS traceroute artifact (an
  internal router replying at two apparent hop-distances), not a real loop.

---

## 5. Tooling changes made along the way

- **`annotate_hops.py`** (new): parses hop IPs from a routes file, resolves
  ASN/name via Team Cymru, geolocates via ip-api.com, caches to
  `hop_geo_cache.json`, writes `hop_geo.csv`.
- **`routing_map.py`** (pre-existing, fixed):
  - Private-IP filter was over-broad (blanket `172.x`/`100.x`) — narrowed to
    real RFC1918/CGNAT ranges via `ipaddress`, so real public IPs (e.g.
    Cloudflare's `172.69.x`) aren't silently excluded.
  - Verdict parser defaulted every path to `'local'` and only ever checked
    for `'TROMBONE'` — so the 28 genuinely `INCONCLUSIVE` traces in this
    snapshot were silently drawn as confirmed-green. Fixed to recognize all
    three verdicts explicitly and skip plotting anything not confirmed
    local/trombone.
  - Added the physics-arbiter + `KNOWN_LOCATIONS` override described in §2.
