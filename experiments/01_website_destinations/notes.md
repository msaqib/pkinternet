# Experiment 01 — Website Destinations

**Author:** Rayan Atif

## Objective

Find out **where Pakistani websites actually live and how Pakistani users' traffic
reaches them**. For each target we run traceroutes from inside several Pakistani
ISPs and record, per probe:

1. the full hop-by-hop path (IP, ASN, operator, RTT),
2. the destination IP / ASN / hosting provider, and
3. the **actual physical serving location** of the destination — not the ASN's
   registration country, which is misleading for anycast CDNs.

The central research question: how much "Pakistani" web traffic stays in Pakistan
vs exits to foreign infrastructure, and where it goes when it leaves. PKIX
(Pakistan Internet Exchange) is largely unused, so traffic between Pakistani
networks often exits to a foreign IXP and returns — this experiment quantifies
that.

## Probes used

Five RIPE Atlas probes, one per major Pakistani access network:

| Probe ID | ASN    | Operator                    |
|----------|--------|-----------------------------|
| 1015679  | 136174 | Transworld (LocalInternetProj) |
| 1015210  | 17557  | PTCL                        |
| 62224    | 38193  | Transworld (Zartash-Office) |
| 60223    | 23674  | Nayatel                     |
| 7613     | 152605 | Z-Com Networks              |

Measuring from multiple ISPs is the point: the same destination is often reached
**differently per ISP**, which is where the routing-inefficiency findings come
from.

## Target list

Pakistani websites across categories (`data/pk_websites_list.csv`): government,
news, banking, ecommerce, telecom, education, real estate, health, food,
entertainment. Run in batches; each batch is one `run_*` folder.

---

## Pipeline & tools (what we use and why)

The flow is: **traceroute → resolve each IP to an operator → geolocate the real
serving point → render human-readable output.**

| Tool / source | Where | What it does | Why it's used |
|---------------|-------|--------------|---------------|
| **RIPE Atlas** ICMP Paris traceroute | `pk_multi_probe.py` | Runs the measurements from the 5 PK probes | Real per-ISP routing seen from *inside* Pakistan — the only way to see ISP-specific paths and RTTs |
| **Team Cymru** DNS (`origin.asn.cymru.com`) | `asn_for_ip()` | Maps each hop/destination IP → origin ASN + country from the **global BGP table** | Free, fast, no API key; the standard IP→ASN source |
| **RDAP** via `rdap.org` → correct RIR | `registry_lookup()` (`geo_utils` uses same idea) | Fallback when Cymru returns nothing | Many internal backbone/IXP hops are in **unannounced prefixes** (not in BGP), so Cymru can't see them; RDAP's *allocation* record still names the operator. This is what surfaced the foreign IXP hops (Equinix-SG, DE-CIX-FRA, EMIX-UAE) |
| **ip-api.com** IP geolocation | `geo_utils.geolocate()` | IP → city, region, country | Gives the **actual physical location** of a server or a handoff router (cached on disk in `.geo_cache.json`) |
| **Cloudflare `/cdn-cgi/trace`** | manual `curl` spot check | Reads `colo=` = exact serving datacenter (IATA) | Ground-truth serving PoP — but only from the machine running it, so it can't represent the probes. Not part of the pipeline; useful only as an occasional single-vantage sanity check |

### Why serving location needs special handling (anycast)

`target_country` from the ASN is wrong for CDNs. Cloudflare (AS13335) is
**anycast**: the same IP is announced from 300+ cities and you reach the nearest
one. Cymru/RDAP report "US" only because that's where the AS is registered.

- **RIPE Atlas probes cannot run HTTP**, so we can't read Cloudflare's `colo`
  from a probe.
- Instead we infer the serving metro from the traceroute: the **handoff hop** —
  the last real router *before* traffic enters the CDN's ASN — is a normal
  unicast peering router that geolocates reliably and marks the city where that
  probe hands off to the CDN. RTT corroborates the distance.
- For **unicast** destinations (real single servers) we just geolocate the
  destination IP; that location is the same regardless of vantage.

This logic lives in `geo_utils.serving_location()` and is shared by the live run,
the summaries, and the route reports so they all agree.

### Scripts

Only three, all required by a normal run:

| Script | Role |
|--------|------|
| `pk_multi_probe.py` | Main run: schedules traceroutes, resolves ASNs (Cymru + RDAP fallback), computes serving location, writes grouped + summary CSVs, and auto-generates the readable routes file (step `[6b]`) |
| `geo_utils.py` | Shared geolocation + anycast handoff logic + on-disk cache (imported by the other two) |
| `format_routes.py` | Renders a grouped CSV into `routes_*.txt` (one readable block per trace). Called automatically at `[6b]`; can also be run standalone to rebuild route files |

Enrichment (RDAP) and serving-location now happen **live during the run**, so a
single `pk_multi_probe.py` invocation produces fully enriched, located grouped +
summary + routes output. (Earlier one-off backfill scripts have been removed.)

---

## Output files per run

`experiments/01_website_destinations/results/{RUN_NAME}/`:

| File | Contents |
|------|----------|
| `pk_grouped_TIMESTAMP.csv` | One row per hop (path detail), with hop ASN/operator/country |
| `pk_summary_TIMESTAMP.csv` | One row per measurement; includes **`dest_location`** (actual serving city) and **`location_via`** (`handoff <ip>` / `server IP` / blank) |
| `routes_TIMESTAMP.txt` | Human-readable: one block per trace with `SOURCE` / `DEST` / location header (**`SERVED`** for real servers, **`ENTERS`** for anycast CDNs), then the hop-by-hop route |

Cross-run reference files (in the experiment folder): `batch_inventory.md`
(every measurement: batch, site, probe, reached, destination) and `website_list.md`
(the 91 unique sites with hosting verdict). Analysis lives in `findings/01_*`.

### Reading a route block

```
 SOURCE   probe 7613 · Z-Com (AS152605) · Pakistan
 DEST     172.67.190.163 · Cloudflare (AS13335) · US · reached, host replied
 ENTERS   Singapore, SG   (Cloudflare network — this probe's handoff 27.111.228.132; not necessarily where HTTP is served)
   ... hops ...
```

The location line is **`SERVED`** for real (unicast) servers — that genuinely is
where the site is served — and **`ENTERS`** for anycast CDNs, which marks where
the probe enters the CDN's network (the handoff), *not* a confirmed serving
location (see the ICMP-vs-HTTP caveat below).

`[registry]` on a hop = operator came from RDAP, not BGP (so the ASN column is
`—` by design).

---

## Findings so far (batches 2–5: government + news, 36 unique sites)

**Hosting split**
- Most **government** sites are genuinely in Pakistan (NTC, PTCL, Cybernet, PITC,
  COMSATS, PITB, FBR, PERN, Multinet) — served from Karachi / Islamabad / Lahore /
  Rawalpindi.
- Most **news** sites are on **Cloudflare** (anycast). Exceptions hosted abroad on
  real servers: **24newshd.tv, dailypakistan.com.pk, nawaiwaqt.com.pk → Hetzner,
  Helsinki (Finland)**. Only **dunyanews.tv** is on a Pakistani network (Multinet).

**Cloudflare is served from different cities depending on the ISP**
- Nayatel → **Islamabad** PoP (~3 ms)
- Z-Com / Transworld → **Karachi** PoP (~18 ms)
- but **bisp.gov.pk** and **express.com.pk** get pushed to **Singapore** (~97 ms)
  on Z-Com/Transworld — a concrete per-ISP routing inefficiency, visible via the
  Equinix-Singapore handoff hop.

**Other CDNs / clouds sit fully abroad (consistent across probes)**
- **nadra.gov.pk** (Akamai) → **Turkey** (~175 ms)
- **hbl.com** (a bank, Incapsula) → **New Jersey, US** (~200 ms)
- **mcb.com.pk** (Sucuri) → splits by ISP: **Singapore / London / Frankfurt**
- **such.tv** → AWS **Montreal**; **balochistan.gov.pk** → Oracle **Ashburn, US**

**DDoS-scrubbing detour**
- `pakistan.gov.pk`, `moitt.gov.pk`, `railways.gov.pk` resolve to a Pakistani ASN
  (Cybernet) but route through **Akamai Prolexic (AS32787) in the US**, never
  reply to the trace, and show 120–210 ms — effectively leaving and returning.

**Foreign IXPs in the path** (previously `(unknown)`, now labelled via RDAP):
Equinix Singapore, DE-CIX Frankfurt, EMIX UAE — evidence of PK traffic exiting to
foreign exchanges rather than staying on PKIX.

**Robust path-based findings (full dataset, batches 2–11, RTT-independent).**
These are the firmest results and don't depend on noisy RTT:
- **Transit dependency:** downstream ISPs route ~**100%** of paths through an LDI
  operator (PTCL AS17557 or Transworld AS38193) — Z-Com 91/91, TPCPL 65/65 — while
  **Nayatel is ~6%** (mostly independent peering). Confirms the transit hierarchy.
- **Hairpinning is concentrated, not pervasive:** of 23 PK-hosted sites, only **5**
  are reached via a foreign hop (pakistan.gov.pk, moitt.gov.pk, railways.gov.pk,
  pitc.com.pk, goto.com.pk), and only by the downstream ISPs (Nayatel, TPCPL,
  Z-Com) — **never PTCL/Transworld**, which have domestic routes. Shaw artifact
  excluded.

---

## Known artifacts & caveats

- **Shaw/Canada artifact:** the Transworld probes always show an early hop
  `70.70.209.16` (AS6327 Shaw, Canada) at ~1.7 ms. It is physically in Pakistan;
  exclude from country-of-hosting analysis.
- **Anycast = vantage-dependent.** A Cloudflare `dest_location` is where *that
  probe* hands off, not a single global truth. A PK handoff city (Karachi/
  Islamabad) means "served from within Pakistan"; the exact PK city is
  approximate (it's an ISP router, not the PoP). Foreign metros (Singapore,
  Frankfurt, Turkey, NJ) sit at the actual peering point and are accurate.
- **Filtered probes:** the **PTCL (AS17557)** and one **Transworld (AS38193)**
  probe drop traceroute probes, so many traces have no visible handoff
  (`dest_location` blank, `location_via` blank). RTT still corroborates
  (e.g. ~24 ms ≈ in-country, ~100 ms ≈ Singapore).
- **RTT is single-packet, and the responding-destination set differs per probe.**
  Stored `rtt_ms` is the first reply per hop, not min-of-N, so it carries jitter;
  and per-ISP "average RTT" compares different destinations (a probe's fastest
  sites, e.g. DDoS-scrubbed gov, often don't reply and drop out). Quote **medians**
  and prefer the **path-based** findings; treat absolute RTT as indicative.
- **Registry geolocation (non-Cloudflare CDNs)** is best-effort: Akamai/Incapsula/
  Sucuri don't expose a `colo`, so their city comes from IP geolocation of the
  registered block, not a guaranteed serving point.
- **ICMP path ≠ HTTP serving location (important anycast caveat).** A traceroute
  can terminate at a *local* Cloudflare node at very low RTT while the actual
  HTTPS request for that zone is served from a distant PoP. Real example:
  `shaukatkhanum.org.pk` traced to a Cloudflare IP at ~4 ms from a Lahore vantage
  (looks local), but `/cdn-cgi/trace` returned `colo=SIN` — HTTP was actually
  served from **Singapore**. This happens for free/basic-plan zones and ISPs
  without full local Cloudflare HTTP peering: the nearest edge answers pings but
  content comes from a regional PoP. Because RIPE Atlas probes can't run HTTP, the
  probe-side handoff/RTT method can therefore report "reaches Cloudflare locally"
  when the site is really served abroad. The honest probe-side claim is
  *"reaches the CDN's network locally"*, not *"the site is served locally."*
  Reliability ranking for serving location: **`colo` (HTTP truth) > traceroute
  handoff+RTT > IP geolocation of an anycast IP (worst)**.
- **RTT guide (from PK):** < 50 ms → likely stayed in Pakistan; > 100 ms → almost
  certainly exited.

## Measurement IDs

(per-run measurement IDs are in each `pk_summary_*.csv`)
