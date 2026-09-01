# Edit — retract "Equinix Muscat" claim on hop `206.148.27.235` in two write-ups

**Date:** 2026-09-01
**Files changed:**
- `experiments/07_longitudinal_panel/analysis/eda_findings.md`
- `experiments/07_longitudinal_panel/analysis/interesting_routes_eda.md`

**Follow-up to:** `edits/2026-09-01_routing_map_gsl_prefix_fix.md` (the code fix). This is the
same correction applied to the two narrative documents that separately asserted the same
now-disproven claim as settled fact.

## What was wrong

`eda_findings.md` §2 stated, as a directly-checked fact: *"`dig -x` on `206.148.27.235` and
neighbouring IPs in the same /24 returns hostnames like `po3.mct-eqxmc1-cr2....`"* and
concluded *"The hop is in Muscat, Oman, not Sydney."*

This is not what `dig -x 206.148.27.235` actually returns. That specific IP resolves to
`peering-edge.globalsecurelayer.com`, a generic hostname with no city code. The
`mct-eqxmc1` hostname belongs to `206.148.27.1` and `.2`, two *different* addresses in the
same block. The write-up conflated "a neighbor of this IP is confirmed Muscat" with "this
IP is confirmed Muscat."

`interesting_routes_eda.md` inherited the same error in its per-hop tables (two rows,
both for `206.148.27.235`, in two separate `efulife.com` traces), since it's built on the
same `KNOWN_LOCATIONS` reasoning as `routing_map.py`.

## Why the label can't just be dropped back to the raw ip-api guess either

The original motivation for correcting this hop at all still stands: ip-api geolocated it
to Sydney, and a sibling IP on the same operator (`160.202.164.165`) gets a wildly
different ip-api answer (Los Angeles) for the same reason, i.e. ip-api's answer here looks
like a company-registration-address default, not a real location. So "Sydney" was already
independently rejected before the Muscat mixup happened. The choice isn't "Muscat or
Sydney," it's "Muscat (unconfirmed for this IP) or admit we don't know the city, while
still being confident it's abroad."

**Confidence that it's abroad, without knowing the city:** every individually-verified
address near `206.148.27.235` in the block (`.225` Ashburn, `.226`-`.227` Adelaide, `.232`-
`.233` Seattle, `.236`-`.237` Phoenix) is outside Pakistan, and the RTT jump from the last
confirmed-domestic hop to this one is large enough to be a genuine long-haul leg, not
measurement noise. Nothing in the data is consistent with `.235` secretly being in
Pakistan. What's not supportable is naming *which* foreign city.

## The fix

Both documents: rows/paragraphs asserting `206.148.27.235` = "Equinix Muscat" changed to
**"Abroad, site unconfirmed"**, with a note explaining the neighbor-based reasoning above.

- `interesting_routes_eda.md`: added a correction notice near the top of the file, changed
  the two affected table rows (`206.148.27.235`, RTT 110.8ms and 430.4ms in two different
  `efulife.com` traces). Left the `206.148.27.1` row (a different IP, genuinely confirmed
  on its own hostname) unchanged.
- `eda_findings.md`: rewrote §2's "What settled it" / "Reusable takeaway" to state the
  correction explicitly rather than silently swapping the conclusion, and updated the §4
  `efulife.com` route summary to match.

## Not changed

Neither document's claims about `206.148.22.141` (Singapore) or `206.148.27.1`/`.2`
(Muscat) were touched — those are confirmed on the exact IP in question, re-verified live
on 2026-09-01, and remain solid. Also not touched: the Zain Omantel / `213.202.6.x`
"Muscat" claim in the same traces — that one comes from a different source (ip-api's
own geolocation for that ASN, not a PTR-block-extension), was not part of what this
conversation checked, and hasn't been shown wrong.

**Not checked:** whether either document is cited by a paper draft. If it is, the cited
number/label there would need the same correction; worth a targeted grep before the next
paper revision if these specific hops are quoted anywhere.

---

## Second correction, same date: `160.202.164.165` "Los Angeles"

Same conversation, next hop over on the same trace. `eda_findings.md` §2 quotes
`160.202.164.165` geolocating to "Los Angeles" per `ip-api.com`, used only as evidence that
`ip-api` contradicts itself between two GSL addresses (the other being the Sydney/Muscat
one above), never asserted as a verified answer. `interesting_routes_eda.md`'s table
carried the same unverified "Los Angeles" through into its per-hop row with no
`(corrected)` tag, i.e. it was sitting there as plain, unchecked `ip-api` output, same
category of claim as the Sydney one that was already disproven, just never actually
checked.

**Checked now:** `.165` itself resolves to the generic `unknown.globalsecurelayer.com`
(no city code). Its real neighbors (`160.202.164.158`-`.172`) resolve to Brisbane, Sydney,
Muscat, Singapore, Dallas, Frankfurt, and Phoenix, six countries in a 12-address span.
APNIC RDAP confirms `160.202.164.0/24` ("KEYSTONE") is one registered block handed to one
organization, not a single physical site, same pattern as `206.148.27.0/24` above. Also
notable: the block's own RDAP record lists `country: US` at the top level but its abuse
contact is `IRT-KEYSTONE-NZ`, i.e. even the official registration paperwork for this one
block doesn't agree with itself on country, independent of anything PTR-related.

**Fix:** both documents' `160.202.164.165` = "Los Angeles" changed to **"Abroad, site
unconfirmed"**, with the neighbor list and RDAP finding noted inline.

**Not changed:** nothing else in either document referenced `160.202.164.x`.
