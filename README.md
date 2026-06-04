# Assessing Local Interconnectivity Resilience in Pakistan

A network measurement research project studying Pakistani internet infrastructure
using RIPE Atlas probes. 

The study uses traceroutes launched from Pakistani RIPE Atlas probes to determine:
- Where Pakistani websites are physically hosted (in-country vs abroad)
- How traffic is routed across Pakistani ISPs
- Whether traffic transits Pakistan's internet exchange point (PKIX) or exits the country unnecessarily

## Repository Structure

```
scripts/measurement/   Python scripts for launching and processing measurements
targets/               Input files (website lists, probe lists)
experiments/           One subfolder per experiment with notes and results
findings/              Summaries and analysis outputs
```

## Experiments

- [01 — Website Destinations](experiments/01_website_destinations/notes.md):
  Traceroutes to Pakistani websites to determine hosting location by ASN and RTT.

## Probe Setup

Instructions for deploying a RIPE Atlas software probe on Raspberry Pi hardware:

- [Raspberry Pi 2](pi2.md) (32-bit, build from source)
- [Raspberry Pi 3 and later](pi3.md) (64-bit, official Debian package)
