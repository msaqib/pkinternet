# Research Findings: Pakistan Internet Topology & Inter-Domain Routing Study

**Project:** Assessing Local Interconnectivity Resilience & Routing Efficiency in Pakistan  
**Author:** Rayan Atif (Research Assistant, LUMS)  
**Supervisor:** Dr. Saqib Ilyas (LUMS)  
**Funding:** APNIC Foundation  
**Target Submission:** ACM AINTEC '26 / IEEE Transactions on Network and Service Management  
**Status:** Canonical Internal Research Summary (Branch: docs/findings)

---

## Executive Summary

This study presents the first comprehensive empirical measurement of Pakistan's inter-domain routing topology, traffic locality, and infrastructure resilience, combining data-plane active measurements from RIPE Atlas probes with global BGP control-plane telemetry (IIJ Internet Health Report) and national population datasets (APNIC Labs). 

Across **222,944 longitudinal Paris traceroutes**, **445,749 ICMP latency pings**, a **747-prefix block-level small-ISP census (18,260 traces)**, and **real-time observation of the July 2026 SEA-ME-WE 5 (SMW5) submarine cable cut**, the study establishes four foundational findings:

1. **Structural Upstream Duopoly:** 89.7% of the 291 BGP-visible Pakistani ASes and 99.63% of Pakistan's ~42.3M estimated internet users depend on either PTCL (AS17557) or Transworld (AS38193) for their majority upstream routing, creating a single point of failure in international transit.
2. **Submarine Cable Outage Absorption & Rerouting:** The July 2026 SMW5 cable fault caused a 78-sigma latency spike on international paths (loss jumping from 1.5% to 7.3%, median RTT doubling) while domestic traffic remained 100% insulated. Recovery within 24–36 hours was achieved entirely through upstream control-plane re-carriering onto Hurricane Electric (+7.1 to +9.1 percentage points) rather than physical undersea cable repair.
3. **National IXP Bypass:** In the 7-day longitudinal panel across 906 observed routers, exactly **0 traces crossed the peering fabrics of PKIX Lahore or PIE Karachi**, despite active member status. Member ISPs bypass public exchange fabrics in favor of private bilateral links or foreign transit.
4. **Domestic Path Tromboning & Sector Penalty:** Between 5.52% (strict lower bound) and 15.1% (headline baseline) of domestic packets leave Pakistan and hairpin back via Singapore, the US, or China. Financial services is the most severely affected sector (58.3%–85.6% trombone rate; 103.1–118.0 ms median RTT), with 24.0%–26.6% of domestic paths exceeding 10× the theoretical speed-of-light propagation floor.

---

## 1. National Measurement Census & Longitudinal Panel Scale

### Finding & Key Numbers
- **Longitudinal Flagship Panel (Exp 07):** Executed a continuous 7-day uniform measurement panel (2026-07-11 to 2026-07-18) deploying dual RIPE Atlas accounts across 16 Pakistani hardware and software vantage points (14-probe core analysis roster) targeting a stratified sample of 100 Pakistani websites.
  - Total Volume: **222,944 TCP/80 Paris traceroutes** (hourly cadence) + **445,749 ICMP ping rounds** (half-hourly cadence).
  - Target Stratification (Physics-Corrected): 37 Pakistan-hosted, 40 CDN-fronted, and 23 Abroad-hosted websites across 8 CISA infrastructure sectors.
- **Small-ISP Block-Level Census (Exp 4.1):** Conducted the first national prefix-level routing census of Pakistan's entire local Fixed Local Loop (FLL) ISP population.
  - Scope: Targeted 48 ISPs across **747 announced /24 prefix blocks** (8 spread IP targets per block, probing 5,976 distinct destination IPs) from 7 Pakistani source probes, returning **18,260 complete traceroutes** (45 ISPs / 696 blocks responding).
- **Website Hosting Census (Exp 01 / 1.4):** Initial 91-site survey across 10 batches revealed that ~75% of top Pakistani sites are not hosted on in-country servers (25% PK, 29% abroad, 46% CDN). The PK100 top-site census classified 60% PK-hosted, 31% CDN-fronted, and 8% abroad-hosted.
- **Per-ISP DNS Resolution Validation (Exp 1.1):** Probing from each ISP's local recursive resolver revealed GeoDNS differences on only 8 of 103 sites (~7.8%), proving centralized DNS resolution valid for >92% of national web properties.
- **BGP State Validation (Exp 05):** Cross-validation of data-plane traceroute AS paths against RIPEstat BGP state and Hurricane Electric (bgp.he.net) peering tables confirmed **78 of 80 unique ISP-site paths (97.5%)** were strictly consistent with public BGP advertisements.

### Methodology
- Active measurement engine utilizing 
ipe-atlas-cousteau and sagan parsing libraries.
- Dual-account scheduling separating Paris traceroute streams (Account A) from fine-grained latency ping streams (Account B) to prevent rate-limiting and bufferbloat.
- Paris traceroute implementation maintaining constant flow identifiers (IP identification / port hashes) to eliminate false route changes from flow-based load balancing (ECMP).
- Rigorous IP-to-ASN mapping via Team Cymru bulk lookup with RDAP registry fallback and ip-api geolocation cross-checked against minimum fibre propagation delays.

### Caveats & Failure Modes
- **Domestic ICMP Filtering:** 54.8% of ping rounds to domestic PK-hosted sites timed out (22 of 100 sites completely silent) due to corporate/governmental edge firewalls. Latency ratio metrics for domestic sites therefore describe the responding 45% of hosts.
- **TCP/80 Terminal Opacity:** 19.6% of traceroutes terminated in non-responding hops (hop 255) due to TCP filtering at the target host. Path analysis remains valid up to the final ingress router.
- **Vantage Point Filtering:** Probe 7764 (PTCL Lahore anchor) suffered 90% ping packet loss throughout the panel, and probe 1015491 was identified as a co-located duplicate of probe 7613 (Z-Com Lahore). Both were excluded from the 14-probe core analytical roster.

---

## 2. International Transit Concentration & The Duopoly

### Finding & Key Numbers
- **Global Control-Plane Concentration (Exp 09):** Analysis of IIJ Internet Health Report (IHR) AS Hegemony across all 291 BGP-visible Pakistani ASNs revealed that **89.7% (261 ASes) depend on PTCL (AS17557) or Transworld (AS38193) for the majority of their AS paths** (hegemony >= 0.50). Material dependency (hegemony >= 0.10) reaches **92.1%**.
  - Median Hegemony across Pakistani origin ASNs: **Transworld = 0.50, PTCL = 0.17**.
- **Population-Weighted Impact (Exp 6.1.1, W1/W4):** Mapping APNIC Labs user-population datasets to transit dependencies establishes that **99.63% of Pakistan's estimated ~42.3M internet users** sit behind networks majority-dependent on the duopoly:
  - **70.3% (29.6M users)** on PTCL-majority networks.
  - **29.7% (12.5M users)** on Transworld-majority networks.
- **Data-Plane Transit Partitioning (Exp 4.1):** Attributable international transit handoffs in the small-ISP census split almost evenly between the two carriers: **Transworld carried 589 handoffs** and **PTCL carried 566 handoffs** (together comprising ~58% of all attributable hairpins).
- **Unannounced Domestic Infrastructure (Exp 07):** Out of 143 distinct Transworld routers observed in data-plane traceroutes, **125 routers (87.4%) are unannounced in global BGP tables**, demonstrating that pure control-plane analysis fails to observe the vast majority of Pakistan's physical transit topology.

### Methodology
- Querying IIJ IHR public API for AS Hegemony scores (Fontugne et al. metric), measuring the viewpoint-trimmed fraction of global BGP paths toward an origin ASN traversing a given transit ASN.
- User population weighting using APNIC Labs AS-population dataset (pnic_aspop_pk_20260717.json).
- Hop-by-hop ASN extraction and router clustering across 906 data-plane interfaces.

### Caveats & Failure Modes
- AS Hegemony quantifies BGP path counts rather than carried traffic volume.
- Private peering links and unannounced internal backbones are invisible to BGP collectors (RouteViews/RIPE RIS), making BGP hegemony a conservative lower bound on true transit dependency.

---

## 3. Submarine-Cable Fault Resilience (The July 2026 SMW5 Event)

### Finding & Key Numbers
- **Outage Profile & Early Detection (Exp 06, 6.1, 6.1.1):** The SEA-ME-WE 5 (SMW5) cable fault (announced by PTA on 2 July 2026) was an international latency degradation and jitter surge, not a total blackout.
  - Independent worldwide RIPE Atlas anchor telemetry (~1,000 global anchors probing Z-Com Lahore anchor) proved fault onset at **1 July 2026 17:00 PKT (~32 hours prior to PTA's public announcement)**.
  - At peak disruption, Z-Com anchor experienced a **78-sigma latency spike** (median RTT doubling from 176 ms baseline to 323.9 ms, and packet loss surging from 1.5% to **7.3%**).
- **Upstream BGP Absorption (Exp 6.1):** Both duopoly transit operators dynamically rerouted international traffic at their upstream borders:
  - Transworld shifted **20.9%** and PTCL shifted **13.5%** of their world-bound paths, surging heavily onto Hurricane Electric (TWA share: 2% -> 20.5%; PTCL share: 0% -> 14.2%) while shedding Cogent and Sparkle.
- **Downstream Structural Stability (Exp 6.1.1, W1/W4):** Downstream domestic networks remained virtually static:
  - **99.63% of Pakistan's ~42.1M matched users** remained on networks whose majority gateway never shifted.
  - Nationally, only **4 out of 273 gate-dependent ASNs (1.5%)** swapped majority gateways (e.g., Fasttel temporary 2-day swap from PTCL 0.74 to TWA 0.54 before reverting).
- **Domestic Traffic Insulation (Exp 06):** In the 12-hour high-cadence monitor across 14 vantage points, domestic-hosted Pakistani targets (isra.edu.pk, punjab.gov.pk, 	elenor.com.pk) remained 100% flat and unaffected, whereas international paths suffered +31% jitter (+50% jitter on PTCL paths).
- **Recovery Mechanism (Exp 06 & 6.1.1):** Comparing public hop paths across the 12-hour window showed that 159 of 252 pairs were path-identical, while the remaining 93 pairs alternated between parallel load-balanced links within the same transit carrier (exit countries remained invariant). Rapid normalization within 24–36 hours corroborates that recovery was achieved via upstream traffic re-engineering rather than physical undersea cable repair.

### Methodology
- High-cadence periodic monitoring (15-minute interval across 12 hours) from 14 RIPE Atlas probes to 18 targets (6 CDN, 6 Abroad, 6 PK).
- Daily control-plane AS-hegemony timeseries across a 56-day baseline window (2026-05-15 to 2026-07-10).
- Four-operator placebo test: Tested churn metrics against 2 SMW5 landing operators (Oman, Sri Lanka) and 2 non-SMW5 zero-exposure controls (Nepal, Vietnam). While general churn magnitude was found to be a global BGP artifact, the Hurricane Electric swing was **2–8x larger** in SMW5-exposed networks (+7.1 to +13.2 points) than in controls (+1.5 to +3.8 points), verifying the physical fault attribution.

### Caveats & Failure Modes
- Active 12-hour monitor commenced after the fault was already underway (captured degraded baseline).
- User population figures represent exposure ceilings based on APNIC estimates, not counted individual subscriber disruptions.
- A 5-day anchor data gap exists between 6–10 July 2026 prior to the Exp 07 panel launch.

---

## 4. IXP Adoption, Bypass, and CDN Locality Disparity

### Finding & Key Numbers
- **Total National IXP Bypass (Exp 07 & Exp 08):** In the 7-day longitudinal panel across 222,944 traceroutes, **0 traces traversed the public peering LANs of PKIX Lahore (100.128.0.0/24) or PIE Karachi (58.181.127.0/24)**.
  - During the same observation period, 11,756 traceroutes to domestic Pakistani targets exited abroad through international transit providers and hairpinned back.
- **Bilateral Member Bypassing (Exp 08):** Traceroutes between active members of PIE Karachi (PTCL, Connect Communications, ACE CDN/Tencent EdgeOne) and PKIX Lahore (Z-Com, Transworld) bypass shared switching fabrics:
  - PTCL and Connect Communications route via PTCL private backbone interfaces (119.159.224.18).
  - Z-Com and Transworld route via direct private cross-connects (110.93.205.184, 17–20 ms).
- **Absence of On-Net CDN Caching (Exp 10):** Direct probing of Google Global Cache (GGC) across 10 Pakistani ISPs confirmed **0 on-net edge caches hosted directly inside local access networks**.
- **Extreme CDN Locality Lottery (Exp 07, Exp 08, Exp 1.2):** 46.6% of panel fetches to CDN-fronted websites left Pakistan entirely. CDN performance is entirely determined by ISP peering topology:
  - **Nayatel:** 85.0% local CDN delivery (median RTT 3.7 ms, 2 hops).
  - **Cybernet Karachi:** 41.0% local CDN delivery.
  - **PTCL / Fasttel / Orbit / Nova:** **0.0% local CDN delivery** (PTCL median RTT 130–275 ms).
  - **Tencent / ACE CDN (Exp 08.4):** Reachable at 23 ms for PTCL and Nayatel via private peering, but 255 ms for Cybernet customers via Singapore/Hong Kong (an **11x latency disparity** for identical content).

### Methodology
- Peering LAN prefix matching against official PeeringDB records and DE-CIX looking glass tables.
- Cross-ISP targeted probing of major CDN anycast prefixes (Cloudflare, Akamai, Tencent, Google, Meta).
- Calculation of per-ISP CDN Locality Scores based on physical RTT thresholds (<15 ms domestic vs >50 ms foreign).

### Caveats & Failure Modes
- Router interface masking: Approximately 45.1% of traceroute hops exhibit unresponsive middle-hop interfaces (private IP or timeout), which could theoretically obscure an exchange IP; however, end-to-end latency convergence and explicit bilateral hops confirm fabric bypassing.

---

## 5. Domestic Path Tromboning & Latency Ratios

### Finding & Key Numbers
- **Tromboning Rates on Domestic Targets:**
  - **Exp 07 Panel (75,600 domestic traces):**
    - **15.1% headline rate** (11,449 traces) under the dual RTT-jump / foreign-hop detector.
    - **5.52% strict lower bound** (4,170 traces) under the 5-condition verified foreign-hop detector (artifact ASNs {6327, 174} excluded).
    - **8.30% robustness bound** (6,275 traces) with destination-RTT corroboration across unresponsive middle hops.
  - **Small-ISP Census (Exp 4.1):** **11.0% of 18,260 traces** (2,002 traces) hairpin abroad; 325 traces entered the destination ISP's network only after foreign transit (Brain Telecom accounting for 182).
  - **Worldcall Census (Exp 04):** **31.0% of Worldcall's 52 /24 blocks** trombone via Transworld to Equinix Singapore, while PTCL reaches identical IPs locally.
- **Source PoP Dominance (Exp 4.1):** Tromboning is heavily determined by source vantage rather than destination:
  - **Cybernet Haripur:** **46.3% trombone rate** (260/562).
  - **PTCL Karachi:** **38.4% trombone rate** (586/1,525).
  - **Cybernet Karachi:** **10.5% trombone rate** (218/2,084) — proving tromboning is a per-PoP/per-router property rather than an ISP-wide invariant.
  - **Nayatel:** **4.0% trombone rate** (128/3,204).
- **Critical Infrastructure & Sector Penalty (Exp 07):**
  - **Financial Services is the most degraded sector:** **58.3% (strict) to 85.6% (baseline) trombone rate**, with median domestic ping RTT of **103.1–118.0 ms** (ZTBL Bank hairpins 86.4%, EFU Life 72.0%).
  - **Government Services:** **14.6% (strict) to 27.6% (baseline) trombone rate**, driven by specific misconfigured targets (Federal Government Employees Housing Authority geha.gov.pk hairpins **89.2%** via Singapore).
- **Speed-of-Light Latency Ratio Violations (Exp 07):**
  - Measuring the dimensionless Latency Ratio (Measured RTT / Fibre Physics Floor [d/100 ms]):
  - **Abroad Class (Control):** Median ratio 2.46x, p90 4.20x, **0% > 10x**, R^2 = 0.48. International routing closely tracks physical geodesic distance.
  - **Pakistan Class:** Median ratio 2.88x–2.98x, p90 14.9x, **24.0%–26.6% > 10x**, maximum ratio reaching **75.17x**, R^2 = 0.022. Domestic latency is completely decoupled from physical distance due to international tromboning loops.
- **Route Dynamics & Intermittency (Exp 07):**
  - Diurnal variation is minimal (4.5%–4.8% / 12.6%–16.0%), confirming tromboning is structural rather than congestion-driven.
  - At the pair level, **44.8% of ever-tromboning pairs** are also reached locally during the same week.
  - **23 confirmed gate-flips** occurred between PTCL and Transworld on the exact same probe-target pair.

### Methodology
- 5-Condition Strict Trombone Classifier: Evaluates a trace as tromboned iff a responding hop satisfies: (1) resolves to country != PK, (2) non-private IP, (3) ASN not in {6327, 174}, (4) valid response, (5) hop RTT between 40 ms and 500 ms.
- Geodesic distance calculation via Haversine formula against calibrated probe/target coordinates cross-checked with physical speed-of-light lower bounds (c_glass ~ 200,000 km/s -> RTT_min ~ 2d/200 = d/100 ms).

### Caveats & Failure Modes
- **Artifact ASNs:** Cogent (AS174) operates a router in Pakistan with foreign IP registration; failure to exclude AS174 artificially inflates US exit counts from 253 to 1,750. Shaw (AS6327) exhibits identical registration artifacts.
- **Short-Distance Access-Floor Inflation:** For intra-city pairs (<20 km), last-mile access link serialization delays (2–10 ms) inflate the dimensionless ratio (producing the 75.17x max ratio) without indicating an international detour.

---

## 6. Methodological Advances & Research Reproducibility

1. **Physics Arbiter for Geolocation Validation:** Overrode 37 of 78 initial geo-IP site classifications where observed ping latency violated speed-of-light vacuum bounds (e.g., anycast CDNs misattributed to headquarters in Toronto).
2. **Double-Vantage Validation:** Independent verification across data plane (RIPE Atlas) and control plane (IIJ IHR AS Hegemony) proved consistent ISP rankings across independent measurement systems.
3. **Artifact-Robust Longitudinal Pipeline:** Production of reproducible Python/Jupyter workflows validating Paris traceroute flow invariants, automated Cymru/RDAP caching, and continuous Prometheus/Grafana metric telemetry.
