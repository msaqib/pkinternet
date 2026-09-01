# Edit — `routing_map.py`, GSL "Equinix Muscat" block-wide location fix

**Date:** 2026-09-01
**File changed:** `experiments/07_longitudinal_panel/analysis/routing_map.py`
**Triggered by:** re-checking the EFU Life / PTCL Karachi trace live (Exp 13), specifically
whether hop 6 (`206.148.27.235`, labeled "Equinix Muscat" in the existing analysis) is
really in Muscat.

## What was wrong

`KNOWN_LOCATIONS` had two entries keyed by whole `/24` prefix:

```python
'206.148.27.': (23.610, 58.590, 'Equinix Muscat (GSL, via PTR)'),
'206.148.22.': (1.290, 103.850, 'Equinix Singapore (GSL, via PTR)'),
```

The comment justifying this said `206.148.27.1` and `.2` have PTR hostnames
(`mct-eqxmc1`) confirming Muscat, and `206.148.22.141` has a PTR hostname
(`sg-eqxsg3-cr7`) confirming Singapore. Both of those individual facts are true.
The bug is the generalization from "these specific IPs are in Muscat/Singapore" to
"the whole /24 block is in Muscat/Singapore" — `.startswith(prefix)` matches all 256
addresses in each block, not just the two/one that were actually checked.

## What the re-check found

Reverse-DNS on the addresses immediately around `206.148.27.235` (the IP that actually
appears in the EFU Life trace, not `.1`/`.2`):

```
206.148.27.225  ash-eqxdc10-cr1   -> Ashburn, Virginia, US
206.148.27.226  adl-eqxae1-bb4    -> Adelaide, Australia
206.148.27.227  adl-yourdc-cr8    -> Adelaide, Australia
206.148.27.232  sea-drtsea10-cr3  -> Seattle, US
206.148.27.233  sea-drtsea10-cr3  -> Seattle, US
206.148.27.234  transit-edge      -> (generic, no city code)
206.148.27.235  peering-edge      -> (generic, no city code)   <- our hop
206.148.27.236  phx-pnap-cr2      -> Phoenix, Arizona, US
206.148.27.237  phx-pnap-cr2      -> Phoenix, Arizona, US
```

Four different cities on two continents inside one /24. GSL Networks numbers router
interfaces out of shared address pools globally, not per physical site, so "same /24"
carries no location information for this operator. `.235` itself has a functional,
non-geographic hostname ("peering-edge" — describes the router's role, not its city) and
cannot be assumed to sit in Muscat just because `.1`/`.2` do.

`.1` and `.2` were re-checked directly and still resolve to `mct-eqxmc1` today — that part
of the original finding is unaffected. It's specifically the block-wide generalization to
every other address in `206.148.27.0/24` (including `.235`, the one that matters for this
trace) that doesn't hold.

## The fix

- Replaced both prefix-keyed entries with exact-IP-keyed entries (`206.148.27.1`,
  `206.148.27.2`, `206.148.22.141` — only the addresses whose own PTR hostname was
  actually checked and carries a city code).
- Updated `resolve_hop_location()`'s matching logic: a `KNOWN_LOCATIONS` key ending in
  `.` still does a `/24`-prefix match (used correctly by the untouched Singapore/`27.111.x`
  entries, which cover a real single-site block); a key with no trailing dot now requires
  an **exact** IP match, so `'206.148.27.1'` no longer also matches `206.148.27.10`,
  `.100`-`.199`, etc. (the old `startswith()` call would have made that mistake the moment
  a bare single-IP key was ever added, so this had to be fixed alongside the dict, not
  just the dict alone).
- Net effect: `206.148.27.235` (hop 6 of the PTCL Karachi -> EFU Life trace) is no longer
  force-labeled Muscat. It now falls through to the normal ip-api + physics-floor check
  like any other unverified IP, per the function's own stated fallback behavior ("dropped
  from the plotted path rather than shown somewhere false").

## Not yet fixed — flagging for a decision, not doing unilaterally

The same "Equinix Muscat (GSL, via PTR)" claim for this exact hop (`206.148.27.235`) also
appears as asserted fact, not hedged, in:

- `experiments/07_longitudinal_panel/analysis/interesting_routes_eda.md` (the table this
  conversation's "relabeled traceroute" was originally pulled from)
- `experiments/07_longitudinal_panel/analysis/eda_findings.md` ("confirmed via RIPEstat +
  PTR" for the same trace)

These are narrative/findings documents, not code, and may already be cited elsewhere
(paper drafts search on "Muscat"/"GSL" turned up references). Only `routing_map.py` was
changed here per the explicit request; the two docs above should be revisited to either
soften the Muscat claim to "unconfirmed, same operator as a confirmed-Muscat address" or
drop it, but that's a content edit to already-written findings and worth a separate,
deliberate pass rather than folding into this fix.
