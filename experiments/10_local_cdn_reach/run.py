#!/usr/bin/env python3
"""
Experiment 10 — CDN Peering Local Reach
=========================================
Traces from all 14 Pakistani probes to major CDN domains.
Checks whether traffic reaches CDN nodes locally (within Pakistan)
or exits internationally before hitting CDN infrastructure.

Run from repo root:
    python3 experiments/10_local_cdn_reach/run.py

Results saved to experiments/10_local_cdn_reach/results/
"""

import requests
import csv
import time
import os
import dns.resolver
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────

API_KEY = os.environ.get("RIPE_API_KEY", "your-api-key-here")
RUN_NAME = f"run_cdn_peering_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

PROBES = [
    (1016036, 'Cybernet (Haripur)'),
    (1016143, 'Cybernet (Karachi)'),
    (1016154, 'Cybernet (Karachi)'),
    (1014872, 'Fasttel (Islamabad)'),
    (60223,   'Nayatel (Islamabad)'),
    (65892,   'Nayatel (Islamabad)'),
    (1015679, 'Nova (Lahore)'),
    (64535,   'Orbit (Faisalabad)'),
    (1016126, 'PTCL (Karachi)'),
    (1016393, 'PTCL (Mianwali)'),
    (64078,   'TES (Rawalpindi)'),
    (64722,   'TES (Karachi)'),
    (62224,   'Transworld (Lahore)'),
    (7613,    'Zcom (Lahore)'),
]

TARGETS = [
    'google.com',
    'youtube.com',
    'facebook.com',
    'instagram.com',
    'akamai.com',
]

# CDN ASN sets for detection
CDN_ASNS = {
    'google':   {'15169', '139190', '139070', '45566', '36040'},
    'meta':     {'32934', '54115'},
    'akamai':   {'20940', '16625'},
}

# all CDN ASNs combined
ALL_CDN_ASNS = set()
for asns in CDN_ASNS.values():
    ALL_CDN_ASNS.update(asns)

RESULTS_DIR = os.path.join('experiments', '10_local_cdn_reach', 'results', RUN_NAME)
TIMESTAMP   = datetime.now().strftime('%Y%m%d_%H%M%S')
RESULTS_CSV = os.path.join(RESULTS_DIR, f'cdn_peering_{TIMESTAMP}.csv')
ROUTES_TXT  = os.path.join(RESULTS_DIR, f'routes_{TIMESTAMP}.txt')

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {"Authorization": f"Key {API_KEY}", "Content-Type": "application/json"}

RESULT_TIMEOUT = 1800

# ── ASN LOOKUP ────────────────────────────────────────────────────────────────

_asn_cache = {}

def asn_for_ip(ip):
    if ip in _asn_cache:
        return _asn_cache[ip]
    try:
        rev = '.'.join(reversed(ip.split('.')))
        ans = dns.resolver.resolve(f'{rev}.origin.asn.cymru.com', 'TXT', lifetime=5)
        for r in ans:
            parts = [x.strip() for x in str(r).strip('"').split('|')]
            asn = parts[0].strip().split()[0]
            cc  = parts[2].strip() if len(parts) > 2 else ''
            _asn_cache[ip] = (asn, cc)
            return asn, cc
    except Exception:
        pass
    _asn_cache[ip] = ('', '')
    return '', ''

def is_private(ip):
    return ip.startswith(('192.168.', '10.', '172.', '100.'))

# ── RIPE ATLAS ────────────────────────────────────────────────────────────────

def create_traceroute(probe_id, target, description):
    payload = {
        "definitions": [{
            "target":           target,
            "description":      description,
            "type":             "traceroute",
            "protocol":         "TCP",
            "port":             80,
            "af":               4,
            "paris":            16,
            "first_hop":        1,
            "max_hops":         32,
            "size":             48,
            "dont_fragment":    True,
            "resolve_on_probe": True,   # fresh DNS from probe location
        }],
        "probes": [{"type": "probes", "value": str(probe_id), "requested": 1}],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]

def wait_for_all(msm_ids, timeout=1800):
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

def check_probe_status(probes):
    """Query current RIPE Atlas connection status for all probes in one bulk
    call and split into (connected, disconnected). Probe connectivity
    fluctuates (see METHODOLOGY.md), so this is checked live rather than hardcoded —
    scheduling a traceroute on a disconnected probe is what produces the
    'No suitable probes' failures."""
    ids = ",".join(str(p[0]) for p in probes)
    r = requests.get(f"{BASE}/probes/", params={"id__in": ids, "page_size": 100}, timeout=15)
    r.raise_for_status()
    status_by_id = {p["id"]: p["status"]["name"] for p in r.json()["results"]}

    connected, disconnected = [], []
    for probe_id, label in probes:
        st = status_by_id.get(probe_id, "Unknown")
        if st == "Connected":
            connected.append((probe_id, label))
        else:
            disconnected.append((probe_id, label, st))
    return connected, disconnected

# ── ANALYSIS ──────────────────────────────────────────────────────────────────

def analyse(probe_label, target, raw):
    rows = []
    route_lines = []

    for result in raw:
        hops = result.get("result", [])
        dest_rtt        = None
        first_cdn_hop   = None
        path_exits_pk   = False
        last_pk_hop_rtt = None
        handoff_hop     = None   # last non-CDN public hop seen so far —
                                  # becomes the ISP→CDN handoff once a CDN hop is found

        route_lines.append(f"\n{'='*70}")
        route_lines.append(f"  {probe_label} → {target}")
        route_lines.append(f"{'='*70}")
        route_lines.append(f"  {'hop':<5} {'rtt':>8}  {'ip':<20} {'asn':<8} {'cc':<4} note")
        route_lines.append(f"  {'-'*65}")

        for hop in hops:
            hop_num = hop.get("hop", "?")
            replies = hop.get("result", [])
            chosen  = next((r for r in replies if "from" in r), None)

            if not chosen:
                route_lines.append(f"  {hop_num:<5} {'*':>8}  {'(no response)':<20}")
                continue

            ip  = chosen["from"]
            rtt = chosen.get("rtt", 0)

            if is_private(ip):
                route_lines.append(f"  {hop_num:<5} {rtt:>8.1f}  {ip:<20} {'':8} {'':4} private")
                continue

            asn, cc = asn_for_ip(ip)
            note = ""

            # check if this is a CDN hop
            if asn in ALL_CDN_ASNS and first_cdn_hop is None:
                first_cdn_hop = {
                    'hop_num': hop_num,
                    'ip':      ip,
                    'asn':     asn,
                    'cc':      cc,
                    'rtt':     rtt,
                    'handoff_ip':  handoff_hop['ip']  if handoff_hop else None,
                    'handoff_asn': handoff_hop['asn'] if handoff_hop else None,
                    'handoff_cc':  handoff_hop['cc']  if handoff_hop else None,
                    'handoff_rtt': handoff_hop['rtt'] if handoff_hop else None,
                }
                note = f"<<< FIRST CDN HOP ({asn})"
                if handoff_hop:
                    note += f"  [handoff: AS{handoff_hop['asn']} {handoff_hop['ip']}]"
            elif asn not in ALL_CDN_ASNS:
                # still on the ISP side of the path — track as the candidate handoff hop
                handoff_hop = {'hop_num': hop_num, 'ip': ip, 'asn': asn, 'cc': cc, 'rtt': rtt}

            # check if traffic exited Pakistan before hitting CDN
            if cc and cc != 'PK' and not is_private(ip):
                if rtt and rtt >= 40 and first_cdn_hop is None:
                    path_exits_pk = True
                    note = f"<<< EXITS PK (rtt={rtt:.0f}ms)"

            if cc == 'PK':
                last_pk_hop_rtt = rtt

            # record destination RTT
            if hop_num == max(h.get("hop", 0) for h in hops):
                dest_rtt = rtt

            route_lines.append(
                f"  {hop_num:<5} {rtt:>8.1f}  {ip:<20} {asn:<8} {cc:<4} {note}"
            )

        # determine if CDN was reached locally
        local_cdn = False
        if first_cdn_hop:
            if first_cdn_hop['cc'] == 'PK':
                local_cdn = True
            elif first_cdn_hop['rtt'] and first_cdn_hop['rtt'] < 20:
                local_cdn = True  # very low RTT suggests nearby even if CC wrong

        route_lines.append(f"\n  dest_rtt={dest_rtt}ms  first_cdn_asn={first_cdn_hop['asn'] if first_cdn_hop else 'none'}")
        route_lines.append(f"  first_cdn_cc={first_cdn_hop['cc'] if first_cdn_hop else 'none'}")
        route_lines.append(f"  first_cdn_rtt={first_cdn_hop['rtt'] if first_cdn_hop else 'none'}ms")
        route_lines.append(f"  handoff_asn={first_cdn_hop['handoff_asn'] if first_cdn_hop else 'none'}  handoff_ip={first_cdn_hop['handoff_ip'] if first_cdn_hop else 'none'}")
        route_lines.append(f"  path_exits_pk={path_exits_pk}  local_cdn={local_cdn}")

        rows.append({
            'probe_label':       probe_label,
            'target':            target,
            'dest_rtt_ms':       round(dest_rtt, 1) if dest_rtt else None,
            'first_cdn_hop_num': first_cdn_hop['hop_num'] if first_cdn_hop else None,
            'first_cdn_hop_ip':  first_cdn_hop['ip']      if first_cdn_hop else None,
            'first_cdn_hop_asn': first_cdn_hop['asn']     if first_cdn_hop else None,
            'first_cdn_hop_cc':  first_cdn_hop['cc']      if first_cdn_hop else None,
            'first_cdn_hop_rtt': round(first_cdn_hop['rtt'], 1) if first_cdn_hop else None,
            'handoff_asn':       first_cdn_hop['handoff_asn'] if first_cdn_hop else None,
            'handoff_ip':        first_cdn_hop['handoff_ip']  if first_cdn_hop else None,
            'handoff_cc':        first_cdn_hop['handoff_cc']  if first_cdn_hop else None,
            'handoff_rtt':       round(first_cdn_hop['handoff_rtt'], 1) if first_cdn_hop and first_cdn_hop['handoff_rtt'] else None,
            'path_exits_pk':     path_exits_pk,
            'local_cdn':         local_cdn,
        })

    return rows, '\n'.join(route_lines)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  Experiment 10 — CDN Peering Local Reach")
    print("=" * 70)
    print(f"\n  Probes:  {len(PROBES)} configured")
    print(f"  Targets: {TARGETS}")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    # preflight: skip probes that are currently disconnected — scheduling a
    # traceroute on one is exactly what produces "No suitable probes"
    print(f"\n[0] Checking probe connection status...")
    active_probes, offline_probes = check_probe_status(PROBES)
    for probe_id, probe_label, st in offline_probes:
        print(f"  SKIP  {probe_label:<25} (id {probe_id}): {st}")
    print(f"  {len(active_probes)}/{len(PROBES)} probes connected")

    # schedule
    print(f"\n[1] Scheduling measurements...")
    scheduled = []
    for probe_id, probe_label in active_probes:
        for target in TARGETS:
            try:
                mid = create_traceroute(probe_id, target, f"{probe_label}→{target}")
                scheduled.append((mid, probe_id, probe_label, target))
                print(f"  {probe_label:<25} → {target:<20} ID: {mid}")
                time.sleep(2.0)
            except requests.HTTPError as e:
                print(f"  ERROR {probe_label} → {target}: {e.response.status_code} — {e.response.text[:100]}")

    # wait
    print(f"\n[2] Waiting for {len(scheduled)} measurements...")
    completed = wait_for_all([mid for mid, _, _, _ in scheduled], RESULT_TIMEOUT)

    # analyse
    print(f"\n[3] Analysing results...")
    all_rows   = []
    all_routes = []

    for mid, probe_id, probe_label, target in scheduled:
        if mid not in completed:
            continue
        raw = fetch_result(mid)
        rows, route_text = analyse(probe_label, target, raw)
        all_rows.extend(rows)
        all_routes.append(route_text)

        for row in rows:
            local = "LOCAL" if row['local_cdn'] else "international"
            print(f"  {probe_label:<25} → {target:<20} {local:<15} rtt={row['dest_rtt_ms']}ms  first_cdn_cc={row['first_cdn_hop_cc']}")

    # save CSV
    fields = ['probe_label','target','dest_rtt_ms','first_cdn_hop_num',
              'first_cdn_hop_ip','first_cdn_hop_asn','first_cdn_hop_cc',
              'first_cdn_hop_rtt','handoff_asn','handoff_ip','handoff_cc',
              'handoff_rtt','path_exits_pk','local_cdn']

    with open(RESULTS_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n  CSV → {RESULTS_CSV}")

    # save routes
    with open(ROUTES_TXT, 'w') as f:
        f.write(f"Exp 10 — CDN Peering Local Reach — {TIMESTAMP}\n")
        f.write('\n'.join(all_routes))
    print(f"  Routes → {ROUTES_TXT}")

    # summary
    print(f"\n{'='*70}")
    print("  SUMMARY — Local CDN reach by probe and target")
    print(f"{'='*70}")
    print(f"  {'Probe':<25} {'Target':<20} {'Local':<8} {'Dest RTT':>10}  First CDN CC")
    print(f"  {'-'*70}")
    for row in sorted(all_rows, key=lambda x: (x['target'], x['probe_label'])):
        local = "YES" if row['local_cdn'] else "no"
        print(f"  {row['probe_label']:<25} {row['target']:<20} {local:<8} {str(row['dest_rtt_ms'])+'ms':>10}  {row['first_cdn_hop_cc'] or 'unknown'}")

    # PoP comparison — for each target, which distinct CDN nodes/handoffs did
    # different ISPs land on? Answers "same domain, different PoP by ISP?"
    print(f"\n{'='*70}")
    print("  CDN PoP comparison by target (per-ISP handoff + PoP reached)")
    print(f"{'='*70}")
    pop_fields = ['target', 'probe_label', 'first_cdn_hop_ip', 'first_cdn_hop_asn',
                  'first_cdn_hop_cc', 'first_cdn_hop_rtt', 'handoff_asn', 'handoff_ip']
    pop_rows = [
        {k: row[k] for k in pop_fields}
        for row in all_rows if row['first_cdn_hop_ip']
    ]
    for target in TARGETS:
        rows_for_target = [r for r in pop_rows if r['target'] == target]
        pops = sorted({(r['first_cdn_hop_ip'], r['first_cdn_hop_cc']) for r in rows_for_target})
        print(f"\n  {target}  —  {len(pops)} distinct CDN PoP(s) across {len(rows_for_target)} responding probes")
        for r in sorted(rows_for_target, key=lambda x: x['probe_label']):
            print(f"    {r['probe_label']:<25} PoP={r['first_cdn_hop_ip']:<16} cc={r['first_cdn_hop_cc'] or '?':<4} "
                  f"rtt={r['first_cdn_hop_rtt']}ms  handoff=AS{r['handoff_asn'] or '?'} {r['handoff_ip'] or ''}")

    pop_csv = os.path.join(RESULTS_DIR, f'cdn_pop_comparison_{TIMESTAMP}.csv')
    with open(pop_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=pop_fields)
        writer.writeheader()
        writer.writerows(sorted(pop_rows, key=lambda x: (x['target'], x['probe_label'])))
    print(f"\n  PoP comparison CSV → {pop_csv}")

if __name__ == "__main__":
    main()