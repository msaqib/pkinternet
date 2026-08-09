#!/usr/bin/env python3
"""
Experiment 10 addon — Google Global Cache (GGC) detection via report_mapping
==============================================================================
DOES NOT WORK AS WRITTEN — DO NOT RE-RUN WITHOUT READING THIS FIRST.

Tried 2026-08-09: RIPE Atlas's "http" measurement type refuses any target
that isn't a RIPE Atlas anchor. Every create_http() call here 400s with
{"source": {"pointer": "/definitions/0/target"}, "detail": "Only anchors
may be targeted"}. This is a platform-wide policy (presumably anti-abuse —
Atlas won't let ~thousands of home-router probes fire arbitrary HTTP GETs
at any host on the internet), not something fixable by changing this
payload. Confirmed by reproducing the raw API call directly — same error
regardless of probe.

Working alternative (not yet executed — blocked on Tailscale access as of
2026-08-09, see conversation): the "LocalInternetProjNN" probes in the
"RIPE Atlas Probes Status" Google Sheet are physical Raspberry Pis with
Tailscale hostnames (e.g. raslas-01.taile9d635.ts.net). SSH into one
directly and just run:
    curl -s 'http://redirector.googlevideo.com/report_mapping?di=no'
No Atlas restriction applies — it's a plain unrestricted Linux box, not a
rented Atlas probe slot. Needs whoever admins that tailnet (Dr Saqib) to
add the operator's machine to it first.

--- original design doc below, still accurate for the *idea*, just not the
    execution path ---

Traceroute-based GGC detection (run.py / fetch.py) can't tell an ISP's own
peering router from an actual embedded cache: any traceroute leaving a PK
ISP into Google's network shows a PK-ASN hop right before AS15169 regardless
of whether a cache exists, so ASN-adjacency alone is not a valid signal.

Google exposes a diagnostic endpoint that sidesteps this: a GET to
http://redirector.googlevideo.com/report_mapping?di=no returns the specific
cache hostname Google's redirector has assigned to the requesting network,
e.g. "cyber-lhe12" (operator + IATA city code + node number). This script
*attempts* to fire that request as an Atlas HTTP measurement from every
currently connected Pakistani probe, with DNS resolved on the probe itself
(so the GeoDNS/network answer reflects that probe's real ISP path) — see the
"DOES NOT WORK" note above for why that attempt fails.

Results saved to experiments/10_local_cdn_reach/results/ggc_mapping_<ts>/
"""

import requests
import csv
import json
import re
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("RIPE_API_KEY", "your-api-key-here")
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# All probes currently known to be Connected (checked live 2026-08-09), spanning
# every ISP in the roster including the 3 newly-discovered ones from the
# "RIPE Atlas Probes Status" sheet (1016467 Nayatel, 1016468 Orbit, 65761 Cybernet).
PROBES = [
    (1015679, 'Nova (Lahore)',              136174),
    (1016036, 'Cybernet (Haripur)',           9541),
    (1016143, 'Cybernet (Karachi)',            9541),
    (65761,   'Cybernet (Karachi) 2',          9541),
    (1016126, 'PTCL (Karachi)',               17557),
    (7764,    'PTCL (LUMS, Lahore)',          17557),
    (64535,   'Orbit (Faisalabad)',          151983),
    (1016468, 'Orbit (Faisalabad) 2',        151983),
    (62224,   'Wateen (Lahore, ex-Zartash)',  38264),
    (60223,   'Nayatel (Islamabad)',          23674),
    (65892,   'Nayatel (Islamabad) 2',        23674),
    (1016467, 'Nayatel (Islamabad) 3',        23674),
    (7613,    'Zcom (Lahore)',               152605),
    (64078,   'TES (Rawalpindi)',            135407),
    (64722,   'TES (Karachi)',               135407),
    (1014872, 'Fasttel (Islamabad)',         150683),
]

TARGET_HOST = "redirector.googlevideo.com"
TARGET_PATH = "/report_mapping"
TARGET_QS   = "di=no"

RESULTS_DIR = os.path.join('experiments', '10_local_cdn_reach', 'results', f'ggc_mapping_{TIMESTAMP}')
RESULTS_CSV = os.path.join(RESULTS_DIR, f'ggc_mapping_{TIMESTAMP}.csv')
RAW_JSON    = os.path.join(RESULTS_DIR, f'ggc_mapping_raw_{TIMESTAMP}.json')

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {"Authorization": f"Key {API_KEY}", "Content-Type": "application/json"}

RESULT_TIMEOUT = 900

# ── RIPE ATLAS ────────────────────────────────────────────────────────────────

def check_probe_status(probes):
    """Live connection check — same preflight pattern as run.py, so we never
    schedule against a probe that will just return 'No suitable probes'."""
    ids = ",".join(str(p[0]) for p in probes)
    r = requests.get(f"{BASE}/probes/", params={"id__in": ids, "page_size": 100}, timeout=15)
    r.raise_for_status()
    status_by_id = {p["id"]: p["status"]["name"] for p in r.json()["results"]}

    connected, disconnected = [], []
    for probe_id, label, asn in probes:
        st = status_by_id.get(probe_id, "Unknown")
        if st == "Connected":
            connected.append((probe_id, label, asn))
        else:
            disconnected.append((probe_id, label, asn, st))
    return connected, disconnected


def create_http(probe_id, description):
    payload = {
        "definitions": [{
            "target":           TARGET_HOST,
            "description":      description,
            "type":             "http",
            "af":               4,
            "method":           "GET",
            "path":             TARGET_PATH,
            "query_string":     TARGET_QS,
            "port":             80,
            "header_bytes":     1024,
            "body_bytes":       4096,
            "resolve_on_probe": True,   # DNS from the probe's own ISP resolver
        }],
        "probes": [{"type": "probes", "value": str(probe_id), "requested": 1}],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]


def wait_for_all(msm_ids, timeout=RESULT_TIMEOUT):
    pending, done, failed = set(msm_ids), set(), set()
    deadline = time.time() + timeout
    print(f"  Polling {len(pending)} measurements", end="", flush=True)
    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                r = requests.get(f"{BASE}/measurements/{mid}/", headers=HDR, timeout=10)
                status = r.json().get("status", {})
                sid, sname = status.get("id", 0), status.get("name", "")
                if sid >= 4 or sname == "Stopped":
                    pending.remove(mid)
                    if sname == "Stopped":
                        done.add(mid)
                    else:
                        failed.add(mid)
                        print(f"\n  FAILED {mid}: {sname}")
            except Exception:
                pass
        if pending:
            print(".", end="", flush=True)
            time.sleep(10)
    print(f"  done ({len(done)} completed, {len(failed)} failed, {len(pending)} timed out)")
    return done


def fetch_result(msm_id):
    r = requests.get(f"{BASE}/measurements/{msm_id}/results/", headers=HDR, timeout=15)
    r.raise_for_status()
    return r.json()

# ── PARSING ───────────────────────────────────────────────────────────────────

MAPPING_RE = re.compile(r'([0-9a-fA-F:.]+)\s*=>\s*([\w.-]+)\s*\(([^)]+)\)')

def extract_mapping(raw_json_blob):
    """Find the '<addr> => <cache-host> (<prefix>)' line wherever it lives in
    the result payload — regexing over the raw JSON text sidesteps needing to
    know the exact nested key path or body encoding RIPE Atlas used."""
    text = json.dumps(raw_json_blob)
    m = MAPPING_RE.search(text)
    if m:
        return {"src_addr": m.group(1), "cache_host": m.group(2), "prefix": m.group(3)}
    return None


def city_code_from_host(host):
    """Cache hostnames follow <operator>-<iata><n>[.<domain>], e.g. cyber-lhe12.
    Pull the 3-letter IATA-looking segment out for a quick human-readable read."""
    m = re.match(r'([a-z0-9]+)-([a-z]{3})\d*', host or '', re.I)
    if m:
        return m.group(1), m.group(2).upper()
    return (host or ''), None


_prefix_asn_cache = {}

def asn_for_prefix(prefix):
    """RIPEstat prefix-overview — who actually announces the network the mapped
    cache lives in. This is the automated version of the IPvFoo check: does the
    cache's own prefix belong to the probe's ISP (stayed in-network), or to
    Google/a third party (named locally but numbered/routed elsewhere)?"""
    if prefix in _prefix_asn_cache:
        return _prefix_asn_cache[prefix]
    try:
        r = requests.get("https://stat.ripe.net/data/prefix-overview/data.json",
                          params={"resource": prefix}, timeout=10)
        r.raise_for_status()
        asns = r.json().get("data", {}).get("asns", [])
        result = [(a.get("asn"), a.get("holder")) for a in asns] if asns else []
    except Exception:
        result = []
    _prefix_asn_cache[prefix] = result
    return result

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Experiment 10 addon — GGC detection via report_mapping")
    print("=" * 70)
    print(f"\n  Target: http://{TARGET_HOST}{TARGET_PATH}?{TARGET_QS}")
    print(f"  Probes: {len(PROBES)} configured")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"\n[0] Checking probe connection status...")
    active_probes, offline_probes = check_probe_status(PROBES)
    for probe_id, label, asn, st in offline_probes:
        print(f"  SKIP  {label:<30} (id {probe_id}): {st}")
    print(f"  {len(active_probes)}/{len(PROBES)} probes connected")

    print(f"\n[1] Scheduling HTTP measurements...")
    scheduled = []
    for probe_id, label, asn in active_probes:
        try:
            mid = create_http(probe_id, f"{label}→report_mapping")
            scheduled.append((mid, probe_id, label, asn))
            print(f"  {label:<30} ID: {mid}")
            time.sleep(1.0)
        except requests.HTTPError as e:
            print(f"  ERROR {label}: {e.response.status_code} — {e.response.text[:150]}")

    print(f"\n[2] Waiting for {len(scheduled)} measurements...")
    completed = wait_for_all([mid for mid, _, _, _ in scheduled])

    print(f"\n[3] Fetching + parsing results...")
    rows = []
    all_raw = {}
    for mid, probe_id, label, asn in scheduled:
        if mid not in completed:
            rows.append({'probe_id': probe_id, 'label': label, 'asn': asn,
                         'msm_id': mid, 'status': 'no_result', 'cache_host': '',
                         'operator_code': '', 'city_code': '', 'prefix': '',
                         'prefix_asn': '', 'prefix_holder': '', 'stays_in_isp': ''})
            continue
        raw = fetch_result(mid)
        all_raw[mid] = raw
        mapping = extract_mapping(raw)
        if mapping:
            op, city = city_code_from_host(mapping['cache_host'])
            # Automated version of the IPvFoo check: does the cache's own prefix
            # actually belong to this probe's ISP (AS<asn>), or to Google/someone
            # else — i.e. is the "local-sounding" hostname backed by real
            # in-network routing, or just Google's own naming convention?
            owners = asn_for_prefix(mapping['prefix'])
            owner_asns = [str(o[0]) for o in owners]
            stays_in_isp = str(asn) in owner_asns
            prefix_holder = "; ".join(f"AS{o[0]} {o[1]}" for o in owners) if owners else ""
            rows.append({'probe_id': probe_id, 'label': label, 'asn': asn,
                         'msm_id': mid, 'status': 'mapped', 'cache_host': mapping['cache_host'],
                         'operator_code': op, 'city_code': city or '', 'prefix': mapping['prefix'],
                         'prefix_asn': "; ".join(owner_asns), 'prefix_holder': prefix_holder,
                         'stays_in_isp': stays_in_isp})
            tag = f"{mapping['cache_host']}" + (f"  (city={city})" if city else "")
            tag += f"  prefix_owner=[{prefix_holder or 'unknown'}]  stays_in_isp={stays_in_isp}"
            print(f"  {label:<30} {tag}")
        else:
            rows.append({'probe_id': probe_id, 'label': label, 'asn': asn,
                         'msm_id': mid, 'status': 'no_mapping_found', 'cache_host': '',
                         'operator_code': '', 'city_code': '', 'prefix': '',
                         'prefix_asn': '', 'prefix_holder': '', 'stays_in_isp': ''})
            print(f"  {label:<30} no mapping line found in response")

    fields = ['probe_id', 'label', 'asn', 'msm_id', 'status', 'cache_host',
              'operator_code', 'city_code', 'prefix', 'prefix_asn', 'prefix_holder',
              'stays_in_isp']
    with open(RESULTS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n  CSV → {RESULTS_CSV}")

    with open(RAW_JSON, 'w') as f:
        json.dump(all_raw, f, indent=2)
    print(f"  Raw results → {RAW_JSON}")

    print(f"\n{'='*70}")
    print("  SUMMARY — cache hostname + does it actually stay inside the ISP's own network?")
    print(f"{'='*70}")
    for r in sorted(rows, key=lambda x: x['label']):
        print(f"  {r['label']:<30} {r['status']:<18} {r['cache_host']:<20} "
              f"city={r['city_code']:<4} stays_in_isp={r['stays_in_isp']}")

if __name__ == "__main__":
    main()
