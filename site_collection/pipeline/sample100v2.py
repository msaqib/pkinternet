#!/usr/bin/env python3
"""
Proportional sampling of 100 sites from site_candidates_cisa.csv.
Allocation based on PK+CDN site counts per CISA sector.
Within each sector: 40% Pakistani, 40% CDN, 20% Abroad.
Fallback: if not enough of one type, fill from largest remaining pool.
Reproducible with seed=42.

Run from site_collection/, not from pipeline/:
    python3 pipeline/sample100v2.py

Input:  pipeline/outputs/site_candidates_cisa.csv
Output: pipeline/outputs/pk_100_final_v2.csv
"""

import csv
import random
from collections import defaultdict, Counter

INPUT_FILE  = "outputs/site_candidates_cisa.csv"
OUTPUT_FILE = "outputs/pk_100_final_v2.csv"
TARGET      = 100
SEED        = 42
MIN_PER_SECTOR = 2

def main():
    # ── load sites ────────────────────────────────────────────────────────────
    sites = []
    with open(INPUT_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sites.append(row)

    print(f"Loaded {len(sites)} sites from {INPUT_FILE}")

    # ── group by sector and hosting ───────────────────────────────────────────
    by_sector = defaultdict(lambda: defaultdict(list))
    for s in sites:
        by_sector[s['cisa_sector']][s['hosting']].append(s)

    all_sectors = sorted(by_sector.keys())

    # ── compute PK+CDN counts per sector for allocation ───────────────────────
    pk_cdn_counts = {}
    for sector in all_sectors:
        hd = by_sector[sector]
        pk_cdn_counts[sector] = (
            len(hd.get('Pakistani', [])) +
            len(hd.get('CDN', []))
        )

    total_pk_cdn = sum(pk_cdn_counts.values())

    print(f"\nPK+CDN pool per sector:")
    for s in all_sectors:
        hd = by_sector[s]
        pk  = len(hd.get('Pakistani', []))
        cdn = len(hd.get('CDN', []))
        abl = len(hd.get('Abroad', []))
        print(f"  {s:<45} PK={pk:<4} CDN={cdn:<4} Abroad={abl:<4} PK+CDN={pk_cdn_counts[s]}")

    # ── proportional allocation based on PK+CDN counts ───────────────────────
    # give everyone minimum first, distribute remainder proportionally
    allocations = {s: MIN_PER_SECTOR for s in all_sectors}
    remainder = TARGET - MIN_PER_SECTOR * len(all_sectors)

    extras = {}
    for s in all_sectors:
        extras[s] = round(pk_cdn_counts[s] / total_pk_cdn * remainder)

    # adjust to exactly remainder
    diff = remainder - sum(extras.values())
    largest = max(extras, key=lambda x: pk_cdn_counts[x])
    extras[largest] += diff

    allocations = {s: MIN_PER_SECTOR + extras[s] for s in all_sectors}

    print(f"\nAllocations (total={sum(allocations.values())}):")
    for s, n in sorted(allocations.items(), key=lambda x: -x[1]):
        print(f"  {s:<45} {n}")

    # ── sample 40-40-20 within each sector ───────────────────────────────────
    random.seed(SEED)
    sampled = []
    notes = []

    for sector in all_sectors:
        total_n  = allocations[sector]
        pk_pool  = by_sector[sector].get('Pakistani', [])
        cdn_pool = by_sector[sector].get('CDN', [])
        abl_pool = by_sector[sector].get('Abroad', [])

        n_pk  = round(total_n * 0.40)
        n_cdn = round(total_n * 0.40)
        n_abl = total_n - n_pk - n_cdn

        actual_pk  = min(n_pk,  len(pk_pool))
        actual_cdn = min(n_cdn, len(cdn_pool))
        actual_abl = min(n_abl, len(abl_pool))
        shortfall  = total_n - actual_pk - actual_cdn - actual_abl

        if shortfall > 0:
            rem_pk  = len(pk_pool)  - actual_pk
            rem_cdn = len(cdn_pool) - actual_cdn
            rem_abl = len(abl_pool) - actual_abl
            if rem_pk >= rem_cdn and rem_pk >= rem_abl:
                actual_pk  = min(actual_pk  + shortfall, len(pk_pool))
            elif rem_cdn >= rem_abl:
                actual_cdn = min(actual_cdn + shortfall, len(cdn_pool))
            else:
                actual_abl = min(actual_abl + shortfall, len(abl_pool))
            notes.append(
                f"  NOTE: {sector} used fallback "
                f"(PK={actual_pk} CDN={actual_cdn} Abroad={actual_abl})"
            )

        picked = (
            random.sample(pk_pool,  actual_pk)  +
            random.sample(cdn_pool, actual_cdn) +
            random.sample(abl_pool, actual_abl)
        )
        for s in picked:
            s['sampled_sector'] = sector
            sampled.append(s)

    # ── print results ─────────────────────────────────────────────────────────
    if notes:
        print(f"\nFallback notes:")
        for n in notes:
            print(n)

    print(f"\nFinal sample: {len(sampled)} sites")
    print("\nBreakdown by sector and hosting:")
    by_s = defaultdict(Counter)
    for s in sampled:
        by_s[s['cisa_sector']][s['hosting']] += 1
    for sector in sorted(by_s.keys()):
        c = by_s[sector]
        total = sum(c.values())
        print(f"  {sector:<45} PK={c.get('Pakistani',0):<4} "
              f"CDN={c.get('CDN',0):<4} Abroad={c.get('Abroad',0):<4} total={total}")

    # ── save ──────────────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(
            f, fieldnames=['website', 'hosting', 'isp_cdn', 'rank', 'cisa_sector']
        )
        writer.writeheader()
        for s in sampled:
            writer.writerow({
                'website':     s['website'],
                'hosting':     s['hosting'],
                'isp_cdn':     s.get('isp_cdn', ''),
                'rank':        s.get('rank', ''),
                'cisa_sector': s['cisa_sector'],
            })

    print(f"\nSaved to {OUTPUT_FILE}")
    print(f"Seed used: {SEED} — rerun anytime to get identical results")

if __name__ == "__main__":
    main()