#!/usr/bin/env python3
"""
Exp 1.4 — Pass A: hosting identity for the PK100 sites.
Resolve each domain -> IP -> ASN (Team Cymru) + geolocation (ip-api) -> classify
CDN / Pakistan (ISP) / Abroad (country). No RIPE credits.

    python experiments/01.4_pk100_hosting/pass_a_hosting.py
Output: results/pass_a_hosting.csv
"""
import os, re, sys, csv, socket, time
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "measurement"))
import pk_multi_probe as pk

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
SITES = os.path.join(ROOT, "data", "PK100sites.md")
OUT = os.path.join(os.path.dirname(__file__), "results")

# known anycast/CDN/cloud networks (ASN -> label)
CDN = {
    "13335": "Cloudflare", "209242": "Cloudflare", "394536": "Cloudflare",
    "20940": "Akamai", "16625": "Akamai", "21342": "Akamai", "32787": "Akamai/Prolexic",
    "16509": "AWS", "14618": "AWS", "8987": "AWS", "16510": "AWS",
    "15169": "Google", "396982": "Google Cloud", "19527": "Google",
    "54113": "Fastly", "19551": "Imperva/Incapsula", "30148": "Sucuri",
    "8075": "Microsoft/Azure", "8068": "Microsoft", "12076": "Azure",
    "13238": "Yandex", "20446": "StackPath", "60068": "CDN77", "44907": "CDN",
}
CDN_WORDS = ("cloudflare", "akamai", "fastly", "amazon", "aws", "google", "microsoft",
             "azure", "incapsula", "imperva", "sucuri", "cdn", "prolexic", "cloudfront")


def domains():
    out, seen = [], set()
    for line in open(SITES, encoding="utf-8"):
        m = re.match(r"^([a-z0-9][a-z0-9.-]*\.(?:pk|com|tv|org|net|edu))\b", line.strip(), re.I)
        if m and m.group(1) not in seen:
            seen.add(m.group(1)); out.append(m.group(1))
    return out


def geoloc(ips):
    """ip-api batch geolocation -> {ip: {...}}."""
    out = {}
    for i in range(0, len(ips), 100):
        chunk = ips[i:i + 100]
        try:
            r = requests.post("http://ip-api.com/batch?fields=status,country,countryCode,city,isp,org,as,query",
                              json=chunk, timeout=25)
            for d in r.json():
                out[d.get("query")] = d
        except Exception:
            pass
        time.sleep(1)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    doms = domains()
    print(f"resolving {len(doms)} domains...")
    resolved = {}
    for d in doms:
        try:
            resolved[d] = socket.gethostbyname(d)
        except Exception:
            resolved[d] = None
    geo = geoloc([ip for ip in resolved.values() if ip])

    rows = []
    for d in doms:
        ip = resolved[d]
        if not ip:
            rows.append(dict(domain=d, ip="", category="unresolved", host="", asn="",
                             asn_name="", geo_country="", geo_city="")); continue
        asn, prefix, cc = pk.asn_for_ip(ip)
        name = pk.asn_name(asn) if asn else ""
        g = geo.get(ip, {})
        gcc, gcountry, gcity = g.get("countryCode", ""), g.get("country", ""), g.get("city", "")
        gorg = g.get("org") or g.get("isp") or ""
        blob = f"{name} {gorg} {g.get('as','')}".lower()
        is_cdn = (asn in CDN) or any(w in blob for w in CDN_WORDS)
        if is_cdn:
            cat = "CDN"; host = CDN.get(asn) or next((w.title() for w in CDN_WORDS if w in blob), "CDN")
        elif gcc == "PK" or cc == "PK":
            cat = "Pakistan"; host = name or gorg
        else:
            cat = "Abroad"; host = f"{gcountry} ({gorg[:28]})" if gorg else gcountry
        rows.append(dict(domain=d, ip=ip, category=cat, host=host,
                         asn=("AS" + asn) if asn else "", asn_name=name[:34],
                         geo_country=gcc, geo_city=gcity))
        print(f"  {d:26} {cat:9} {host[:40]:42} {ip}")

    cols = ["domain", "ip", "category", "host", "asn", "asn_name", "geo_country", "geo_city"]
    with open(os.path.join(OUT, "pass_a_hosting.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    import collections
    c = collections.Counter(r["category"] for r in rows)
    print("\n=== HOSTING SPLIT ===")
    for k in ("CDN", "Pakistan", "Abroad", "unresolved"):
        print(f"  {k:11} {c.get(k,0):3} ({100*c.get(k,0)/len(rows):.0f}%)")
    print("\n  CDNs:", dict(collections.Counter(r["host"] for r in rows if r["category"] == "CDN")))
    print("  PK hosting ISPs:", dict(collections.Counter(r["asn_name"][:18] for r in rows if r["category"] == "Pakistan")))
    print("  Abroad countries:", dict(collections.Counter(r["geo_country"] for r in rows if r["category"] == "Abroad")))
    print(f"\n  wrote {os.path.join(OUT,'pass_a_hosting.csv')}")


if __name__ == "__main__":
    main()
