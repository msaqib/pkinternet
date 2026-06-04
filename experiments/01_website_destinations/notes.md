# Experiment 01 — Website Destinations

## Objective

Determine where Pakistani websites are actually hosted by running ICMP Paris
traceroutes from Pakistani ISP probes to 100 target websites. For each website
record the full hop-by-hop path, destination IP, destination ASN, destination
country, and whether the destination responded to ICMP. No classification is
done during collection — analysis is manual.

## Probes Used

| Probe ID | ASN   | Operator          | City    |
|----------|-------|-------------------|---------|
| 1015679  | 38193 | Transworld/Nova   | Lahore  |
| 1015210  | 17557 | PTCL              | Pakistan |
| 62224    | 38193 | Zartash-Office (Transworld) | Pakistan |
| 60223    | 23674 | PK_Inara (Nayatel) | Pakistan |
| 7613     | 152605 | Z COM Networks   | Pakistan |

## Target List

100 Pakistani websites across 10 categories from `targets/pk_websites_list.csv`:

- government
- news
- banking
- ecommerce
- telecom
- education
- real estate
- health
- food
- entertainment

## How to Run

Run from repo root:

```bash
python scripts/measurement/pk_multi_probe.py
```

Before each run:
1. Set `RUN_NAME` in the CONFIG section of the script
2. Ensure `RIPE_API_KEY` is set in the `.env` file at the repo root

## Output Files

Each run saves two files to `experiments/01_website_destinations/results/{RUN_NAME}/`:

| File | Contents |
|------|----------|
| `pk_grouped_TIMESTAMP.csv` | Sorted website → probe → hop |
| `pk_summary_TIMESTAMP.csv` | One row per measurement |

Key columns in grouped CSV:

```
target_hostname, probe_id, probe_asn, probe_city, hop, hop_ip,
rtt_ms, hop_asn, hop_country, hop_asn_name, target_ip,
target_asn, target_country, destination_responded
```

**Known artifact:** Probe 1015679 always shows hop 2 as `70.70.209.16`
(Shaw Communications, Canada, AS6327) at ~1.7 ms. This IP is physically in
Pakistan despite the foreign ASN. Exclude from country analysis.

**RTT interpretation (from Lahore):**
- Under 50 ms → traffic stayed in Pakistan
- Over 100 ms → traffic almost certainly exited Pakistan

## Measurement IDs


## Notes

