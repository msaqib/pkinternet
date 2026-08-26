#!/usr/bin/env python3
"""
Find Pakistani websites hosted on ACE CDN (AS139341 - Tencent EdgeOne)
Run from pkinternet root:
    python3 other/find_ace_cdn_sites.py
"""

import json
import dns.resolver

INPUT_JSON = "../../site_collection/pipeline/outputs/tranco_350k_resolved.json"
OUTPUT_TXT = "experiments/08_CDN/ace_cdn_sites.txt"
TARGET_ASN = "139341"

def asn_for_ip(ip):
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split("|")]
            asn = parts[0].strip().split()[0]
            return asn
    except Exception:
        pass
    return None

def main():
    with open(INPUT_JSON) as f:
        data = json.load(f)

    print(f"Checking {len(data)} domains...")
    ace_sites = []

    for domain, v in data.items():
        ip = v if isinstance(v, str) else v.get("ip")
        if not ip:
            continue
        asn = asn_for_ip(ip)
        if asn == TARGET_ASN:
            print(f"  FOUND: {domain} → {ip} (AS{asn})")
            ace_sites.append(domain)

    with open(OUTPUT_TXT, "w") as f:
        for d in ace_sites:
            f.write(d + "\n")

    print(f"\nFound {len(ace_sites)} ACE CDN sites")
    print(f"Saved to {OUTPUT_TXT}")

if __name__ == "__main__":
    main()