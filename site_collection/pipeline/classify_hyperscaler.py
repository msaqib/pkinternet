#!/usr/bin/env python3
"""
Small side-check for a candidate list (e.g. top global sites Pakistani
users actually visit), separate from the main CISA-sector-stratified
panel. Classifies into four buckets instead of the usual three:

  Pakistani | CDN (resold, e.g. Cloudflare/Akamai) | Hyperscaler (owns
  its network and runs its own edge/cache boxes, sometimes inside
  Pakistan) | Abroad (plain foreign hosting, no local presence)

Reuses resolved_cache.json / asn_cache.json from the 300k Tranco run
when a domain's already there; resolves+classifies fresh otherwise.

Run from site_collection/pipeline/:
    python3 classify_hyperscaler.py --list outputs/hyperscaler_candidates.txt
"""
import argparse
import csv
import json
import os
import socket

import dns.resolver

RESOLVED_CACHE = "outputs/resolved_cache.json"
ASN_CACHE = "outputs/asn_cache.json"
OUT_FILE = "outputs/hyperscaler_check.csv"

CDN_KEYWORDS = [
    "CLOUDFLARE", "AKAMAI", "FASTLY", "EDGECAST", "LIMELIGHT",
    "INCAPSULA", "IMPERVA", "STACKPATH", "CDN77", "KEYCDN",
    "CDNETWORKS", "MAXCDN", "QUANTIL", "CHINACACHE",
]

# Own-network operators known to run their own global edge/cache
# infrastructure, sometimes physically inside Pakistan, distinct from
# a resold CDN service and distinct from plain "hosted abroad".
HYPERSCALER_KEYWORDS = [
    "GOOGLE", "FACEBOOK", "META-", "MICROSOFT", "AMAZON", "APPLE",
    "NETFLIX", "TWITTER", "OPENAI", "LINKEDIN", "TIKTOK", "BYTEDANCE",
]


def resolve(hostname):
    try:
        return socket.gethostbyname(hostname), None
    except Exception as e:
        return None, str(e)


def cymru_lookup(ip):
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            asn = p[0].strip().split()[0]
            country = p[2].strip() if len(p) > 2 else ""
        ans2 = dns.resolver.resolve(f"AS{asn}.asn.cymru.com", "TXT", lifetime=5)
        as_name = ""
        for r in ans2:
            p = [x.strip() for x in str(r).strip('"').split("|")]
            as_name = p[-1].strip()
        return {"asn": asn, "country": country, "as_name": as_name}
    except Exception:
        return None


def classify(as_name, country):
    up = as_name.upper()
    if any(kw in up for kw in CDN_KEYWORDS):
        return "CDN"
    if any(kw in up for kw in HYPERSCALER_KEYWORDS):
        return "Hyperscaler"
    if country == "PK":
        return "Pakistani"
    return "Abroad"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", required=True)
    args = ap.parse_args()

    with open(args.list) as f:
        domains = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    resolved_cache = json.load(open(RESOLVED_CACHE)) if os.path.exists(RESOLVED_CACHE) else {}
    asn_cache = json.load(open(ASN_CACHE)) if os.path.exists(ASN_CACHE) else {}

    rows = []
    for domain in domains:
        ip = None
        if domain in resolved_cache and resolved_cache[domain].get("ip"):
            ip = resolved_cache[domain]["ip"]
        else:
            ip, err = resolve(domain)
            if not ip:
                rows.append([domain, "", "", "", "", f"resolve-failed: {err}"])
                continue

        info = asn_cache.get(ip)
        if not info:
            info = cymru_lookup(ip)
            if not info:
                rows.append([domain, ip, "", "", "", "asn-lookup-failed"])
                continue

        category = classify(info["as_name"], info["country"])
        rows.append([domain, ip, info["asn"], info["country"], info["as_name"], category])

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "country", "as_name", "category"])
        w.writerows(rows)

    print(f"{'domain':<24} {'category':<12} {'as_name'}")
    print("-" * 80)
    for r in rows:
        print(f"{r[0]:<24} {r[-1]:<12} {r[4] if len(r) > 4 else ''}")

    print(f"\nSaved to {OUT_FILE}")


if __name__ == "__main__":
    main()
