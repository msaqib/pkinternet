# EFU Life via Globalping -- 7 Pakistani ISP vantages, live 2026-09-01/02

Source: Globalping (globalping.io), a separate, non-RIPE-Atlas measurement network.
Only `eyeball-network`-tagged probes used (real ISP customer connections, per the
data-quality check already established in `globalping_colo_confirmed.md`; the
`datacenter-network`-tagged PK probes -- 2E Telekomunikasyon, Virtury Cloud x3,
BrainStorm -- were excluded). One traceroute per network, target 103.154.196.33
(efulife.com), ICMP. Raw output: `globalping_raw.json`.

## Result

| ISP | City | max RTT | Path |
|---|---|--:|---|
| Sharp Telecom | Karachi | **4.6 ms** | direct, all-domestic |
| LEAP DIGITALS | Arifwala | 43.5 ms | all-domestic, via Transworld-style backbone |
| IN CABLE INTERNET | Lahore | 109.2 ms | hairpin: GSL Singapore -> Omantel |
| Fariya Networks | Karachi | 120.5 ms | hairpin: GSL Singapore -> Omantel |
| FASTTEL BROADBAND | Rawalpindi | 121.4 ms | hairpin: GSL Singapore -> Omantel |
| PTCL | Lahore | 125.4 ms | hairpin: GSL Singapore -> Omantel |
| Nayatel | Islamabad | 113.4 ms | all-domestic (but see anomaly note) |

Every path, domestic or hairpin, still ends at the same `124.29.240.218` (Cybernet)
doorway immediately before EFU Life, same as every RIPE Atlas probe checked earlier.

## The main new finding: the hairpin isn't PTCL-specific

**4 of these 7 ISPs (PTCL, Fariya Networks, IN CABLE INTERNET, FASTTEL BROADBAND) all
route through the exact same three hops**, in the exact same order, that the RIPE
Atlas PTCL-Karachi trace used:

```
206.148.27.235  ("Abroad, site unconfirmed" -- see prior correction)
  -> 206.148.22.141  (Equinix Singapore -- confirmed on its own PTR, same as before)
    -> 160.202.164.165  ("Abroad, site unconfirmed" -- see prior correction)
      -> [Zain Omantel block, 213.202.x.x / 134.0.220.x]  (Oman -- RDAP-confirmed
         country, city unconfirmed, see prior correction)
        -> 124.29.240.218 (Cybernet) -> EFU Life
```

Three of these four ISPs (Fariya Networks, IN CABLE INTERNET, FASTTEL BROADBAND) have
**no RIPE Atlas presence in this project at all** -- this is the first time they've
been checked against this destination. That the same specific GSL-Singapore-then-
Omantel chain shows up independently across four unrelated ISPs, not just PTCL, is
new: it means this specific intermediary path is a shared chokepoint multiple
Pakistani networks route through to reach EFU Life, not a PTCL-only quirk.

Location labels above follow the same corrected standard established earlier this
session for these exact IPs (`206.148.27.235`, `206.148.22.141`, `160.202.164.165`
recur verbatim; the Omantel-block IPs differ per trace but are the same `/21`/`/22`
blocks already RDAP-checked as `country: OM`). No new geolocation claims are made
here beyond what was already verified; do not re-introduce "Muscat" or "Los Angeles"
if extending this table.

## Two things worth flagging, not yet explained

1. **Sharp Telecom, Karachi: 4.6ms.** The fastest vantage found in this entire
   investigation, RIPE Atlas included (Cybernet's own RIPE probes were ~24ms). This
   is the clearest confirmation yet of the case study's original framing: EFU Life
   really is reachable in single-digit milliseconds from the right vantage point in
   Karachi, the 15-30x penalty other ISPs pay is not a distance problem.

2. **Nayatel, Islamabad: 113.4ms, but still all-domestic.** This contradicts the
   RIPE Atlas Nayatel probes checked earlier the same day (24-26ms, same all-domestic
   Transworld-to-Cybernet path shape). Same path shape, very different RTT. Hop 8
   (`192.168.76.189`, private, unlabelable) shows the RTT jump from ~25ms to ~99ms
   with no foreign ASN appearing anywhere in the trace, so this reads as congestion
   or a routing inefficiency internal to Nayatel/Transworld's domestic backbone
   right now, not a new hairpin, but it's a real, live discrepancy between two
   Nayatel vantages on the same day and hasn't been investigated further.
