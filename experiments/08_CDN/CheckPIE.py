#!/usr/bin/env python3
"""
Experiment 08.1 — PIE Karachi: PTCL + Nayatel → ACE CDN
=========================================================
Tests whether PIE Karachi peering LAN (58.181.127.x) appears
when PTCL Karachi traces to ACE CDN (AS139341 / Tencent EdgeOne).

Run from repo root:
    python3 experiments/08_CDN/exp08_1_pie_ace_cdn.py
"""

import requests, csv, time, os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

API_KEY  = os.environ.get("RIPE_API_KEY", "your-api-key-here")
RUN_NAME = "run_pie_karachi_ace_cdn"

PROBES = [
    (1016126, 17557, "Pakistan", "PTCL Karachi"),
    (60223,   23674, "Pakistan", "Nayatel ISB"),
]

TARGETS = [
    {"ip": "43.132.69.1",   "label": "ACE-CDN-1",   "asn": "139341"},
    {"ip": "43.132.69.2",   "label": "ACE-CDN-2",   "asn": "139341"},
    {"ip": "43.132.69.100", "label": "ACE-CDN-100",  "asn": "139341"},
]

IXP_LAN      = "58.181.127."
IXP_NAME     = "PIE Karachi"
PTCL_PIE_IP  = "58.181.127.1"
ACE_CDN_IP   = "58.181.127.4"

RESULT_TIMEOUT = 1800
RESULTS_DIR    = os.path.join("experiments", "08_CDN", "results", RUN_NAME)
TIMESTAMP      = datetime.now().strftime("%Y%m%d_%H%M%S")
ROUTES_FILE    = os.path.join(RESULTS_DIR, f"routes_{TIMESTAMP}.txt")
SUMMARY_FILE   = os.path.join(RESULTS_DIR, f"summary_{TIMESTAMP}.csv")

BASE = "https://atlas.ripe.net/api/v2"
HDR  = {"Authorization": f"Key {API_KEY}", "Content-Type": "application/json"}

def create_traceroute(probe_id, target_ip, description):
    payload = {
        "definitions": [{"target": target_ip, "description": description,
            "type": "traceroute", "protocol": "ICMP", "af": 4,
            "paris": 16, "first_hop": 1, "max_hops": 32,
            "size": 48, "dont_fragment": True, "resolve_on_probe": False}],
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
                    if sname == "Stopped": done.add(mid)
                    else:
                        failed.add(mid)
                        print(f"\n  FAILED msm {mid}: {sname}")
            except: pass
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
    lines, ixp_found, dest_rtt = [], False, None
    for result in raw:
        lines.append(f"\n{'='*60}\n  {probe_desc} → {target['ip']} ({target['label']})\n{'='*60}")
        lines.append(f"  {'hop':<5} {'rtt(ms)':<10} {'ip':<22} note")
        lines.append(f"  {'-'*60}")
        for hop in result.get("result", []):
            hop_num = hop.get("hop", "?")
            chosen  = next((r for r in hop.get("result", []) if "from" in r), None)
            if not chosen:
                lines.append(f"  {hop_num:<5} {'*':<10} {'(no response)':<22}")
                continue
            ip, rtt = chosen["from"], chosen.get("rtt", 0)
            if ip == target["ip"]: dest_rtt = rtt
            note = ""
            if ip.startswith(IXP_LAN): note = f"<<< {IXP_NAME} LAN"; ixp_found = True
            if ip == PTCL_PIE_IP:      note = "<<< PTCL PIE router"
            if ip == ACE_CDN_IP:       note = "<<< ACE CDN PIE router"
            lines.append(f"  {hop_num:<5} {rtt:<10.1f} {ip:<22} {note}")
    verdict = f"{IXP_NAME} USED" if ixp_found else f"{IXP_NAME} NOT SEEN"
    lines.append(f"\n  Destination RTT: {dest_rtt:.1f}ms" if dest_rtt else "\n  Destination RTT: N/A")
    lines.append(f"  VERDICT: {verdict}")
    return "\n".join(lines), ixp_found, dest_rtt

def main():
    print("=" * 60)
    print(f"  Experiment 08.1 — {IXP_NAME}: PTCL + Nayatel → ACE CDN")
    print("=" * 60)
    print(f"\n  Watching for {IXP_NAME} LAN ({IXP_LAN}x)")
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
    completed = wait_for_all([mid for mid, _, _, _ in scheduled], RESULT_TIMEOUT)
    print(f"\n[3] Analysing results...")
    all_routes, summary = [], []
    for mid, probe_id, desc, t in scheduled:
        if mid not in completed: continue
        route_text, ixp_found, dest_rtt = analyse(desc, t, fetch_result(mid))
        all_routes.append(route_text)
        summary.append({"probe": desc, "probe_id": probe_id, "target_ip": t["ip"],
            "target_label": t["label"], "dest_rtt_ms": round(dest_rtt, 1) if dest_rtt else None,
            "ixp_found": ixp_found, "measurement_id": mid})
        print(f"  {desc} → {t['ip']}: {'IXP FOUND' if ixp_found else 'no IXP'} RTT={f'{dest_rtt:.1f}ms' if dest_rtt else 'N/A'}")
    with open(ROUTES_FILE, "w") as f:
        f.write(f"Exp 08.1 — {IXP_NAME} ACE CDN — {TIMESTAMP}\n" + "\n".join(all_routes))
    with open(SUMMARY_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["probe","probe_id","target_ip","target_label","dest_rtt_ms","ixp_found","measurement_id"])
        writer.writeheader(); writer.writerows(summary)
    print(f"\n  Routes → {ROUTES_FILE}\n  Summary → {SUMMARY_FILE}")
    print(f"\n{'='*60}\n  FINAL RESULTS\n{'='*60}")
    for row in summary:
        verdict = f"{IXP_NAME} USED ✓" if row["ixp_found"] else "IXP not seen ✗"
        print(f"  {row['probe']:<25} → {row['target_ip']:<18} RTT={str(row['dest_rtt_ms'])+'ms':<10} {verdict}")

if __name__ == "__main__":
    main()