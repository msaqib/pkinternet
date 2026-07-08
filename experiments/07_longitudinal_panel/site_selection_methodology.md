# Site Selection Methodology

## Overview

This document describes the methodology used to select 100 target websites for the week-long longitudinal routing experiment. The goal was to assemble a representative sample of Pakistani internet infrastructure across critical sectors, with a controlled mix of hosting types, to enable measurement of routing inefficiency and traffic tromboning.

## Step 1: Candidate Pool Assembly

The candidate pool was assembled from three sources:

**Tranco top-1M (.pk filter):** The Tranco top-1 million domain ranking list was filtered for domains ending in `.pk`, yielding 1,522 candidate domains. Tranco aggregates traffic data from multiple sources (Alexa, Majestic, Umbrella, Quantcast) and is designed for reproducible network measurement research \[cite: tranco\].

**PTA licensed operator list:** The Pakistan Telecommunication Authority's published list of licensed ISP operators was cross-referenced to identify ISP corporate websites. Each domain was verified via DNS resolution and manual HTTP check. 86 valid ISP domains were retained after removing unreachable and non-functional sites.

**Manual additions:** Healthcare sector sites identified from prior DNS+ASN analysis were added explicitly since healthcare entities are underrepresented in the Tranco .pk slice. Six additional PK-hosted sites identified during ASN lookup but absent from the Tranco list were also added.

The combined candidate pool contains **1,814 unique sites**.

## Step 2: Hosting Classification

Each site was classified into one of three hosting categories:

- **Pakistani** — resolves to an IP registered to a Pakistani ASN (country code PK) via Team Cymru DNS lookup
- **CDN** — resolves to a known content delivery network (Cloudflare, Akamai, Fastly, Alibaba, etc.) regardless of geographic location
- **Abroad** — resolves to a foreign ASN that is not a CDN (hosted on foreign cloud or dedicated servers)

Classification was performed programmatically using `socket.gethostbyname()` for DNS resolution followed by Team Cymru bulk WHOIS for ASN and country code lookup.

## Step 3: CISA Sector Categorization

Every site was assigned to one of the nine critical infrastructure sectors defined by the US Cybersecurity and Infrastructure Security Agency (CISA) \[cite: cisa\], following the approach used in prior IXP peering measurement research \[cite: ixp-worth-peering\]:

| CISA Sector | Example sites |
|---|---|
| Government Services & Facilities | fbr.gov.pk, punjab.gov.pk, ecp.gov.pk |
| Education | nu.edu.pk, aiou.edu.pk, hec.gov.pk |
| Communications | ptcl.com.pk, zong.com.pk, nayatel.com |
| Commercial Facilities | dunya.com.pk, daraz.pk, jazztv.pk |
| Energy | lesco.gov.pk, wapda.gov.pk, tplpower.pk |
| Financial Services | hbl.com, mcb.com.pk, jazzcash.com.pk |
| Healthcare & Public Health | pmdc.pk, mohw.gov.pk, shifa.com.pk |
| Transportation Systems | piac.com.pk, pakrail.gov.pk, airblue.com |

Categorization was performed by mapping raw source categories (e.g. News, Banks, ISPs, Energy DISCO) to their corresponding CISA sector. Healthcare sites were identified by keyword matching and manual verification. Ambiguous cases were resolved manually.

## Step 4: Proportional Sampling

A final set of 100 sites was selected using proportional random sampling with a fixed seed of 42 for reproducibility.

**Sector allocation** was determined as follows. Every sector was first guaranteed a minimum of 2 slots to ensure no sector is completely unrepresented. The remaining 82 slots were distributed proportionally based on each sector's PK+CDN candidate pool size relative to the total PK+CDN pool across all sectors. PK+CDN pool size was used as the weighting factor rather than total pool size because the research question concerns tromboning — traffic that should be exchangeable domestically. Pakistani-hosted and CDN-hosted sites are directly relevant to this question; internationally-hosted sites are legitimately abroad and thus less relevant to the allocation decision.

**Within each sector**, allocated slots were divided into three hosting type quotas:
- 20% internationally-hosted (Abroad), with a minimum of 1 if the sector pool contains Abroad sites and has at least 3 allocated slots
- 40% Pakistani-hosted
- 40% CDN-hosted

If a sector's candidate pool did not contain enough sites of one hosting type to fill its quota, the shortfall was filled from whichever hosting type had the largest remaining pool. All fallbacks are logged explicitly.

**Final allocation:**

| Sector | Total | PK | CDN | Abroad |
|---|---|---|---|---|
| Commercial Facilities | 60 | 24 | 24 | 12 |
| Government Services & Facilities | 11 | 4 | 5 | 2 |
| Education | 10 | 4 | 4 | 2 |
| Communications | 7 | 3 | 3 | 1 |
| Financial Services | 4 | 2 | 1 | 1 |
| Energy | 3 | 1 | 1 | 1 |
| Healthcare & Public Health | 3 | 1 | 1 | 1 |
| Transportation Systems | 2 | 1 | 1 | 0 |
| **Total** | **100** | **40** | **40** | **20** |

The overall hosting split is exactly **40% Pakistani, 40% CDN, 20% internationally-hosted**.

## Reproducibility

The full pipeline is implemented in three scripts:

- `other/dns_resolve_resume.py` — DNS resolution with atomic checkpointing
- `other/asn_pk_filter.py` — Team Cymru ASN lookup and PK classification
- `other/sample_100_v2.py` — proportional sampling (reads `other/site_candidates_cisa_v2.csv`, writes `other/pk_100_final_v3.csv`, seed=42)

Running these scripts in order on the same input files produces identical output.
