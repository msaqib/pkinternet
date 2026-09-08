# EFU Life live snapshot -- what the 9-probe RIPE Atlas traceroute showed

**What this is:** one one-off traceroute per currently-live RIPE Atlas PK probe
to `efulife.com` (103.154.196.33), run live on 2026-09-01, re-checking the
archived Exp 07 case study (`case_study_efulife_cybernet_gatekeeper.md`) with a
fresh, current measurement instead of historical data. 16 probes discovered
live (RIPE, country_code=PK, Connected), 9 returned usable results.

Full data: `results/run_20260901_214922/routes_efulife_20260901_214922.txt`
(raw) and the `_CORRECTED.txt` copy (relabeled after the geolocation
verification pass, see below).

## Headline result: one gatekeeper hop, confirmed live

**Every single probe that reached the destination passed through the identical
hop, `124.29.240.218` (Cybernet, AS9541), immediately before EFU Life's own
network.** No exceptions among the 8 probes that got a full reply. This is the
same finding the archived case study made from panel data weeks ago, now
independently reconfirmed with a fresh measurement: there is no other domestic
door into AS141008, right now, today.

## The 9 results, sorted fastest to slowest

| Probe / ISP | max RTT | Path |
|---|--:|---|
| Cybernet | 23.8 ms | direct, all-domestic |
| PERN | 24.4 ms | direct, all-domestic (mostly timeouts mid-path, but reaches at 24ms) |
| Nayatel (x2 probes) | 25.9 / 26.0 ms | via Transworld backbone, then Cybernet, all-domestic |
| TES | 48.3 ms | via Transworld, then Cybernet, all-domestic |
| Nova | 56.8 ms | via Transworld, then Cybernet, all-domestic (a "Shaw Communications, Canada" ASN label on hop 2 is a known project-wide artifact -- that IP is physically Nova's own CPE in Pakistan, not a real hop to Canada) |
| Z-Com | 100.9 ms | via Transworld, then Cybernet, all-domestic but slow |
| PTCL (probe 1016126, Karachi) | 203.2 ms | leaves the country: GSL Networks (Singapore-confirmed hop) then a Zain Omantel block (Oman, RDAP-confirmed), then Cybernet |
| PTCL (probe 7764, Lahore) | no reply | known ICMP-filtered probe, excluded from path analysis project-wide |

## What this confirms vs. what's new

**Confirms the archived case study, live:** the same domestic-vs-hairpin split
holds today that the panel data showed weeks ago. Cybernet/PERN/Nayatel/TES/Nova
stay inside Pakistan the whole way (with real cost differences between them,
24ms to 57ms, but no international exit). PTCL still leaves the country.

**New this round, from re-checking the actual hop IPs instead of trusting the
labels:** two of PTCL's three foreign hops turned out not to be what they were
originally labeled. The GSL Networks hop was called "Equinix Muscat" in the
archived analysis; re-verified live, that specific IP's own hostname is generic
with no city code, and its real neighbors span Ashburn, Adelaide, Seattle, and
Phoenix, so "Muscat" doesn't hold up for that IP, corrected to "abroad, site
unconfirmed." A second GSL hop, previously an uncorrected "Los Angeles" guess
from a geolocation database, fails the same check for the same reason. The one
label that did hold up under direct verification is the Singapore hop, its own
hostname (`sg-eqxsg3-cr7`) confirms it, unchanged between the original archive
and today. Full detail and the corrections made to the underlying project docs:
`edits/2026-09-01_eda_docs_gsl_muscat_correction.md`.

**Also new: PTCL got slower, not faster.** The archived panel measurement of
this exact same probe (1016126) recorded 119.2ms on 2026-07-18. Today it's
203.2ms, same three-network hairpin (GSL Singapore, then the Omantel block),
same re-entry IP. Whatever Cybernet's July 27 fix was (see
`bgp_july27_investigation.md`), it didn't touch this path, and if anything the
path has degraded since.

## Gaps

7 of the 16 live-discovered probes (falcon, fasttel, both extra Cybernet
vantages, a third Nayatel, orbit, leapdigital) failed to return results, RIPE
reported them "Failed" or stuck at "Scheduled" even though they self-report as
Connected. This is a known limitation of the live-discovery method (see Exp 12
notes, "Which live source") -- a probe can look online in the roster and still
be too busy or flaky to actually run a fresh one-off measurement. A retry
attempt on all 7 also failed to complete. This snapshot should be read as "9
real vantages, live," not as full coverage of the 16-probe roster.

## Complementary Globalping check (non-RIPE probes)

A separate check via Globalping (7 additional Pakistani ISPs, none overlapping
with the RIPE roster except Nayatel/PTCL) found the same GSL-Singapore-then-
Omantel hairpin independently on 4 more ISPs (Fariya Networks, IN CABLE
INTERNET, FASTTEL BROADBAND, plus PTCL again), meaning this isn't a PTCL-only
pattern, several unrelated Pakistani networks funnel through the same
international chokepoint to reach a server sitting in their own country. Also
found the single fastest vantage in the whole investigation, Sharp Telecom in
Karachi at 4.6ms, all-domestic. Full detail:
`results/run_20260901_214922/globalping_efulife_summary.md`.
