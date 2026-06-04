# Project Context for Claude Code

## What this project does

RIPE Atlas traceroutes from Pakistani probes to Pakistani websites to determine
where those websites are hosted (in-country vs abroad) and how traffic is routed.
Funded by APNIC Foundation; supervised by Dr Saqib Ilyas at LUMS.

## Key files

| Path | Purpose |
|------|---------|
| `scripts/measurement/pk_multi_probe.py` | Main measurement + analysis script |
| `targets/pk_websites_list.csv` | Input: list of Pakistani websites to probe |
| `experiments/01_website_destinations/notes.md` | Experiment log |
| `experiments/01_website_destinations/results/` | Output CSVs, one subfolder per run |

## Run workflow

1. Set `RUN_NAME` at the top of `pk_multi_probe.py` (format: `run_YYYYMMDD_description`)
2. Run the script — it creates `results/{RUN_NAME}/` automatically
3. Commit the results folder to git

## Output files per run

- `pk_grouped_TIMESTAMP.csv` — per-destination rows with RTT and resolved ASN
- `pk_summary_TIMESTAMP.csv` — aggregate: how many destinations are hosted in PK vs abroad

Results CSVs **should be committed to git**. Each run gets its own subfolder.

## API key

Never hardcode the RIPE Atlas API key. Script reads it from the environment:

```bash
export RIPE_API_KEY="your-key-here"
```

## RTT interpretation (from Lahore)

| RTT | Interpretation |
|-----|---------------|
| < 50 ms | Traffic likely stayed in Pakistan |
| > 100 ms | Traffic almost certainly exited Pakistan |

## ASN lookup

Destination ASN is resolved via Team Cymru DNS (no API key required).

## Known measurement artifact

The probe on **Transworld (AS38193)** always shows hop 2 as `70.70.209.16`
(Shaw Communications, Canada) at ~1.7 ms. This IP is physically located in
Pakistan despite the foreign ASN. Exclude it from country-of-hosting analysis.

## Key Pakistani ASNs

| ASN | Operator |
|-----|---------|
| AS38193 | Transworld |
| AS17557 | PTCL |
| AS9541 | Cybernet |
| AS38264 | Wateen |
| AS9260 | Multinet |
| AS45773 | PERN |
| AS23888 | NTC |

## PKIX

Pakistan Internet Exchange — largely unused. Traffic between Pakistani networks
often exits to a foreign IXP and returns, which is a central finding this
research investigates.
