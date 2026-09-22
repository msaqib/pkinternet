#!/usr/bin/env python3
"""
Step 2: bulk ASN/country classification via Team Cymru's bulk whois
service. One TCP session classifies thousands of IPs at once, vastly
faster than one-IP-at-a-time DNS TXT lookups (the old asn_pk_filter.py
approach, fine for ~1,500 domains, not for 300k-500k).

Checkpoints after every batch, resumable the same way as resolve_dns.py.

Run from site_collection/pipeline/:
    python3 classify_bulk.py
"""
import json
import os
import socket
import time

RESOLVED_CACHE = "outputs/resolved_cache.json"
ASN_CACHE = "outputs/asn_cache.json"
BATCH_SIZE = 1000


def bulk_cymru_lookup(ip_list):
    query = "begin\nverbose\n" + "\n".join(ip_list) + "\nend\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect(("whois.cymru.com", 43))
    sock.sendall(query.encode())
    response = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    sock.close()
    return response.decode(errors="replace")


def main():
    with open(RESOLVED_CACHE) as f:
        resolved = json.load(f)

    ips = sorted({v["ip"] for v in resolved.values() if v.get("ip")})

    if os.path.exists(ASN_CACHE):
        with open(ASN_CACHE) as f:
            asn_cache = json.load(f)
    else:
        asn_cache = {}

    todo = [ip for ip in ips if ip not in asn_cache]
    print(f"{len(todo)} IPs left to classify out of {len(ips)} unique IPs")

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        raw = bulk_cymru_lookup(batch)
        for line in raw.strip().split("\n")[1:]:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                asn, ip, prefix, cc, registry, allocated, as_name = parts[:7]
                asn_cache[ip] = {"asn": asn, "country": cc, "as_name": as_name}

        with open(ASN_CACHE, "w") as f:
            json.dump(asn_cache, f)
        print(f"  [checkpoint] {min(i + BATCH_SIZE, len(todo))}/{len(todo)} IPs classified")
        time.sleep(1)  # stay polite to Cymru's service between batches

    print(f"Done: {len(asn_cache)} IPs classified")


if __name__ == "__main__":
    main()
