# Experiment 03 — targets and probes (`run_20260612_48h`)

8 probes × 10 targets, ICMP Paris traceroute every 15 min + 1 ping / 5 min, over
**48 h** (two diurnal cycles). Edit the `PROBES` / `TARGETS` lists in
`trace_monitor.py` to match these tables.

## 10 targets

Picked from the Exp 01 results to span the behaviours most likely to **change over
time**, with two stable PK controls. Mix: 2 PK-hosted, 2 local-Cloudflare, 2
international-Cloudflare, 1 ecommerce abroad, 2 banks abroad, 1 GeoDNS/anycast gov.

| # | Hostname | Label | Category | Hosting (Exp 01) | Why watch it over time |
|---|----------|-------|----------|------------------|------------------------|
| 1 | `dunyanews.tv` | Dunya News | news | **PK** — Multinet (AS9260), Islamabad | Stable local control + continuity with the 24 h run. |
| 2 | `fbr.gov.pk` | FBR | government | **PK** — FBR (AS138424), Islamabad | Second local control on a different network. |
| 3 | `dawn.com` | Dawn | news | Cloudflare → **Karachi** (local edge) | Top-traffic news on a local CDN edge; watch for per-ISP edge / evening shifts. |
| 4 | `geo.tv` | Geo TV | news | Cloudflare → **Karachi** (local edge) | Second local-CDN watcher, high traffic. |
| 5 | `express.com.pk` | Express | news | Cloudflare → **Singapore** (served abroad) | International-CDN: does the handoff metro ever flip PK↔SG over the day? |
| 6 | `telemart.pk` | Telemart | ecommerce | Cloudflare → **Hong Kong** (served abroad) | Second international-CDN PoP-flip candidate. |
| 7 | `daraz.pk` | Daraz | ecommerce | Alibaba, **Singapore** | #1 shopping site → evening-congestion / diurnal-RTT candidate. |
| 8 | `hbl.com` | HBL Bank | banking | Incapsula, **New Jersey US** | Offshore bank (~200 ms); continuity with the 24 h run. |
| 9 | `mcb.com.pk` | MCB Bank | banking | Sucuri, **Singapore** | Offshore bank (~130 ms); **ICMP-blocked at host** → loss signal, trust the path. |
| 10 | `nadra.gov.pk` | NADRA | government | Akamai (**GeoDNS / anycast**) | Best path-change candidate — Akamai edge varies per ISP; watch the serving metro. |

## 8 probes

All connected PK RIPE Atlas probes **except the Endangered one (1014872, AS150683)**.
Six distinct ISPs; Cybernet (AS9541) and PTCL (AS17557) each contribute two probes.

| Probe | ASN | ISP | City | Note |
|-------|-----|-----|------|------|
| 60223 | AS23674 | Nayatel | Islamabad | most route-visible (full hop visibility) |
| 62224 | AS38193 | Transworld | Lahore | LDI (licensed international transit) |
| 7613 | AS152605 | Z COM Networks | Lahore | **anchor** |
| 1016036 | AS9541 | Cybernet | Haripur | LocalInternetProj02 |
| 1016143 | AS9541 | Cybernet | Karachi | LocalInternetProj04 (2nd Cybernet) |
| 7764 | AS17557 | **PTCL** | LUMS | **anchor** — PTCL vantage (dominant LDI), new this run |
| 1016126 | AS17557 | PTCL | Karachi | LocalInternetProj05 (2nd PTCL) |
| 1015679 | AS136174 | TPCPL / Nova | Lahore | LocalInternetProj01 |
| 1016153 | AS135407 | TES-PL (Transworld retail/home) | Karachi | **LocalInternetProj14** — unfiltered, best Transworld-family path visibility (Exp 04 RQ4) |
| 1016154 | AS9541 | Cybernet | Karachi | Proj# unconfirmed |
| 64535 | AS151983 | Orbit | Faisalabad | Proj# unconfirmed |

(Canonical probe roster — including ICMP-filtered and disconnected probes — is the
table in `METHODOLOGY.md` → *Probe configuration*. RIPE's API does not expose the
`LocalInternetProjNN` names, so both tables are maintained by hand.)

Each result records the probe's **live-measured egress ASN** (`probe_asn`) alongside
the registered one (`probe_asn_reg`) — useful here since two probes share AS9541 and
two share AS17557. See `notes.md` → *Dynamic probe ASN*.

## Caveats on this target set

- **GeoDNS (`nadra.gov.pk`, and Akamai/Cloudflare generally):** the hostname is
  resolved **once at schedule time**, so all 8 probes measure the **same IP** — we do
  *not* capture per-ISP GeoDNS IP differences (only anycast *routing* differences to
  that IP). Exp 1.1 flagged `nadra` as GeoDNS; the script records each round's
  `dst_addr` so any silent re-resolution is still visible.
- **`mcb.com.pk`** firewalls ICMP at the host (100 % no-reply) — treat the traceroute
  *path* as the signal, not the loss.
