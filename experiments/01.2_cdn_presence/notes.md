# Experiment 1.2 - CDN / Cache Presence in Pakistan

**Author:** Rayan Atif

## Objective

Determine which major content providers (Netflix, Google/YouTube, Meta, Akamai,
Cloudflare, Microsoft, Apple, ...) actually **serve from a cache physically inside
Pakistan**, and through which ISP. Prompted by Dr Saqib's note that Netflix caches
are reportedly hosted by PTCL, Nayatel, Optix, StormFiber, Fiberlink, Telenor and
TWA, and that Akamai/Meta/Google "must" have presence (a hypothesis to verify).

## Framing

These are **global services**, not Pakistani-hosted sites. The question is whether
their content is delivered from an **embedded cache / PoP inside a Pakistani ISP**
(so it loads locally) or fetched from abroad. Embedded-cache programs:
- Netflix Open Connect (OCA), Google Global Cache (GGC), Meta FNA appliance,
  Akamai embedded (AANP), Cloudflare PoPs.

## Method

`cdn_check.py` runs a **PING** to each target from each Pakistani probe with
`resolve_on_probe = True`, so every probe resolves the name via its own ISP and
pings the IP it received. One measurement yields both:
- the **IP each ISP was handed** (we look up its ASN and country), and
- the **RTT** to it.

Verdict per (target, probe):
- **PK-local** (RTT < 15 ms) = a cache inside Pakistan,
- **regional** (< 50 ms) = nearby (Gulf / India),
- **abroad** (>= 50 ms) = no local cache,
- plus the resolved IP's network/country for confirmation (a PK-ISP ASN is direct
  evidence of an embedded cache).

Run from the repo root:
```
python experiments/01.2_cdn_presence/cdn_check.py
```
Targets are in `data/pk_cdn_targets.csv` (hostname, provider, category). The
`provider` column is the hypothesis; the measurement decides.

## Output

`results/{RUN_NAME}/cdn_{TIMESTAMP}.csv` and a readable `.txt`, with per-service,
per-ISP: resolved IP, ASN/operator, country, RTT, verdict. The run prints which
providers have a PK-local cache and which ISPs see it.

## Notes / caveats

- Currently queries the 3 online probes (Nayatel, Transworld, Z-Com); PTCL and
  TPCPL are skipped while offline (`OFFLINE_PROBES`).
- RTT is the primary signal; a single-digit ms RTT to a foreign-registered CDN IP
  (e.g. Cloudflare) still means the cache is physically local.
- This is delivery/cache presence, not origin hosting. A "PK-local" result means
  the content is served locally for that ISP, not that the company is in Pakistan.
- To study coverage across more ISPs, deploy probes on the ISPs Dr Saqib listed
  (Optix, StormFiber, Telenor, Fiberlink, ...) - ties into Experiment 02.
