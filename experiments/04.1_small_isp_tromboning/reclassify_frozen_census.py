#!/usr/bin/env python3
"""
Exp 4.1 — one-time migration: backfill the trombone_hop / trombone_rtt split into
the already-collected frozen census. No new measurements: the `evidence` column
census_sweep.py already wrote per row (foreign_hop vs rtt(jump=..,max=..)) fully
determines the split, so this just relabels `status` to match what classify()
would now produce, then regenerates the CSVs derived from it.

    python experiments/04.1_small_isp_tromboning/reclassify_frozen_census.py
"""
import os, csv, glob

RUN = os.path.join(os.path.dirname(__file__), "results", "run_20260627_192918")
census_path = sorted(glob.glob(os.path.join(RUN, "census_*.csv")))[-1]

rows = list(csv.DictReader(open(census_path, encoding="utf-8")))
cols = list(rows[0].keys())
changed = 0
for r in rows:
    if r["status"] == "trombone":
        r["status"] = "trombone_hop" if r["evidence"] == "foreign_hop" else "trombone_rtt"
        changed += 1

with open(census_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print(f"relabelled {changed} rows in {census_path}")

# ---- regenerate isp_tromboning.csv (per-ISP per-source block rates) ----
by_block = {}   # (asn,prefix) -> source -> [statuses]
company_of = {}
for r in rows:
    company_of[r["asn"]] = r["company"]
    by_block.setdefault((r["asn"], r["prefix"]), {}).setdefault(r["source"], []).append(r["status"])

isp = {}  # asn -> source -> [tromb, hop, rtt, total]
for (asn, prefix), srcs in by_block.items():
    for s, statuses in srcs.items():
        any_hop = any(x == "trombone_hop" for x in statuses)
        any_rtt = any(x == "trombone_rtt" for x in statuses)
        d = isp.setdefault(asn, {}).setdefault(s, [0, 0, 0, 0])
        d[3] += 1
        if any_hop or any_rtt: d[0] += 1
        if any_hop: d[1] += 1
        if any_rtt: d[2] += 1

isp_csv = os.path.join(RUN, "isp_tromboning.csv")
with open(isp_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["asn", "company", "source", "trombone_blocks", "trombone_hop_blocks",
                "trombone_rtt_blocks", "total_blocks", "pct"])
    for asn in sorted(isp):
        for s in sorted(isp[asn]):
            tb, hb, rb, tot = isp[asn][s]
            w.writerow([asn, company_of[asn], s, tb, hb, rb, tot, f"{100*tb/tot:.0f}" if tot else 0])
print(f"wrote {isp_csv}")

# ---- regenerate filtered_reached_tromboned.csv (reached=True AND tromboned) ----
filt_path = os.path.join(RUN, "filtered_reached_tromboned.csv")
filt_rows = [r for r in rows if r["reached_isp"] == "True"
             and r["status"] in ("trombone_hop", "trombone_rtt")]
with open(filt_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(filt_rows)
print(f"wrote {filt_path} ({len(filt_rows)} rows)")

st = {}
for r in rows: st[r["status"]] = st.get(r["status"], 0) + 1
print("status counts:", st)
