#!/usr/bin/env python3
"""
Step 1: DNS Resolution only — fast, no Team Cymru
Resolves all 1522 domains to IPs and saves results.
Run from pkinternet root:
    python3 other/dns_pk_filter.py
"""

import socket
import json

INPUT_FILE  = "other/isps.txt"
OUTPUT_JSON = "other/isps_res.json"

def resolve(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ip, None
    except Exception as e:
        return None, str(e)

def main():
    with open(INPUT_FILE) as f:
        domains = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(domains)} domains")

    # load existing cache if resuming
    try:
        with open(OUTPUT_JSON) as f:
            results = json.load(f)
        print(f"Resuming from cache ({len(results)} already done)")
    except Exception:
        results = {}

    for i, domain in enumerate(domains):
        if domain in results:
            continue

        ip, err = resolve(domain)
        results[domain] = {"ip": ip, "error": err}

        if ip:
            print(f"  ✓ {domain:<45} → {ip}")
        else:
            print(f"  ✗ {domain:<45} — {err}")

        # save checkpoint every 50 domains
        if i % 50 == 0:
            with open(OUTPUT_JSON, "w") as f:
                json.dump(results, f, indent=2)
            print(f"  [checkpoint {i}/{len(domains)}]")

    # final save
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    resolved = sum(1 for v in results.values() if v["ip"])
    failed   = sum(1 for v in results.values() if not v["ip"])
    print(f"\nDone: {resolved} resolved, {failed} failed")
    print(f"Saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()