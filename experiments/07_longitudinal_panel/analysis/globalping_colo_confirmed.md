# Cloudflare colo, via Globalping — 6 new/confirmed ISP vantages, no probe or SSH access needed

Globalping (globalping.io) is a free, public, third-party distributed
network-testing API — not RIPE Atlas, so the "HTTP measurements only target
anchors" restriction does not apply. It has its own volunteer-hosted probes,
including several on Pakistani networks we have no RIPE Atlas presence on at
all. Method: `POST /v1/measurements`, `type: http`, path `/cdn-cgi/trace`,
`locations: [{"network": "<name>"}]`.

**Data-quality catch, applied before trusting any of this**: 2 of the 8
matched "PK" networks in Globalping's directory (`2E TELEKOMUNIKASYON`,
`BrainStorm Network`) returned Cloudflare's own `loc=` field as US/Bulgaria/
Canada/Puerto Rico, not PK — meaning these are mislabelled or
tunnelled/VPN-style nodes, not real Pakistani eyeball traffic. **Excluded.**
The other 6 all show `loc=PK` consistently across every site and are used
below.

## Results (colo, 5 sites x 6 confirmed-real PK networks)

| Network (ASN) | ibcc.edu.pk | auroracloset.pk | digikhata.pk | apkamazon.com.pk | ajk.gov.pk |
|---|---|---|---|---|---|
| **Nayatel** (23674) | **ISB** | **ISB** | **ISB** | **ISB** | **ISB** |
| Fariya Networks (45814) | LHE | LHE | SIN | SIN | SIN |
| Fasttel (150683) | LHE | LHE | SIN | SIN | SIN |
| PTCL (17557) | KHI | KHI | MCT | SIN | MCT |
| Virtury Cloud (150315) | KHI | KHI | MCT | SIN | SIN |
| Sharp Telecom (9387) | KHI | KHI | SIN | SIN | SIN |

KHI=Karachi, LHE=Lahore, ISB=Islamabad, SIN=Singapore, MCT=Muscat.

## Why this matters

**Nayatel gets a genuinely local Pakistani colo — Islamabad — for every
single one of the 5 test sites, including the two (`digikhata.pk`,
`apkamazon.com.pk`) that our earlier Pi-based check (5 other ISPs: Nova,
Cybernet x2, PTCL x2) found were Singapore for *everyone*.** That earlier
claim ("confirmed Singapore for every ISP, no exceptions" in
`cloudflare_colo_confirmed.md`) is now known to be wrong as a general claim
— it was true for the 5 ISPs we'd checked, not for Nayatel. Correcting it:
those two sites are local for Nayatel and far for every other ISP tested.
This is now the single strongest piece of evidence in the whole project for
"Nayatel is the best-peered network" — not inferred from RTT, not
"physics-consistent," Cloudflare's own confirmed answer, 5 for 5.

**Cloudflare has at least three distinct Pakistani colocations, not one**:
Karachi (KHI — PTCL, Virtury, Sharp), Lahore (LHE — Fariya, Fasttel), and
Islamabad (ISB — Nayatel). Different ISPs are landing on different cities
entirely, not just different speeds to the same place.

**Two visible clusters of shared behaviour**, worth investigating further:
Fariya Networks and Fasttel show an *identical* pattern across all 5 sites
(LHE/LHE/SIN/SIN/SIN) — consistent with sharing an upstream transit path to
Cloudflare. Virtury Cloud's pattern closely tracks PTCL's (KHI/KHI/MCT/
SIN/~SIN) — Virtury is listed as a PKIX Islamabad member in the PTA roster
already cited in the paper, and this is consistent with it depending on PTCL
for Cloudflare reachability specifically, not with its own independent
peering.

## What Globalping actually is, and how much to trust it

Globalping (globalping.io) is a free, open-source, community-run distributed
network-testing platform built by jsDelivr (the CDN project) — confirmed via
its own `User-Agent` string on every request (`globalping probe
(https://github.com/jsdelivr/globalping)`). Volunteers run lightweight probe
software; anyone can query them through a public API (ping, traceroute, DNS,
MTR, HTTP). It is **not** vetted to the standard RIPE Atlas holds itself to —
Globalping tags each probe `eyeball-network` (a real residential/business ISP
connection) or `datacenter-network` (a VPS/hosting box), and that tag is the
only thing separating a real ISP-customer vantage from a cloud server that
happens to sit on a Pakistani IP block. **Checked all 6 candidate PK networks
against this tag before trusting any of them**: Fariya, Nayatel, Fasttel,
PTCL, and Sharp Telecom are `eyeball-network` (real customer connections);
**Virtury Cloud is `datacenter-network`** — real Pakistani AS, but a hosted
server, not representative of an ordinary Virtury customer, so its numbers
get a caveat rather than being compared 1:1 with the others. 2E
Telekomunikasyon and BrainStorm are also `datacenter-network`, consistent
with their bogus non-PK `loc=` results — correctly excluded. Coverage
changes as volunteers join/leave, so re-check the tag every time before
trusting a "new" PK network that shows up.

## Nayatel scaled to the full 33-site Cloudflare list, with the RTT-physics cross-check actually done

Colo alone is Cloudflare's self-report — worth checking against something
Cloudflare doesn't control. Globalping's HTTP measurement also returns
connection timings, so every result below is checked two ways: what
Cloudflare *says* (`colo=`) and how fast the raw TCP handshake actually was
(a number Cloudflare's application layer has no way to fake).

**31 of 33 Cloudflare sites return `colo=ISB` (Islamabad) from Nayatel — no
exceptions among the ones that responded** (`reading.pk` and
`thefrontierpost.com` failed outright, twice, from this vantage — no colo
data of any kind, not a "far" result, a non-response).

**TCP handshake time across all 31: 0-3ms, median 1ms, zero exceptions.**
This is the clean signal — a TCP handshake is one raw network round-trip
with no server-side processing folded in, so this number cannot be faked by
a slow origin server the way total request time can. 0-3ms is flatly
impossible for anywhere outside Pakistan; this is the strongest physics
confirmation in the project.

**Two sites, `apkamazon.com.pk` (firstByte 209ms) and `glory-casino.net.pk`
(firstByte 441ms), look like they contradict this** — but their TCP
handshakes were still 1ms each. Fast handshake, slow first byte means the
*network path* was local and the *delay happened after that*, almost
certainly the edge server fetching from origin on a cache miss (a
first-request/cold-cache effect), not distance. Flagging this rather than
either hiding it or letting it undercut the 31/31 handshake result — it's a
server-side artifact, not a locality contradiction, and the distinction
matters methodologically (don't conflate total request time with network
RTT).

Raw data: `nayatel_globalping_33sites.json`.

## Access method (for reproducing / extending)

No credentials, no SSH, no RIPE Atlas credits. Public API:
```
POST https://api.globalping.io/v1/measurements
{"type":"http","target":"<site>","locations":[{"network":"<network name>"}],
 "measurementOptions":{"request":{"path":"/cdn-cgi/trace","method":"GET"},"protocol":"https"}}
```
then poll `GET /v1/measurements/<id>` until `status: finished`, read
`results[0].result.rawBody`. Check `loc=` on every result before trusting a
network — not every "PK" label in Globalping's directory is real (see
data-quality catch above). Available PK networks may change over time as
volunteers join/leave; re-list via `GET /v1/probes` filtered to
`location.country == "PK"`.
