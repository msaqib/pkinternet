#!/usr/bin/env python3
"""
Pull a small, provider-diverse sample out of cdn_hits.csv (66k+ rows,
dominated by Cloudflare). Groups sub-ASNs under their parent brand
(e.g. CLOUDFLARENET + CLOUDFLARESPECTRUM -> Cloudflare) then samples
up to N per brand, so the result actually spans providers instead of
just being mostly Cloudflare.

Run from site_collection/pipeline/:
    python3 sample_cdn_providers.py --per-provider 10
"""
import argparse
import csv
import random
from collections import defaultdict

IN_FILE = "outputs/cdn_hits.csv"
OUT_FILE = "outputs/cdn_sample.csv"
SEED = 42

BRAND_MAP = {
    "CLOUDFLARENET": "Cloudflare",
    "CLOUDFLARESPECTRUM": "Cloudflare",
    "FASTLY": "Fastly",
    "AKAMAI-ASN1": "Akamai",
    "AKAMAI-ASN2": "Akamai",
    "AKAMAI-AS": "Akamai",
    "AKAMAI-AMS": "Akamai",
    "AKAMAI-LINODE-AP": "Akamai",
    "PROLEXIC-IP-PROTECT": "Akamai (Prolexic)",
    "PROLEXIC-TECHNOLOGIES-DDOS-MITIGATION-NETWORK": "Akamai (Prolexic)",
    "INCAPSULA": "Imperva/Incapsula",
    "CDN77": "CDN77",
    "CDNetworks": "CDNetworks",
    "CDNETWORKS-AS-KR-KR": "CDNetworks",
}


def brand_of(as_name):
    key = as_name.split(" - ")[0].strip()
    return BRAND_MAP.get(key, key)


def even_split(total, n_buckets):
    base, remainder = divmod(total, n_buckets)
    return [base + 1 if i < remainder else base for i in range(n_buckets)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-provider", type=int, default=None)
    ap.add_argument("--total", type=int, default=None)
    args = ap.parse_args()

    by_brand = defaultdict(list)
    with open(IN_FILE) as f:
        for row in csv.DictReader(f):
            by_brand[brand_of(row["as_name"])].append(row)

    brands = sorted(by_brand.items(), key=lambda x: -len(x[1]))

    if args.total:
        shares = even_split(args.total, len(brands))
    else:
        per = args.per_provider or 10
        shares = [per] * len(brands)

    random.seed(SEED)
    sampled = []
    print("CDN brands found:")
    for (brand, rows), share in zip(brands, shares):
        n = min(share, len(rows))
        picked = random.sample(rows, n)
        sampled.extend((brand, r) for r in picked)
        print(f"  {brand:<22} {n:>3} sampled  (of {len(rows)} available)")

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "as_name", "cdn_brand"])
        for brand, r in sampled:
            w.writerow([r["domain"], r["ip"], r["asn"], r["as_name"], brand])

    print(f"\nTotal sampled: {len(sampled)} -> {OUT_FILE}")


if __name__ == "__main__":
    main()
