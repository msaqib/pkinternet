#!/usr/bin/env python3
"""
Draw a CISA-sector- and CDN-provider-diverse sample of TOTAL sites from
cdn_hits_cisa.csv. Not a full sector x provider grid (most sectors only
have a handful of providers with any real presence), instead:

  1. Split TOTAL evenly across the 8 CISA sectors.
  2. Within each sector's slice, spread picks across whichever
     providers are available there, preferring providers that are
     least-used so far in the overall sample (so one sector's slice
     isn't accidentally all-Cloudflare), and preferring rarer
     providers on ties (so CDN77/CDNetworks/Prolexic, which barely
     exist outside Commercial Facilities, get a shot when they're
     available there).

Run from site_collection/pipeline/:
    python3 sample_cdn_diverse.py --total 40
"""
import argparse
import csv
import random
from collections import Counter, defaultdict

IN_FILE = "outputs/cdn_hits_cisa.csv"
OUT_FILE = "outputs/cdn_sample_diverse.csv"
SEED = 42

SECTORS = [
    "Commercial Facilities", "Education", "Financial Services",
    "Government Services & Facilities", "Healthcare & Public Health",
    "Energy", "Communications", "Transportation Systems",
]

BRAND_MAP = {
    "CLOUDFLARENET": "Cloudflare", "CLOUDFLARESPECTRUM": "Cloudflare",
    "FASTLY": "Fastly",
    "AKAMAI-ASN1": "Akamai", "AKAMAI-ASN2": "Akamai", "AKAMAI-AS": "Akamai",
    "AKAMAI-AMS": "Akamai", "AKAMAI-LINODE-AP": "Akamai",
    "PROLEXIC-IP-PROTECT": "Akamai (Prolexic)",
    "PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK": "Akamai (Prolexic)",
    "INCAPSULA": "Imperva/Incapsula",
    "CDN77": "CDN77",
    "CDNetworks": "CDNetworks", "CDNETWORKS-AS-KR-KR": "CDNetworks",
}


def brand_of(as_name):
    return BRAND_MAP.get(as_name.split(" - ")[0].strip(), "Other")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, required=True)
    args = ap.parse_args()

    by_sector_brand = defaultdict(lambda: defaultdict(list))
    with open(IN_FILE) as f:
        for row in csv.DictReader(f):
            by_sector_brand[row["cisa_sector"]][brand_of(row["as_name"])].append(row)

    total_pool_by_brand = Counter()
    for sector in by_sector_brand.values():
        for brand, rows in sector.items():
            total_pool_by_brand[brand] += len(rows)

    per_sector, remainder = divmod(args.total, len(SECTORS))
    shares = [per_sector + 1 if i < remainder else per_sector for i in range(len(SECTORS))]

    random.seed(SEED)
    global_usage = Counter()
    final = []

    for sector, need in zip(SECTORS, shares):
        brand_pools = {b: rows for b, rows in by_sector_brand[sector].items() if rows}
        order = sorted(brand_pools, key=lambda b: (global_usage[b], total_pool_by_brand[b]))

        picked_this_sector = []
        used_domains = set()
        i = 0
        while len(picked_this_sector) < need and order:
            brand = order[i % len(order)]
            pool = [r for r in brand_pools[brand] if r["domain"] not in used_domains]
            if pool:
                choice = random.choice(pool)
                used_domains.add(choice["domain"])
                picked_this_sector.append((brand, choice))
                global_usage[brand] += 1
            i += 1
            if i > len(order) * (need + 5):  # safety valve, pool exhausted
                break

        final.extend((sector, brand, row) for brand, row in picked_this_sector)

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "as_name", "cisa_sector", "cdn_brand"])
        for sector, brand, r in final:
            w.writerow([r["domain"], r["ip"], r["asn"], r["as_name"], sector, brand])

    print(f"{'sector':<32} {'provider':<20} domain")
    print("-" * 80)
    for sector, brand, r in final:
        print(f"{sector:<32} {brand:<20} {r['domain']}")

    print(f"\n{len(final)} total -> {OUT_FILE}")
    print("\nProvider totals across the sample:")
    for brand, n in Counter(b for _, b, _ in final).most_common():
        print(f"  {brand:<20} {n}")


if __name__ == "__main__":
    main()
