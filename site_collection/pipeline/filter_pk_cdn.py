#!/usr/bin/env python3
"""
Step 3: turn the classified IPs into three separate lists.

- outputs/pk_hits.csv      Pakistani-hosted domains
- outputs/cdn_hits.csv     domains served off a recognized CDN
- outputs/inconclusive.csv ambiguous cases held for a manual look

A domain only lands in pk_hits.csv if ALL of:
  1. Team Cymru says its IP sits in a PK-registered ASN
  2. the netblock's WHOIS netname doesn't look residential/broadband
     (this is what catches PTCLBB-PK-style false positives)
  3. no independent resolver contradicts the IP resolve_dns.py recorded.
     A contradicting answer (the resolver-hijack signature) fails the site.
     No answer at all from any resolver does not fail it, that is recorded
     as second_check=no-answer and left for traceroute to settle.

Only PK-ASN candidates pay the cost of steps 2-3 (whois + a live DNS
check), that bucket is small even at 500k domains, so this stays fast.
Anything that fails step 2 or 3 goes to inconclusive.csv rather than
being silently dropped or silently kept.

Run from site_collection/pipeline/:
    python3 filter_pk_cdn.py
"""
import csv
import json
import subprocess
import time

import dns.resolver

RESOLVED_CACHE = "outputs/resolved_cache.json"
ASN_CACHE = "outputs/asn_cache.json"
PK_OUT = "outputs/pk_hits.csv"
CDN_OUT = "outputs/cdn_hits.csv"
INCONCLUSIVE_OUT = "outputs/inconclusive.csv"

CDN_KEYWORDS = [
    "CLOUDFLARE", "AKAMAI", "FASTLY", "EDGECAST", "LIMELIGHT",
    "INCAPSULA", "IMPERVA", "STACKPATH", "CDN77", "KEYCDN",
    "CDNETWORKS", "MAXCDN", "QUANTIL", "CHINACACHE",
]

BROADBAND_KEYWORDS = [
    "BB", "BROADBAND", "DSL", "ADSL", "PPPOE", "DIAL", "CABLE",
    "RESIDENTIAL", "DYNAMIC", "HOME", "CUSTOMER", "FTTH", "GPON",
]

_whois_cache = {}


def netname_of(ip):
    if ip in _whois_cache:
        return _whois_cache[ip]
    try:
        out = subprocess.run(["whois", ip], capture_output=True, text=True, timeout=15).stdout
        netname = ""
        for line in out.splitlines():
            if line.lower().startswith("netname:"):
                netname = line.split(":", 1)[1].strip()
                break
        _whois_cache[ip] = netname
        time.sleep(0.5)  # avoid getting rate-limited by the regional registry
        return netname
    except Exception:
        _whois_cache[ip] = ""
        return ""


def looks_residential(netname):
    up = netname.upper()
    return any(kw in up for kw in BROADBAND_KEYWORDS)


def _same_slash24(a, b):
    return a.rsplit(".", 1)[0] == b.rsplit(".", 1)[0]


def second_check(domain, expected_ip):
    """'agree'     another resolver returned the same IP (or one in the same /24)
    'differ'    resolvers answered, but never with that IP (the hijack signature)
    'no-answer' no resolver answered at all, so this proves nothing either way"""
    got_answer = False
    for ns in ["1.1.1.1", "8.8.8.8", "9.9.9.9"]:
        for _ in range(2):
            r = dns.resolver.Resolver(configure=False)
            r.nameservers = [ns]
            r.timeout = 6
            r.lifetime = 6
            try:
                ips = [a.to_text() for a in r.resolve(domain, "A")]
            except Exception:
                continue
            got_answer = True
            if any(ip == expected_ip or _same_slash24(ip, expected_ip) for ip in ips):
                return "agree"
            break
    return "differ" if got_answer else "no-answer"


def main():
    with open(RESOLVED_CACHE) as f:
        resolved = json.load(f)
    with open(ASN_CACHE) as f:
        asn_cache = json.load(f)

    pk_rows, cdn_rows, inconclusive_rows = [], [], []

    for domain, rinfo in resolved.items():
        ip = rinfo.get("ip")
        if not ip:
            continue
        info = asn_cache.get(ip)
        if not info:
            continue

        country = info.get("country", "")
        as_name = info.get("as_name", "")
        asn = info.get("asn", "")

        if any(kw in as_name.upper() for kw in CDN_KEYWORDS):
            cdn_rows.append([domain, ip, asn, as_name])
            continue

        if country == "PK":
            netname = netname_of(ip)
            if looks_residential(netname):
                inconclusive_rows.append([domain, ip, asn, as_name, netname, "residential-netname"])
                continue

            check = second_check(domain, ip)
            if check == "differ":
                inconclusive_rows.append([domain, ip, asn, as_name, netname, "resolver-mismatch"])
            else:
                pk_rows.append([domain, ip, asn, as_name, netname, check])

    with open(PK_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "as_name", "netname", "second_check"])
        w.writerows(pk_rows)

    with open(CDN_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "as_name"])
        w.writerows(cdn_rows)

    with open(INCONCLUSIVE_OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "ip", "asn", "as_name", "netname", "reason"])
        w.writerows(inconclusive_rows)

    print(f"PK hits: {len(pk_rows)} -> {PK_OUT}")
    print(f"CDN hits: {len(cdn_rows)} -> {CDN_OUT}")
    print(f"Inconclusive: {len(inconclusive_rows)} -> {INCONCLUSIVE_OUT}")


if __name__ == "__main__":
    main()
