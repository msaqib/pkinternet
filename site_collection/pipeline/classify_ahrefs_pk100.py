#!/usr/bin/env python3
"""
Resolve + classify the Ahrefs "Top Websites in Pakistan" list (actual
PK search-traffic ranking, not generic global Tranco rank). Small list
(100), so this runs synchronously, no checkpointing needed.

Run from site_collection/pipeline/:
    python3 classify_ahrefs_pk100.py
"""
import csv
import socket
import time

import dns.resolver

IN_FILE = "outputs/ahrefs_pk_top100.csv"
OUT_FILE = "outputs/ahrefs_pk100_classified.csv"

RESOLVERS = ["8.8.8.8", "1.1.1.1"]

CDN_KEYWORDS = [
    "CLOUDFLARE", "AKAMAI", "FASTLY", "EDGECAST", "LIMELIGHT",
    "INCAPSULA", "IMPERVA", "STACKPATH", "CDN77", "KEYCDN",
    "CDNETWORKS", "MAXCDN", "QUANTIL", "CHINACACHE",
]
# Only the hyperscaler's OWN first-party network, not "hosted on their
# cloud" — AMAZON-02 / GOOGLE-CLOUD-PLATFORM / MICROSOFT-AZURE are
# generic rented-compute ASNs used by unrelated third parties (Netflix,
# ESPN, Wiley, and Spotify/LinkedIn all showed up under one of these
# and none of them are Google/Amazon products). Matched as an AS-name
# prefix, not a loose substring, specifically to exclude those.
#
# Amazon has no reliable split at all: primevideo.com (a real Amazon
# product) showed the same AMAZON-02 ASN as Netflix and Wiley (not
# Amazon). So Amazon is left out of this list entirely — Amazon's own
# properties will default to "Abroad" here, a known false negative,
# preferred over false-positiving every AWS-hosted third party.
HYPERSCALER_ASNAME_PREFIXES = [
    "GOOGLE - Google LLC",
    "FACEBOOK",
    "APPLE-ENGINEERING",
    "MICROSOFT-CORP-MSN-AS-BLOCK",
]


def resolve(domain):
    for resolver_ip in RESOLVERS:
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = [resolver_ip]
        r.timeout = 5
        r.lifetime = 5
        try:
            ans = r.resolve(domain, "A")
            return ans[0].to_text(), None
        except Exception as e:
            last_err = type(e).__name__
    return None, last_err


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


def classify(as_name, country):
    if any(as_name.startswith(p) for p in HYPERSCALER_ASNAME_PREFIXES):
        return "Hyperscaler"
    up = as_name.upper()
    if any(kw in up for kw in CDN_KEYWORDS):
        return "CDN"
    if country == "PK":
        return "Pakistani"
    return "Abroad"


def main():
    rows = list(csv.DictReader(open(IN_FILE)))

    resolved = {}
    for r in rows:
        ip, err = resolve(r["domain"])
        resolved[r["domain"]] = ip
        print(f"  {r['domain']:<24} -> {ip or 'FAILED: ' + str(err)}")

    ips = sorted({ip for ip in resolved.values() if ip})
    raw = bulk_cymru_lookup(ips)
    asn_info = {}
    for line in raw.strip().split("\n")[1:]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7:
            asn, ip, prefix, cc, registry, allocated, as_name = parts[:7]
            asn_info[ip] = {"asn": asn, "country": cc, "as_name": as_name}

    out_rows = []
    for r in rows:
        ip = resolved.get(r["domain"])
        info = asn_info.get(ip, {}) if ip else {}
        infra_type = classify(info.get("as_name", ""), info.get("country", "")) if info else "resolve-failed"
        out_rows.append({
            "rank": r["rank"],
            "domain": r["domain"],
            "ahrefs_category": r["ahrefs_category"],
            "ip": ip or "",
            "asn": info.get("asn", ""),
            "country": info.get("country", ""),
            "as_name": info.get("as_name", ""),
            "infra_type": infra_type,
        })

    with open(OUT_FILE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"\nSaved -> {OUT_FILE}\n")
    print(f"{'domain':<24} {'infra_type':<12} {'ahrefs_category':<22} as_name")
    print("-" * 100)
    for r in out_rows:
        print(f"{r['domain']:<24} {r['infra_type']:<12} {r['ahrefs_category']:<22} {r['as_name']}")

    from collections import Counter
    print("\nInfra type breakdown:")
    for t, n in Counter(r["infra_type"] for r in out_rows).most_common():
        print(f"  {t:<14} {n}")


if __name__ == "__main__":
    main()
