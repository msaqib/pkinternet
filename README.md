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

## Probe Setup

Instructions for deploying a RIPE Atlas software probe on Raspberry Pi hardware:

- [Raspberry Pi 2](pi2.md) (32-bit, build from source)
- [Raspberry Pi 3 and later](pi3.md) (64-bit, official Debian package)
