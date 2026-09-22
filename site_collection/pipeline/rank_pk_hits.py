#!/usr/bin/env python3
"""
Attach each PK hit's Tranco rank (looked up in the cached Tranco list the
slice was cut from, not counted from line numbers) and sort by rank.

Run from site_collection/pipeline/:
    python3 rank_pk_hits.py
"""
import csv

TRANCO_LIST = "../.tranco/N2PYW.csv"
PK_IN = "outputs/pk_hits.csv"
FIRST_PASS = "outputs/pk_hits_pass1.csv"
OUT = "outputs/pk_hits_ranked.csv"


def main():
    rank = {}
    with open(TRANCO_LIST) as f:
        for r, d in csv.reader(f):
            rank[d] = int(r)

    first = {r["domain"] for r in csv.DictReader(open(FIRST_PASS))}
    rows = list(csv.DictReader(open(PK_IN)))
    for r in rows:
        r["tranco_rank"] = rank[r["domain"]]
        r["in_pass1"] = "yes" if r["domain"] in first else "no"
    rows.sort(key=lambda r: r["tranco_rank"])

    fields = ["tranco_rank", "domain", "ip", "asn", "as_name", "netname", "second_check", "in_pass1"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})
    print(f"{len(rows)} PK hits ranked -> {OUT}")


if __name__ == "__main__":
    main()
