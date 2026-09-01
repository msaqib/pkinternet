# Interesting routes — Pakistan-hosted sites reached via a foreign hairpin

Auto-extracted from `results/a/routes_20260718_195946.txt` (Exp 07 panel, latest trace per probe/target, 2026-07-18 snapshot), joined against `hop_geo.csv` and **corrected using the same `KNOWN_LOCATIONS` override + physics-arbiter logic already in `routing_map.py`** (imported directly, not copied, so this stays in sync with the map) — this fixes the raw ip-api.com mislabels (e.g. Equinix Singapore showing as "Sydney") documented in `eda_findings.md` §2. Filtered to traces where: (1) the target site is classified `[Pakistan]` (should be reached locally), and (2) the RTT-physics verdict is `TROMBONE` (path actually left the country and came back). Sorted worst-first: routes crossing the most distinct foreign countries, then by max RTT.

**Totals in this snapshot:** 124 Pakistan-class traces are TROMBONE out of 640 total. Of those, **37 cross 2+ distinct foreign countries**, 34 cross exactly 1, and 53 have no hop that resolved to a foreign country (unresolved/private hops only). Correction pass: **43 hop-occurrences fixed via KNOWN_LOCATIONS**, **43 hop-occurrences flagged physically-impossible** (RTT below the speed-of-light floor for the claimed city — shown inline below, not silently kept).

**Correction, 2026-09-01 [†]:** every row below showing IP `206.148.27.235` as "Equinix Muscat (GSL, via PTR)" has been relabeled **"Abroad, site unconfirmed"**. That label came from extending a real PTR confirmation on two *different* IPs (`206.148.27.1`/`.2`) to the whole `/24` block. Re-checked: `.235`'s own hostname is generic (no city code), and its actual neighbors in that block resolve to Ashburn, Adelaide, Seattle, and Phoenix, four cities on two continents, so the block isn't single-site and the Muscat label doesn't transfer to `.235`. It's still confidently **abroad** (the RTT jump getting there, and the fact every directly-checked neighbor is abroad too, both rule out Pakistan) — just not confirmed to specifically be Muscat. Rows showing `206.148.27.1` itself (a different IP, hop 11 in the second `efulife.com` trace below) are unaffected; that one's PTR confirmation is direct and still holds.

Same-day, same issue, one more row: `160.202.164.165` was shown below as "Los Angeles". That was never a PTR finding for this IP at all, it was `eda_findings.md` §2's raw, uncorrected `ip-api.com` guess, quoted there only to show `ip-api` contradicts itself between GSL addresses, not as a verified answer. Reverse-DNSing `.165`'s actual neighbors turns up Brisbane, Sydney, Muscat, Singapore, Dallas, Frankfurt, and Phoenix all within about 12 addresses, confirming (via APNIC RDAP) that the whole `160.202.164.0/24` block is one company-wide global pool, not a single site, exactly the same pattern as the `206.148.27.x` case. Relabeled **"Abroad, site unconfirmed"** too.

See `edits/2026-09-01_eda_docs_gsl_muscat_correction.md` and `eda_findings.md` §2 for the full re-check on both hops.

**Caveats before presenting these:**
- **`toptop.net` and `youth.cn`** may actually be genuinely offshore sites mislabeled `[Pakistan]` class (flagged separately in `findings/07_longitudinal_panel.md`) — don't cite these as PKIX/hairpin evidence without checking that classification first.
- **Probe `ptcl.1016393` (PTCL-Mianwali)** RTTs cluster suspiciously near a 490-500ms ceiling elsewhere in this dataset (`eda_findings.md` §1, likely an ICMP-delay artifact) — treat this probe's specific RTT numbers with caution; its path/hop sequence is still informative.
- **`fgeha.gov.pk` / `ztbl.com.pk`** reproduce the same Prolexic/Singapore/NTC detour independently across 8 different probes/ISPs — the most solid, structural example in this file, good headline candidate.
- **`efulife.com`** is TROMBONE from PTCL here but separately confirmed genuinely PK-hosted and delivered locally (4.7-23ms) from 3 Cybernet probes — not a contradiction: PTCL specifically hairpins to reach it, Cybernet doesn't.

## Contents

**A. Multi-country hairpins**
1. [efulife.com — ptcl.1016126, 4 countries, 119.2ms](#1-efulifecom-probe-ptcl1016126-1016126)
2. [toptop.net — ptcl.1016393, 3 countries, 475.8ms](#2-toptopnet-probe-ptcl1016393-1016393)
3. [networld.pk — ptcl.1016393, 3 countries, 462.0ms](#3-networldpk-probe-ptcl1016393-1016393)
4. [fgeha.gov.pk — ptcl.1016393, 3 countries, 439.3ms](#4-fgehagovpk-probe-ptcl1016393-1016393)
5. [youth.cn — ptcl.1016393, 3 countries, 335.6ms](#5-youthcn-probe-ptcl1016393-1016393)
6. [ztbl.com.pk — orbit.64535, 3 countries, 280.8ms](#6-ztblcompk-probe-orbit64535-64535)
7. [fgeha.gov.pk — orbit.64535, 3 countries, 273.7ms](#7-fgehagovpk-probe-orbit64535-64535)
8. [ztbl.com.pk — zcom.7613, 3 countries, 271.4ms](#8-ztblcompk-probe-zcom7613-7613)
9. [fgeha.gov.pk — zcom.7613, 3 countries, 267.2ms](#9-fgehagovpk-probe-zcom7613-7613)
10. [ztbl.com.pk — ptcl.1016393, 3 countries, 249.9ms](#10-ztblcompk-probe-ptcl1016393-1016393)
11. [fgeha.gov.pk — fasttel.1014872, 3 countries, 218.4ms](#11-fgehagovpk-probe-fasttel1014872-1014872)
12. [fgeha.gov.pk — nova.1015679, 3 countries, 213.8ms](#12-fgehagovpk-probe-nova1015679-1015679)
13. [ztbl.com.pk — ptcl.1016126, 3 countries, 210.5ms](#13-ztblcompk-probe-ptcl1016126-1016126)
14. [ztbl.com.pk — nova.1015679, 3 countries, 210.3ms](#14-ztblcompk-probe-nova1015679-1015679)
15. [fgeha.gov.pk — ptcl.1016126, 3 countries, 205.3ms](#15-fgehagovpk-probe-ptcl1016126-1016126)
16. [networld.pk — ptcl.1016126, 3 countries, 202.4ms](#16-networldpk-probe-ptcl1016126-1016126)
17. [ztbl.com.pk — fasttel.1014872, 3 countries, 202.3ms](#17-ztblcompk-probe-fasttel1014872-1014872)
18. [ztbl.com.pk — tes.64078, 3 countries, 192.2ms](#18-ztblcompk-probe-tes64078-64078)
19. [ztbl.com.pk — tes.64722, 3 countries, 187.3ms](#19-ztblcompk-probe-tes64722-64722)
20. [fgeha.gov.pk — tes.64078, 3 countries, 179.9ms](#20-fgehagovpk-probe-tes64078-64078)
21. [fgeha.gov.pk — tes.64722, 3 countries, 178.7ms](#21-fgehagovpk-probe-tes64722-64722)
22. [toptop.net — ptcl.1016126, 3 countries, 131.8ms](#22-toptopnet-probe-ptcl1016126-1016126)
23. [youth.cn — ptcl.1016126, 3 countries, 115.2ms](#23-youthcn-probe-ptcl1016126-1016126)
24. [efulife.com — ptcl.1016393, 2 countries, 430.4ms](#24-efulifecom-probe-ptcl1016393-1016393)
25. [toptop.net — cybernet.1016143, 2 countries, 237.0ms](#25-toptopnet-probe-cybernet1016143-1016143)
26. [youth.cn — zcom.7613, 2 countries, 184.4ms](#26-youthcn-probe-zcom7613-7613)
27. [toptop.net — zcom.7613, 2 countries, 169.6ms](#27-toptopnet-probe-zcom7613-7613)
28. [toptop.net — nova.1015679, 2 countries, 147.3ms](#28-toptopnet-probe-nova1015679-1015679)
29. [youth.cn — orbit.64535, 2 countries, 146.3ms](#29-youthcn-probe-orbit64535-64535)
30. [toptop.net — orbit.64535, 2 countries, 126.1ms](#30-toptopnet-probe-orbit64535-64535)
31. [kknetworks.com.pk — cybernet.1016036, 2 countries, 121.1ms](#31-kknetworkscompk-probe-cybernet1016036-1016036)
32. [youth.cn — nova.1015679, 2 countries, 100.6ms](#32-youthcn-probe-nova1015679-1015679)
33. [youth.cn — tes.64722, 2 countries, 82.7ms](#33-youthcn-probe-tes64722-64722)
34. [youth.cn — cybernet.1016143, 2 countries, 79.5ms](#34-youthcn-probe-cybernet1016143-1016143)
35. [toptop.net — cybernet.1016154, 2 countries, 78.8ms](#35-toptopnet-probe-cybernet1016154-1016154)
36. [toptop.net — tes.64722, 2 countries, 78.6ms](#36-toptopnet-probe-tes64722-64722)
37. [youth.cn — cybernet.1016154, 2 countries, 78.3ms](#37-youthcn-probe-cybernet1016154-1016154)

**B. Single foreign-country hairpins**
1. [sonic.pk — ptcl.1016393, 481.1ms](#1-sonicpk-probe-ptcl1016393-1016393)
2. [trax.pk — ptcl.1016393, 453.6ms](#2-traxpk-probe-ptcl1016393-1016393)
3. [mepco.com.pk — ptcl.1016393, 427.1ms](#3-mepcocompk-probe-ptcl1016393-1016393)
4. [kknetworks.com.pk — ptcl.1016393, 417.0ms](#4-kknetworkscompk-probe-ptcl1016393-1016393)
5. [efulife.com — zcom.7613, 251.7ms](#5-efulifecom-probe-zcom7613-7613)
6. [trax.pk — fasttel.1014872, 238.9ms](#6-traxpk-probe-fasttel1014872-1014872)
7. [zcomnetworks.com.pk — cybernet.1016036, 211.4ms](#7-zcomnetworkscompk-probe-cybernet1016036-1016036)
8. [youth.cn — cybernet.1016036, 197.7ms](#8-youthcn-probe-cybernet1016036-1016036)
9. [toptop.net — cybernet.1016036, 192.7ms](#9-toptopnet-probe-cybernet1016036-1016036)
10. [efulife.com — orbit.64535, 176.7ms](#10-efulifecom-probe-orbit64535-64535)
11. [sonic.pk — ptcl.1016126, 166.9ms](#11-sonicpk-probe-ptcl1016126-1016126)
12. [trax.pk — ptcl.1016126, 144.5ms](#12-traxpk-probe-ptcl1016126-1016126)
13. [sonic.pk — fasttel.1014872, 140.8ms](#13-sonicpk-probe-fasttel1014872-1014872)
14. [efulife.com — nova.1015679, 118.3ms](#14-efulifecom-probe-nova1015679-1015679)
15. [youth.cn — fasttel.1014872, 107.2ms](#15-youthcn-probe-fasttel1014872-1014872)

---
# A. Multi-country hairpins (strongest examples — widest detours)

## 1. efulife.com — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **119.2ms**, exit=US, transit AS=PTCL, foreign countries crossed: **AE, NZ, OM, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.5 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 25.7 | 10.253.5.94 | (unresolved) |  |  |
| 4 | 25.9 | 10.253.4.122 | (unresolved) |  |  |
| 5 | 27.5 | 10.253.4.24 | (unresolved) |  |  |
| 6 | 110.8 | 206.148.27.235 | GSL - Global Secure Layer, AU |  | **Abroad, site unconfirmed [†]** |
| 7 | 119.2 | 206.148.22.141 | GSL - Global Secure Layer, AU |  | **Equinix Singapore (GSL, via PTR)** _(corrected)_ |
| 8 | 112.8 | 160.202.164.165 | GSLNETWORKS-AS-AP - GSL Networks Pty LTD | NZ | **Abroad, site unconfirmed [†]** _(was "Los Angeles" -- that was raw, uncorrected ip-api output, never PTR-verified; see correction)_ |
| 10 | 114.1 | 213.202.6.197 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 11 | 111.8 | 134.0.220.234 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 12 | 111.8 | 213.202.7.209 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 13 | 108.1 | 192.168.5.29 | (unresolved) |  |  |
| 14 | 107.6 | 192.168.4.6 | (unresolved) |  |  |
| 15 | 108.8 | 192.168.200.34 | (unresolved) |  |  |
| 16 | 108.5 | 10.15.64.114 | (unresolved) |  |  |
| 17 | 108.7 | 124.29.240.218 | CYBERNET-AP - Cyber Internet Services (P | PK | Karachi |
| 18 | 109.0 | 103.154.196.31 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 20 | 109.3 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |

---
## 2. toptop.net — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **475.8ms**, exit=US, transit AS=PTCL, foreign countries crossed: **CA, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 369.0 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 413.9 | 10.253.9.146 | (unresolved) |  |  |
| 4 | 442.8 | 10.253.4.74 | (unresolved) |  |  |
| 5 | 459.8 | 10.253.4.24 | (unresolved) |  |  |
| 6 | 560.7 | 27.111.230.102 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 626.3 | 162.128.6.38 | (unresolved) |  | Singapore |
| 8 | 642.7 | 162.128.1.113 | ZEN-NET - Zenlayer Inc, US | SG | Singapore |
| 9 | 475.8 | 98.98.230.81 | ZEN-NET - Zenlayer Inc, US | US | Los Angeles |
| 11 | 109.1 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 3. networld.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **462.0ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **IT, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 462.0 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 443.3 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 422.3 | 10.253.4.52 | (unresolved) |  |  |
| 6 | 429.8 | 116.51.17.201 | NTT-DATA-2914 - NTT America, Inc., US | SG | Singapore |
| 7 | 555.0 | 93.186.133.54 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Singapore |
| 8 | 715.7 | 213.144.176.160 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Paris |
| 9 | 532.1 | 213.144.170.13 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Rome |
| 10 | 644.8 | 110.93.252.188 | (unresolved) |  | Karachi |
| 11 | 535.5 | 110.93.252.137 | (unresolved) |  | Karachi |
| 12 | 551.8 | 110.93.255.169 | (unresolved) |  | Karachi |
| 13 | 623.1 | 149.40.227.129 | COGENT-174 - Cogent Communications, LLC, | US | Frankfurt am Main |
| 14 | 517.4 | 10.221.198.125 | (unresolved) |  |  |
| 15 | 679.5 | 10.222.180.17 | (unresolved) |  |  |
| 16 | 526.0 | 10.200.107.10 | (unresolved) |  |  |
| 17 | 654.8 | 10.99.99.2 | (unresolved) |  |  |
| 18 | 715.8 | 192.168.80.30 | (unresolved) |  |  |
| 19 | 565.4 | 14.192.150.180 | FARIYA-PK - Fariya Networks Pvt. Ltd., P | PK | Karachi |

---
## 4. fgeha.gov.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **439.3ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 364.5 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 218.4 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 274.9 | 10.253.4.52 | (unresolved) |  |  |
| 6 | 327.1 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 283.0 | 2.21.120.144 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 712.9 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 9 | 439.3 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 345.5 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 380.0 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 348.8 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 342.7 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 5. youth.cn — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **335.6ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **CA, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 335.6 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 291.6 | 10.253.9.146 | (unresolved) |  |  |
| 4 | 27.7 | 10.253.4.74 | (unresolved) |  |  |
| 6 | 100.8 | 27.111.230.102 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 109.3 | 162.128.6.38 | (unresolved) |  | Singapore |
| 8 | 109.8 | 162.128.1.113 | ZEN-NET - Zenlayer Inc, US | SG | Singapore |
| 9 | 106.8 | 98.98.230.81 | ZEN-NET - Zenlayer Inc, US | US | Los Angeles |
| 11 | 103.3 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 6. ztbl.com.pk — probe orbit.64535 (64535)
Verdict: **TROMBONE**, max RTT **280.8ms**, exit=SG, transit AS=174, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.3 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 4.4 | 10.14.14.10 | (unresolved) |  |  |
| 4 | 5.3 | 172.29.244.9 | (unresolved) |  |  |
| 5 | 3.3 | 149.40.227.42 | COGENT-174 - Cogent Communications, LLC, | US | _Frankfurt am Main (PHYSICALLY IMPOSSIBLE at 3.3ms — dropped)_ |
| 6 | 21.5 | 110.93.254.126 | (unresolved) |  | Karachi |
| 7 | 20.8 | 110.93.252.136 | (unresolved) |  | Karachi |
| 8 | 101.1 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 96.3 | 2.21.120.112 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 10 | 277.1 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 11 | 279.7 | 192.168.51.90 | (unresolved) |  |  |
| 12 | 280.8 | 192.168.201.6 | (unresolved) |  |  |
| 13 | 204.9 | 172.16.54.3 | (unresolved) |  |  |
| 14 | 204.2 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 15 | 210.6 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 7. fgeha.gov.pk — probe orbit.64535 (64535)
Verdict: **TROMBONE**, max RTT **273.7ms**, exit=SG, transit AS=174, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 3.9 | 10.14.14.10 | (unresolved) |  |  |
| 4 | 5.3 | 172.29.244.9 | (unresolved) |  |  |
| 5 | 4.4 | 149.40.227.42 | COGENT-174 - Cogent Communications, LLC, | US | _Frankfurt am Main (PHYSICALLY IMPOSSIBLE at 4.4ms — dropped)_ |
| 6 | 20.8 | 110.93.254.124 | (unresolved) |  | Karachi |
| 7 | 21.1 | 110.93.252.246 | (unresolved) |  | Karachi |
| 8 | 96.0 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 95.9 | 2.21.120.208 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 10 | 271.4 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 11 | 270.8 | 192.168.51.90 | (unresolved) |  |  |
| 12 | 273.7 | 192.168.201.6 | (unresolved) |  |  |
| 13 | 196.9 | 172.16.54.3 | (unresolved) |  |  |
| 14 | 195.0 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 15 | 194.9 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 8. ztbl.com.pk — probe zcom.7613 (7613)
Verdict: **TROMBONE**, max RTT **271.4ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.5 | 157.20.147.17 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |
| 2 | 0.7 | 110.93.205.184 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 0.7ms — dropped)_ |
| 3 | 16.4 | 110.93.254.66 | (unresolved) |  | Karachi |
| 4 | 16.2 | 110.93.252.246 | (unresolved) |  | Karachi |
| 5 | 95.4 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 6 | 95.2 | 2.21.120.114 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 7 | 271.2 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 8 | 270.6 | 192.168.51.90 | (unresolved) |  |  |
| 9 | 271.4 | 192.168.201.6 | (unresolved) |  |  |
| 10 | 195.0 | 172.16.54.3 | (unresolved) |  |  |
| 11 | 193.4 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 12 | 193.6 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 9. fgeha.gov.pk — probe zcom.7613 (7613)
Verdict: **TROMBONE**, max RTT **267.2ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.4 | 157.20.147.17 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |
| 2 | 0.7 | 110.93.205.184 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 0.7ms — dropped)_ |
| 3 | 16.1 | 110.93.252.48 | (unresolved) |  | Karachi |
| 4 | 16.4 | 110.93.252.136 | (unresolved) |  | Karachi |
| 5 | 91.6 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 6 | 91.3 | 2.21.120.144 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 7 | 264.6 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 8 | 266.5 | 192.168.51.90 | (unresolved) |  |  |
| 9 | 267.2 | 192.168.201.6 | (unresolved) |  |  |
| 10 | 190.7 | 172.16.54.3 | (unresolved) |  |  |
| 11 | 189.3 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 12 | 189.4 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 10. ztbl.com.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **249.9ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 39.4 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 60.7 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 60.4 | 10.253.4.52 | (unresolved) |  |  |
| 5 | 45.2 | 10.253.4.2 | (unresolved) |  |  |
| 6 | 132.2 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 126.9 | 2.21.120.90 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 248.8 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 9 | 242.7 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 244.7 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 249.9 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 245.2 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 222.3 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 11. fgeha.gov.pk — probe fasttel.1014872 (1014872)
Verdict: **TROMBONE**, max RTT **218.4ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 5.7 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 7.6 | 10.0.9.60 | (unresolved) |  |  |
| 3 | 9.3 | 10.180.44.217 | (unresolved) |  |  |
| 4 | 8.7 | 59.103.181.90 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 6 | 29.8 | 10.253.4.38 | (unresolved) |  |  |
| 8 | 126.7 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 118.8 | 2.21.120.187 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 10 | 218.4 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 14 | 187.0 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 12. fgeha.gov.pk — probe nova.1015679 (1015679)
Verdict: **TROMBONE**, max RTT **213.8ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.3 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 1.6 | 70.70.71.137 | SHAW - Shaw Communications, CA | CA | _Surrey (PHYSICALLY IMPOSSIBLE at 1.6ms — dropped)_ |
| 3 | 2.4 | 110.93.212.161 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 2.4ms — dropped)_ |
| 4 | 19.6 | 110.93.254.66 | (unresolved) |  | Karachi |
| 5 | 26.5 | 110.93.252.246 | (unresolved) |  | Karachi |
| 6 | 97.5 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 98.3 | 2.21.120.146 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 206.7 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 9 | 207.0 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 209.7 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 208.7 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 205.8 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 213.8 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 13. ztbl.com.pk — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **210.5ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.7 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 25.6 | 10.253.5.94 | (unresolved) |  |  |
| 4 | 25.9 | 10.253.4.40 | (unresolved) |  |  |
| 5 | 26.3 | 10.253.4.2 | (unresolved) |  |  |
| 6 | 111.5 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 124.1 | 2.21.120.171 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 208.3 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 9 | 208.7 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 210.5 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 208.8 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 207.7 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 207.9 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 14. ztbl.com.pk — probe nova.1015679 (1015679)
Verdict: **TROMBONE**, max RTT **210.3ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.3 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 10.4 | 70.70.71.137 | SHAW - Shaw Communications, CA | CA | _Surrey (PHYSICALLY IMPOSSIBLE at 10.4ms — dropped)_ |
| 3 | 11.3 | 110.93.212.161 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 4 | 37.3 | 110.93.252.102 | (unresolved) |  | Karachi |
| 5 | 22.8 | 110.93.252.246 | (unresolved) |  | Karachi |
| 6 | 102.2 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 96.5 | 2.21.120.122 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 210.3 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 9 | 207.0 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 205.0 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 203.5 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 201.8 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 205.5 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 15. fgeha.gov.pk — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **205.3ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.9 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 26.0 | 10.253.5.94 | (unresolved) |  |  |
| 5 | 26.7 | 10.253.4.24 | (unresolved) |  |  |
| 6 | 106.6 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 105.7 | 2.21.120.154 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 203.8 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 9 | 203.7 | 192.168.51.90 | (unresolved) |  |  |
| 10 | 205.3 | 192.168.201.6 | (unresolved) |  |  |
| 11 | 204.7 | 172.16.54.3 | (unresolved) |  |  |
| 12 | 202.5 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 203.6 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 16. networld.pk — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **202.4ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **IT, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.4 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 25.7 | 10.253.5.98 | (unresolved) |  |  |
| 4 | 26.3 | 10.253.4.124 | (unresolved) |  |  |
| 6 | 132.4 | 116.51.17.201 | NTT-DATA-2914 - NTT America, Inc., US | SG | Singapore |
| 7 | 193.1 | 93.186.133.54 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Singapore |
| 8 | 192.4 | 213.144.176.160 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Paris |
| 9 | 202.4 | 213.144.170.13 | SEABONE-NET - TELECOM ITALIA SPARKLE S.p | IT | Rome |
| 10 | 193.7 | 110.93.252.174 | (unresolved) |  | Karachi |
| 11 | 193.5 | 110.93.252.225 | (unresolved) |  | Karachi |
| 12 | 194.2 | 110.93.255.169 | (unresolved) |  | Karachi |
| 13 | 194.5 | 149.40.227.129 | COGENT-174 - Cogent Communications, LLC, | US | Frankfurt am Main |
| 14 | 195.3 | 10.221.198.125 | (unresolved) |  |  |
| 15 | 194.7 | 10.222.180.17 | (unresolved) |  |  |
| 16 | 195.1 | 10.200.107.10 | (unresolved) |  |  |
| 17 | 195.2 | 10.99.99.2 | (unresolved) |  |  |
| 18 | 195.9 | 192.168.80.30 | (unresolved) |  |  |
| 19 | 195.4 | 14.192.150.180 | FARIYA-PK - Fariya Networks Pvt. Ltd., P | PK | Karachi |

---
## 17. ztbl.com.pk — probe fasttel.1014872 (1014872)
Verdict: **TROMBONE**, max RTT **202.3ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 6.4 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 7.4 | 10.0.9.60 | (unresolved) |  |  |
| 3 | 10.0 | 10.180.53.133 | (unresolved) |  |  |
| 4 | 9.9 | 117.20.23.46 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 5 | 28.2 | 110.93.254.110 | (unresolved) |  | Karachi |
| 6 | 29.0 | 110.93.252.136 | (unresolved) |  | Karachi |
| 7 | 110.9 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 117.5 | 2.21.120.177 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 9 | 202.3 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 255 | 181.4 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 18. ztbl.com.pk — probe tes.64078 (64078)
Verdict: **TROMBONE**, max RTT **192.2ms**, exit=SG, transit AS=135407, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.101.1 | (unresolved) |  |  |
| 2 | 1.6 | 192.168.18.1 | (unresolved) |  |  |
| 3 | 3.4 | 45.249.11.241 | TES-PL-AS-AP - Trans World Enterprise Se | PK | Lahore |
| 4 | 3.5 | 119.63.137.130 | (unresolved) |  | Lahore |
| 5 | 23.0 | 110.93.253.98 | (unresolved) |  | Karachi |
| 6 | 22.9 | 110.93.252.136 | (unresolved) |  | Karachi |
| 7 | 102.3 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 102.2 | 2.21.120.57 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 9 | 190.8 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 10 | 190.6 | 192.168.51.90 | (unresolved) |  |  |
| 11 | 192.2 | 192.168.201.6 | (unresolved) |  |  |
| 13 | 192.1 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 14 | 190.6 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 19. ztbl.com.pk — probe tes.64722 (64722)
Verdict: **TROMBONE**, max RTT **187.3ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 2.5 | 45.249.11.249 | TES-PL-AS-AP - Trans World Enterprise Se | PK | _Lahore (PHYSICALLY IMPOSSIBLE at 2.5ms — dropped)_ |
| 3 | 2.3 | 110.93.200.204 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 4 | 3.2 | 110.93.255.168 | (unresolved) |  | Karachi |
| 5 | 3.7 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 78.6 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 78.7 | 2.21.120.146 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 187.3 | 72.52.21.194 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | London |
| 12 | 177.1 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 177.3 | 203.101.184.80 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 20. fgeha.gov.pk — probe tes.64078 (64078)
Verdict: **TROMBONE**, max RTT **179.9ms**, exit=SG, transit AS=135407, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.7 | 192.168.101.1 | (unresolved) |  |  |
| 2 | 1.7 | 192.168.18.1 | (unresolved) |  |  |
| 3 | 3.8 | 45.249.11.241 | TES-PL-AS-AP - Trans World Enterprise Se | PK | Lahore |
| 4 | 3.6 | 119.63.137.130 | (unresolved) |  | Lahore |
| 5 | 22.9 | 110.93.252.84 | (unresolved) |  | Karachi |
| 6 | 23.5 | 110.93.252.246 | (unresolved) |  | Karachi |
| 7 | 99.0 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 98.9 | 2.21.120.90 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 9 | 177.9 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 10 | 178.5 | 192.168.51.90 | (unresolved) |  |  |
| 11 | 179.9 | 192.168.201.6 | (unresolved) |  |  |
| 13 | 178.5 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 14 | 178.0 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 21. fgeha.gov.pk — probe tes.64722 (64722)
Verdict: **TROMBONE**, max RTT **178.7ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **NL, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.1 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 2.2 | 45.249.11.249 | TES-PL-AS-AP - Trans World Enterprise Se | PK | _Lahore (PHYSICALLY IMPOSSIBLE at 2.2ms — dropped)_ |
| 3 | 2.6 | 110.93.200.204 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 4 | 2.7 | 110.93.255.168 | (unresolved) |  | Karachi |
| 5 | 2.9 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 78.6 | 27.111.228.157 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 78.3 | 2.21.120.122 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | NL | Singapore |
| 8 | 178.7 | 72.52.25.142 | PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NE | US | Cambridge |
| 12 | 177.4 | 175.107.33.22 | NTC-AS-AP - National Telecommunication C | PK | Islamabad |
| 13 | 176.4 | 203.101.184.78 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |

---
## 22. toptop.net — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **131.8ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **CA, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.5 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 25.6 | 10.253.5.98 | (unresolved) |  |  |
| 4 | 26.1 | 10.253.4.42 | (unresolved) |  |  |
| 5 | 26.1 | 10.253.4.2 | (unresolved) |  |  |
| 6 | 131.8 | 27.111.230.102 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 119.3 | 162.128.6.58 | (unresolved) |  | Singapore |
| 8 | 119.0 | 162.128.1.147 | ZEN-NET - Zenlayer Inc, US | SG | Singapore |
| 9 | 116.2 | 98.98.230.81 | ZEN-NET - Zenlayer Inc, US | US | Los Angeles |
| 11 | 116.8 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 23. youth.cn — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **115.2ms**, exit=SG, transit AS=PTCL, foreign countries crossed: **CA, SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.5 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 26.2 | 10.253.5.98 | (unresolved) |  |  |
| 4 | 26.6 | 10.253.4.42 | (unresolved) |  |  |
| 5 | 26.2 | 10.253.4.2 | (unresolved) |  |  |
| 6 | 115.2 | 27.111.230.102 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 102.6 | 162.128.6.58 | (unresolved) |  | Singapore |
| 8 | 102.6 | 162.128.1.147 | ZEN-NET - Zenlayer Inc, US | SG | Singapore |
| 9 | 99.8 | 98.98.230.81 | ZEN-NET - Zenlayer Inc, US | US | Los Angeles |
| 11 | 100.1 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 24. efulife.com — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **430.4ms**, exit=US, transit AS=PTCL, foreign countries crossed: **AE, OM**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 6.2 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 10.2 | 10.253.9.146 | (unresolved) |  |  |
| 4 | 27.9 | 10.253.4.74 | (unresolved) |  |  |
| 6 | 430.4 | 206.148.27.235 | GSL - Global Secure Layer, AU |  | **Abroad, site unconfirmed [†]** |
| 11 | 315.8 | 206.148.27.1 | GSL - Global Secure Layer, AU |  | **Equinix Muscat (GSL, via PTR)** _(corrected)_ |
| 12 | 364.2 | 213.202.6.197 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 13 | 284.6 | 134.0.220.234 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 14 | 313.8 | 213.202.7.209 | OMANTEL-AS - Zain Omantel International  | AE | Muscat |
| 15 | 313.0 | 192.168.5.21 | (unresolved) |  |  |
| 16 | 398.0 | 192.168.4.41 | (unresolved) |  |  |
| 17 | 598.6 | 192.168.200.38 | (unresolved) |  |  |
| 18 | 505.6 | 10.15.64.114 | (unresolved) |  |  |
| 19 | 554.6 | 124.29.240.218 | CYBERNET-AP - Cyber Internet Services (P | PK | Karachi |
| 20 | 587.9 | 103.154.196.31 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 22 | 148.5 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |

---
## 25. toptop.net — probe cybernet.1016143 (1016143)
Verdict: **TROMBONE**, max RTT **237.0ms**, exit=SG, transit AS=?, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.2 | 192.168.18.1 | (unresolved) |  |  |
| 2 | 4.2 | 202.163.100.236 | (unresolved) |  | _Lahore (PHYSICALLY IMPOSSIBLE at 4.2ms — dropped)_ |
| 3 | 4.2 | 10.15.15.122 | (unresolved) |  |  |
| 7 | 237.0 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 77.7 | 10.8.253.152 | (unresolved) |  |  |
| 9 | 78.2 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 26. youth.cn — probe zcom.7613 (7613)
Verdict: **TROMBONE**, max RTT **184.4ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.4 | 157.20.147.17 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |
| 2 | 0.7 | 110.93.205.184 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 0.7ms — dropped)_ |
| 3 | 16.3 | 110.93.252.102 | (unresolved) |  | Karachi |
| 4 | 16.2 | 110.93.252.246 | (unresolved) |  | Karachi |
| 5 | 91.6 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 6 | 184.4 | 10.8.253.154 | (unresolved) |  |  |
| 7 | 181.4 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 27. toptop.net — probe zcom.7613 (7613)
Verdict: **TROMBONE**, max RTT **169.6ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.3 | 157.20.147.17 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |
| 2 | 0.7 | 110.93.205.184 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 0.7ms — dropped)_ |
| 3 | 16.1 | 110.93.254.144 | (unresolved) |  | Karachi |
| 4 | 16.3 | 110.93.252.136 | (unresolved) |  | Karachi |
| 5 | 91.5 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 6 | 168.8 | 10.8.253.148 | (unresolved) |  |  |
| 7 | 169.6 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 28. toptop.net — probe nova.1015679 (1015679)
Verdict: **TROMBONE**, max RTT **147.3ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.4 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 1.5 | 70.70.71.137 | SHAW - Shaw Communications, CA | CA | _Surrey (PHYSICALLY IMPOSSIBLE at 1.5ms — dropped)_ |
| 3 | 2.5 | 110.93.212.161 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 2.5ms — dropped)_ |
| 4 | 17.4 | 110.93.252.50 | (unresolved) |  | Karachi |
| 5 | 18.3 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 147.3 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 93.5 | 10.8.253.154 | (unresolved) |  |  |
| 8 | 99.0 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 29. youth.cn — probe orbit.64535 (64535)
Verdict: **TROMBONE**, max RTT **146.3ms**, exit=SG, transit AS=174, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 3.7 | 10.14.14.10 | (unresolved) |  |  |
| 4 | 5.6 | 172.29.244.9 | (unresolved) |  |  |
| 5 | 4.3 | 149.40.227.42 | COGENT-174 - Cogent Communications, LLC, | US | _Frankfurt am Main (PHYSICALLY IMPOSSIBLE at 4.3ms — dropped)_ |
| 6 | 21.1 | 110.93.255.176 | (unresolved) |  | Karachi |
| 7 | 21.3 | 110.93.252.246 | (unresolved) |  | Karachi |
| 8 | 96.4 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 145.6 | 10.8.253.148 | (unresolved) |  |  |
| 10 | 146.3 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 30. toptop.net — probe orbit.64535 (64535)
Verdict: **TROMBONE**, max RTT **126.1ms**, exit=SG, transit AS=174, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 3.9 | 10.14.14.10 | (unresolved) |  |  |
| 4 | 4.0 | 172.29.244.9 | (unresolved) |  |  |
| 5 | 4.2 | 149.40.227.42 | COGENT-174 - Cogent Communications, LLC, | US | _Frankfurt am Main (PHYSICALLY IMPOSSIBLE at 4.2ms — dropped)_ |
| 6 | 21.5 | 110.93.254.124 | (unresolved) |  | Karachi |
| 7 | 19.6 | 110.93.252.246 | (unresolved) |  | Karachi |
| 8 | 96.6 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 126.1 | 10.8.253.148 | (unresolved) |  |  |
| 10 | 125.5 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 31. kknetworks.com.pk — probe cybernet.1016036 (1016036)
Verdict: **TROMBONE**, max RTT **121.1ms**, exit=SG, transit AS=9541, foreign countries crossed: **SG, US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.1.1 | (unresolved) |  |  |
| 2 | 2.1 | 203.101.189.254 | CYBERNET-AP - Cyber Internet Services (P | PK | Islamabad |
| 3 | 3.7 | 192.168.72.113 | (unresolved) |  |  |
| 4 | 3.6 | 192.168.51.2 | (unresolved) |  |  |
| 5 | 24.8 | 202.163.97.213 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |
| 6 | 24.8 | 192.168.4.17 | (unresolved) |  |  |
| 8 | 105.0 | 27.111.230.138 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 104.6 | 110.93.252.247 | (unresolved) |  | Karachi |
| 10 | 118.7 | 110.93.252.103 | (unresolved) |  | Karachi |
| 11 | 120.9 | 149.40.227.121 | COGENT-174 - Cogent Communications, LLC, | US | Frankfurt am Main |
| 12 | 121.1 | 172.29.50.62 | (unresolved) |  |  |
| 13 | 120.1 | 103.163.48.205 | KKNETWROK-AS-AP - KK Networks (Pvt) Ltd. | PK | Lahore |

---
## 32. youth.cn — probe nova.1015679 (1015679)
Verdict: **TROMBONE**, max RTT **100.6ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.3 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 3.4 | 70.70.71.137 | SHAW - Shaw Communications, CA | CA | _Surrey (PHYSICALLY IMPOSSIBLE at 3.4ms — dropped)_ |
| 3 | 1.8 | 110.93.212.161 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 1.8ms — dropped)_ |
| 4 | 17.8 | 110.93.252.50 | (unresolved) |  | Karachi |
| 5 | 17.9 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 100.6 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 100.5 | 10.8.253.148 | (unresolved) |  |  |
| 8 | 96.6 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 33. youth.cn — probe tes.64722 (64722)
Verdict: **TROMBONE**, max RTT **82.7ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.1 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 2.7 | 45.249.11.249 | TES-PL-AS-AP - Trans World Enterprise Se | PK | _Lahore (PHYSICALLY IMPOSSIBLE at 2.7ms — dropped)_ |
| 3 | 2.7 | 110.93.200.204 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 4 | 3.3 | 110.93.255.168 | (unresolved) |  | Karachi |
| 5 | 3.1 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 78.7 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 82.7 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 34. youth.cn — probe cybernet.1016143 (1016143)
Verdict: **TROMBONE**, max RTT **79.5ms**, exit=SG, transit AS=?, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.2 | 192.168.18.1 | (unresolved) |  |  |
| 2 | 4.0 | 202.163.100.236 | (unresolved) |  | _Lahore (PHYSICALLY IMPOSSIBLE at 4.0ms — dropped)_ |
| 3 | 4.2 | 10.15.15.122 | (unresolved) |  |  |
| 7 | 77.7 | 192.168.98.14 | (unresolved) |  |  |
| 8 | 78.6 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 78.0 | 10.8.253.148 | (unresolved) |  |  |
| 10 | 79.5 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 35. toptop.net — probe cybernet.1016154 (1016154)
Verdict: **TROMBONE**, max RTT **78.8ms**, exit=SG, transit AS=?, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.18.1 | (unresolved) |  |  |
| 2 | 3.2 | 202.163.100.245 | (unresolved) |  | _Lahore (PHYSICALLY IMPOSSIBLE at 3.2ms — dropped)_ |
| 7 | 76.9 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 78.8 | 10.8.253.150 | (unresolved) |  |  |
| 9 | 78.7 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 36. toptop.net — probe tes.64722 (64722)
Verdict: **TROMBONE**, max RTT **78.6ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.4 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 2.4 | 45.249.11.249 | TES-PL-AS-AP - Trans World Enterprise Se | PK | _Lahore (PHYSICALLY IMPOSSIBLE at 2.4ms — dropped)_ |
| 3 | 2.5 | 110.93.200.204 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 4 | 3.1 | 110.93.255.168 | (unresolved) |  | Karachi |
| 5 | 3.3 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 78.6 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 78.6 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 37. youth.cn — probe cybernet.1016154 (1016154)
Verdict: **TROMBONE**, max RTT **78.3ms**, exit=SG, transit AS=?, foreign countries crossed: **CA, SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.18.1 | (unresolved) |  |  |
| 2 | 3.0 | 202.163.100.245 | (unresolved) |  | _Lahore (PHYSICALLY IMPOSSIBLE at 3.0ms — dropped)_ |
| 7 | 76.5 | 27.111.231.71 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 8 | 78.3 | 10.8.253.150 | (unresolved) |  |  |
| 9 | 77.7 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
# B. Single foreign-country hairpins

## 1. sonic.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **481.1ms**, exit=?, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 6.1 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 13.9 | 10.253.9.150 | (unresolved) |  |  |
| 5 | 28.4 | 10.253.4.4 | (unresolved) |  |  |
| 7 | 30.7 | 172.69.244.93 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 8 | 30.5 | 172.69.244.93 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 9 | 30.8 | 172.69.244.93 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 142.7 | 10.200.107.174 | (unresolved) |  |  |
| 11 | 154.6 | 10.200.201.37 | (unresolved) |  |  |
| 12 | 145.4 | 10.200.237.10 | (unresolved) |  |  |
| 13 | 621.2 | 172.28.159.5 | (unresolved) |  |  |
| 14 | 481.1 | 119.160.105.77 | Mobilink-Peering-AS-PK - IX Peering for  | PK | Model Town |

---
## 2. trax.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **453.6ms**, exit=?, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 6.4 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 13.8 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 27.5 | 10.253.4.52 | (unresolved) |  |  |
| 5 | 28.6 | 10.253.4.4 | (unresolved) |  |  |
| 7 | 27.6 | 172.69.244.92 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 8 | 27.6 | 172.69.244.92 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 9 | 27.8 | 172.69.244.92 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 131.6 | 10.200.107.174 | (unresolved) |  |  |
| 11 | 143.8 | 10.200.201.37 | (unresolved) |  |  |
| 12 | 134.3 | 10.200.237.10 | (unresolved) |  |  |
| 13 | 665.6 | 172.28.159.5 | (unresolved) |  |  |
| 14 | 453.6 | 119.160.105.78 | Mobilink-AS-PK - PMCL /LDI IP TRANSIT, P | PK | Model Town |

---
## 3. mepco.com.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **427.1ms**, exit=US, transit AS=PTCL, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 266.3 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 266.4 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 534.3 | 10.253.8.24 | (unresolved) |  |  |
| 5 | 427.1 | 119.63.137.48 | (unresolved) |  | Lahore |
| 6 | 414.3 | 149.40.227.93 | COGENT-174 - Cogent Communications, LLC, | US | Frankfurt am Main |

---
## 4. kknetworks.com.pk — probe ptcl.1016393 (1016393)
Verdict: **TROMBONE**, max RTT **417.0ms**, exit=US, transit AS=PTCL, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.9 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 346.4 | 39.45.64.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Mianwali |
| 3 | 417.0 | 10.253.9.150 | (unresolved) |  |  |
| 4 | 267.7 | 10.253.8.24 | (unresolved) |  |  |
| 5 | 247.4 | 119.63.137.48 | (unresolved) |  | Lahore |
| 6 | 206.9 | 149.40.227.121 | COGENT-174 - Cogent Communications, LLC, | US | Frankfurt am Main |
| 7 | 221.8 | 172.29.50.62 | (unresolved) |  |  |
| 8 | 244.4 | 103.163.48.205 | KKNETWROK-AS-AP - KK Networks (Pvt) Ltd. | PK | Lahore |

---
## 5. efulife.com — probe zcom.7613 (7613)
Verdict: **TROMBONE**, max RTT **251.7ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.4 | 157.20.147.17 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |
| 2 | 0.7 | 110.93.205.184 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 0.7ms — dropped)_ |
| 3 | 16.4 | 110.93.252.102 | (unresolved) |  | Karachi |
| 4 | 16.3 | 110.93.252.246 | (unresolved) |  | Karachi |
| 5 | 155.5 | 27.111.230.181 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 6 | 220.2 | 192.168.98.1 | (unresolved) |  |  |
| 7 | 221.9 | 192.168.4.41 | (unresolved) |  |  |
| 8 | 165.9 | 192.168.200.38 | (unresolved) |  |  |
| 9 | 168.1 | 10.15.64.114 | (unresolved) |  |  |
| 10 | 167.8 | 124.29.240.218 | CYBERNET-AP - Cyber Internet Services (P | PK | Karachi |
| 11 | 250.2 | 103.154.196.31 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 12 | 166.6 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 13 | 251.7 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |

---
## 6. trax.pk — probe fasttel.1014872 (1014872)
Verdict: **TROMBONE**, max RTT **238.9ms**, exit=?, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 6.8 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 7.9 | 10.0.9.60 | (unresolved) |  |  |
| 3 | 9.8 | 10.180.44.217 | (unresolved) |  |  |
| 4 | 9.2 | 59.103.181.90 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 5 | 9.4 | 10.253.12.24 | (unresolved) |  |  |
| 6 | 29.8 | 10.253.4.18 | (unresolved) |  |  |
| 7 | 23.7 | 10.253.4.4 | (unresolved) |  |  |
| 9 | 29.8 | 172.69.244.98 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 31.6 | 172.69.244.98 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 11 | 30.5 | 172.69.244.98 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 12 | 126.7 | 10.200.107.174 | (unresolved) |  |  |
| 13 | 126.5 | 10.200.201.37 | (unresolved) |  |  |
| 14 | 128.8 | 10.200.237.10 | (unresolved) |  |  |
| 16 | 238.9 | 119.160.105.78 | Mobilink-AS-PK - PMCL /LDI IP TRANSIT, P | PK | Model Town |
| 18 | 136.9 | 119.160.105.78 | Mobilink-AS-PK - PMCL /LDI IP TRANSIT, P | PK | Model Town |

---
## 7. zcomnetworks.com.pk — probe cybernet.1016036 (1016036)
Verdict: **TROMBONE**, max RTT **211.4ms**, exit=HK, transit AS=9541, foreign countries crossed: **HK**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.7 | 192.168.1.1 | (unresolved) |  |  |
| 2 | 2.1 | 203.101.189.254 | CYBERNET-AP - Cyber Internet Services (P | PK | Islamabad |
| 3 | 3.7 | 192.168.72.113 | (unresolved) |  |  |
| 5 | 24.9 | 202.163.97.213 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |
| 6 | 25.5 | 192.168.4.61 | (unresolved) |  |  |
| 11 | 189.2 | 223.121.3.98 | CMI-INT-HK - China Mobile International  | HK | Kwai Chung |
| 12 | 187.8 | 110.93.252.247 | (unresolved) |  | Karachi |
| 13 | 211.4 | 110.93.254.67 | (unresolved) |  | Karachi |
| 14 | 140.9 | 110.93.205.185 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | Karachi |
| 15 | 120.7 | 157.20.147.244 | ZCOMNETWORKS-AS-AP - Z COM NETWORKS, PK | PK | Lahore |

---
## 8. youth.cn — probe cybernet.1016036 (1016036)
Verdict: **TROMBONE**, max RTT **197.7ms**, exit=CA, transit AS=9541, foreign countries crossed: **CA**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.7 | 192.168.1.1 | (unresolved) |  |  |
| 2 | 2.1 | 203.101.189.254 | CYBERNET-AP - Cyber Internet Services (P | PK | Islamabad |
| 3 | 3.7 | 192.168.72.113 | (unresolved) |  |  |
| 5 | 24.8 | 202.163.97.213 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |
| 6 | 24.8 | 192.168.4.61 | (unresolved) |  |  |
| 11 | 197.7 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 9. toptop.net — probe cybernet.1016036 (1016036)
Verdict: **TROMBONE**, max RTT **192.7ms**, exit=CA, transit AS=9541, foreign countries crossed: **CA**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.7 | 192.168.1.1 | (unresolved) |  |  |
| 2 | 2.1 | 203.101.189.254 | CYBERNET-AP - Cyber Internet Services (P | PK | Islamabad |
| 3 | 3.6 | 192.168.72.113 | (unresolved) |  |  |
| 5 | 25.2 | 202.163.97.213 | CYBERNET-AP - Cyber Internet Services (P | PK | Lahore |
| 6 | 24.9 | 192.168.4.65 | (unresolved) |  |  |
| 11 | 192.7 | 153.43.76.226 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
## 10. efulife.com — probe orbit.64535 (64535)
Verdict: **TROMBONE**, max RTT **176.7ms**, exit=SG, transit AS=174, foreign countries crossed: **SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.7 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 4.2 | 10.14.14.10 | (unresolved) |  |  |
| 4 | 5.2 | 172.29.244.9 | (unresolved) |  |  |
| 5 | 4.9 | 149.40.227.42 | COGENT-174 - Cogent Communications, LLC, | US | _Frankfurt am Main (PHYSICALLY IMPOSSIBLE at 4.9ms — dropped)_ |
| 6 | 19.7 | 110.93.252.124 | (unresolved) |  | Karachi |
| 7 | 19.4 | 110.93.252.136 | (unresolved) |  | Karachi |
| 8 | 109.1 | 27.111.230.181 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 9 | 174.0 | 192.168.98.25 | (unresolved) |  |  |
| 10 | 175.5 | 192.168.4.14 | (unresolved) |  |  |
| 12 | 172.6 | 10.15.64.114 | (unresolved) |  |  |
| 13 | 172.4 | 124.29.240.218 | CYBERNET-AP - Cyber Internet Services (P | PK | Karachi |
| 14 | 176.7 | 103.154.196.31 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 16 | 173.5 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |

---
## 11. sonic.pk — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **166.9ms**, exit=US, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.0 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.9 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 28.5 | 10.253.5.98 | (unresolved) |  |  |
| 4 | 28.0 | 10.253.4.124 | (unresolved) |  |  |
| 5 | 26.8 | 10.253.4.22 | (unresolved) |  |  |
| 7 | 50.5 | 172.69.244.96 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 8 | 26.7 | 172.69.244.96 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 9 | 27.1 | 172.69.244.96 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 149.7 | 10.200.107.174 | (unresolved) |  |  |
| 11 | 151.8 | 10.200.201.37 | (unresolved) |  |  |
| 12 | 152.4 | 10.200.237.10 | (unresolved) |  |  |
| 13 | 166.9 | 172.28.158.5 | (unresolved) |  |  |
| 14 | 153.8 | 119.160.105.77 | Mobilink-Peering-AS-PK - IX Peering for  | PK | Model Town |

---
## 12. trax.pk — probe ptcl.1016126 (1016126)
Verdict: **TROMBONE**, max RTT **144.5ms**, exit=?, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.8 | 192.168.10.1 | (unresolved) |  |  |
| 2 | 25.3 | 39.39.0.1 | PKTELECOM-AS-PK - Pakistan Telecommunica | PK | Karachi |
| 3 | 26.1 | 10.253.5.98 | (unresolved) |  |  |
| 4 | 26.0 | 10.253.4.124 | (unresolved) |  |  |
| 5 | 26.7 | 10.253.4.22 | (unresolved) |  |  |
| 7 | 27.3 | 172.69.244.84 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 8 | 26.7 | 172.69.244.84 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 9 | 26.4 | 172.69.244.84 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 141.4 | 10.200.107.174 | (unresolved) |  |  |
| 11 | 143.6 | 10.200.201.37 | (unresolved) |  |  |
| 12 | 142.4 | 10.200.237.10 | (unresolved) |  |  |
| 13 | 144.5 | 172.28.158.5 | (unresolved) |  |  |
| 14 | 143.9 | 119.160.105.78 | Mobilink-AS-PK - PMCL /LDI IP TRANSIT, P | PK | Model Town |

---
## 13. sonic.pk — probe fasttel.1014872 (1014872)
Verdict: **TROMBONE**, max RTT **140.8ms**, exit=?, transit AS=14789, foreign countries crossed: **US**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 6.3 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 7.4 | 10.0.9.60 | (unresolved) |  |  |
| 5 | 9.4 | 10.253.12.46 | (unresolved) |  |  |
| 6 | 30.2 | 10.253.4.38 | (unresolved) |  |  |
| 7 | 29.4 | 10.253.4.22 | (unresolved) |  |  |
| 9 | 30.4 | 172.69.244.100 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 10 | 29.8 | 172.69.244.100 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 11 | 30.5 | 172.69.244.100 | CLOUDFLARENET - Cloudflare, Inc., US | US | Karachi |
| 12 | 135.1 | 10.200.107.174 | (unresolved) |  |  |
| 13 | 135.6 | 10.200.201.37 | (unresolved) |  |  |
| 14 | 135.2 | 10.200.237.10 | (unresolved) |  |  |
| 16 | 140.8 | 119.160.105.77 | Mobilink-Peering-AS-PK - IX Peering for  | PK | Model Town |
| 19 | 133.2 | 119.160.105.77 | Mobilink-Peering-AS-PK - IX Peering for  | PK | Model Town |

---
## 14. efulife.com — probe nova.1015679 (1015679)
Verdict: **TROMBONE**, max RTT **118.3ms**, exit=SG, transit AS=Transworld, foreign countries crossed: **SG**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 0.4 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 4.4 | 70.70.71.137 | SHAW - Shaw Communications, CA | CA | _Surrey (PHYSICALLY IMPOSSIBLE at 4.4ms — dropped)_ |
| 3 | 4.9 | 110.93.212.161 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 4.9ms — dropped)_ |
| 4 | 21.3 | 110.93.252.48 | (unresolved) |  | Karachi |
| 5 | 24.1 | 110.93.252.136 | (unresolved) |  | Karachi |
| 6 | 100.6 | 27.111.230.181 | (unresolved) |  | **Equinix Singapore** _(corrected)_ |
| 7 | 109.6 | 192.168.98.5 | (unresolved) |  |  |
| 8 | 104.5 | 192.168.4.2 | (unresolved) |  |  |
| 9 | 113.8 | 192.168.200.34 | (unresolved) |  |  |
| 10 | 107.5 | 10.15.64.114 | (unresolved) |  |  |
| 11 | 118.3 | 124.29.240.218 | CYBERNET-AP - Cyber Internet Services (P | PK | Karachi |
| 12 | 114.7 | 103.154.196.31 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |
| 14 | 98.7 | 103.154.196.33 | EFULIFEAssuranceLtd-AS-AP - EFU LIFE Ass | PK | Karachi |

---
## 15. youth.cn — probe fasttel.1014872 (1014872)
Verdict: **TROMBONE**, max RTT **107.2ms**, exit=CA, transit AS=Transworld, foreign countries crossed: **CA**

| hop | rtt(ms) | ip | asn (raw ip-api) | country | location |
|---|---|---|---|---|---|
| 1 | 1.2 | 192.168.100.1 | (unresolved) |  |  |
| 2 | 2.7 | 10.0.9.60 | (unresolved) |  |  |
| 3 | 5.8 | 10.180.53.133 | (unresolved) |  |  |
| 4 | 4.7 | 117.20.23.46 | TWA-AS-AP - Transworld Associates (Pvt.) | PK | _Karachi (PHYSICALLY IMPOSSIBLE at 4.7ms — dropped)_ |
| 5 | 23.2 | 110.93.253.182 | (unresolved) |  | Karachi |
| 6 | 23.9 | 110.93.252.246 | (unresolved) |  | Karachi |
| 9 | 107.2 | 153.43.76.237 | ML-1432-54994 - Meteverse Limited., CA | CA | Singapore |

---
_...and 19 more single-country hairpins not shown (full set filterable from the snapshot file)._
