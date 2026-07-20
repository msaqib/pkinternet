# Case study — EFU Life: one ISP holds the only domestic door, everyone else flies abroad

**Prompted by:** Dr. Saqib noticing something unusual in the Cybernet→EFU Life traces.
**Target:** `efulife.com` (EFU Life Assurance Ltd) — Pakistan-class, Karachi, geo-IP passed the
physics check unmodified. Hosted on its **own ASN, AS141008**, not on any ISP's network — this
is not a hosted-on-Cybernet story, it's a peering story.

## The headline number

| Vantage | median RTT | vs. Cybernet's best |
|---|--:|--:|
| **Cybernet (3rd vantage)** | **5.4 ms** | 1.0× |
| Cybernet (2nd vantage) | 5.8 ms | 1.1× |
| Cybernet (Haripur) | 25.4 ms | 4.7× |
| TES (2nd vantage) | 80.4 ms | 14.9× |
| Transworld | 98.0 ms | 18.1× |
| Nayatel (1st vantage) | 98.9 ms | 18.3× |
| Nova | 100.1 ms | 18.5× |
| Fasttel | 101.5 ms | 18.8× |
| TES (1st vantage) | 103.8 ms | 19.2× |
| PTCL (Karachi) | 113.5 ms | 21.0× |
| PTCL (Mianwali) | 163.1 ms | 30.2× |
| Z-Com | 167.8 ms | 31.1× |
| Orbit | 174.0 ms | 32.2× |
| Nayatel (2nd vantage) | 177.3 ms | **32.8×** |

Every non-Cybernet ISP pays **15–33× the latency** to reach a server that is, per the traceroutes
themselves, sitting inside Pakistan the entire time.

## Why: every path — including the hairpins — converges on the exact same Cybernet hop

This is the part worth documenting carefully, because it's not "Cybernet is fast and everyone else
is slow" — it's more specific and more damning than that. Checking the hop immediately before the
destination, across every probe:

| Probe / ISP | pre-destination hop |
|---|---|
| Cybernet ×2 | `124.29.240.218` — **AS9541 (Cybernet)** |
| Fasttel | AS9541 (Cybernet) |
| Orbit | AS9541 (Cybernet) |
| TES ×2 | AS9541 (Cybernet) |
| Nova | AS9541 (Cybernet) |
| Z-Com | AS9541 (Cybernet) |
| PTCL (Mianwali) | AS9541 (Cybernet) |
| Nayatel, Cybernet-3rd-vantage | unresolved (`*`) — same segment, non-responding that round |
| PTCL (7764, excluded probe) | AS17557 (PTCL itself) — the one exception, on the already-excluded 90%-loss probe |

**Every single ISP's traffic — no matter where it started — ends up entering EFU Life's network
through the same Cybernet edge.** There is no other domestic door to AS141008. The difference is
only *how each ISP gets to that door*:

**Cybernet, direct (6–8 hops, all domestic):**
```
Cybernet access -> ... -> 124.29.240.218 (Cybernet, AS9541) -> 103.154.196.31/33 (EFU, AS141008)
```

**PTCL (hairpins via Oman):**
```
PTCL -> ... -> GSL (AS7578/AS137409) -> OMANTEL (AS8529, Zain Oman) -> [back into PK] ->
... -> 124.29.240.218 (Cybernet, AS9541) -> EFU Life
```

**Nova / Z-Com (hairpin via Singapore, through Transworld):**
```
[Nova/Z-Com] -> Transworld (AS38193) -> TWA backbone -> Equinix Singapore (AS?) -> [back into PK]
-> ... -> 124.29.240.218 (Cybernet, AS9541) -> EFU Life
```

Every non-Cybernet ISP sends the packet **out of the country and back** solely so it can re-enter
Pakistan at Cybernet's specific edge — there is no domestic peering path from Transworld, PTCL,
Nova, Z-Com, TES, Orbit, or Fasttel directly into Cybernet's network for this destination.

## What this is a case study of

This is the tromboning thesis in its most literal, single-destination form: a domestic host,
reachable in single-digit milliseconds if you happen to be the one ISP with a working connection
to it, and reachable *only* via an international round-trip for everyone else — not because the
content is abroad, not because of a routing bug, but because **the domestic interconnect between
Cybernet and the rest of the country's ISPs doesn't exist for this path**, and every other ISP's
fallback is to leave the country and come back in through the front door instead. An exchange
that actually connected these networks would turn every one of those 15–33× numbers into
something close to 1×, in one hop, at zero marginal cost per site — this is exactly the shape of
problem PKIX exists to solve and, per the panel's zero-crossing result, isn't solving here.

## Caveats

- **n=1 site.** This is one destination, chosen because it's unusually clean and complete —
  it should be read as an illustration of the mechanism, not resampled evidence of its
  prevalence. (The prevalence claim is what §RQ1/RQ3's aggregate statistics are for.)
- The PTCL-via-Oman path is itself interesting and not yet explained — worth a follow-up look at
  whether this is a stable, common PTCL pattern for other Karachi-hosted destinations or specific
  to this one.
- Not yet checked: whether EFU Life's own network engineers are aware of this (a single-homed
  arrangement with Cybernet, or a deliberate choice) — this is exactly the kind of question an
  ISP could confirm directly, per the outreach-questions discussion.

## Reproducing

Hop data: `.paths_series.json` (built from the raw archive), filtered to `efulife.com`.
RTT table: `results/b/panel_20260718_200355.csv`, filtered to `target=="efulife.com"`, grouped by
probe. ASN annotations: `hop_annotations.csv`.
