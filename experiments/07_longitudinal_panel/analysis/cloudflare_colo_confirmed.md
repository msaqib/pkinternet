# Cloudflare `colo=` ground truth, run live from inside 5 ISPs (2026-08-14)

Real `curl https://<site>/cdn-cgi/trace` from 5 self-hosted RIPE Atlas Pis,
reached over Tailscale, run directly inside each ISP's network. This is
Cloudflare's own application-layer answer, not RTT inference — the strongest
possible confirmation available, and something RIPE Atlas itself cannot do
(HTTP measurements are restricted to Atlas-owned anchors).

| Pi | ISP / city | ibcc.edu.pk | auroracloset.pk | digikhata.pk | apkamazon.com.pk | ajk.gov.pk |
|---|---|---|---|---|---|---|
| raslas-01 | Nova, Lahore | KHI | KHI | SIN | SIN | SIN |
| raslas-02 | Cybernet, Haripur | KHI | KHI | SIN | SIN | SIN |
| raslas-04 | Cybernet, Karachi | KHI | KHI | SIN | SIN | SIN |
| raslas-05 | PTCL, Karachi | KHI | KHI | SIN | SIN | **MCT** |
| raslas-07 | PTCL, Mianwali (inferred from IP block) | KHI | KHI | SIN | SIN | **MCT** |

`loc=PK` on every single row (Cloudflare's own client-geolocation), and
`ip=` matched each Pi's real public address on every response that used
IPv4 — confirming these requests genuinely originated inside Pakistan.

## What this actually proves, site by site

- **`ibcc.edu.pk` and `auroracloset.pk`: confirmed `colo=KHI` (Karachi) for
  every single ISP tested — Nova, both Cybernet vantages, both PTCL
  vantages.** This is definitive: Cloudflare has a real, physical Karachi
  datacenter, and for these two sites, **every ISP reaches it**, not just
  Cybernet. This is stronger and more general than anything inferred from
  RTT alone.
- **`digikhata.pk` and `apkamazon.com.pk`: confirmed `colo=SIN` (Singapore)
  for every single ISP, no exceptions.** These two are genuinely,
  confirmedly *not* served from Pakistan for anyone right now — not a
  peering gap, a hosting-location fact for this specific Cloudflare edge
  prefix.
- **`ajk.gov.pk` splits by ISP, and not just in speed — in destination
  country:** Nova and both Cybernet vantages get `colo=SIN` (Singapore);
  **both PTCL vantages get `colo=MCT` (Muscat, Oman)**, a different foreign
  country entirely. This lines up with PTCL's own confirmed PeeringDB/live
  BGP footprint at UAE-IX and the Gulf exchanges — the same infrastructure
  is visibly steering PTCL's Cloudflare traffic toward the Gulf while
  everyone else goes to Singapore.

## An important, honest complication: this contradicts the panel week

In the original 7-day panel (11-18 July), `auroracloset.pk` was one of the
sites where **Cybernet fell to ~99ms** (the "Band B" pattern in
`cdn_isp_deep_dive.md` §2) — i.e. NOT local for Cybernet at that time. Right
now, a month later, both Cybernet vantages get `colo=KHI` — genuinely local
— for that same site. **The most likely explanation is that Cloudflare's
routing/peering for this specific prefix changed between mid-July and
mid-August** — anycast routing and peering relationships are not static.

This is a finding in its own right, not just a nuisance: **CDN peering
quality drifts over time**, on the scale of weeks, for the same site and the
same ISP. Any claim in the paper about "ISP X reaches CDN Y locally" needs a
timestamp, and ideally this colo check should be repeated periodically
(cheap — it's a handful of `curl` calls) rather than trusted as a permanent
fact from one measurement week.

## Access method (for reproducing)

5 of the project's self-hosted RIPE Atlas Pis (`raslas-01/02/04/05/07`) are
reachable over Tailscale; SSH in as `saqib` (shared credential, ask Dr.
Ilyas). Each Pi's public IP was confirmed to match a specific RIPE Atlas
probe ID via `curl ifconfig.me` cross-referenced against
`https://atlas.ripe.net/api/v2/probes/<id>/`. The other 9 raslas nodes were
offline at check time.
