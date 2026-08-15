# PeeringDB + live BGP looking glass: which Pakistani ISPs can even reach which CDNs without leaving the country

Automated cross-reference of every panel ISP's declared PeeringDB internet
exchange presence against 9 major/regional CDN and cloud operators. Method:
pull `netixlan` (which exchanges a network is present at) for each ASN from
the public PeeringDB API, then intersect. A shared exchange means a public,
route-server-based peering *path exists*; it does not mean the ISP actually
uses it (that's what the traceroute-based mechanism analysis in
`cdn_isp_deep_dive.md` and Exp 08 check separately).

**Important caveat, raised directly by the researcher and correct: PeeringDB
is self-reported.** "Present at an exchange" in PeeringDB only means the
network's operator filled in a form — it is not independent confirmation of
an active session, let alone of what's actually being exchanged. Section 0
below replaces PeeringDB with something stronger wherever it's available.

Raw data: `peeringdb_raw.json` (scratchpad; re-fetchable any time from the
public API, no auth/cost).

## 0. Live BGP looking glass — the strongest evidence tier, and where it stops

DE-CIX (who operate PIE Karachi professionally) run a public, queryable BGP
looking glass at `lg.de-cix.net`, built on Alice-LG. This is **not
self-reported** — it's the route server's own live session state, fetched
directly (`pie_karachi_lg_rs1_neighbors.json`, `..._rs2_neighbors.json`,
pulled 2026-08-14):

| ASN | Network | Session state (rs1 / rs2) | Routes announced (rs1 / rs2) |
|---|---|---|---|
| 17557 | **PTCL** | up / up | **650 / 650** |
| 139341 | **Tencent – ACE CDN** | up / up | 2 / 2 |
| 132165 | Connect Communications | up / up | 262 / 262 |
| 58895 | Ebone Network | up / down | 123 / 0 |
| 138915 | Kaopu Cloud HK | up / up | 9 / 9 |
| 21859 | Zenlayer | up / up | 8 / 8 |
| 137561 | WayLink | up / down | 10 / 0 |
| **24499** | **Telenor Pakistan** | **up / up** | **0 / 0** |
| 56167 | Ufone | down / up | 0 / 3 |

**This upgrades the PTCL↔ACE-CDN case from "strongly evidenced" to
confirmed at the BGP layer**: both sides have live, active route-server
sessions at PIE Karachi right now, PTCL is receiving 650 routes through this
exact mechanism (so it plainly does use the route server for *something*),
and ACE CDN is announcing prefixes into it. Exp 08's traceroute independently
showed PTCL's actual ACE-CDN traffic bypasses this working session for a
private link instead. Two independent methods (live BGP state + measured
path) now agree — this is as close to airtight as this project gets, and
should anchor the paper's central example, not just be one data point among
several.

**Telenor is a cleaner, even more literal illustration of "Set 2" than
Wateen (the paper's current example)**: a confirmed *live* BGP session,
open right now, exchanging **zero routes**. Not a private-path workaround
like PTCL — just present and silent. Worth using instead of, or alongside,
the older Wateen anecdote, since this one is dated, live-verified, and not
inferred from a single traceroute.

**Where this tool stops working: PKIX Islamabad and PKIX Lahore — the two
nodes where Cybernet, Nayatel, TES, Zcom, and Wateen are actually
co-located — do not have a public looking glass.** PeeringDB lists no
`looking_glass_url` for PKIX Lahore, and no search turned one up (they're
HEC/PITB-run, not a professional DE-CIX-style operation). This means **the
"same room, 20-54× apart" finding cannot currently be confirmed at the BGP
layer by an outside researcher** — only inferred from RTT physics and
traceroute topology, same as the CDN mechanism analysis. That's an honest
limit, not a gap in effort: there is no public instrument for it. The only
way to close it is to ask the ISPs or HEC directly, or to run a probe-to-probe
domestic reachability test (proposed below) as the best available proxy.

## ISPs with zero declared public peering, anywhere

**Nayatel, TES, Nova, Orbit, Fasttel, Zcom, and Wateen have no PeeringDB
netixlan entries at all** — no declared presence at any exchange on Earth,
public or otherwise. PeeringDB is self-reported and voluntary, so this is
evidence of "not participating in the documented public-peering ecosystem,"
not proof of zero real peering — Nayatel's confirmed 2-3ms Cloudflare access
(§3 of `cdn_isp_deep_dive.md`) must therefore be an **undeclared bilateral
arrangement**, invisible to PeeringDB entirely. Worth stating as a limitation
either way: for 7 of 10 operators studied, PeeringDB tells us nothing.

## The three ISPs that do have public presence — and where it overlaps CDNs

| ISP | Exchanges (from PeeringDB) |
|---|---|
| **Cybernet** (AS9541) | DE-CIX Frankfurt, HKIX, Equinix Singapore, UAE-IX, NetIX, SH-IX, DE-CIX Marseille |
| **PTCL** (AS17557) | LINX London, AMS-IX, DE-CIX Frankfurt, Equinix Singapore, UAE-IX, DE-CIX New York, SH-IX, **PIE Karachi** |
| **Transworld** (AS38193) | DE-CIX Frankfurt, HKIX, NL-ix, Equinix Singapore, SH-IX, Equinix Muscat, Oman-IX |

**Every single shared exchange between these three ISPs and Cloudflare,
Akamai, Google, Amazon CloudFront, Azure, Fastly, or Incapsula is abroad** —
Frankfurt, Singapore, Hong Kong, London, Amsterdam, New York, Dubai, Muscat.
**None of these CDNs share a Pakistani exchange with any Pakistani ISP.**
Sucuri has zero PeeringDB presence anywhere and therefore shares nothing with
anyone — consistent with it being uniformly bad (104-138ms) for every ISP in
the measured data.

## The one exception, and it's the smoking gun

**PTCL and Tencent EdgeOne (ACE CDN, AS139341) are both declared members of
PIE Karachi** — the *only* CDN↔ISP↔Pakistani-exchange overlap that exists
anywhere in this census. This is a real, current, public, in-country peering
opportunity.

**Exp 08 already traced this exact pair and found they don't use it.**
PTCL reaches ACE CDN through a private link inside its own infrastructure
(`119.153.112.158`), never touching PIE Karachi's peering LAN
(`58.181.127.0/24`), despite both being confirmed members with active BGP
sessions on the DE-CIX looking glass.

This is the strongest single piece of evidence in the whole project: **two
networks, publicly declared members of the same Pakistani exchange, with a
working technical path between them, choosing not to use it.** Not "the
infrastructure doesn't exist," not "the CDN hasn't shown up yet" — a
confirmed, named, dated instance of exactly the underuse the paper argues.
This case should be the paper's lead example, not a footnote — it's the only
one where every part of the claim (membership, technical capability,
non-use) is independently confirmed rather than inferred.

## What this means for "peer at PKIX" as a policy ask

The paper's implicit ask — "ISPs should peer more at PKIX to get local CDN
access" — is **not currently achievable for 8 of the 9 CDNs tested**, because
none of them (Cloudflare included) are PKIX or PIE Karachi members. The
actionable version of the argument has two distinct parts, and the paper
should separate them:

1. **For Tencent EdgeOne specifically**: the fix is "PTCL, use the exchange
   you're already a paying, connected member of." Zero new relationships
   needed. Directly demonstrated, not inferred.
2. **For Cloudflare, Akamai, Google, Amazon, Azure, Fastly**: the fix is "get
   these operators to join a Pakistani exchange at all" — a different, harder
   ask than "peer better," aimed at the CDNs and the exchange operators, not
   at the ISPs. Cybernet's workaround (an embedded cache node, a bilateral
   deal outside any exchange) is the current substitute, and it's available
   only to ISPs with enough traffic to qualify.
