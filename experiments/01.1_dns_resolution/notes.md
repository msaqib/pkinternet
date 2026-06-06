# Experiment 1.1 - DNS Resolution Study

**Author:** Rayan Atif

## Objective

Find out whether **different Pakistani ISPs receive different IP addresses for the
same website**, and whether the answer **changes over time**. This is a refinement
of Experiment 01, prompted by the observation that DNS can return different results
from different vantage points and at different moments.

## Why this is separate from Experiment 01

Experiment 01 resolved each hostname **once, centrally** (on the machine running
the script) and then sent that **single IP to all five probes**. That is fine for:
- real single-server sites (one IP everywhere), and
- anycast CDNs like Cloudflare (one IP announced from many places; only the path
  differs, which Experiment 01 already captured per probe).

But it is blind to **GeoDNS** sites, which hand out a *different IP* depending on
who is asking, to steer each region to its nearest server. Experiment 01 could not
see those per-ISP differences. Rather than change the finished Experiment 01, this
study measures DNS directly.

## Method

`dns_check.py` schedules a **RIPE Atlas DNS measurement** (A record) for each
website, run on all five probes, with `use_probe_resolver = True` so each probe
resolves the name through **its own ISP's resolver**. DNS measurements are much
cheaper than traceroutes, so this is a light, repeatable check.

For each (site, probe) it records the resolved IP(s), the origin ASN of the first
IP, and a timestamp. It then reports which sites returned **different IP sets
across ISPs** - those are the GeoDNS cases, and the only ones that would be worth
re-tracing per vantage.

Run from the repo root:
```
python experiments/01.1_dns_resolution/dns_check.py
```
(Set `RIPE_API_KEY` in the environment / `.env` first. Edit `RUN_NAME`,
`BATCH_START`, `BATCH_SIZE` at the top of the script.)

## Output

`results/{RUN_NAME}/dns_{TIMESTAMP}.csv` with columns:
`hostname, label, category, probe_id, probe_asn, resolved_ips, first_ip_asn,
first_ip_asn_name, timestamp`.

To study **change over time**, run it repeatedly (e.g. on a schedule) and compare
the IPs for the same site across timestamps.

## Results (run_20260606_dns)

103 sites, resolved per-ISP. PTCL and TPCPL were offline, so 3 probes responded
(Nayatel, Transworld, Z-Com). Full per-site, per-probe IPs are in
`batch_inventory.md`; analysis in `findings/01.1_dns_resolution_analysis.md`.

- **Only 8 of 103 sites (~8%) returned different IPs across ISPs (GeoDNS):**
  `bisp.gov.pk`, `bykea.com`, `ishopping.pk`, `khaadi.com`, `lums.edu.pk`,
  `nadra.gov.pk`, `nayatel.com`, `olx.com.pk`.
- The other ~92% resolved to the **same IP from every ISP** - so Experiment 01's
  single central lookup was representative for them.
- The 8 GeoDNS sites are the only per-vantage re-trace candidates. Most are on
  GeoDNS CDNs/clouds (e.g. nadra/khaadi on Akamai-style steering); their
  "hosting country" was already ambiguous in Exp 01.

## How it feeds back into Experiment 01

- Sites where all ISPs get the same IP (~92%): Experiment 01's result stands as-is.
- The 8 GeoDNS sites: flagged here, the targeted set to re-traceroute per vantage
  if we want their true per-ISP paths.

## Probes

Same five as Experiment 01 (Z-Com, Nayatel, PTCL, Transworld AS38193, and
TPCPL/Nova AS136174). The probe list is imported from the main script so the two
experiments stay in sync.
