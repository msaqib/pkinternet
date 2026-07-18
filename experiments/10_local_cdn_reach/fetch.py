#!/usr/bin/env python3
"""
Fetch full hop-by-hop paths for experiment 10 measurements.
Shows ASN and country for each hop to check if traffic stays
within ISP network before reaching CDN (GGC detection).

Run from repo root:
    python3 experiments/10_local_cdn_reach/fetch_routes.py
"""

import requests
import dns.resolver
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get('RIPE_API_KEY')
BASE = "https://atlas.ripe.net/api/v2"
HDR = {"Authorization": f"Key {API_KEY}"}

MEASUREMENTS = {
    191508237: "Cybernet (Haripur) → google.com",
    191508242: "Cybernet (Haripur) → youtube.com",
    191508244: "Cybernet (Haripur) → facebook.com",
    191508246: "Cybernet (Haripur) → instagram.com",
    191508249: "Cybernet (Haripur) → akamai.com",
    191508254: "Cybernet (Karachi) → google.com",
    191508256: "Cybernet (Karachi) → youtube.com",
    191508258: "Cybernet (Karachi) → facebook.com",
    191508264: "Cybernet (Karachi) → instagram.com",
    191508265: "Cybernet (Karachi) → akamai.com",
    191508294: "Fasttel (Islamabad) → google.com",
    191508298: "Fasttel (Islamabad) → youtube.com",
    191508301: "Fasttel (Islamabad) → facebook.com",
    191508302: "Fasttel (Islamabad) → instagram.com",
    191508303: "Fasttel (Islamabad) → akamai.com",
    191508307: "Nayatel (Islamabad) → google.com",
    191508310: "Nayatel (Islamabad) → youtube.com",
    191508317: "Nayatel (Islamabad) → facebook.com",
    191508321: "Nayatel (Islamabad) → instagram.com",
    191508322: "Nayatel (Islamabad) → akamai.com",
    191508326: "Nayatel (Islamabad) 2 → google.com",
    191508329: "Nayatel (Islamabad) 2 → youtube.com",
    191508336: "Nayatel (Islamabad) 2 → facebook.com",
    191508339: "Nayatel (Islamabad) 2 → instagram.com",
    191508342: "Nayatel (Islamabad) 2 → akamai.com",
    191508347: "Nova (Lahore) → google.com",
    191508349: "Nova (Lahore) → youtube.com",
    191508350: "Nova (Lahore) → facebook.com",
    191508352: "Nova (Lahore) → instagram.com",
    191508356: "Nova (Lahore) → akamai.com",
    191508362: "Orbit (Faisalabad) → google.com",
    191508366: "Orbit (Faisalabad) → youtube.com",
    191508373: "Orbit (Faisalabad) → facebook.com",
    191508376: "Orbit (Faisalabad) → instagram.com",
    191508381: "Orbit (Faisalabad) → akamai.com",
    191508386: "PTCL (Karachi) → google.com",
    191508391: "PTCL (Karachi) → youtube.com",
    191508395: "PTCL (Karachi) → facebook.com",
    191508396: "PTCL (Karachi) → instagram.com",
    191508397: "PTCL (Karachi) → akamai.com",
    191508424: "TES (Rawalpindi) → google.com",
    191508427: "TES (Rawalpindi) → youtube.com",
    191508430: "TES (Rawalpindi) → facebook.com",
    191508431: "TES (Rawalpindi) → instagram.com",
    191508440: "TES (Rawalpindi) → akamai.com",
    191508441: "TES (Karachi) → google.com",
    191508443: "TES (Karachi) → youtube.com",
    191508448: "TES (Karachi) → facebook.com",
    191508454: "TES (Karachi) → instagram.com",
    191508458: "TES (Karachi) → akamai.com",
    191508460: "Transworld (Lahore) → google.com",
    191508463: "Transworld (Lahore) → youtube.com",
    191508466: "Transworld (Lahore) → facebook.com",
    191508472: "Transworld (Lahore) → instagram.com",
    191508475: "Transworld (Lahore) → akamai.com",
    191508476: "Zcom (Lahore) → google.com",
    191508478: "Zcom (Lahore) → youtube.com",
    191508483: "Zcom (Lahore) → facebook.com",
    191508487: "Zcom (Lahore) → instagram.com",
    191508493: "Zcom (Lahore) → akamai.com",
}

GOOGLE_ASNS  = {'15169', '139190', '139070', '45566', '36040'}
META_ASNS    = {'32934', '54115'}
AKAMAI_ASNS  = {'20940', '16625'}
ALL_CDN_ASNS = GOOGLE_ASNS | META_ASNS | AKAMAI_ASNS

_cache = {}

def asn_for_ip(ip):
    if ip in _cache:
        return _cache[ip]
    try:
        rev = '.'.join(reversed(ip.split('.')))
        ans = dns.resolver.resolve(f'{rev}.origin.asn.cymru.com', 'TXT', lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split('|')]
            asn = parts[0].strip().split()[0]
            cc  = parts[2].strip() if len(parts) > 2 else ''
            _cache[ip] = (asn, cc)
            return asn, cc
    except Exception:
        pass
    _cache[ip] = ('?', '?')
    return '?', '?'

def is_private(ip):
    return ip.startswith(('192.168.', '10.', '172.', '100.', '127.'))

def fetch_and_print(mid, label):
    r = requests.get(f"{BASE}/measurements/{mid}/results/", headers=HDR, timeout=15)
    if not r.ok:
        print(f"\n  {label}: HTTP {r.status_code} — skipping")
        return
    results = r.json()
    if not results:
        print(f"\n  {label}: no results")
        return
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(f"  {'hop':<5} {'rtt':>8}  {'ip':<20} {'asn':<8} {'cc':<4}  note")
    print(f"  {'-'*65}")
    for result in results:
        for hop in result.get('result', []):
            hop_num = hop.get('hop', '?')
            chosen  = next((h for h in hop.get('result', []) if 'from' in h), None)
            if not chosen:
                print(f"  {hop_num:<5} {'*':>8}  {'(no response)':<20}")
                continue
            ip  = chosen['from']
            rtt = chosen.get('rtt', 0)
            if is_private(ip):
                print(f"  {hop_num:<5} {rtt:>8.1f}  {ip:<20} {'':8} {'':4}  private")
                continue
            asn, cc = asn_for_ip(ip)
            note = ''
            if asn in ALL_CDN_ASNS:
                cdn = 'Google' if asn in GOOGLE_ASNS else ('Meta' if asn in META_ASNS else 'Akamai')
                note = f'<<< FIRST {cdn} HOP'
            elif cc not in ('PK', '?', '') and not is_private(ip) and rtt >= 40:
                note = f'exits PK ({cc})'
            print(f"  {hop_num:<5} {rtt:>8.1f}  {ip:<20} {asn:<8} {cc:<4}  {note}")


class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
    def flush(self):
        for f in self.files:
            f.flush()


def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    outfile = os.path.join(
        'experiments', '10_local_cdn_reach', 'results', f'routes_full_{timestamp}.txt'
    )
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    with open(outfile, 'w') as f:
        sys.stdout = Tee(sys.__stdout__, f)
        print("Experiment 10 — Full Hop-by-Hop Routes")
        print("Looking for GGC: path stays within ISP ASN before hitting CDN")
        print("="*70)
        for mid, label in MEASUREMENTS.items():
            fetch_and_print(mid, label)
        print(f"\n\nDone.")
        sys.stdout = sys.__stdout__

    print(f"Routes saved to {outfile}")


if __name__ == "__main__":
    main()