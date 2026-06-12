# Experiment 1 — Where Are Pakistani Websites Actually Hosted? (Overview)

**Author:** Rayan Atif

This is the overview of the Experiment 1 family: the main hosting/routing study
(**01**) plus its two follow-ups, per-ISP DNS resolution (**1.1**) and CDN presence
in Pakistan (**1.2**). Detailed write-ups live in `findings/01*.md`.

---

## Objective

Determine where Pakistani websites are **physically hosted** and how Pakistani
users' traffic **reaches** them — i.e. how much "Pakistani" web traffic actually
stays in-country versus exiting to foreign infrastructure. The broader goal is to
assess how effectively Pakistan's Internet Exchange (**PKIX**) is used.

## Method and tools

- **Measurement:** ICMP Paris traceroutes via **RIPE Atlas**, run from **5 probes on
  5 Pakistani ISPs**: Z-Com, Nayatel, PTCL, Transworld (AS38193), and TPCPL/Nova
  (AS136174, which buys transit from Transworld). Measuring from multiple ISPs is
  deliberate — the same site is often routed differently per ISP.
- **IP → network (operator):** Team Cymru DNS (BGP origin ASN), with an **RDAP
  registry fallback** for hops whose prefixes are not announced in BGP. This exposes
  internal backbone hops and foreign IXPs that would otherwise show as "unknown".
- **Actual location:** ip-api geolocation. For **real servers** we geolocate the
  destination IP. For **anycast CDNs** (same IP announced from many cities) we
  geolocate the **handoff hop** — the last router before traffic enters the CDN —
  which reveals where each probe enters the CDN. RTT corroborates distance.
- **Output per run:** a hop-by-hop CSV, a per-measurement summary CSV (with the real
  serving location), and a human-readable route report.

---

## Experiment 01 — Hosting census (all 10 batches, 91 unique sites)

Categories: government, news, banking, e-commerce, education, telecom, health, real
estate, food, entertainment.

| Where it's hosted | Sites | Share |
|---|---:|---:|
| **Real server in Pakistan** | 23 | 25% |
| **Real server abroad** | 26 | 29% |
| **Anycast CDN** (almost all Cloudflare: 38) | 42 | 46% |

**~75% of Pakistan's top websites are not hosted on a Pakistani server.**

### What we observed

- **Government is the only sector that mostly stays in-country.** 13 of 18 gov sites
  are on real PK servers (NTC, Cybernet, PERN, COMSATS, PITB, PITC, FBR, Multinet) in
  Karachi, Islamabad, Lahore, Rawalpindi.
- **The consumer internet has largely left.** Most news sites are on Cloudflare; only
  `dunyanews.tv` is on a Pakistani network, and three (24News, Daily Pakistan,
  Nawa-i-Waqt) are on Hetzner in Finland. Banking and e-commerce are similar, with
  **UBL** the main bank that self-hosts in Pakistan (Karachi).
- **Pakistani companies often host abroad by choice.** Banks: Easypaisa → Singapore
  (AWS), Bank Alfalah → Dubai (Microsoft), SadaPay/HabibMetro/Faysal → US, HBL
  fronted from New Jersey (Imperva). Even PK telecoms host their own sites abroad
  (Wateen → Jakarta, Zong → Singapore), while PTCL, Nayatel, StormFiber, Nexlinx
  self-host in PK. The foreign footprint spans **10 countries** (US, Singapore,
  Canada, Finland, Ireland, UAE, Indonesia, India, Bahrain, Oman).
- **The transit hierarchy is stark — the most robust finding.** Downstream ISPs route
  essentially everything through the two licensed international-transit operators:
  **Z-Com ~100%** and **TPCPL ~100%** of paths pass through **PTCL or Transworld**.
  **Nayatel is the most independent** (largely direct peering). *Note on the number:*
  an ASN-only count understates Nayatel's transit use as **~6%** because Transworld's
  backbone is not announced in BGP; detecting the operator by **ASN + RDAP registry
  name** raises it to **~40% (37/91)**. Either way, Nayatel is far less
  transit-dependent than the other downstream ISPs.
- **Domestic routing quality is sharply ISP-dependent.** Nayatel reaches most
  destinations in single-digit ms (strong local peering); other ISPs are much higher,
  and every ISP sends a fifth to a third of traffic abroad. For the *same*
  Cloudflare-fronted site, Nayatel often reaches a local edge in 3–4 ms while PTCL can
  take hundreds of ms — identical content.
- **Hairpinning is concentrated, not pervasive.** Of the 23 PK-hosted sites, only
  five leave the country on their path (`pakistan.gov.pk`, `moitt.gov.pk`,
  `railways.gov.pk`, `pitc.com.pk`, `goto.com.pk`), and only for the downstream ISPs
  (Nayatel, TPCPL, Z-Com), never for PTCL or Transworld (which have domestic routes).
  The three government cases route through **Akamai Prolexic** DDoS-scrubbing in the
  US (~120–210 ms); `pitc` rides US Cogent.
- **Traffic exits to foreign IXPs.** Paths were observed transiting **Equinix
  Singapore, DE-CIX Frankfurt, and EMIX UAE** — direct evidence that **PKIX is
  underused**, the central problem this research investigates.

### Caveat — CDN "local" delivery

A traceroute reaching a local Cloudflare node does **not** prove the page is served
locally. For `shaukatkhanum.org.pk` the trace reached a local node at ~4 ms, but
Cloudflare's own diagnostic reported the request was actually served from
**Singapore**. "Reaches the CDN locally" ≠ "served locally".

### Headline

Of 91 sites, **23 (~a quarter) are confidently hosted on real servers inside
Pakistan** — almost all government, plus UBL and Dunya News. The consumer internet
(news, banking, e-commerce) is **~three-quarters offshore**, mostly Cloudflare and
foreign clouds. Domestic routing is heavily **ISP-dependent**: smaller ISPs send
essentially all traffic through the two big transit providers, a handful of PK-hosted
sites still leave the country, and Nayatel's independent peering delivers far better
local performance. Together this is direct evidence that **local exchange through
PKIX is not happening uniformly**.

### Pakistani-hosted sites (23)

| # | Website | Category | Hosted on | ASN | City | Note |
|---|---|---|---|---|---|---|
| 1 | ubldigital.com | banking | UBL-PK | AS56126 | Karachi | |
| 2 | goto.com.pk | ecommerce | TELECARD-AS-AP | AS55340 | Karachi | |
| 3 | lums.edu.pk | education | PKTELECOM-AS-PK | AS17557 | Lahore | |
| 4 | pu.edu.pk | education | HECPERN-AS-PK | AS45773 | Lahore | |
| 5 | pucit.edu.pk | education | LDN-AS-PK | AS23966 | Islamabad | |
| 6 | fbr.gov.pk | government | FBR-AS-AP | AS138424 | Islamabad | |
| 7 | hec.gov.pk | government | HECPERN-AS-PK | AS45773 | Lahore | |
| 8 | kp.gov.pk | government | NTC-AS-AP | AS23888 | Rawalpindi | |
| 9 | moitt.gov.pk | government | CYBERNET-AP | AS9541 | Karachi | routes via US Akamai Prolexic (DDoS scrubbing) before the PK origin |
| 10 | pakistan.gov.pk | government | CYBERNET-AP | AS9541 | Karachi | routes via US Akamai Prolexic (DDoS scrubbing) before the PK origin |
| 11 | pbs.gov.pk | government | NTC-AS-AP | AS23888 | Islamabad | |
| 12 | pid.gov.pk | government | COMSATS | AS7590 | Islamabad | |
| 13 | pitc.com.pk | government | PITC1-AS-AP | AS153561 | Lahore | |
| 14 | pseb.org.pk | government | MULTINET-AS-AP | AS9260 | Karachi | |
| 15 | pta.gov.pk | government | NTC-AS-AP | AS23888 | Rawalpindi | |
| 16 | punjab.gov.pk | government | PITB-PUNJAB-PK | AS59323 | Lahore | |
| 17 | railways.gov.pk | government | CYBERNET-AP | AS9541 | Karachi | routes via US Akamai Prolexic (DDoS scrubbing) before the PK origin |
| 18 | sindh.gov.pk | government | NTC-AS-AP | AS23888 | Rawalpindi | |
| 19 | dunyanews.tv | news | MULTINET-AS-AP | AS9260 | Islamabad | |
| 20 | nayatel.com | telecom | NAYATEL-PK | AS23674 | Islamabad | |
| 21 | nexlinx.net.pk | telecom | NEXLINX-AS-AP | AS17563 | Lahore | |
| 22 | ptcl.com.pk | telecom | PKTELECOM-AS-PK | AS17557 | Islamabad | |
| 23 | stormfiber.com | telecom | CYBERNET-AP | AS9541 | Karachi | |

---

## Experiment 1.1 — Per-ISP DNS resolution

Resolving each site from **every ISP's own resolver** showed only **8 of 103 sites**
return different IPs per ISP (GeoDNS). So the central DNS lookup used in Experiment 01
was **representative for ~92%** of sites — the hosting census isn't distorted by
per-ISP DNS answers for the large majority.

→ detail: `findings/01.1_dns_resolution_analysis.md`

## Experiment 1.2 — CDN presence in Pakistan

Pinging major content services per ISP found that **most big content (Google, Meta,
Apple, Microsoft) is reached at regional latency (~20–50 ms), not from inside
Pakistan**, from our three online probes. Only **Cloudflare and X** were served
locally — and only via **Nayatel**. The ISPs reported to host embedded caches (PTCL,
Optix, StormFiber, Telenor) are **not yet among our probes**, so this *undercounts*
local CDN presence — which is exactly what motivates the **Experiment 02** probe
deployment.

→ detail: `findings/01.2_cdn_presence_analysis.md`

## Experiment 1.3 — Nayatel routing (what it transits)

A deep-dive on the Nayatel probe's 91 paths, with transit detected by **ASN + RDAP**
(Transworld's backbone is unannounced, so the registry label is used). This resolves
the "~6% vs ~40%" point above.

| Path type | destinations | share |
|---|---:|---:|
| **Transworld (LDI)** | 35 | 38% |
| **PTCL (LDI)** | 2 | 2% |
| **No LDI** | 54 | 59% |

So **~40% of Nayatel paths use an LDI** (almost all Transworld) and **~59% avoid the
LDIs entirely**. The "no-LDI" paths break down as: **direct Cloudflare peering (~38,
~3 ms)**, **direct Microsoft peering (3** — aku.edu, bankalfalah, hum.tv**)**, **direct
domestic PK peering (~7** — Multinet/dunyanews, PERN/hec/pu, PITB/punjab,
COMSATS+Multinet via HTISPL**)**, and **its own international transit that bypasses
Transworld (**daraz via SingTel→Alibaba; mcb/iba via NTT→Sucuri**)**, plus a few other
direct foreign (AWS, OVH, Cloudflare Spectrum).

**Key takeaway:** Nayatel is not just a Transworld transit customer — it is
effectively **multi-homed**, peering directly with the big content networks
(Cloudflare, Microsoft, AWS) and using alternative transit (SingTel, NTT) that
bypasses Transworld. It only falls back to **Transworld for the long tail of foreign
hosts it doesn't peer with** (Hetzner, Oracle, Akamai, Incapsula, generic clouds) and
a few PK ISPs it lacks domestic peering with. That's why everyday sites are ~3 ms yet
~40% of paths still show Transworld — **the 40% is essentially the foreign-hosted
tail**, not a lack of independence.

→ detail: `findings/01.3_nayatel_routes.md`

---

## How this connects to the rest of the project

- **Exp 02 (probe deployment):** 1.2 undercounts local caches because we lack probes
  on the cache-hosting ISPs — Exp 02 plans the 20-probe PKIX-set deployment to fix the
  coverage gap.
- **Exp 03 (longitudinal routing):** Exp 01 is a one-off *snapshot*; Exp 03 adds the
  **time axis** — re-tracing the same sites every 15 min from multiple ISPs to see
  whether paths/RTT change over the day (and now measuring each probe's egress ASN
  live, for multi-homed campus probes).

**Related write-ups:** `findings/01_hosting_and_routing_analysis.md`,
`findings/01.1_dns_resolution_analysis.md`, `findings/01.2_cdn_presence_analysis.md`,
`findings/01.3_nayatel_routes.md`.
