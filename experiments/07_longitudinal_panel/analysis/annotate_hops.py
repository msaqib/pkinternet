#!/usr/bin/env python3
"""
Annotate every unique hop IP in an Exp 07 routes file with ASN + geolocation.

Parses hop rows out of a `routes_*.txt` report (format: `format_routes.py` /
`panel_monitor.py`), skips private IPs, deduplicates, resolves ASN + AS name
via Team Cymru DNS (same two-step lookup as `pk_multi_probe.py`), and
geolocates via ip-api.com. Results are cached on disk (`hop_geo_cache.json`)
so reruns only look up IPs not already resolved.

Run from repo root:
    python3 experiments/07_longitudinal_panel/analysis/annotate_hops.py [routes_file]

Output: experiments/07_longitudinal_panel/analysis/hop_geo.csv
"""

import csv
import ipaddress
import json
import os
import re
import sys
import time

import dns.resolver
import requests

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_ROUTES_FILE = os.path.join(
    HERE, "..", "results", "a", "routes_20260718_195946.txt"
)
CACHE_PATH = os.path.join(HERE, "hop_geo_cache.json")
OUTPUT_CSV = os.path.join(HERE, "hop_geo.csv")

IPAPI_DELAY = 1.3  # seconds between ip-api requests (45/min free-tier limit)

HOP_LINE_RE = re.compile(r"^\s*(\d+)\s+(\*|[\d.]+)\s+(\d{1,3}(?:\.\d{1,3}){3})")


_PRIVATE_NETS = [ipaddress.ip_network(n) for n in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # RFC1918
    "100.64.0.0/10",                                    # CGNAT (RFC 6598)
    "127.0.0.0/8",                                       # loopback
)]


def is_private(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return any(addr in net for net in _PRIVATE_NETS)


def parse_hop_ips(routes_file):
    """Return the set of unique, non-private hop IPs found in a routes_*.txt file."""
    ips = set()
    with open(routes_file, encoding="utf-8") as f:
        for line in f:
            m = HOP_LINE_RE.match(line)
            if not m:
                continue
            ip = m.group(3)
            if not is_private(ip):
                ips.add(ip)
    return ips


# ── CACHE ─────────────────────────────────────────────────────────────────────

def load_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception:
        cache = {}
    cache.setdefault("ips", {})
    cache.setdefault("asn_names", {})
    return cache


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=0, sort_keys=True)


# ── TEAM CYMRU (ASN + country; two-step lookup for ASN + AS name) ─────────────

def asn_for_ip(ip):
    """Returns (asn, country_code) for an IP via Team Cymru origin lookup."""
    try:
        rev = ".".join(reversed(ip.split(".")))
        ans = dns.resolver.resolve(f"{rev}.origin.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split("|")]
            asn = parts[0].strip().split()[0]
            cc = parts[2].strip() if len(parts) > 2 else ""
            return asn, cc
    except Exception:
        pass
    return "", ""


def asn_name(asn, cache):
    """Returns org name for an ASN via Team Cymru, cached across IPs sharing an ASN."""
    if not asn:
        return ""
    if asn in cache["asn_names"]:
        return cache["asn_names"][asn]
    name = ""
    try:
        ans = dns.resolver.resolve(f"AS{asn}.asn.cymru.com", "TXT", lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split("|")]
            name = parts[4].strip() if len(parts) > 4 else parts[-1].strip()
    except Exception:
        pass
    cache["asn_names"][asn] = name
    return name


# ── IP-API GEOLOCATION ────────────────────────────────────────────────────────

def geolocate(ip):
    """Returns (city, lat, lon, country) via ip-api.com, or ('', None, None, '') on failure."""
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,city,lat,lon,country"},
            timeout=10,
        )
        d = r.json()
        if d.get("status") == "success":
            return d.get("city") or "", d.get("lat"), d.get("lon"), d.get("country") or ""
    except Exception:
        pass
    return "", None, None, ""


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    routes_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROUTES_FILE

    print(f"Parsing hop IPs from {routes_file} ...")
    ips = parse_hop_ips(routes_file)
    print(f"  {len(ips)} unique public hop IPs")

    cache = load_cache()
    todo = [ip for ip in sorted(ips) if ip not in cache["ips"]]
    print(f"  {len(ips) - len(todo)} already cached, {len(todo)} to look up")

    for i, ip in enumerate(todo, 1):
        asn, cc = asn_for_ip(ip)
        name = asn_name(asn, cache)
        city, lat, lon, country = geolocate(ip)

        cache["ips"][ip] = {
            "asn": asn,
            "asn_name": name,
            "country_code": cc,
            "city": city,
            "lat": lat,
            "lon": lon,
        }
        save_cache(cache)  # incremental — safe to interrupt/resume

        print(f"  [{i}/{len(todo)}] {ip:<16} AS{asn or '?':<7} {name[:30]:<30} {city or '?'}")
        time.sleep(IPAPI_DELAY)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ip", "asn", "asn_name", "country_code", "city", "lat", "lon"])
        for ip in sorted(ips, key=lambda x: tuple(int(p) for p in x.split("."))):
            row = cache["ips"].get(ip, {})
            writer.writerow([
                ip,
                row.get("asn", ""),
                row.get("asn_name", ""),
                row.get("country_code", ""),
                row.get("city", ""),
                row.get("lat", ""),
                row.get("lon", ""),
            ])

    print(f"\nCSV -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
