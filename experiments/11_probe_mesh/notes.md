# Exp 11 — Probe-to-probe mesh

## Question

Does inter-ISP handoff quality depend on *which pair* of PKIX-connected ISPs
you measure between, and is the route/RTT symmetric in both directions?
Every prior experiment infers peering quality from probe -> website paths,
which confounds the website's own hosting choice with the ISP-to-ISP path.
This experiment isolates the ISP pair by measuring directly between probes.

Feeds RQ2 (same-ISP customers, similar service?) and the PKIX Set 1/2/3
classification: a Set-3 pair should show a low-RTT, non-tromboning path in
*both* directions; a Set-2 pair should hairpin through PTCL/Transworld
despite both members being physically present at the same IXP node.

## Why this can't be "traceroute probe A to probe B" directly

RIPE Atlas measurements always target an IP or hostname, not a probe ID.
There is no first-class "inter-probe" measurement type. The workaround: pull
each probe's own public `address_v4` from the public `/api/v2/probes/`
endpoint (no API key or login needed — this is the same call
`tools/probe_status/app.py` makes) and use *that* as the traceroute/ping
target, with the peer probe as the measurement source. This still gives a
real inter-ISP path even if the destination probe's host itself doesn't
answer past the last routed hop — same partial-visibility discipline as
every other experiment here (CLAUDE.md "Analysis discipline").

Consequence: probes behind CGNAT or reporting only a private/tunnel IP can't
be usable *targets* (they can still be sources). As of 2026-08-24 none of
the 13 currently-Connected probes hit this — all have a public IPv4.

## Live roster (fetched fresh every run, never hardcoded)

`python mesh_sweep.py --list` hits RIPE's public status API and prints the
current Connected + usable-IPv4 set. Snapshot from 2026-08-24:

13 of 19 known-roster probes (CLAUDE.md probe tables) are Connected:
zcom.lhe, ptcl.lhe (anchor, ICMP-filtered), nayatel.isb, transworld.lhe
(ICMP-filtered), tes.lhe, tes.khi, nayatel.lhe, fasttel.isb, nova.lhe,
cybernet.hrp, ptcl.khi, cybernet.khi, ntc.khi.

Offline: 1015210 (PTCL, Docker-artifact probe), 1016153 (TES), 1016154
(Cybernet), 64535 (Orbit), 1015491 (Z-Com), 1016393 (PTCL N. Punjab).

Cross-checked via SSH against 4 of these that run on our own Raspberry Pis
(Tailscale hosts raslas-01/02/04/05 = probes 1015679, 1016036, 1016143,
1016126) — `ripe-atlas.service` active with a live control tunnel to RIPE's
Dublin controllers on all four, confirming the public API status is accurate.

## Design

- **Directed pairs, all of them.** N=13 connected probes -> N*(N-1) = 156
  directed pairs. Both i->j and j->i are measured separately (not inferred by
  symmetry) — asymmetric routing is itself a finding, per the Shaw/Nova and
  PTCL<->Transworld precedent (CLAUDE.md "Known measurement artifacts",
  "ISP handoff measurements").
- **Two measurement types per pair:** TCP/80 Paris traceroute (paris=16,
  packets=3 — same convention as Exp 04 onward) for the path, plus an ICMP
  ping (packets=3) for a clean RTT where traceroute is filtered.
  156 pairs x 2 = 312 measurements total.
- **Quota check:** each destination probe receives N-1=12 inbound
  measurements per kind — under RIPE's 25-one-off-per-target cap. The script
  warns if the connected roster ever grows past ~26 probes.
- **Credits:** traceroute 30cr + ping 3cr per result x 156 pairs ≈ 5,150
  credits. Trivial against the 10M/day cap.
- **Batching:** BATCH_SIZE=40 / BATCH_WAIT=20s per chunk, well under the
  100-concurrent-per-account limit (no need for the two-account split Exp 07
  used — this run is an order of magnitude smaller).
- **One-off census, repeated a few times.** Not a 7-day panel — a single pass
  first, then repeat manually 3-4 times over ~24h to catch the kind of
  minutes-apart route flip Exp 04 found on a Worldcall IP. `mesh_sweep.py`
  timestamps each run into its own `results/run_<ts>/` so repeats don't
  collide; compare verdicts across runs at analysis time.
- **ICMP-filtered probes** (62224 Transworld, 7764 PTCL anchor) will show
  thin/opaque traceroutes as both source AND now destination too — ping
  RTT is the reliable signal for those, matching existing convention.

## Analysis plan (next, once results land)

1. **Per-pair verdict** using the same RTT-physics tromboning detector as
   Exp 04/4.1 (foreign hop >=40ms, RTT jump >=60ms, or any hop >=70ms =
   left PK; max RTT <45ms = local) — already wired into `mesh_sweep.py`.
2. **Symmetry table.** For every unordered pair {i,j}, diff the i->j and j->i
   verdicts/RTTs. The script already prints pairs with a flipped
   local/trombone verdict; build the full N x N matrix (heatmap: rows=source,
   cols=dest, cell=trombone y/n) at analysis time.
3. **Set 2 vs Set 3 classification.** Cross-reference PKIX's slide-7 ISP list
   (CLAUDE.md "PKIX status") against which pairs actually route
   local/low-RTT vs hairpin through PTCL/Transworld — this is the direct,
   probe-measured version of the "listed as connected but not peering"
   argument that was previously made only from probe -> website evidence
   (e.g. the Wateen/Cloudflare-HKG case).
4. **Handoff attribution.** For tromboning pairs, record `transit_name`
   (already in the CSV) to see whether PTCL or Transworld is doing the
   hairpinning, matching the Exp 4.1 methodology.

## Run

```
export RIPE_API_KEY="..."
python experiments/11_probe_mesh/mesh_sweep.py --list     # check live roster first, free
python experiments/11_probe_mesh/mesh_sweep.py            # launch + poll + parse
```

Output per run: `results/run_<ts>/mesh_<ts>.csv` (per-pair verdicts),
`routes_<ts>.txt` (hop-by-hop, traceroute pairs only), `raw_<ts>.json`
(full sagan-parseable results, re-parseable offline via `--reparse
results/run_<ts>`, zero extra credits).
