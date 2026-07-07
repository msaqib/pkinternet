#!/usr/bin/env python3
"""
Proportional sampling of 100 sites from 223 PK-hosted sites.
Reproducible with a fixed random seed.

Run from pkinternet root:
    python3 other/sample_100.py

Inputs:
    other/pk_223_categorized.csv   — full categorized list
Outputs:
    other/pk_100_final.csv         — final 100-site sample
"""

import csv
import random
from collections import defaultdict, Counter

INPUT_FILE  = "other/pk_223_categorized.csv"
OUTPUT_FILE = "other/pk_100_final.csv"
TARGET      = 100
SEED        = 42  # fixed seed for reproducibility

def main():
    # load sites
    sites = []
    with open(INPUT_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sites.append(row)

    print(f"Loaded {len(sites)} sites")

    # group by CISA sector
    by_cat = defaultdict(list)
    for s in sites:
        by_cat[s['CISA Sector']].append(s)

    print("\nCategory distribution:")
    for cat, group in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        print(f"  {cat:<45} {len(group)}")

    # proportional allocation — minimum 1 per category
    total = len(sites)
    allocations = {}
    for cat, group in by_cat.items():
        allocations[cat] = max(1, round(len(group) / total * TARGET))

    # adjust to exactly TARGET
    diff = TARGET - sum(allocations.values())
    largest = max(allocations, key=lambda x: len(by_cat[x]))
    allocations[largest] += diff

    print(f"\nProportional allocation (seed={SEED}):")
    for cat, n in sorted(allocations.items(), key=lambda x: -x[1]):
        print(f"  {cat:<45} sample {n} from {len(by_cat[cat])}")

    # sample
    random.seed(SEED)
    sampled = []
    for cat, n in allocations.items():
        group = by_cat[cat]
        sample = random.sample(group, min(n, len(group)))
        sampled.extend(sample)

    print(f"\nFinal sample: {len(sampled)} sites")

    # save
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Domain', 'IP', 'ASN', 'CISA Sector'])
        writer.writeheader()
        for s in sampled:
            writer.writerow({
                'Domain':      s['Domain'],
                'IP':          s['IP'],
                'ASN':         s['ASN'],
                'CISA Sector': s['CISA Sector'],
            })

    print(f"Saved to {OUTPUT_FILE}")

    print("\nFinal breakdown:")
    cats = Counter(s['CISA Sector'] for s in sampled)
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<45} {n}")

if __name__ == "__main__":
    main()