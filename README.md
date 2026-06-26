# Assessing Local Interconnectivity Resilience in Pakistan

A network measurement research project studying Pakistani internet infrastructure
using RIPE Atlas probes. 

The study uses traceroutes launched from Pakistani RIPE Atlas probes to determine:
- Where Pakistani websites are physically hosted (in-country vs abroad)
- How traffic is routed across Pakistani ISPs
- Whether traffic transits Pakistan's internet exchange point (PKIX) or exits the country unnecessarily

## Repository Structure

```
scripts/measurement/   Python scripts (pk_multi_probe, geo_utils, format_routes)
data/                  Input files (website list, ISP/FLL list)
experiments/           One subfolder per experiment with notes and results
findings/              Analysis writeups and the charts notebook
```

## Experiments

- [01 — Website Destinations](experiments/01_website_destinations/notes.md):
  Traceroutes to Pakistani websites to determine hosting location and routing.
  Per-run outputs (grouped/summary CSV + readable routes), a full
  [batch inventory](experiments/01_website_destinations/batch_inventory.md), and a
  [website list](experiments/01_website_destinations/website_list.md).
- [1.1 — DNS Resolution](experiments/01.1_dns_resolution/notes.md):
  Per-ISP DNS lookups to find sites that resolve differently per ISP (GeoDNS).
  ~8% of sites differ; refines Exp 01's central-resolution shortcut.
- [1.2 — CDN Presence](experiments/01.2_cdn_presence/notes.md):
  Pings major content services (Netflix, Google, Meta, ...) per ISP to detect
  caches served from inside Pakistan.
- [02 — ISP Classification](experiments/02_isp_classification/notes.md):
  Classifying ISPs into PKIX Sets 1/2/3, with the roster, probe coverage, and the
  ~21-probe deployment plan (in progress).
- [03 — Longitudinal Routing](experiments/03_longitudinal_routing/notes.md):
  Re-traces the same sites every 15 min over days to add the time axis (path/RTT
  change, diurnal cycle, outages).
- [04 — Path Tromboning](experiments/04_path_tromboning/notes.md):
  Systematically detecting domestic traffic that hairpins abroad across an ISP's
  whole address space, via prefix-based target selection (TASS-adapted) and paced
  `tcptraceroute` (planning).

## Findings

- [01 — Hosting & Routing Analysis](findings/01_hosting_and_routing_analysis.md)
  with the [charts notebook](findings/01_hosting_and_routing.ipynb)
  (re-run after new batches to refresh every figure).
- [1.1 — Per-ISP DNS Resolution](findings/01.1_dns_resolution_analysis.md):
  which sites resolve differently per ISP, and how much it matters.
- [1.2 — CDN Presence in Pakistan](findings/01.2_cdn_presence_analysis.md):
  whether Netflix/Google/Meta/etc. are served from caches inside Pakistan.
- [1.3 — Nayatel Routing](findings/01.3_nayatel_routes.md):
  per-destination breakdown of what Nayatel transits (LDI vs direct peering).
- [3.1 — PTCL RTT Jumps & PTCL↔Transworld Peering](findings/03.1_ptcl_rtt_jumps.md):
  where PTCL paths jump RTT (access floor vs international exit) and that PTCL peers
  with Transworld domestically (100%) but never for abroad traffic (0%).
- [04 — Path Tromboning across Worldcall](findings/04_path_tromboning_worldcall.md):
  31% of Worldcall's sampled /24s hairpin through Transworld → Equinix Singapore,
  while PTCL reaches the same IPs locally — so Transworld chooses the hairpin.
  Destination-dependent and time-variable (intra-/24 consistency not yet verified).

## Probe Setup

Instructions for deploying a RIPE Atlas software probe on Raspberry Pi hardware:

- [Raspberry Pi 2](pi2.md) (32-bit, build from source)
- [Raspberry Pi 3 and later](pi3.md) (64-bit, official Debian package)
