# Experiment 1.4 — Hosting census of 100 Pakistani websites (PK100)

**Author:** Rayan Atif

## Objective

For the 100 Pakistani websites in `data/PK100sites.md` (government, education,
utilities, telecom, banking, …), determine **where each is hosted**, classified as:

- **CDN** — anycast content network (Cloudflare, Akamai, Fastly, …); name the CDN.
- **Pakistan** — a real server inside PK; name the **hosting ISP** (the ASN, e.g. PTCL,
  NTC, PERN, Cybernet, Multinet, COMSATS).
- **Abroad** — a real server outside PK; name the **country** (and operator, e.g.
  Hetzner–DE, AWS–US, OVH–FR).

Same method as Experiment 01 (`pk_multi_probe.py` hosting/serving-location logic),
applied to this gov/edu-heavy list.

## Vantage points

- **Pass A — hosting identity (which network / which country).** Domains resolved via
  the project machine's DNS (a Pakistani vantage), then each IP mapped to its **ASN**
  (Team Cymru + RDAP fallback) and **geolocation** (ip-api). This identifies the
  *owning network and country of the server IP*, which is a property of the IP and is
  essentially vantage-independent — so Pass A is the authoritative "who hosts it /
  which country" pass. Script: `pass_a_hosting.py`.
- **Pass B — serving location & latency from a real PK user.** ICMP Paris traceroute
  from **RIPE Atlas probe 64078** — **Transworld / TES-PL (AS135407), Rawalpindi**
  (LocalProject / hardware probe "Atif Jalil, Home"). This is the *"from my vantage
  point"* measurement: destination RTT and, for anycast CDNs, the **handoff PoP** the
  packet enters as experienced **from Transworld's network**. Script: `pass_b_probe.py`.

**Why two passes:** Pass A says *what network/country the IP belongs to*; Pass B says
*how far it is and which CDN PoP serves it from this vantage*. For anycast CDNs the
ASN's registered country lies (Cloudflare reads "US" even when served from Karachi),
so the RTT/handoff from Pass B is what tells the real serving location.

## Caveat (from Exp 01)

A low ICMP RTT proves the **network edge** is local, **not** that the HTTP page is
served locally (e.g. `shaukatkhanum.org.pk` traced ~4 ms but served from Singapore per
`/cdn-cgi/trace`). So "CDN served locally" is only confirmed by an HTTP check
(`/cdn-cgi/trace` for Cloudflare) — RIPE probes can't run HTTP; a laptop can.

## Results

### Pass A — hosting identity  *(done 2026-07-01)*

Resolved from the project machine (PK vantage); IP→ASN via Cymru, geo via ip-api.
Full table: `results/pass_a_hosting.csv`.

**Hosting split (100 sites):**

| Category | Count |
|---|---|
| **Pakistan** (real PK server) | **99 (99%)** |
| **CDN** (Cloudflare) | 1 (1%) |
| **Abroad** | 0 |

**Headline:** unlike Exp 01's commercial/news/banking list (~75% offshore/CDN), this
**government + education + utility** list is **almost entirely hosted inside Pakistan**
— the state and public sector self-host domestically.

**Top PK hosting ISPs (by # of sites):** Cybernet ~28 (incl. the `203.101.184.x`
gov/PITC block), COMSATS 12, PITB 9, PITC 7, Nayatel 6, PTCL 6, LinkDotNet 5,
Multinet 5, Nexlinx 4, Wateen 3, FBR (own ASN) 2, Gemnet 2, plus PERN, NTC, CMPak,
Telecard, LinkdotNet, UBL, Gourmet, Iqra-University, etc.

**Caveats:** CDN detection is ASN-based (Cloudflare/Akamai/Fastly/AWS/Google/…); the
low CDN count reflects that these sites mostly serve from their own PK infrastructure
rather than fronting a CDN. Pass B (traceroute RTT from a real probe) will confirm the
"genuinely local" claim and catch any anycast nuance.

**Sites grouped by host (ASN):**

- **Cybernet (28)** — `CYBERNET-AP` (25): agp, agpr, aviation, cga, cii, ead, mocc,
  mofept, moitt, nab, ncsw, nhmp, nhsrc, nitb, ntc.net, paec, pakistan.gov, pcsir,
  pemra, petroleum, pims, pmo, pts, stormfiber, ztbl; `CYBERNET-APII` (3): alfalahamc,
  parco, silkbank. *(The `203.101.184.x` block hosts many federal gov sites.)*
- **COMSATS (12)** — comsats.net, eobi, fc, iesco, kiu.edu, nu.edu, ogdcl, pid, pmc.edu,
  rmc.edu, sacgb, uaf.edu.
- **PITB — Punjab IT Board (9)** — irrigation.punjab, lhc, livestock.punjab, pap,
  pcsw.punjab, pdma, pitb, punjab.gov, pvtc. *(Punjab government sites.)*
- **PITC — Power IT Company (7)** — fesco, gepco, mepco, pitc, qesco, sepco, wapda.
  *(The power-sector DISCOs.)*
- **PTCL (6)** — ecp, ndma, ntdc, ppra, ptcl.com, ufone.
- **Nayatel (6)** — fauji, nacp, nayatel.com, ppaf, pra.gop, psl.
- **LinkDotNet (5)** — aust.edu, hitecuni.edu, jinnah.edu, pucit.edu, yansrhr.
- **Multinet (5)** — `MULTINET-AS` (4): dunyanews.tv, pseb, tevta, ubank;
  `MULTINET-IE` (1): crcp.
- **Nexlinx (4)** — lesco, nexlinx.net, phc, prsp.
- **Wateen (3)** — digiskills, maju.edu, sngpl.
- **FBR (own ASN) (2)** — fbr, pral.  ·  **Gemnet (2)** — bisehyd.edu, isra.edu.
- **Transworld (2)** — adamjeeinsurance, dunya.com.
- **Singletons:** PERN/HEC → hec.gov · NTC → pbs · CMPak → zong · UBL → ubldigital ·
  Telecard → goto · Gourmet Foods → gnnhd.tv · Iqra University → iqra.edu ·
  Broadband/BBI → irrigation.sindh · **Cloudflare (CDN)** → secp.gov.

**Read of this:** hosting is concentrated in a handful of providers — **Cybernet
(federal gov), PITB (Punjab gov), PITC (power sector), COMSATS, PTCL, Nayatel** carry
the bulk. That concentration matters for the PKIX story: reaching these ~6 networks
well covers most public-sector traffic.

### Pass B — RTT / serving PoP from Transworld (probe 64078)  *(done 2026-07-01)*

ICMP Paris traceroute to all 100 sites from probe 64078 (Transworld/TES-PL, Rawalpindi).
Full data: `results/pass_b_probe.csv`; readable traceroutes: `results/routes_pass_b_*.txt`.

**Reachability (did the destination itself answer the ICMP probe):**

| Outcome | Sites |
|---|---|
| destination replied (reached) | 31 |
| path traced but destination silent (`* * *` at the end) | 58 |
| no usable path at all | 11 |

**Why so few "reached": PK government/public servers firewall ICMP.** All 69
not-reached sites are PK gov/edu/utility hosts — they drop ping/traceroute as a
security policy, so the trace maps the path but the final host never answers. It does
**not** mean the site is down or mis-hosted — **hosting comes from Pass A (DNS→ASN)**,
which needs no ICMP; Pass B's value is the **path** (where it hairpins) and the RTT to
the last visible hop. Two flavours: (a) *local-but-silent* (e.g. `fbr.gov.pk` at 3.6 ms
on its own network, just won't answer), and (b) *hairpinned + DDoS-fronted* (behind
Prolexic/Akamai AS32787 — path goes Transworld → Equinix-SG → Prolexic NL/US ~205 ms,
origin hidden — the Cybernet federal-block gov sites).

**RTT buckets** (RTT to the destination for the 31 reached; to the last responding hop
for the silent ones — so treat these as *path* latency, not confirmed serving RTT):

| Bucket | Sites |
|---|---|
| same-city (<10 ms) | 22 |
| in-PK (<50 ms) | 49 |
| **far (>150 ms)** | **18** |
| no reply | 11 |

Median (PK-hosted) ≈ **34 ms**, min 4 ms — most PK-hosted sites are genuinely local
from Transworld; the 18 "far" are the hairpin below.

**Key finding — hosting local ≠ path local (a hairpin caught):** **18 PK-hosted
*government* sites, ALL on Cybernet's federal block (`203.101.184.x` / `CYBERNET-AP`),
are reached at ~195–216 ms from Transworld** (agp, agpr, aviation, cga, cii, ead,
mofept, moitt, nab, ncsw, nhmp, nitb, pakistan.gov, pcsir, pemra, pmo, ntc.net, ztbl).
They are hosted *inside Pakistan* (Pass A) but a **Transworld** user reaches them via a
**~200 ms international hairpin** — Transworld has no good domestic route to Cybernet's
gov block. This is the tromboning story hitting government hosting directly, and it is
exactly the kind of vantage-dependence Pass B exists to expose: *the site is local, the
path is not.* (See the `<<< LEAVES PK` markers in `routes_pass_b_*.txt`.)

---

## Combined census — Experiment 01 + Experiment 1.4

Merges Exp 01's list (commercial / news / banking / e-commerce, etc.) with Exp 1.4's
(government / education / utility). **172 unique sites** (Exp 01 = 91, Exp 1.4 = 100,
**19 in both**). Full per-site table (category, hosting ISP/operator, where hosted):
`results/combined_hosting.csv` (built by `combine_with_exp01.py`).

**Vantage points of the two groups:**
- **Exp 01** — ICMP Paris traceroutes from **5 Pakistani RIPE probes**: Nova/TPCPL
  (AS136174), PTCL (AS17557), Transworld (AS38193), Nayatel (AS23674), Z-Com
  (AS152605). DNS resolved centrally; the serving city (`dest_location`) derived from
  the **traceroute handoff hop + ip-api** (`geo_utils.serving_location`) — so CDN/anycast
  sites get a real *serving* metro, not just the registered country.
- **Exp 1.4** — **Pass A** from the project machine (a **PK** vantage): DNS + Team Cymru
  ASN + ip-api geolocation (hosting identity). **Pass B** from RIPE probe **64078**
  (**Transworld / TES-PL AS135407, Rawalpindi**): traceroute RTT + serving PoP.

**Combined hosting split (172 sites):**

| Category | Combined | Exp 01 (commercial) | Exp 1.4 (gov/edu) |
|---|---|---|---|
| **Pakistan** (real PK server) | **104 (60%)** | 23 (25%) | 98 (98%) |
| **CDN** (Cloudflare/Akamai/…) | **54 (31%)** | 54 (59%) | 1 (1%) |
| **Abroad** (real foreign server) | **14 (8%)** | 14 (15%) | 1 (1%) |

**The headline contrast — sector predicts hosting:**
- **Public sector (gov/edu/utility) self-hosts in Pakistan: 98%**, on a handful of
  domestic networks (Cybernet, PITB, PITC, COMSATS, PTCL, Nayatel — see the grouping
  above).
- **Private sector (commercial/news/banking) goes offshore/CDN: only 25% on a PK
  server**, 59% behind a CDN (mostly Cloudflare, often serving from Singapore/HK/EU),
  15% on foreign servers (banks in the US/Singapore, news on Hetzner-EU, etc.).
- Overall **~40% of the combined set is NOT on a Pakistani server** (CDN + abroad),
  driven almost entirely by the commercial half.

**Combined — sites per host / network (all 172):**

*Pakistan (104):*

| Host ISP | Sites |
|---|---|
| Cybernet (`CYBERNET-AP` 26 + `-APII` 3) | 29 |
| COMSATS | 12 |
| PITB (Punjab gov) | 9 |
| PTCL | 7 |
| PITC (power sector) | 7 |
| Nayatel | 6 |
| LinkDotNet | 5 |
| Multinet (`-AS` 4 + `-IE` 1) | 5 |
| NTC | 4 |
| Nexlinx | 4 |
| Wateen | 3 |
| PERN/HEC | 2 |
| FBR (own ASN) | 2 |
| Transworld | 2 |
| Gemnet | 2 |
| Telecard, UBL, Gourmet Foods, Iqra Univ, Broadband/BBI | 1 each |

*CDN (54):* Cloudflare **39**, AWS 8, Microsoft/Azure 3, Sucuri 2, Imperva/Incapsula 1,
Akamai 1.

*Abroad (14):* Hetzner–DE/FI **4**, Hostinger 2, then 1 each: Oracle Cloud, Alibaba
(CN), OVH (FR), Network Solutions (US), DOSarrest, LiquidWeb (US), GoDaddy (US), EDNS.

So the domestic hosting is concentrated in **Cybernet (29)** and a long tail of public
providers; the offshore side is dominated by **Cloudflare (39)** and Hetzner among real
foreign hosts.

**Combined — hosting by sector (172 sites):**

| Sector | Pakistan | CDN | Abroad | Total |
|---|---|---|---|---|
| Government | 43 | 4 | 1 | 48 |
| Education | 19 | 8 | 1 | 28 |
| News & Media | 3 | 12 | 3 | 18 |
| Banking & Finance | 6 | 10 | 2 | 18 |
| Business / E-commerce | 2 | 10 | 4 | 16 |
| Telecom & ISP | 7 | 2 | 3 | 12 |
| Power & Utilities | 11 | 0 | 0 | 11 |
| Health | 3 | 3 | 0 | 6 |
| NGO / Non-profit | 5 | 0 | 0 | 5 |
| Energy (Oil & Gas) | 4 | 0 | 0 | 4 |
| Food | 0 | 2 | 0 | 2 |
| Real Estate | 0 | 2 | 0 | 2 |
| Sports & Entertainment | 1 | 1 | 0 | 2 |
| **TOTAL** | **104** | **54** | **14** | **172** |

Reading down the sectors: **Government (90% PK), Power & Utilities (100% PK), Energy
(100% PK), NGO (100% PK)** are almost entirely domestic. **News & Media (67% CDN),
Business/E-commerce (63% CDN + abroad), Banking (67% CDN + abroad)** are almost
entirely offshore/CDN. Education splits (68% PK, mostly on PERN/COMSATS/university
ASNs, but 8 on CDN). Sector is the strongest predictor of where a site is hosted.

For per-site detail — each site's **category, hosting ISP/operator, and location** —
see `results/combined_hosting.csv` (columns: `hostname, exp, exp_category, category,
host, where, asn`). Note: for the 19 sites in both lists, the Exp 01 classification
(5-probe, serving-location-aware) is used.
