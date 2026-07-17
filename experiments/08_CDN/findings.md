# Experiment 08: CDN Peering at PIE Karachi

## Overview

This experiment investigates whether CDN networks connected to PIE Karachi (Pakistan's DE-CIX-operated internet exchange) are actually reachable through the exchange, and quantifies the RTT inequality across Pakistani ISPs caused by private peering arrangements versus public exchange peering.

---

## Background

PIE Karachi is an internet exchange point operated by DE-CIX in partnership with PTCL, located inside PTCL's Misri Shah data centre in Karachi. According to PeeringDB, PIE Karachi has 9 active members including PTCL (100G port), ACE CDN/Tencent EdgeOne (20G), Zenlayer (10G), Connect Communications (30G), Telenor Pakistan, and Ufone. The DE-CIX looking glass confirms all BGP sessions are operationally active — routes are being exchanged between members.

ACE CDN (AS139341) is Tencent's global EdgeOne content delivery network, headquartered in Singapore with over 5,000 IPv4 prefixes globally and presence at 124 internet exchanges. It is listed at PIE Karachi with IP address 58.181.127.4 on a 20G port with an open peering policy.

---

## Experiment 08.1: Does PIE Karachi Appear in Traceroutes to ACE CDN?

We ran traceroutes from PTCL Karachi (probe 1016126) and Nayatel ISB (probe 60223) to three ACE CDN IP addresses (43.132.69.1, 43.132.69.2, 43.132.69.100) and checked whether PIE Karachi's peering LAN (58.181.127.0/24) appeared in any path.

**Result:** PIE Karachi's peering LAN did not appear in any of the six traceroutes. Instead, both PTCL and Nayatel reached ACE CDN through 119.153.112.158, which belongs to PTCL (AS17557, prefix 119.153.112.0/24, PK, APNIC). ACE CDN was reachable at approximately 25ms from both probes.

**Interpretation:** PTCL has a private direct connection to ACE CDN inside its own network infrastructure — likely inside PTCL's Misri Shah data centre where PIE Karachi is also located. Despite both PTCL and ACE CDN being physically present at PIE Karachi, their traffic exchange bypasses PIE's shared switching fabric and uses a private bilateral connection instead.

---

## Experiment 08.2: Does PIE Karachi Appear for Inter-ISP Traffic?

We tested whether PIE Karachi is used for traffic between two of its Pakistani ISP members: PTCL (58.181.127.1) and Connect Communications (58.181.127.10, AS132165). We traced from PTCL Karachi and Nayatel to Connect Communications IP addresses (115.42.64.1, 113.203.207.1).

**Result:** PIE Karachi did not appear in any path. Both PTCL and Nayatel reached Connect Communications through 119.159.224.18 and 119.159.240.166, both belonging to PTCL (AS17557). Connect Communications was reachable at 26ms.

**Interpretation:** Even for inter-ISP traffic between two confirmed PIE Karachi members, the shared exchange fabric is bypassed. PTCL routes Connect Communications traffic through its own private backbone.

---

## Experiment 08.3: Does PKIX Lahore Appear for ISP-to-ISP Traffic?

We tested whether PKIX Lahore (peering LAN 100.128.0.0/24) is used for traffic between Zcom (AS152605) and Transworld (AS38193), both confirmed PKIX Lahore members. We traced from Zcom (probe 7613) and Nayatel (probe 60223) to Transworld IP addresses (110.93.215.1, 110.93.250.1).

**Result:** PKIX Lahore did not appear in any path. Zcom reached Transworld at hop 2 through 110.93.205.184 (AS38193, Transworld), indicating a direct private connection. RTT was 17-20ms.

**Interpretation:** Zcom has a direct private peering arrangement with Transworld that bypasses PKIX Lahore entirely, despite both being members. The IXP membership exists on paper but traffic takes a private path.

---

## Experiment 08.4: RTT to ACE CDN Across All Probes

We ran traceroutes from all 7 probes to ACE CDN (43.132.69.1 and 43.132.69.2) to quantify RTT inequality across Pakistani ISPs.

| Probe | RTT to ACE CDN | Path |
|---|---|---|
| PTCL Lahore | 23–25ms | Through PTCL private connection |
| Nayatel ISB | 23ms | Through Transworld → PTCL private connection |
| PTCL Karachi | 26–70ms | Through PTCL (variable) |
| Nova Lahore | 100–112ms | Exits Pakistan |
| Zcom Lahore | 107–113ms | Exits Pakistan |
| Transworld Lahore | 113ms | Exits Pakistan |
| Cybernet Haroonabad | 255ms | Far international (Singapore/HK) |

**Key finding:** The same CDN (ACE CDN/Tencent EdgeOne) is reachable at 23ms for PTCL and Nayatel customers, and at 255ms for Cybernet customers — an 11x RTT difference. This disparity is entirely caused by private peering arrangements. PTCL has a direct private connection to ACE CDN inside its own infrastructure. ISPs that route through PTCL (like Nayatel) inherit this benefit indirectly. ISPs that do not use PTCL as a transit provider (like Cybernet, which owns its own PEACE submarine cable) exit Pakistan entirely to reach the same CDN.

---

## Summary of Findings

Across three separate experiments covering PIE Karachi and PKIX Lahore, the pattern is consistent:

1. Pakistani IXPs are operationally active — BGP sessions are up, routes are exchanged, members are physically connected.
2. Despite this, actual user traffic between IXP members does not flow through the shared exchange fabric. Members use private bilateral connections instead.
3. CDN traffic that could be served locally through PIE Karachi is instead served through PTCL's private infrastructure, creating a two-tier system: ISPs with PTCL upstream relationships get local CDN latency (~23ms), while ISPs without such relationships pay international latency (100–255ms) for the same content.

If ACE CDN were to peer at PKIX — which has 13–22 members at each of three Pakistani cities — all member ISPs would achieve local latency to ACE CDN simultaneously, rather than only those with a private PTCL arrangement. The RTT saving for Cybernet customers alone would be approximately 230ms per request to any ACE CDN hosted content.

---

## Measurement Details

- **Probes used:** 1016126 (PTCL Karachi), 60223 (Nayatel ISB), 7613 (Zcom Lahore), 1015679 (Nova Lahore), 1016036 (Cybernet Haroonabad), 62224 (Transworld Lahore), 7764 (PTCL Lahore)
- **Platform:** RIPE Atlas one-off traceroute measurements
- **Protocol:** ICMP Paris traceroute
- **Date:** July 15, 2026
- **PIE Karachi peering LAN:** 58.181.127.0/24
- **PKIX Lahore peering LAN:** 100.128.0.0/24
- **ACE CDN ASN:** AS139341 (Tencent EdgeOne)
- **Connect Communications ASN:** AS132165
- **Transworld ASN:** AS38193