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
- [02 — ISP Classification](experiments/02_isp_classification/probe_deployment_plan.md):
  Plan for deploying 20 probes to classify ISPs by PKIX peering status (in progress).

## Findings

- [01 — Hosting & Routing Analysis](findings/01_hosting_and_routing_analysis.md)
  with the [charts notebook](findings/01_hosting_and_routing.ipynb)
  (re-run after new batches to refresh every figure).

## Probe Setup

Instructions for deploying a RIPE Atlas software probe on Raspberry Pi hardware:

- [Raspberry Pi 2](pi2.md) (32-bit, build from source)
- [Raspberry Pi 3 and later](pi3.md) (64-bit, official Debian package)
