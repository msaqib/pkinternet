#!/usr/bin/env python3
"""
Experiment 08 — ACE CDN All Probes
====================================
Traces from all probes to ACE CDN (AS139341) to measure
RTT inequality between ISPs with and without PTCL upstream.

Run from repo root:
    python3 experiments/08_CDN/run.py
"""

import requests
import csv
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.environ.get("RIPE_API_KEY", "your-api-key-here")
RUN_NAME = "run_ace_cdn_all_probes"

PROBES = [
    (7613,    152605, "Pakistan", "Zcom Lahore"),
    (1015679, 136174, "Pakistan", "Nova Lahore"),
    (1016036,   9541, "Pakistan", "Cybernet Hrp"),
    (62224,   38193,  "Pakistan", "Transworld Lhe"),
    (7764,    17557,  "Pakistan", "PTCL Lahore"),
    (1016126, 17557,  "Pakistan", "PTCL Karachi"),
    (60223,   23674,  "Pakistan", "Nayatel ISB"),
]

TARGETS = [
    {"ip": "43.132.69.1",   "label": "ACE-CDN-1", "asn": "139341"},
    {"ip": "43.132.69.2",   "label": "ACE-CDN-2", "asn": "139341"},
]

# IXP peering LAN IPs to watch for
PIE_KARACHI_LAN  = "58.181.127."
PKIX_LAHORE_LAN  = "100.128.0."
PTCL_PIE_IP      = "58.181.127.1"
ACE_CDN_PIE_IP   = "58.181.127.4"

RESULT_TIMEOUT = 1800
RESULTS_DIR    = os.path.join("experiments", "08_CDN", "results", RUN_NAME)
TIMESTAMP      = datetime.now().strftime("%Y%m%d_%H%M%S")
ROUTES_FILE    = os.path.join(RESULTS_DIR, f"routes_{TIMESTAMP}.txt")
SUMMARY_FILE   = os.path.join(RESULTS_DIR, f"summary_{TIMESTAMP}.csv")

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {
    "Authorization": f"Key {API_KEY}",
    "Content-Type":  "application/json",
}

def create_traceroute(probe_id, target_ip, description):
    payload = {
        "definitions": [{
            "target":           target_ip,
            "description":      description,
            "type":             "traceroute",
            "protocol":         "ICMP",
            "af":               4,
            "paris":            16,
            "first_hop":        1,
            "max_hops":         32,
            "size":             48,
            "dont_fragment":    True,
            "resolve_on_probe": False,
        }],
        "probes": [{
            "type":      "probes",
            "value":     str(probe_id),
            "requested": 1,
        }],
        "is_oneoff": True,
    }
    r = requests.post(f"{BASE}/measurements/", headers=HDR, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()["measurements"][0]

def wait_for_all(msm_ids, timeout=1800):
    pending  = set(msm_ids)
    done     = set()
    failed   = set()
    deadline = time.time() + timeout

    print(f"  Polling {len(pending)} measurements", end="", flush=True)
    while pending and time.time() < deadline:
        for mid in list(pending):
            try:
                r = requests.get(f"{BASE}/measurements/{mid}/", headers=HDR, timeout=10)
                r.raise_for_status()
                status = r.json().get("status", {})
                sid, sname = status.get("id", 0), status.get("name", "")
                if sid >= 4 or sname == "Stopped":
                    pending.remove(mid)
                    if sname == "Stopped":
                        done.add(mid)
                    else:
                        failed.add(mid)
                        print(f"\n  FAILED msm {mid}: status={sname} (id={sid})")
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

def analyse(probe_desc, target, raw):
    lines = []
    pie_found  = False
    pkix_found = False
    min_rtt    = None

    for result in raw:
        hops = result.get("result", [])
        lines.append(f"\n{'='*60}")
        lines.append(f"  {probe_desc} → {target['ip']} ({target['label']})")
        lines.append(f"{'='*60}")
        lines.append(f"  {'hop':<5} {'rtt(ms)':<10} {'ip':<22} note")
        lines.append(f"  {'-'*60}")

        for hop in hops:
            hop_num = hop.get("hop", "?")
            replies = hop.get("result", [])
            chosen  = next((r for r in replies if "from" in r), None)

            if chosen is None:
                lines.append(f"  {hop_num:<5} {'*':<10} {'(no response)':<22}")
                continue

            ip  = chosen["from"]
            rtt = chosen.get("rtt", 0)

            if ip == target['ip']:
                min_rtt = rtt

            note = ""
            if ip.startswith(PIE_KARACHI_LAN):
                note = "<<< PIE KARACHI LAN"
                pie_found = True
            if ip.startswith(PKIX_LAHORE_LAN):
                note = "<<< PKIX LAHORE LAN"
                pkix_found = True
            if ip == PTCL_PIE_IP:
                note = "<<< PTCL PIE router"
            if ip == ACE_CDN_PIE_IP:
                note = "<<< ACE CDN PIE router"

            lines.append(f"  {hop_num:<5} {rtt:<10.1f} {ip:<22} {note}")

    verdict = []
    if pie_found:
        verdict.append("PIE KARACHI USED")
    if pkix_found:
        verdict.append("PKIX LAHORE USED")
    if not pie_found and not pkix_found:
        verdict.append("no IXP seen")

    lines.append(f"\n  RTT to destination: {min_rtt:.1f}ms" if min_rtt else "\n  RTT: N/A")
    lines.append(f"  VERDICT: {', '.join(verdict)}")
    return "\n".join(lines), pie_found, pkix_found, min_rtt

def main():
    print("=" * 60)
    print("  Experiment 08 — ACE CDN RTT across all probes")
    print("=" * 60)
    print(f"\n  Watching for PIE Karachi ({PIE_KARACHI_LAN}x)")
    print(f"  Watching for PKIX Lahore ({PKIX_LAHORE_LAN}x)")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"\n[1] Scheduling {len(PROBES)} probes × {len(TARGETS)} targets...")
    scheduled = []
    for probe_id, asn, city, desc in PROBES:
        for t in TARGETS:
            try:
                mid = create_traceroute(probe_id, t["ip"], f"{desc}→{t['label']}")
                scheduled.append((mid, probe_id, desc, t))
                print(f"  {desc} → {t['ip']}  ID: {mid}")
                time.sleep(2.0)
            except requests.HTTPError as e:
                print(f"  ERROR {desc} → {t['ip']}: {e.response.status_code} — {e.response.text[:150]}")

    print(f"\n[2] Waiting for {len(scheduled)} measurements...")
    all_ids   = [mid for mid, _, _, _ in scheduled]
    completed = wait_for_all(all_ids, RESULT_TIMEOUT)

    print(f"\n[3] Analysing results...")
    all_routes = []
    summary    = []

    for mid, probe_id, desc, t in scheduled:
        if mid not in completed:
            continue
        raw = fetch_result(mid)
        route_text, pie_found, pkix_found, min_rtt = analyse(desc, t, raw)
        all_routes.append(route_text)
        summary.append({
            "probe":        desc,
            "probe_id":     probe_id,
            "target_ip":    t["ip"],
            "target_label": t["label"],
            "min_rtt_ms":   round(min_rtt, 1) if min_rtt else None,
            "pie_found":    pie_found,
            "pkix_found":   pkix_found,
            "measurement_id": mid,
        })
        rtt_str = f"{min_rtt:.1f}ms" if min_rtt else "N/A"
        print(f"  {desc:<25} → {t['ip']:<18} RTT={rtt_str:<10} {'PIE' if pie_found else '   '} {'PKIX' if pkix_found else ''}")

    with open(ROUTES_FILE, "w") as f:
        f.write(f"ACE CDN All Probes Experiment — {TIMESTAMP}\n")
        f.write("\n".join(all_routes))
    print(f"\n  Routes → {ROUTES_FILE}")

    with open(SUMMARY_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "probe","probe_id","target_ip","target_label",
            "min_rtt_ms","pie_found","pkix_found","measurement_id"
        ])
        writer.writeheader()
        writer.writerows(summary)
    print(f"  Summary → {SUMMARY_FILE}")

    print(f"\n{'='*60}")
    print("  RTT COMPARISON — ACE CDN (AS139341)")
    print(f"{'='*60}")
    print(f"  {'Probe':<25} {'Target':<18} {'RTT':>8}  IXP")
    print(f"  {'-'*60}")
    for row in sorted(summary, key=lambda x: x['min_rtt_ms'] or 999):
        rtt = f"{row['min_rtt_ms']}ms" if row['min_rtt_ms'] else "N/A"
        ixp = "PIE" if row['pie_found'] else ("PKIX" if row['pkix_found'] else "none")
        print(f"  {row['probe']:<25} {row['target_ip']:<18} {rtt:>8}  {ixp}")

if __name__ == "__main__":
    main()