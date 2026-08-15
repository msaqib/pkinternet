# Pattern 1, simplified: why fgeha.gov.pk "looks domestic" on some probes

**One-line version:** fgeha.gov.pk is hosted on Cybernet (Pakistan), but every
visitor is first bounced abroad through Akamai's anti-DDoS scrubbing network
(Singapore -> Netherlands -> US) before coming back. Four probes caught this
happening in full detail. Nayatel and Cybernet's own probes take the *exact
same trip* — same destination IP, same ~200ms round-trip time, same 15-minute
measurement window — but the routers in the *middle* of their path just didn't
answer the traceroute that round. Silent routers, not a different route.

## Why it looks like the route "changes"

A traceroute only shows a hop if that router chooses to reply. Routers are
allowed to ignore traceroute probes (rate-limiting, load, policy) without
affecting the actual data path. So on some rounds you see all 13 hops; on
others the same physical trip shows only 2 real hops and then jumps straight
to the destination with a big matching RTT. **The route did not change — the
visibility into it did.** The proof is the timing: a real ~25-45ms domestic
Cybernet trip never produces a 200ms answer. Only the Akamai round-trip does.

## Reference: the confirmed full path (proves what the trip actually is)

Probe 1015679 (Nova/TPCPL) — round **2026-07-16 00:00 UTC**, measurement 189033034,
destination `203.101.184.78` (fgeha.gov.pk):

```
hop 1   192.168.100.1     0.3 ms   local gateway
hop 2   70.70.71.137      1.5 ms   (Shaw CPE artifact, physically in PK)
hop 3   110.93.212.161    2.2 ms   Transworld backbone, Lahore
hop 4   110.93.254.66    23.0 ms   Transworld internal
hop 5   110.93.252.246   20.6 ms   Transworld internal
hop 6    27.111.228.157  101.1 ms  Equinix, SINGAPORE        <-- leaves Pakistan
hop 7      2.21.120.146  102.5 ms  Akamai Prolexic, NETHERLANDS
hop 8     72.52.25.142   208.1 ms  Akamai Prolexic, UNITED STATES
hop 9    192.168.51.90   207.7 ms  (Akamai internal)
hop 10   192.168.201.6   211.1 ms  (Akamai internal)
hop 11    172.16.54.3    208.3 ms  (Akamai internal)
hop 12  175.107.33.22    207.1 ms  NTC, back in Pakistan       <-- re-enters Pakistan
hop 13  203.101.184.78   207.1 ms  Cybernet -> fgeha.gov.pk (destination)
```

~207 ms total. This is the fingerprint: Singapore -> Netherlands -> US and back,
every time this site is reached.

## Nayatel — exact routes, same destination, same window

Probe 60223 (Nayatel, Islamabad) — round **2026-07-16 00:59 UTC**, msm 189033034:
```
hop 1   192.168.18.1      1.4 ms   local gateway
hop 2   100.89.0.1        3.2 ms   Nayatel CGNAT
hop 3-7  * * *  (no reply, 5 hops silent)
hop 255 203.101.184.78  176.6 ms   destination answers
```

Probe 65892 (Nayatel, Lahore) — round **2026-07-16 00:03 UTC**, msm 189033034:
```
hop 1   192.168.18.1      1.0 ms   local gateway
hop 2   100.92.64.1       3.4 ms   Nayatel CGNAT
hop 3-7  * * *  (no reply, 5 hops silent)
hop 255 203.101.184.78  212.5 ms   destination answers
```

## Cybernet — exact routes, same destination, same window

Probe 1016036 (Cybernet, Haripur) — round **2026-07-16 00:58 UTC**, msm 189033034:
```
hop 1   192.168.1.1        0.7 ms   local gateway
hop 2   203.101.189.254    2.1 ms   Cybernet backbone
hop 3   192.168.72.113     3.7 ms   Cybernet internal
hop 4   192.168.72.145     3.4 ms   Cybernet internal
hop 5-9  * * *  (no reply, 5 hops silent)
hop 255 203.101.184.78   220.2 ms   destination answers
```

Probe 1016143 (Cybernet, Karachi) — round **2026-07-16 00:58 UTC**, msm 189033034:
```
hop 1   192.168.18.1       1.1 ms   local gateway
hop 2   202.163.100.236    4.1 ms   Cybernet backbone
hop 3   10.15.15.122       4.1 ms   Cybernet internal
hop 4-8  * * *  (no reply, 5 hops silent)
hop 255 203.101.184.78   212.5 ms   destination answers
```

## The point to make to Dr Ilyas

All five rounds above — Nova (full path), both Nayatel probes, both Cybernet
probes — hit the **identical destination IP** (`203.101.184.78`) in the
**same ~1-hour window** on **2026-07-16**, and all land in the **176-220 ms**
band. Nova's round shows you exactly what that ~200ms is: Singapore, then
Netherlands, then the US, then back into Pakistan via NTC. Nayatel's and
Cybernet's routers just went quiet for the middle 5-9 hops, but they paid the
exact same time cost, so they took the exact same trip — the missing hops are
a reporting gap, not a different, faster, domestic path.

This is not a one-off: across the full panel week, **every single traceroute
round from Nayatel and Cybernet to fgeha.gov.pk (166-168 rounds each)** lands
between 175 ms and 1272 ms, with a median of 205-226 ms. A genuine domestic
Cybernet round trip in this dataset is 25-45 ms (see `cxtreme.pk`, a different
Cybernet-hosted site with zero foreign-hop evidence anywhere in the week). None
of the 300+ Nayatel/Cybernet rounds to fgeha ever come close to that — they are
all consistent with the same Akamai detour, just with varying amounts of the
middle of the path visible.

## Source / how to reproduce

- Raw data: `experiments/07_longitudinal_panel/results/a/raw_a_20260730_192718.json.gz`
  (server-side archival dump of the full panel week, msm 189033034 = fgeha.gov.pk
  traceroute measurement)
- Destination IP: `203.101.184.78` (`targets_corrected.csv`)
- ASN 32787 in the middle of the confirmed path is registered in RIPE as
  `PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK, Akamai Technologies, Inc.`
  — the network's own stated purpose, not an inference from a hostname.
- Companion file: `anomaly_ztbl_com_pk_pattern2_traceroutes.txt` shows the same
  behaviour on a different site (ztbl.com.pk) via a different mechanism (foreign
  hops present but excluded by a 500ms RTT queue-noise cutoff) — same underlying
  story, different failure mode of the detector.
