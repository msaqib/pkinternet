#!/usr/bin/env python3
"""
Step 2: ASN lookup to find PK-hosted sites
Reads tranco_pk_resolved.json, looks up each IP via Team Cymru,
and saves the ones with country == PK.

Run from pkinternet root:
    python3 other/asn_pk_filter.py
"""

import json
import dns.resolver

INPUT_JSON  = "other/tranco_pk_resolved.json"
OUTPUT_JSON = "other/tranco_pk_asn.json"
OUTPUT_PK   = "other/tranco_pk_hosted.txt"

_cache = {}

def asn_for_ip(ip):
    if ip in _cache:
        return _cache[ip]
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split("|")]
            asn     = parts[0].strip().split()[0]
            country = parts[2].strip() if len(parts) > 2 else ""
            _cache[ip] = (asn, country)
            return asn, country
    except Exception:
        pass
    _cache[ip] = (None, "")
    return None, ""

def get_ip(v):
    if isinstance(v, dict):
        return v.get("ip")
    if isinstance(v, str):
        return v if v else None
    return None

def main():
    with open(INPUT_JSON) as f:
        results = json.load(f)

    print(f"Loaded {len(results)} entries")

    pk_sites = []
    all_asn  = {}

    for i, (domain, v) in enumerate(results.items()):
        ip = get_ip(v)
        if not ip:
            continue

        if i % 100 == 0:
            print(f"  [{i}/{len(results)}] processing...")

        asn, country = asn_for_ip(ip)
        all_asn[domain] = {"ip": ip, "asn": asn, "country": country}

        if country == "PK":
            pk_sites.append({"domain": domain, "ip": ip, "asn": asn})
            print(f"  ✓ PK  {domain:<45} {ip:<18} AS{asn}")

    # save full ASN results
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_asn, f, indent=2)

    # save PK-hosted list
    with open(OUTPUT_PK, "w") as f:
        for s in pk_sites:
            f.write(f"{s['domain']},{s['ip']},{s['asn']}\n")

    print(f"\nTotal:       {len(results)}")
    print(f"PK-hosted:   {len(pk_sites)}")
    print(f"Saved ASNs → {OUTPUT_JSON}")
    print(f"Saved PK   → {OUTPUT_PK}")

if __name__ == "__main__":
    main()